import os
import sys
from ollama import Client

# Load configs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.config import OLLAMA_HOST, OLLAMA_MODEL

ollama_client = None

try:
    # Initialize connection to local Ollama Daemon
    ollama_client = Client(host=OLLAMA_HOST)
    print(f"✅ chatbot_service: Client connected to host {OLLAMA_HOST}")
except Exception as e:
    print(f"⚠️ chatbot_service: Warning: Ollama client initialization failed: {e}")

# In-memory session history database indexed by user_id
CHAT_HISTORY_DB = {}

SYSTEM_PROMPT_TEMPLATES = {
    "en": "You are a professional agricultural assistant for the 'Smart Farming Decision Support System'. Your role is to provide farmers with clear, practical, and accurate advice on crops, soil, pest controls, fertilizers, and general farming practices. Avoid inventing facts. If a question is outside agriculture, politely explain that you are designed primarily to assist with agricultural and farming queries. Answer strictly in English.",
    "ta": "You are a professional agricultural assistant for the 'Smart Farming Decision Support System'. Your role is to provide farmers with clear, practical, and accurate advice on crops, soil, pest controls, fertilizers, and general farming practices. Avoid inventing facts. If a question is outside agriculture, politely explain that you are designed primarily to assist with agricultural and farming queries. Answer strictly in Tamil (தமிழ்).",
    "hi": "You are a professional agricultural assistant for the 'Smart Farming Decision Support System'. Your role is to provide farmers with clear, practical, and accurate advice on crops, soil, pest controls, fertilizers, and general farming practices. Avoid inventing facts. If a question is outside agriculture, politely explain that you are designed primarily to assist with agricultural and farming queries. Answer strictly in Hindi (हिंदी)."
}

def get_chatbot_reply(user_message: str, lang: str = "en", conversation_history: list = None) -> str:
    """Send message to Ollama daemon using a multilingual system prompt and conversation history."""
    if ollama_client is None:
        return "Error: Chatbot daemon is offline."
        
    if conversation_history is None:
        conversation_history = []
        
    system_prompt = SYSTEM_PROMPT_TEMPLATES.get(lang, SYSTEM_PROMPT_TEMPLATES["en"])
    
    # Construct full message array: system prompt + limited history + current message
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )
        if response and response.message:
            return response.message.content
        return "Sorry, no response was generated."
    except Exception as e:
        return f"Error: Could not connect to Ollama daemon ({str(e)}). Please check if Ollama is running and '{OLLAMA_MODEL}' model is pulled."
