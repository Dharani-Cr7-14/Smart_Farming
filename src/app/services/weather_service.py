import json
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


class WeatherServiceError(Exception):
    """Raised when the weather provider cannot return current conditions."""


def _fetch_weather_payload(url: str) -> dict:
    for attempt in range(3):
        request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "smart-farming/1.0"},
        )
        try:
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise WeatherServiceError("The Open-Meteo weather provider is unavailable.") from exc
            time.sleep(1 << attempt)
            continue
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == 2:
                raise WeatherServiceError("The Open-Meteo weather provider is unavailable.") from exc
            time.sleep(1 << attempt)
            continue

        if not isinstance(payload, dict) or payload.get("error") is True:
            if attempt == 2:
                reason = payload.get("reason") if isinstance(payload, dict) else None
                message = f"Open-Meteo: {reason}" if reason else "The Open-Meteo weather provider returned an invalid response."
                raise WeatherServiceError(message)
            time.sleep(1 << attempt)
            continue
        return payload

    raise WeatherServiceError("The Open-Meteo weather provider is unavailable.")


def get_current_weather(latitude: float, longitude: float) -> dict:
    """Fetch live conditions and rainfall from Open-Meteo for a coordinate."""
    query = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code",
        "daily": "precipitation_sum",
        "past_days": 30,
        "forecast_days": 1,
        "temperature_unit": "celsius",
        "timezone": "auto",
    })
    payload = _fetch_weather_payload(f"https://api.open-meteo.com/v1/forecast?{query}")
    current = payload.get("current")
    daily = payload.get("daily")
    if not isinstance(current, dict) or not isinstance(daily, dict):
        raise WeatherServiceError("Open-Meteo returned an invalid weather response.")

    try:
        timezone = payload.get("timezone")
        local_today = datetime.now(ZoneInfo(timezone)).date() if timezone else datetime.now().date()
        rainfall = [
            float(amount)
            for date, amount in zip(daily["time"], daily["precipitation_sum"])
            if datetime.fromisoformat(date).date() <= local_today
        ][-30:]
        if len(rainfall) < 30:
            raise WeatherServiceError("Open-Meteo returned insufficient rainfall history.")
        return {
            "temperature": float(current["temperature_2m"]),
            "humidity": float(current["relative_humidity_2m"]),
            "current_rainfall": float(current["rain"]),
            "precipitation": float(current["precipitation"]),
            "rainfall_30d": round(sum(rainfall), 1),
            "rainfall_history_available": True,
            "weather_code": int(current["weather_code"]),
            "time": current.get("time"),
            "timezone": timezone,
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherServiceError("Open-Meteo returned incomplete weather data.") from exc
