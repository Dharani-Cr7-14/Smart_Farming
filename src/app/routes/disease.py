from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
import shutil
import os
import sys

# Setup relative paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from services.auth_service import get_current_user
from services.disease_service import run_disease_inference, generate_disease_visualizations, has_disease_model
from models.database import add_disease_prediction
from utils.translations import get_lang_dict
from routes.templates import templates

router = APIRouter(tags=["disease"])

@router.get("/disease_dashboard", response_class=HTMLResponse)
async def disease_dashboard_get(request: Request, lang: str = "en"):
    """Render leaf disease detector view. Verification redirects to login if unauthenticated."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    lang_dict = get_lang_dict(lang)
    
    error_msg = None
    if not has_disease_model():
        from utils.config import USE_MOCK_MODELS
        if USE_MOCK_MODELS:
            error_msg = "Plant disease classification model is not loaded. Ensure models are trained."
        else:
            error_msg = "Prediction model is currently unavailable. Please contact the administrator."
            
    return templates.TemplateResponse(request=request, name="disease.html", context={"request": request, "prediction": None, "lang": lang, "lang_dict": lang_dict, "user": user, "error": error_msg})

@router.post("/disease_dashboard", response_class=HTMLResponse)
async def disease_dashboard_post(request: Request, file: UploadFile = File(...), lang: str = Form("en")):
    """Uploads a plant leaf image, triggers CNN/ResNet classification, logs records, writes Plotly charts."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    lang_dict = get_lang_dict(lang)
    
    if not has_disease_model():
        from utils.config import USE_MOCK_MODELS
        error_msg = "Plant disease classification model is not loaded. Ensure models are trained." if USE_MOCK_MODELS else "Prediction model is currently unavailable. Please contact the administrator."
        return templates.TemplateResponse(
            request=request,
            name="disease.html",
            context={
                "request": request,
                "prediction": None,
                "error": error_msg,
                "lang": lang,
                "lang_dict": lang_dict,
                "user": user
            }
        )

    upload_folder = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)

    try:
        # Save image locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Trigger leaf inference
        predicted_class, confidence = run_disease_inference(file_path)
        
        # Save log in database
        add_disease_prediction(
            user_id=user['id'],
            image_name=file.filename,
            predicted_class=predicted_class,
            confidence=confidence
        )
        
        # Output Plotly visualization charts
        generate_disease_visualizations(predicted_class, confidence)
        
        prediction_result = {
            "pred_class": predicted_class,
            "confidence": confidence,
            "image_path": f"/static/uploads/{file.filename}"
        }
        
        return templates.TemplateResponse(
            request=request,
            name="disease.html",
            context={
                "request": request,
                "prediction": prediction_result,
                "lang": lang,
                "lang_dict": lang_dict,
                "user": user,
                "error": None
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="disease.html",
            context={
                "request": request,
                "prediction": None,
                "error": f"Image processing failed: {str(e)}",
                "lang": lang,
                "lang_dict": lang_dict,
                "user": user
            }
        )
