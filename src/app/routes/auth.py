from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import sys
import os

# Load modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from services.auth_service import login_farmer, logout_farmer, register_farmer, get_current_user
from utils.translations import get_lang_dict
from routes.templates import templates

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, lang: str = "en"):
    """Render login page. Redirects to main dashboard if session is valid."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=303)
    lang_dict = get_lang_dict(lang)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "lang": lang, "lang_dict": lang_dict, "error": None, "success": None, "user": None})

@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...), lang: str = Form("en")):
    """Process credentials and set cookie. Returns login page with error context on fail."""
    lang_dict = get_lang_dict(lang)
    response = RedirectResponse(url=f"/?lang={lang}", status_code=303)
    user = login_farmer(response, username, password)
    if user:
        return response
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "lang": lang, "lang_dict": lang_dict, "error": "Invalid username or password", "success": None, "user": None})

@router.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, username: str = Form(...), password: str = Form(...), region: str = Form(None), lang: str = Form("en")):
    """Register farmer credentials. Confirms registration status on view."""
    lang_dict = get_lang_dict(lang)
    success = register_farmer(username, password, region, lang)
    if success:
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "lang": lang, "lang_dict": lang_dict, "success": "Registration successful! Please login below.", "error": None, "user": None})
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "lang": lang, "lang_dict": lang_dict, "error": "Username already exists. Choose another.", "success": None, "user": None})

@router.get("/logout")
async def logout(request: Request):
    """Delete session identifiers and redirect client back to login view."""
    response = RedirectResponse(url="/auth/login", status_code=303)
    logout_farmer(response, request)
    return response
