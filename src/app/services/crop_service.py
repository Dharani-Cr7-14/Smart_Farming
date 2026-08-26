import os
import sys
import joblib
import pandas as pd
import numpy as np

# Load configurations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.config import MODELS_DIR, USE_MOCK_MODELS

# Global ML models
crop_model = None
seed_model = None
encoder = None

try:
    if USE_MOCK_MODELS:
        crop_model = joblib.load(os.path.join(MODELS_DIR, "mock_crop_recommender.joblib"))
        seed_model = joblib.load(os.path.join(MODELS_DIR, "mock_seed_recommender.joblib"))
        encoder = joblib.load(os.path.join(MODELS_DIR, "mock_encoder.joblib"))
        print("✅ crop_service: MOCK recommendation models loaded successfully.")
    else:
        crop_model = joblib.load(os.path.join(MODELS_DIR, "crop_recommender.joblib"))
        print("✅ crop_service: PRODUCTION crop model loaded successfully.")
except Exception as e:
    mode_str = "MOCK" if USE_MOCK_MODELS else "PRODUCTION"
    print(f"⚠️ crop_service: Warning: {mode_str} models could not be loaded: {e}")

def has_crop_models():
    """Verify if the required Scikit-Learn models are loaded."""
    if USE_MOCK_MODELS:
        return crop_model is not None and seed_model is not None and encoder is not None
    return crop_model is not None

def recommend_seeds(farmer_input: dict):
    """
    Accepts farm weather and soil attributes.
    Returns predicted crop name, top 3 seeds, and full crop likelihoods.
    """
    if not has_crop_models():
        raise ValueError("Recommendation models are not loaded on server.")
        
    if USE_MOCK_MODELS:
        # Run mock models ML flow for testing/backward compatibility
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

        crop_onehot = pd.get_dummies([pred_crop])
        missing = seed_model.n_features_in_ - (arr.shape[1] + crop_onehot.shape[1])
        if missing > 0:
            crop_dummy = np.hstack([crop_onehot.values, np.zeros((1, missing))])
        else:
            crop_dummy = crop_onehot.values[:, :seed_model.n_features_in_ - arr.shape[1]]

        X_seed = np.hstack([arr, crop_dummy])
        seed_probs = dict(zip(seed_model.classes_, seed_model.predict_proba(X_seed)[0]))
        top_seeds = sorted(seed_probs.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Format confidence as strings
        top_seeds_formatted = [(seed, f"{prob*100:.2f}% confidence") for seed, prob in top_seeds]
        return pred_crop, top_seeds_formatted, crop_probs
    else:
        # Run production single-model crop prediction
        # Feature order ALWAYS: N, P, K, Temp, Rainfall, Humidity, pH (Standard Crop_recommendation features)
        X_input = np.array([[
            float(farmer_input["N"]),
            float(farmer_input["P"]),
            float(farmer_input["K"]),
            float(farmer_input["Temp"]),
            float(farmer_input["Humidity"]),
            float(farmer_input["pH"]),
            float(farmer_input["Rainfall"])
        ]])
        
        pred_crop = crop_model.predict(X_input)[0]
        crop_probs = dict(zip(crop_model.classes_, crop_model.predict_proba(X_input)[0]))
        
        # Call seed variety database lookup deterministically
        from services.seed_service import get_seed_recommendations
        top_seeds = get_seed_recommendations(
            predicted_crop=pred_crop,
            farmer_region=farmer_input.get("Region", ""),
            season_duration=float(farmer_input.get("Season_Duration", 120))
        )
        
        if not top_seeds:
            top_seeds = [("No matching seed variety was found in the available catalog.", "No catalog match")]
            
        return pred_crop, top_seeds, crop_probs

