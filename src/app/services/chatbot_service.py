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
    "en": "You are a concise agricultural assistant. Give practical, accurate advice about crops, soil, pests, fertilizers, and farming. Do not invent facts. For non-agricultural questions, say you focus on farming. Reply only in English and keep answers under 120 words.",
    "ta": "நீங்கள் ஒரு சுருக்கமான விவசாய உதவியாளர். பயிர்கள், மண், பூச்சிகள், உரங்கள் மற்றும் விவசாயம் பற்றி நடைமுறை, துல்லியமான ஆலோசனை வழங்குங்கள். தகவல்களை உருவாக்காதீர்கள். விவசாயம் சாராத கேள்விகளுக்கு, நீங்கள் விவசாயத்தில் கவனம் செலுத்துகிறீர்கள் என்று கூறுங்கள். தமிழில் மட்டும் 120 சொற்களுக்குள் பதிலளிக்கவும்.",
    "hi": "आप एक संक्षिप्त कृषि सहायक हैं। फसलों, मिट्टी, कीटों, उर्वरकों और खेती पर व्यावहारिक, सटीक सलाह दें। तथ्य न गढ़ें। गैर-कृषि प्रश्नों पर कहें कि आपका ध्यान खेती पर है। केवल हिंदी में 120 शब्दों के अंदर उत्तर दें।"
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
            messages=messages,
            options={
                "num_ctx": 2048,
                "num_predict": 128,
                "temperature": 0.1,
            },
            keep_alive="10m",
        )
        if response and response.message:
            return response.message.content
        return "Sorry, no response was generated."
    except Exception as e:
        return f"Error: Could not connect to Ollama daemon ({str(e)}). Please check if Ollama is running and '{OLLAMA_MODEL}' model is pulled."
