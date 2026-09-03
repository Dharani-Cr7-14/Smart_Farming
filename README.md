# Smart Farming Decision Support System 🌾
### An AI-powered Smart Farming Decision Support System

An AI-powered **Smart Farming Decision Support System** that helps farmers make better cultivation decisions through crop recommendation, seed variety recommendation, plant disease detection, and an agricultural AI chatbot. By combining Machine Learning classification, Deep Learning vision models, and Large Language Model (LLM) conversational agents, the system provides crop recommendations, seed variety matches, plant pathogen diagnosis, and localized agricultural advisory.

---

## 🚀 Key Features

* **Farmer Registration & Secure Login**: Secure registration and session lifecycle authenticated via cryptographically signed session cookies.
* **Crop Recommendation**: Machine learning soil suitability classification based on NPK and environmental factors.
* **Seed Variety Recommendation**: Deterministic variety catalog queries matching target region, season, and crop type.
* **Plant Disease Detection**: Deep Learning vision classification identifying 38 distinct crop leaf pathogens from uploaded leaf photographs.
* **AI Agricultural Chatbot**: Interactive LLM advisor with multilingual system prompts (`en`/`ta`/`hi`) and session-isolated conversational memory.
* **Crop/Disease/Chat History**: Persistent query records stored in SQLite, restricted strictly to the logged-in user.
* **Plotly Visualizations**: Interactive Gauges, Radar plots, and Bar charts rendering crop features and pathogen diagnostic metrics.
* **Responsive UI**: Sleek, glassmorphic design utilizing flexbox grids and mobile-toggle navigation panels.
* **Model Health Monitoring**: Dynamic system check diagnosing classifier load states and Ollama daemon connectivity.

---

## 🧠 AI & Architecture Details

### 1. Crop Recommendation Model
* **Dataset**: `Crop_recommendation.csv` (2,200 records, 22 crop classes).
* **Inputs (7 Features)**: Nitrogen (N), Phosphorus (P), Potassium (K), Temperature, Humidity, Soil pH, and Rainfall.
* **Algorithm**: Random Forest Classifier.
* **Accuracy**: **99.55%** on the held-out test split.
* **Preprocessing**: Min-Max feature Scaling and label mapping.

### 2. Seed Recommendation Catalog Lookup
To ensure scientific validity, seed variety recommendation is implemented as a **deterministic catalog lookup** rather than an ML classifier.
* **Rationale**: The seed variety dataset contains only 79 records representing many unique combinations. Training a machine learning classifier on 79 rows is mathematically invalid and leads to severe over-fitting and incorrect recommendations. 
* **Implementation**: Uses a database catalog lookup mapping the ML-predicted crop, the farmer's region/zone, and the desired growth duration to recommend registered seed varieties (e.g., ADT-36, CO-4) sourced from agricultural department catalogs.

### 3. Plant Disease Detection (CNN)
* **Dataset**: PlantVillage master dataset (54,305 leaf photos, 38 health/pathogen classes).
* **Architecture**: ResNet50 Transfer Learning + Two-Stage Fine-Tuning (frozen base stage followed by unfreezing top 15 layers).
* **Metrics**: **98.00%** Test Accuracy (Macro Precision: 0.98, Macro Recall: 0.98, Macro F1: 0.98).
* **Preprocessing**: Resized to $224 \times 224$ RGB and processed using Keras's ImageNet channel-centering normalization (`resnet50.preprocess_input`).

### 4. Interactive AI Chatbot Advisor
* **Engine**: Ollama running Llama 3 (`llama3:latest`).
* **Multilingual Prompts**: Inject system-level instructions directing the response target language based on user selection (`en`, `ta`, `hi`), forcing Llama 3 to output replies strictly in English, Tamil, or Hindi.
* **Context Memory**: Slices in-memory history to the most recent **6 conversation messages** per session to limit context window overhead and prevent latency bloat.
* **Failure Tolerance**: Gracefully catches offline daemons and returns a diagnostic helper string to the user.

---

## 🛠️ Technology Stack

* **Backend**: FastAPI (Python 3.10/3.11 asynchronous web server).
* **Frontend**: HTML5, Vanilla CSS, JavaScript, Jinja2 Templates.
* **Machine Learning**: scikit-learn, joblib.
* **Deep Learning**: TensorFlow, Keras (configured for Apple Silicon M1/M2 GPU/Metal).
* **Conversational AI**: Ollama, Llama 3.
* **Database**: SQLite.
* **Visualization**: Plotly.
* **Data & Image Processing**: Pandas, NumPy, Pillow, OpenCV.

---

## 📁 Project Structure

```text
smart_farming/
├── data/                       # Soil datasets and Excel seed catalogs
│   └── raw/
│       ├── Crop_recommendation.csv
│       └── Crop_varieties_clean.xlsx
├── models/                     # Production model binaries
│   ├── crop_recommender.joblib # Random Forest crop ML model
│   └── plant_disease_model.h5  # Fine-tuned ResNet50 disease model
├── src/
│   ├── app/                    # FastAPI Web Application source
│   │   ├── routes/             # Route routers (auth, chatbot, dashboards, history)
│   │   ├── services/           # Business services (ML inference, Ollama chat, auth)
│   │   ├── static/             # Stylesheets, JS handlers, and uploaded file space
│   │   ├── templates/          # Jinja2 layout templates
│   │   └── main.py             # Server entry point and health monitor
│   ├── inference/              # Core prediction scripts
│   ├── pipelines/              # Catalog loaders and parsing pipelines
│   ├── training/               # Model training scripts
│   └── utils/                  # System configs and translations
├── tests/                      # Unit and regression test suites
└── uzhavan_saathee.db          # Database file
```

