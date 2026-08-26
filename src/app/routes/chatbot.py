from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import sys
import os

# Setup relative paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from services.auth_service import get_current_user
from services.chatbot_service import get_chatbot_reply, CHAT_HISTORY_DB
from models.database import add_chat_message
from utils.translations import get_lang_dict
from routes.templates import templates

router = APIRouter(tags=["chatbot"])

@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_get(request: Request, lang: str = "en"):
    """Render agricultural AI Chat Assistant view."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login?lang=" + lang, status_code=303)
    lang_dict = get_lang_dict(lang)
    return templates.TemplateResponse(request=request, name="chatbot.html", context={"request": request, "lang": lang, "lang_dict": lang_dict, "user": user})

@router.post("/chatbot_message")
async def chatbot_message_post(request: Request, user_message: str = Form(...), lang: str = Form("en")):
    """Exposes AJAX endpoint querying Ollama. Blocks unregistered calls."""
    user = get_current_user(request)
    if not user:
        return JSONResponse({"reply": "Session expired. Please log in again."}, status_code=401)
    
    user_id = user['id']
    
    # 1. Fetch user's conversation history from CHAT_HISTORY_DB (limited to last 6 messages)
    history = CHAT_HISTORY_DB.get(user_id, [])
    history = history[-6:]
    
    # 2. Get AI reply
    reply = get_chatbot_reply(user_message, lang, history)
    
    # 3. Only append and log if reply was successfully generated (no offline/connection errors)
    if not reply.startswith("Error:"):
        # Append exchange to memory
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        CHAT_HISTORY_DB[user_id] = history[-6:]
        
        # Log to database
        add_chat_message(user_id, "user", user_message, lang)
        add_chat_message(user_id, "assistant", reply, lang)
        
    return JSONResponse({"reply": reply})
