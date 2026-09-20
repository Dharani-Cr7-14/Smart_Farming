from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from models.database import get_chat_messages, get_crop_predictions, get_disease_predictions
from services.auth_service import get_current_user

router = APIRouter(prefix="/api", tags=["react-api"])


@router.get("/session")
async def session(request: Request):
    return {"user": get_current_user(request)}


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