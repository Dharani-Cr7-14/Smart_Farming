import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


class WeatherServiceError(Exception):
    """Raised when the weather provider cannot return current conditions."""


def get_current_weather(latitude: float, longitude: float) -> dict:
    """Fetch current temperature, humidity, and precipitation for a coordinate."""
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
    request = Request(
        f"https://api.open-meteo.com/v1/forecast?{query}",
        headers={"Accept": "application/json", "User-Agent": "smart-farming/1.0"},
    )
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise WeatherServiceError("The weather provider is unavailable.") from exc

    if not isinstance(payload, dict):
        raise WeatherServiceError("The weather provider returned an invalid response.")

    current = payload.get("current")
    daily = payload.get("daily")
    if not isinstance(current, dict) or not isinstance(daily, dict):
        raise WeatherServiceError("The weather provider returned an invalid response.")

    try:
        timezone = payload.get("timezone")
        local_today = datetime.now(ZoneInfo(timezone)).date() if timezone else datetime.now().date()
        daily_dates = daily["time"]
        daily_rainfall = daily["precipitation_sum"]
        month_values = [
            float(amount)
            for date, amount in zip(daily_dates, daily_rainfall)
            if datetime.fromisoformat(date).date() <= local_today
        ][-30:]
        if len(month_values) < 30:
            raise WeatherServiceError("The weather provider returned insufficient rainfall history.")
        return {
            "temperature": float(current["temperature_2m"]),
            "humidity": float(current["relative_humidity_2m"]),
            "current_rainfall": float(current["rain"]),
            "precipitation": float(current["precipitation"]),
            "rainfall_30d": round(sum(month_values), 1),
            "weather_code": int(current["weather_code"]),
            "time": current.get("time"),
            "timezone": timezone,
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherServiceError("The weather provider returned incomplete data.") from exc
