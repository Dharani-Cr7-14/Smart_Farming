from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os, shutil, json, joblib, pandas as pd, numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import plotly.express as px
import plotly.graph_objects as go

app = FastAPI(title="Uzhavan Saathee")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "..", "models")
DATA_DIR = os.path.join(BASE_DIR, "..", "..", "data")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ---------------- Load Models ----------------
crop_model = joblib.load(os.path.join(MODELS_DIR, "crop_recommender.joblib"))
seed_model = joblib.load(os.path.join(MODELS_DIR, "seed_recommender.joblib"))
encoder = joblib.load(os.path.join(MODELS_DIR, "encoder.joblib"))

DISEASE_MODEL_PATH = os.path.join(MODELS_DIR, "plant_disease_model.h5")
disease_model = load_model(DISEASE_MODEL_PATH)

CLASS_INDICES_PATH = os.path.join(DATA_DIR, "plant_disease", "class_indices.json")
with open(CLASS_INDICES_PATH, "r") as f:
    class_indices = json.load(f)
inverse_class_indices = {v: k for k, v in class_indices.items()}
DISEASE_CLASSES = [inverse_class_indices[i] for i in range(len(inverse_class_indices))]

# ---------------- Language Dictionary ----------------
LANG_DICT = {
    "en": {
        "home_title": "Uzhavan Saathee",
        "home_subtitle": "Empowering Semi-Urban Farmers with AI",
        "seed": "Seed Recommendation",
        "disease": "Disease Prediction",
        "select_soil": "--Select Soil Type--",
        "select_region": "--Select Region--",
        "soil_options": ["Loamy","Sandy","Clay","Red","Black"],
        "region_options": ["North","South","East","West","Central"],
        "charts_seed": [
            "Feature Importance",
            "Seed Variety Distribution",
            "Crop vs Seed Relationship",
            "Soil Type vs Seed Variety",
            "Expected Yield vs Seed Variety",
            "Soil Nutrient Radar",
            "Feature Correlation Heatmap"
        ],
        "charts_disease": [
            "Overall Leaf Health",
            "Disease Type Distribution",
            "Model Accuracy Gauge",
            "Top Predicted Diseases",
            "Seasonal Disease Trend"
        ]
    },
    "ta": {
        "home_title": "உழவன் சாத்தி",
        "home_subtitle": "கிராமப் பகுதியின் விவசாயிகளுக்கு ஏ.ஐ மூலம் ஆதரவு",
        "seed": "விதை பரிந்துரை",
        "disease": "நோய் கணிப்பு",
        "select_soil": "--மண் வகை தேர்ந்தெடுக்கவும்--",
        "select_region": "--மண்டலத்தை தேர்ந்தெடுக்கவும்--",
        "soil_options": ["மணல்மண்","மணல்","களி","சிவப்பு","கருப்பு"],
        "region_options": ["வடக்கு","தெற்கு","கிழக்கு","மேற்கு","மத்திய"],
        "charts_seed": [
            "முக்கிய அம்சங்கள்",
            "விதை வகை பகிர்வு",
            "பயிர் vs விதை உறவு",
            "மண் வகை vs விதை",
            "எதிர்பார்க்கப்படும் பயிர் உற்பத்தி",
            "மண் ஊட்டச்சத்து ரேடார்",
            "அம்சங்களின் தொடர்பு ஹீட்மேப்"
        ],
        "charts_disease": [
            "இலையின் மொத்த ஆரோக்கியம்",
            "நோய் வகை பகிர்வு",
            "மாதிரி துல்லியக் குறியீடு",
            "முக்கிய கணிக்கப்பட்ட நோய்கள்",
            "பாலிடிக்க சீர்திருத்த பருவத் போக்கு"
        ]
    },
    "hi": {
        "home_title": "उज़्हवन साथी",
        "home_subtitle": "किसानों को समझदारी से निर्णय लेने में मदद करता है",
        "seed": "बीज सिफ़ारिश",
        "disease": "रोग भविष्यवाणी",
        "select_soil": "--मिट्टी का प्रकार चुनें--",
        "select_region": "--क्षेत्र चुनें--",
        "soil_options": ["दोमट", "रेतीली", "मृदा", "लाल", "काली"],
        "region_options": ["उत्तर", "दक्षिण", "पूर्व", "पश्चिम", "केंद्र"],
        "charts_seed": [
            "विशेषता महत्व",
            "बीज विविधता वितरण",
            "फसल vs बीज संबंध",
            "मिट्टी प्रकार vs बीज विविधता",
            "अपेक्षित उपज vs बीज विविधता",
            "मिट्टी पोषक तत्व राडार",
            "विशेषता सहसंबंध हीटमैप"
        ],
        "charts_disease": [
            "संपूर्ण पत्ते का स्वास्थ्य",
            "रोग प्रकार वितरण",
            "मॉडल सटीकता संकेतक",
            "शीर्ष भविष्यवाणी रोग",
            "मौसमी रोग प्रवृत्ति"
        ]
    }
}

