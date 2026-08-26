from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import sys

# Add src and src/app to Python path to support easy module importing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "..")))

from routes.templates import templates
from routes import auth, crop, disease, chatbot, history
from services.auth_service import get_current_user
from models.database import get_crop_predictions, get_disease_predictions
from utils.translations import get_lang_dict

app = FastAPI(title="Smart Farming Decision Support System", description="AI-Powered Smart Farming Decision Support System")

# Mount static folder
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Register routers
app.include_router(auth.router)
app.include_router(crop.router)
app.include_router(disease.router)
app.include_router(chatbot.router)
app.include_router(history.router)

@app.get("/", response_class=HTMLResponse)
async def home_get(request: Request, lang: str = "en"):
    """Dashboard homepage. Redirects to login page if user session is invalid."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login?lang=" + lang, status_code=303)
        
    lang_dict = get_lang_dict(lang)
    
    # Query short logs for summary cards
    crop_logs = get_crop_predictions(user['id'], limit=5)
    disease_logs = get_disease_predictions(user['id'], limit=5)
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "crop_logs": crop_logs,
            "disease_logs": disease_logs,
            "lang": lang,
            "lang_dict": lang_dict,
            "user": user,
            "active_page": "dashboard"
        }
    )

@app.on_event("startup")
async def startup_event():
    """Verify loading status of models and chatbot connection, outputting status to console logs."""
    from services.crop_service import has_crop_models
    from services.disease_service import has_disease_model
    from services.chatbot_service import ollama_client
    from utils.config import OLLAMA_MODEL
    
    crop_status = "READY" if has_crop_models() else "NOT AVAILABLE"
    disease_status = "READY" if has_disease_model() else "NOT AVAILABLE"
    
    chatbot_status = "READY"
    if ollama_client is None:
        chatbot_status = "NOT AVAILABLE"
    else:
        try:
            res = ollama_client.list()
            models = getattr(res, 'models', None)
            if models is None:
                models = res.get('models', [])
            
            downloaded_models = []
            for m in models:
                name = getattr(m, 'name', None)
                if name is None:
                    name = m.get('name', '')
                downloaded_models.append(name.strip())
                
            configured = OLLAMA_MODEL.strip()
            match = False
            for m in downloaded_models:
                if configured in m or m in configured:
                    match = True
                    break
            if not match:
                chatbot_status = "NOT AVAILABLE"
        except Exception:
            chatbot_status = "NOT AVAILABLE"
            
    print("\n" + "="*50)
    print("🔍 SMART FARMING DECISION SUPPORT SYSTEM — MODEL HEALTH CHECK:")
    print(f"Crop Model: {crop_status}")
    print(f"Disease Model: {disease_status}")
    print(f"Chatbot: {chatbot_status}")
    print("="*50 + "\n")

@app.get("/model_health")
async def model_health():
    """Retrieve loading status of models and chatbot connection."""
    from services.crop_service import has_crop_models
    from services.disease_service import has_disease_model
    from services.chatbot_service import ollama_client
    from utils.config import OLLAMA_MODEL
    
    crop_status = "READY" if has_crop_models() else "NOT AVAILABLE"
    disease_status = "READY" if has_disease_model() else "NOT AVAILABLE"
    
    chatbot_status = "READY"
    if ollama_client is None:
        chatbot_status = "NOT AVAILABLE"
    else:
        try:
            res = ollama_client.list()
            models = getattr(res, 'models', None)
            if models is None:
                models = res.get('models', [])
            
            downloaded_models = []
            for m in models:
                name = getattr(m, 'name', None)
                if name is None:
                    name = m.get('name', '')
                downloaded_models.append(name.strip())
                
            configured = OLLAMA_MODEL.strip()
            match = False
            for m in downloaded_models:
                if configured in m or m in configured:
                    match = True
                    break
            if not match:
                chatbot_status = "NOT AVAILABLE"
        except Exception:
            chatbot_status = "NOT AVAILABLE"
            
    return {
        "crop_model": crop_status,
        "disease_model": disease_status,
        "chatbot": chatbot_status
    }