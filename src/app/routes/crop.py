from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sys
import os

# Set paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from services.auth_service import get_current_user
from services.crop_service import recommend_seeds, has_crop_models
from models.database import add_crop_prediction
from utils.translations import get_lang_dict
from routes.templates import templates

router = APIRouter(tags=["crop"])

@router.get("/seed_dashboard", response_class=HTMLResponse)
async def seed_dashboard_get(request: Request, lang: str = "en"):
    """Render seed recommendation dashboard. Rejection routes back to login on missing session."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    lang_dict = get_lang_dict(lang)
    
    error_msg = None
    if not has_crop_models():
        from utils.config import USE_MOCK_MODELS
        if USE_MOCK_MODELS:
            error_msg = "Crop/Seed recommendation models are not loaded on server. Please train models first."
        else:
            error_msg = "Prediction model is currently unavailable. Please contact the administrator."
            
    return templates.TemplateResponse(request=request, name="crop.html", context={"request": request, "prediction": None, "lang": lang, "lang_dict": lang_dict, "user": user, "error": error_msg})

@router.post("/seed_dashboard", response_class=HTMLResponse)
async def seed_dashboard_post(
    request: Request,
    pH: str = Form(...),
    N: str = Form(...),
    P: str = Form(...),
    K: str = Form(...),
    Temp: str = Form(...),
    Rainfall: str = Form(...),
    Humidity: str = Form(...),
    Season_Duration: str = Form(...),
    Soil_Type: str = Form(...),
    Region: str = Form(...),
    lang: str = Form("en")
):
    """Processes agricultural soil entries, saves logs in database, and renders views with recommendations."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    lang_dict = get_lang_dict(lang)
    
    if not has_crop_models():
        from utils.config import USE_MOCK_MODELS
        error_msg = "Crop/Seed recommendation models are not loaded on server. Please train models first." if USE_MOCK_MODELS else "Prediction model is currently unavailable. Please contact the administrator."
        return templates.TemplateResponse(
            request=request,
            name="crop.html",
            context={
                "request": request,
                "prediction": None,
                "error": error_msg,
                "lang": lang,
                "lang_dict": lang_dict,
                "user": user
            }
        )

    try:
        farmer_input = {
            "pH": float(pH),
            "N": float(N),
            "P": float(P),
            "K": float(K),
            "Temp": float(Temp),
            "Rainfall": float(Rainfall),
            "Humidity": float(Humidity),
            "Season_Duration": float(Season_Duration),
            "Soil Type": Soil_Type,
            "Region": Region
        }
        pred_crop, top_seeds, crop_probs = recommend_seeds(farmer_input)
        
        # Save search trace to local SQLite DB
        add_crop_prediction(
            user_id=user['id'],
            pH=float(pH),
            N=float(N),
            P=float(P),
            K=float(K),
            temp=float(Temp),
            humidity=float(Humidity),
            rainfall=float(Rainfall),
            duration=int(Season_Duration),
            soil_type=Soil_Type,
            region=Region,
            pred_crop=pred_crop,
            top_seeds=top_seeds
        )
        
        prediction_result = {
            "pred_crop": pred_crop,
            "top_seeds": top_seeds,
            "crop_probs": crop_probs
        }
        return templates.TemplateResponse(
            request=request,
            name="crop.html",
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
            name="crop.html",
            context={
                "request": request,
                "prediction": None,
                "error": f"Error during model prediction: {str(e)}",
                "lang": lang,
                "lang_dict": lang_dict,
                "user": user
            }
        )
