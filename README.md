# Smart Farming Decision Support System

An AI-powered farming workspace for crop recommendations, seed variety matching, plant disease detection, and multilingual agricultural guidance.

## Features

- React dashboard with responsive navigation and activity history
- Live temperature, humidity, and rainfall from the browser's current location
- Soil-report PDF extraction for automatic crop and seed form prefilling
- Real crop photos from the local PlantVillage dataset on prediction results
- Registration and login with username, email, password, region, and signed session cookies
- Crop recommendation from soil and weather inputs
- Regional seed variety lookup based on the predicted crop
- Plant disease detection from leaf images
- Multilingual AI assistant for English, Tamil, and Hindi
- SQLite history for crop predictions, disease scans, and chatbot messages
- Model health endpoint at `/model_health`

## Technology

- Frontend: React and Vite
- Backend: FastAPI and Uvicorn
- Models: scikit-learn, TensorFlow, Keras, and joblib
- Chatbot: Ollama with Llama 3
- Database: SQLite
- Data processing: Pandas, NumPy, Pillow, and OpenCV

## Machine Learning Models

| Feature | Model or method | Stored or configured as |
| --- | --- | --- |
| Crop recommendation | Scikit-learn `RandomForestClassifier` with 100 trees and maximum depth 12 | `models/crop_recommender.joblib` |
| Seed recommendation | Deterministic catalog lookup using the predicted crop and region | `data/processed/seed_catalog.csv` |
| Plant disease detection | TensorFlow/Keras **ResNet50 transfer-learning CNN**, with the final 15 base-model layers fine-tuned; images use ResNet50 preprocessing and are resized to `224 x 224` | `models/plant_disease_model.h5` |
| Agricultural chatbot | Ollama large language model | `OLLAMA_MODEL`, default `llama3:latest` |

The seed recommender is a catalog lookup, not a separately trained machine learning classifier. When `USE_MOCK_MODELS=True`, the application can load the mock joblib models in `models/` for development and testing.

## Requirements

- Python 3.10 or 3.11
- Node.js and npm
- Ollama, if chatbot features are required

## Setup

Create the Python environment and install backend dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install and build the React frontend:

```bash
npm install
npm run build
```

Create a `.env` file in the project root:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:latest
USE_MOCK_MODELS=False
COOKIE_SECRET=replace-with-a-long-random-secret
```

The trained model files should be available in `models/`.

## Run

The recommended command builds the React frontend, starts Ollama when available, and launches FastAPI:

```bash
./start.sh
```

Or run the server directly after building the frontend:

```bash
disease_train_env/bin/python3.10 -m uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000 in a browser.

To enable the chatbot, install Ollama and download the configured model:

```bash
ollama pull llama3
```

## Project Layout

```text
src/
  frontend/       React application
  app/
    main.py       FastAPI entrypoint and React shell serving
    routes/       Authentication, prediction, chatbot, history, and API routes
    services/     Authentication, model inference, and chatbot services
    models/       SQLite database helpers
    static/       CSS, JavaScript, and uploaded images
    templates/    Legacy server-rendered fallback templates
  inference/      Prediction utilities
  pipelines/      Dataset and catalog processing
  training/       Model training scripts
  utils/          Configuration and translations
models/           Trained model files
data/             Raw and processed datasets
```

## Useful Routes

| Route | Purpose |
| --- | --- |
| `/` | React dashboard |
| `/seed_dashboard` | Crop and seed recommendation |
| `/disease_dashboard` | Plant disease scan |
| `/chatbot` | AI agricultural assistant |
| `/history` | Saved prediction and chat history |
| `/model_health` | Model and chatbot readiness status |

React data requests use `/api/session` and `/api/history`. Authentication and prediction form endpoints remain under `/auth`, `/seed_dashboard`, `/disease_dashboard`, and `/chatbot_message`.
The dashboard requests browser geolocation and uses the coordinates with Open-Meteo's weather API through `/api/weather`. Location permission is optional; users can still enter weather values manually when unavailable. Rainfall is automatically calculated as the total precipitation for the last 30 completed/current days in millimeters.
On the Crop & Seeds page, upload a text-based PDF soil report to extract pH, nitrogen, phosphorus, and potassium. Extracted values are shown in the form for review before submitting. Scanned-image PDFs are not supported yet.
Prediction results use a matching real crop photo. The application first checks curated crop assets (including the bundled jute field photo), then searches for a healthy image in the local PlantVillage dataset. If the predicted crop is not represented by either source, the interface uses a neutral fallback illustration. The bundled jute photo is from [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Jute_Field_Bangladesh_(7749587518).jpg).

## Optional Training Commands

These commands are only needed when retraining models:

```bash
python3 src/training/train_crop_model.py
python3 src/training/train_disease_fine_tune.py
```

## Testing

Run the available test suite with:

```bash
pytest -q
```

The tests cover authentication cookies, route regressions, chatbot behavior, disease uploads, and production recommendation flows.

## Docker and deployment

The local two-container setup runs the React frontend at `http://localhost:8080`
and FastAPI at `http://localhost:8000`:

```bash
cp .env.example .env
# Set COOKIE_SECRET to a long random value in .env
docker compose up --build
```

Open `http://localhost:8080` for the latest React UI. The backend image also
builds and serves the same React UI at `http://localhost:8000`, so rebuild the
images after frontend changes:

```bash
docker compose down
docker compose build --no-cache frontend backend
docker compose up
```

If an old page remains visible, use a hard refresh (`Cmd+Shift+R` on macOS)
or an incognito window. Do not open the old `dist/index.html` file directly.

The backend container mounts `models/` and `data/plant_disease/` read-only so
large model artifacts do not need to be committed to Git. Keep these artifacts
in the private storage mechanism provided by the hosting platform (or attach a
private volume) and set `USE_MOCK_MODELS=true` only for environments where
production crop models are unavailable. The TensorFlow disease model is
required for disease detection.

For separate hosting, set `VITE_API_URL` to the public backend URL and set
`FRONTEND_ORIGINS` on the backend to the exact public frontend origin. For
cross-site cookies, use `COOKIE_SECURE=true` and `COOKIE_SAMESITE=none` over
HTTPS. Never commit `.env`, database files, model files, datasets, or API
credentials.

The frontend can be deployed as a static Docker service from
`Dockerfile.frontend`; deploy `Dockerfile.backend` as a Python web service
listening on port `8000`. Suitable providers include Render, Railway, Fly.io,
or a container platform with private persistent storage for the models and
SQLite database. Ollama is optional and should be configured as a private
reachable service; chatbot requests report unavailable when it is absent.

## Notes

- The chatbot requires a running Ollama service and a downloaded model.
- Disease predictions are intended as decision support and should be confirmed by an agricultural expert.
- Uploaded leaf images are stored under `src/app/static/uploads/`.