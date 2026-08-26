import uuid
import hmac
import hashlib
import base64
from fastapi import Request, Response
import sys
import os

# Import database methods
# Support path routing in case this service is imported in submodules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from models.database import authenticate_user, register_user
from utils.config import COOKIE_SECRET

# In-memory session database mapping: session_id (UUID) -> User Record Dict
SESSIONS = {}

def sign_value(value: str) -> str:
    """Sign a string value using HMAC-SHA256."""
    key = COOKIE_SECRET.encode("utf-8")
    val_bytes = value.encode("utf-8")
    signature = hmac.new(key, val_bytes, hashlib.sha256).digest()
    sig_b64 = base64.b64encode(signature).decode("utf-8")
    return f"{value}.{sig_b64}"

def unsign_value(signed_value: str) -> str:
    """Verify the HMAC signature of a signed value and return the original string if valid."""
    if not signed_value or "." not in signed_value:
        return None
    try:
        parts = signed_value.split(".", 1)
        value, sig_b64 = parts[0], parts[1]
        expected_sig = hmac.new(
            COOKIE_SECRET.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256
        ).digest()
        actual_sig = base64.b64decode(sig_b64.encode("utf-8"))
        if hmac.compare_digest(expected_sig, actual_sig):
            return value
    except Exception:
        pass
    return None

def get_current_user(request: Request):
    """Retrieve currently logged-in user profile from session store."""
    signed_session_id = request.cookies.get("session_id")
    if not signed_session_id:
        return None
        
    session_id = unsign_value(signed_session_id)
    if session_id and session_id in SESSIONS:
        return SESSIONS[session_id]
    return None

def login_farmer(response: Response, username, password):
    """Authenticate credentials. Stores signed session UUID in httpOnly cookie."""
    user = authenticate_user(username, password)
    if user:
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = user
        signed_session_id = sign_value(session_id)
        # Store signed cookie on browser client
        response.set_cookie(
            key="session_id",
            value=signed_session_id,
            httponly=True,
            samesite="lax",
            path="/"
        )
        return user
    return None

def logout_farmer(response: Response, request: Request):
    """Clear session key in memory and delete client cookie."""
    signed_session_id = request.cookies.get("session_id")
    if signed_session_id:
        session_id = unsign_value(signed_session_id)
        if session_id and session_id in SESSIONS:
            del SESSIONS[session_id]
    response.delete_cookie("session_id", path="/")

def register_farmer(username, password, region=None, language='en'):
    """Delegate signup request to persistence layer."""
    return register_user(username, password, region, language)
