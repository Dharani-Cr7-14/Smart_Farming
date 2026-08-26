from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import sys
import os

# Setup relative paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from services.auth_service import get_current_user
from models.database import get_crop_predictions, get_disease_predictions, get_chat_messages
from utils.translations import get_lang_dict
from routes.templates import templates

router = APIRouter(tags=["history"])

@router.get("/history", response_class=HTMLResponse)
async def history_get(request: Request, lang: str = "en"):
    """Query logs from SQLite and render the history tables."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login?lang=" + lang, status_code=303)
    lang_dict = get_lang_dict(lang)
    
    # Fetch recent predictions logged under the authenticated farmer ID
    crop_logs = get_crop_predictions(user['id'], limit=50)
    disease_logs = get_disease_predictions(user['id'], limit=50)
    chat_logs = get_chat_messages(user['id'], limit=50)
    
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "request": request,
            "crop_logs": crop_logs,
            "disease_logs": disease_logs,
            "chat_logs": chat_logs,
            "lang": lang,
            "lang_dict": lang_dict,
            "user": user
        }
    )
