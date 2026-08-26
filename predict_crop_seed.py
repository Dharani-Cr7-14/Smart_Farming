import os
import sys
import joblib
import numpy as np
import pandas as pd

# Add src and src/app to python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "src"))
sys.path.append(os.path.join(BASE_DIR, "src", "app"))

from utils.config import USE_MOCK_MODELS, MODELS_DIR

# Load crop recommendation model
try:
    if USE_MOCK_MODELS:
        crop_model = joblib.load(os.path.join(MODELS_DIR, "mock_crop_recommender.joblib"))
        seed_model = joblib.load(os.path.join(MODELS_DIR, "mock_seed_recommender.joblib"))
        encoder = joblib.load(os.path.join(MODELS_DIR, "mock_encoder.joblib"))
        print("✅ CLI Loaded MOCK models.")
    else:
        crop_model = joblib.load(os.path.join(MODELS_DIR, "crop_recommender.joblib"))
        print("✅ CLI Loaded PRODUCTION model.")
except FileNotFoundError as e:
    print(f"❌ Error: Required model files are missing ({e.filename}).")
    print("Please make sure models exist in the models directory.")
    sys.exit(1)

def recommend_seeds(farmer_input):
    if USE_MOCK_MODELS:
        # Backward compatibility mock path
        num_cols = ['pH', 'N', 'P', 'K', 'Temp', 'Rainfall', 'Humidity', 'Season_Duration']
        df_num = pd.DataFrame([{k: float(farmer_input[k]) for k in num_cols}])
        cat_cols = encoder.feature_names_in_
        df_cat = pd.DataFrame([{k: str(farmer_input.get(k, "")) for k in cat_cols}])
        df_cat_encoded = pd.DataFrame(encoder.transform(df_cat), columns=encoder.get_feature_names_out())
        X_input = pd.concat([df_num, df_cat_encoded], axis=1)
        expected_features = crop_model.n_features_in_
        if X_input.shape[1] < expected_features:
            extra_cols = expected_features - X_input.shape[1]
            X_input = pd.concat([X_input, pd.DataFrame(np.zeros((1, extra_cols)))], axis=1)
        elif X_input.shape[1] > expected_features:
            X_input = X_input.iloc[:, :expected_features]
        X_input_array = X_input.values
        pred_crop = crop_model.predict(X_input_array)[0]
        crop_probs = dict(zip(crop_model.classes_, crop_model.predict_proba(X_input_array)[0]))
        crop_onehot = pd.get_dummies([pred_crop])
        missing_cols = seed_model.n_features_in_ - (X_input_array.shape[1] + crop_onehot.shape[1])
        if missing_cols > 0:
            crop_dummy_array = np.hstack([crop_onehot.values, np.zeros((1, missing_cols))])
        else:
            crop_dummy_array = crop_onehot.values[:, :seed_model.n_features_in_ - X_input_array.shape[1]]
        X_seed_input = np.hstack([X_input_array, crop_dummy_array])
        seed_probs = dict(zip(seed_model.classes_, seed_model.predict_proba(X_seed_input)[0]))
        top_seeds = sorted(seed_probs.items(), key=lambda x: x[1], reverse=True)[:3]
        top_seeds_formatted = [(seed, f"{prob*100:.2f}% confidence") for seed, prob in top_seeds]
        return pred_crop, top_seeds_formatted, crop_probs
    else:
        # Production path
        # Feature order: N, P, K, Temp, Rainfall, Humidity, pH (Standard Crop_recommendation features)
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
        
        # Load seed catalog lookup deterministically
        from services.seed_service import get_seed_recommendations
        top_seeds = get_seed_recommendations(
            predicted_crop=pred_crop,
            farmer_region=farmer_input.get("Region", "South"),
            season_duration=float(farmer_input.get("Season_Duration", 120))
        )
        
        if not top_seeds:
            top_seeds = [("No matching seed variety was found in the available catalog.", "No catalog match")]
            
        return pred_crop, top_seeds, crop_probs

if __name__ == "__main__":
    farmer_input = {
        "pH": 6.5,
        "N": 50,
        "P": 30,
        "K": 40,
        "Temp": 25,
        "Rainfall": 120,
        "Humidity": 80,
        "Season_Duration": 90,
        "Soil Type": "Loamy",
        "Region": "South"
    }

    crop, top_seeds, crop_probs = recommend_seeds(farmer_input)

    print(f"\nPredicted Crop: {crop}")
    print("\nTop Recommended Seed Varieties:")
    for seed, match_status in top_seeds:
        print(f"• {seed} → {match_status}")
