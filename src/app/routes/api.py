from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from models.database import get_chat_messages, get_crop_predictions, get_disease_predictions
from services.auth_service import get_current_user
from services.weather_service import WeatherServiceError, get_current_weather

router = APIRouter(prefix="/api", tags=["react-api"])


@router.get("/session")
async def session(request: Request):
    return {"user": get_current_user(request)}


@router.get("/weather")
async def weather(
    request: Request,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    if not get_current_user(request):
        return JSONResponse({"error": "Session expired"}, status_code=401)
    try:
        return get_current_weather(latitude, longitude)
    except WeatherServiceError as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)


@router.get("/history")
async def history(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Session expired"}, status_code=401)
    return {
        "crop_logs": get_crop_predictions(user["id"], limit=50),
        "disease_logs": get_disease_predictions(user["id"], limit=50),
        "chat_logs": get_chat_messages(user["id"], limit=50),
    }