# ---------------- Utility Functions ----------------
def get_lang_dict(lang: str):
    return LANG_DICT.get(lang, LANG_DICT["en"])

# ---------------- Seed Recommendation Logic ----------------
def recommend_seeds(farmer_input: dict):
    num_cols = ['pH','N','P','K','Temp','Rainfall','Humidity','Season_Duration']
    df_num = pd.DataFrame([{k: float(farmer_input[k]) for k in num_cols}])
    cat_cols = encoder.feature_names_in_
    df_cat = pd.DataFrame([{k: str(farmer_input.get(k, "")) for k in cat_cols}])
    df_cat_enc = pd.DataFrame(encoder.transform(df_cat), columns=encoder.get_feature_names_out())
    X_input = pd.concat([df_num, df_cat_enc], axis=1)

    expected = crop_model.n_features_in_
    if X_input.shape[1] < expected:
        X_input = pd.concat([X_input, pd.DataFrame(np.zeros((1, expected - X_input.shape[1])))], axis=1)
    else:
        X_input = X_input.iloc[:, :expected]

    arr = X_input.values
    pred_crop = crop_model.predict(arr)[0]
    crop_probs = dict(zip(crop_model.classes_, crop_model.predict_proba(arr)[0]))

    # Prepare input for seed model
    crop_onehot = pd.get_dummies([pred_crop])
    missing = seed_model.n_features_in_ - (arr.shape[1] + crop_onehot.shape[1])
    if missing > 0:
        crop_dummy = np.hstack([crop_onehot.values, np.zeros((1, missing))])
    else:
        crop_dummy = crop_onehot.values[:, :seed_model.n_features_in_ - arr.shape[1]]

    X_seed = np.hstack([arr, crop_dummy])
    seed_probs = dict(zip(seed_model.classes_, seed_model.predict_proba(X_seed)[0]))
    top_seeds = sorted(seed_probs.items(), key=lambda x: x[1], reverse=True)[:3]

    return pred_crop, top_seeds, crop_probs

# ---------------- Disease Visualizations ----------------
def generate_disease_visualizations(pred_class, confidence):
    IMAGES_PATH = os.path.join(BASE_DIR, "static", "images")
    os.makedirs(IMAGES_PATH, exist_ok=True)

    # Gauge
    fig1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence,
        title={'text': f"Prediction Confidence for {pred_class} (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#45a29e"},
            'steps': [
                {'range': [0,50], 'color':'#e74c3c'},
                {'range': [50,80], 'color':'#f1c40f'},
                {'range': [80,100], 'color':'#2ecc71'}
            ]
        }
    ))
    fig1.write_html(os.path.join(IMAGES_PATH, "dynamic_visualization_1.html"), full_html=False)

    # Bar chart
    df = pd.DataFrame({"Disease": [pred_class, "Others"], "Confidence": [confidence, 100-confidence]})
    fig2 = px.bar(df, x="Disease", y="Confidence", color="Disease", text="Confidence")
    fig2.update_layout(yaxis_range=[0,100])
    fig2.write_html(os.path.join(IMAGES_PATH, "dynamic_visualization_2.html"), full_html=False)

    # Pie chart
    df_pie = pd.DataFrame({"Status": [pred_class, "Others"], "Confidence": [confidence, 100-confidence]})
    fig3 = px.pie(df_pie, names="Status", values="Confidence", title="Prediction Confidence Breakdown")
    fig3.update_traces(textinfo="label+percent")
    fig3.write_html(os.path.join(IMAGES_PATH, "dynamic_visualization_3.html"), full_html=False)

