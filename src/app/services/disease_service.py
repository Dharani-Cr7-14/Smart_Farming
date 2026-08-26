import os
import sys
import json
import shutil
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.config import MODELS_DIR, DATA_DIR

# Optional TensorFlow import
try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.resnet50 import preprocess_input
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

disease_model = None
class_indices = None
DISEASE_CLASSES = []

# Load model binary
if HAS_TENSORFLOW:
    try:
        DISEASE_MODEL_PATH = os.path.join(MODELS_DIR, "plant_disease_model.h5")
        if os.path.exists(DISEASE_MODEL_PATH):
            disease_model = load_model(DISEASE_MODEL_PATH)
            print("✅ disease_service: TensorFlow model loaded successfully.")
        else:
            print(f"⚠️ disease_service: Model file not found at {DISEASE_MODEL_PATH}")
    except Exception as e:
        print(f"⚠️ disease_service: Warning: Model could not be loaded: {e}")
else:
    print("⚠️ disease_service: TensorFlow not installed. Model bypassed.")

# Load class index files
try:
    CLASS_INDICES_PATH = os.path.join(DATA_DIR, "plant_disease", "class_indices.json")
    if not os.path.exists(CLASS_INDICES_PATH):
        # Fallback to root directory class_indices.json
        CLASS_INDICES_PATH = os.path.join(os.path.dirname(BASE_DIR), "class_indices.json")
    
    if os.path.exists(CLASS_INDICES_PATH):
        with open(CLASS_INDICES_PATH, "r") as f:
            class_indices = json.load(f)
        inverse_class_indices = {v: k for k, v in class_indices.items()}
        DISEASE_CLASSES = [inverse_class_indices[i] for i in range(len(inverse_class_indices))]
        print("✅ disease_service: Class indices loaded successfully.")
    else:
        print(f"⚠️ disease_service: Class indices file not found at {CLASS_INDICES_PATH}")
except Exception as e:
    print(f"⚠️ disease_service: Warning: Class indices could not be loaded: {e}")

def has_disease_model():
    """Verify if disease CNN model and label mapping are loaded."""
    return HAS_TENSORFLOW and disease_model is not None and class_indices is not None

def run_disease_inference(file_path: str):
    """Run model prediction on a leaf image. Returns (predicted_class, confidence)."""
    if not has_disease_model():
        raise ValueError("Plant disease classification model is not loaded on server.")
        
    img = image.load_img(file_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    preds = disease_model.predict(img_array)
    predicted_index = np.argmax(preds)
    predicted_class = DISEASE_CLASSES[predicted_index]
    confidence = float(preds[0][predicted_index] * 100)
    
    return predicted_class, confidence

def generate_disease_visualizations(pred_class, confidence):
    """Create interactive gauges, bars, and pies of prediction confidence."""
    IMAGES_PATH = os.path.join(BASE_DIR, "static", "images")
    os.makedirs(IMAGES_PATH, exist_ok=True)

    # 1. Gauge indicator
    fig1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence,
        title={'text': f"Confidence: {pred_class} (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#45a29e"},
            'steps': [
                {'range': [0, 50], 'color': '#e74c3c'},
                {'range': [50, 80], 'color': '#f1c40f'},
                {'range': [80, 100], 'color': '#2ecc71'}
            ]
        }
    ))
    fig1.write_html(os.path.join(IMAGES_PATH, "dynamic_visualization_1.html"), full_html=False)

    # 2. Bar chart
    df = pd.DataFrame({"Disease": [pred_class, "Others"], "Confidence": [confidence, 100 - confidence]})
    fig2 = px.bar(df, x="Disease", y="Confidence", color="Disease", text="Confidence")
    fig2.update_layout(yaxis_range=[0, 100])
    fig2.write_html(os.path.join(IMAGES_PATH, "dynamic_visualization_2.html"), full_html=False)

    # 3. Pie chart
    df_pie = pd.DataFrame({"Status": [pred_class, "Others"], "Confidence": [confidence, 100 - confidence]})
    fig3 = px.pie(df_pie, names="Status", values="Confidence", title="Prediction Breakdown")
    fig3.update_traces(textinfo="label+percent")
    fig3.write_html(os.path.join(IMAGES_PATH, "dynamic_visualization_3.html"), full_html=False)