---

## ⚙️ Installation & Setup

### Prerequisites
* **Python**: Python 3.10 or 3.11 (Required for compatibility with TensorFlow/Keras and Metal acceleration plugins).
* **Ollama**: Local daemon installed and active.

### Steps
1. **Set up virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```env
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3:latest
   USE_MOCK_MODELS=False
   COOKIE_SECRET=<your-cryptographic-cookie-signing-secret>
   ```

---

## 🚀 Running the Services

### A. Running the Web Application
No model training is required to run the application. Pre-trained models must be located in `/models`.
To run the server locally:
```bash
uvicorn src.app.main:app --reload --port 8000 --host 127.0.0.1
```
Open your browser and navigate to: `http://127.0.0.1:8000`

### B. Training the Crop Recommendation Model
If you need to retrain the crop model:
```bash
python3 src/training/train_crop_model.py
```

### C. Training/Fine-Tuning the Disease Model
If you need to retrain the disease model:
```bash
python3 src/training/train_disease_fine_tune.py
```

---

## 🤖 Chatbot Setup
1. Download and install [Ollama](https://ollama.com/).
2. Launch the Ollama daemon.
3. Download the model in your terminal:
   ```bash
   ollama pull llama3
   ```
4. Verify `OLLAMA_MODEL=llama3:latest` in your `.env`.
5. Start the FastAPI server. Log in to the application and navigate to the **AI Chatbot** screen.

---

## 🗄️ Database Schema
The SQLite database `uzhavan_saathee.db` contains four tables:
* **`users`**: Stores profile information (username, salted SHA-256 password hash, region, target language).
* **`crop_predictions`**: Logs NPK values, environmental inputs, recommended crop, and deterministic seed selections.
* **`disease_predictions`**: Logs uploaded leaf photo names, pathogen predictions, and confidence levels.
* **`chat_messages`**: Logs conversational questions and answers linked to user IDs.

*All prediction and chat history queries filter records dynamically using the authenticated `user_id` parsed from the secure cookie session. Data leakage between users is impossible.*

---

## 🔒 Security Hardening
* **Password Encryption**: Salts and hashes passwords via SHA-256 before database insertion.
* **Session Cookie Integrity**: Cryptographically signs the `session_id` cookie via HMAC-SHA256. Any client-side value modifications invalidate the session immediately.
* **Cookie Attributes**: Cookies are marked `HttpOnly` and configured with `SameSite=Lax` to mitigate XSS and CSRF vectors.
* **SQL Injection Prevention**: Parameterized queries are used for all database queries.
* **Upload Validation**: Restricts uploads to `.jpg`, `.jpeg`, and `.png` file extensions, utilizing path basenames to eliminate directory traversal risks.

---

## 🧪 Test Coverage & Verification
The codebase is validated by the following test suites:
* `test_production_disease.py`: Validates E2E leaf image upload and prediction against the promoted model.
* `test_multiple_production_uploads.py`: Asserts multi-class predictions, format rejections, and empty payload failures.
* `test_chatbot.py`: Verifies mock response routing, 6-turn history truncation, user memory isolation, and database logging.
* `test_routes_regression.py`: Performs regression HTTP checks across all FastAPI paths.
* `test_cookies_hardening.py`: Verifies registration, valid/invalid logins, cookie signature validation, and tampered cookie rejections.

*Result*: **100% of test assertions passed successfully, confirming system integrity.**

---

## ⚠️ Limitations & Disclaimers
* **Dataset Constraints**: The disease vision model is trained and evaluated on the PlantVillage dataset. Real-world farm conditions (e.g. ambient lighting, diverse angles) may impact prediction accuracy.
* **Chatbot Dependency**: Chatbot availability depends on a running local Ollama daemon and the pulled Llama 3 image.
* **Seed Lookup**: Recommends seed varieties based on catalog lookup from state registries. It is not an ML prediction model.
* **Disclaimer**: This system is a decision-support assistant. Its outputs should be verified against local agricultural experts and extension officers before purchasing inputs or executing crop management plans.

---

## 📊 Final Project Architecture

```text
[ Farmer Client ]
      │
      ├── Authentication Check (HMAC-SHA256 Signed Session Cookie)
      │
      ├───► Smart Farming Dashboard (Interactive Summaries & Charts)
      │
      ├───► Crop/Seed Dashboard (Random Forest ML + Seed Catalog Lookup)
      │
      ├───► Leaf Disease Scan (ResNet50 Vision Pathogen Diagnosis)
      │
      └───► AI Chat Advisor (Ollama Llama 3 Multilingual Chatbot)
            │
            └───► SQLite History Logging (Isolated Database Records)
```