# ---------------- Routes ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "en"):
    lang_dict = get_lang_dict(lang)
    return templates.TemplateResponse("index.html", {"request": request, "lang": lang, "lang_dict": lang_dict})

@app.get("/seed_dashboard", response_class=HTMLResponse)
async def seed_dashboard_get(request: Request, lang: str = "en"):
    lang_dict = get_lang_dict(lang)
    return templates.TemplateResponse("seed_dashboard.html", {"request": request, "prediction": None, "lang": lang, "lang_dict": lang_dict})

@app.post("/seed_dashboard", response_class=HTMLResponse)
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
    farmer_input = {
        "pH": float(pH),
        "N": float(N),
        "P": float(P),
        "K": float(K),
        "Temp": float(Temp),
        "Rainfall": float(Rainfall),
        "Humidity": float(Humidity),
        "Season_Duration": float(Season_Duration),
        "Soil_Type": Soil_Type,
        "Region": Region
    }
    pred_crop, top_seeds, crop_probs = recommend_seeds(farmer_input)
    lang_dict = get_lang_dict(lang)
    return templates.TemplateResponse(
        "seed_dashboard.html",
        {
            "request": request,
            "prediction": {
                "pred_crop": pred_crop,
                "top_seeds": top_seeds,
                "crop_probs": crop_probs
            },
            "lang": lang,
            "lang_dict": lang_dict
        }
    )

@app.get("/disease_dashboard", response_class=HTMLResponse)
async def disease_dashboard_get(request: Request, lang: str = "en"):
    lang_dict = get_lang_dict(lang)
    return templates.TemplateResponse("disease_dashboard.html", {"request": request, "prediction": None, "error": None, "lang": lang, "lang_dict": lang_dict})

@app.post("/disease_dashboard", response_class=HTMLResponse)
async def disease_dashboard_post(request: Request, file: UploadFile = File(...), lang: str = Form("en")):
    upload_folder = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        img = image.load_img(file_path, target_size=(224,224))
        img_array = image.img_to_array(img)/255.0
        img_array = np.expand_dims(img_array, axis=0)

        preds = disease_model.predict(img_array)
        predicted_index = np.argmax(preds)
        predicted_class = DISEASE_CLASSES[predicted_index]
        confidence = preds[0][predicted_index]*100

        prediction_result = {
            "pred_class": predicted_class,
            "confidence": confidence,
            "image_path": f"/static/uploads/{file.filename}"
        }

        generate_disease_visualizations(predicted_class, confidence)
        lang_dict = get_lang_dict(lang)

    except Exception as e:
        return templates.TemplateResponse(
            "disease_dashboard.html",
            {"request": request, "prediction": None, "error": str(e), "lang": lang, "lang_dict": get_lang_dict(lang)}
        )

    return templates.TemplateResponse(
        "disease_dashboard.html",
        {"request":request, "prediction":prediction_result, "error":None, "lang":lang, "lang_dict":lang_dict}
    )
from fastapi.responses import JSONResponse
from ollama import Client

ollama_client = Client()  # Make sure your Ollama daemon is running

@app.post("/chatbot_message")
async def chatbot_message(user_message: str = Form(...), lang: str = Form("en")):
    try:
        response = ollama_client.chat(
            model="llama3:latest",
            messages=[{"role": "user", "content": user_message}]
        )

        # Extract only the assistant's text content
        bot_reply = response.message.content if response.message else "Sorry, no reply."

    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    return JSONResponse({"reply":bot_reply})