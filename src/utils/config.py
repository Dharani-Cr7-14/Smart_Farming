import os
from dotenv import load_dotenv

# Load local .env if it exists
load_dotenv()

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/
PROJECT_ROOT = os.path.dirname(BASE_DIR)                              # uzhavan_saathee/

# Resolved paths for data and models
MODELS_DIR = os.getenv("MODELS_DIR", os.path.join(PROJECT_ROOT, "models"))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")

# Comma-separated browser origins allowed to call the API when the frontend is
# deployed separately from FastAPI.
FRONTEND_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

# Model Mode configuration (True enables mock modes for local testing)
USE_MOCK_MODELS = os.getenv("USE_MOCK_MODELS", "False").lower() in ("true", "1", "yes")

# Cryptographic Cookie Secret Key
COOKIE_SECRET = os.getenv("COOKIE_SECRET", "uzhavan_saathee_default_fallback_secret_key_2026")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
