import joblib
import numpy as np
import pandas as pd

# ----------------------------
# Load trained models & encoder
# ----------------------------
crop_model = joblib.load("models/crop_recommender.joblib")
seed_model = joblib.load("models/seed_recommender.joblib")
encoder = joblib.load("models/encoder.joblib")

# ----------------------------
# Corrected recommend_seeds function
# ----------------------------
def recommend_seeds(farmer_input):
    """
    Input: farmer_input (dict) matching training column names
    Output: predicted crop, top 3 seed varieties, crop probabilities
    """

    # 1️⃣ Numeric columns exactly as trained
    num_cols = ['pH', 'N', 'P', 'K', 'Temp', 'Rainfall', 'Humidity', 'Season_Duration']
    df_num = pd.DataFrame([{k: float(farmer_input[k]) for k in num_cols}])

    # 2️⃣ Categorical columns exactly as encoder expects
    cat_cols = encoder.feature_names_in_
    df_cat = pd.DataFrame([{k: str(farmer_input.get(k, "")) for k in cat_cols}])

    # 3️⃣ Encode categorical features
    df_cat_encoded = pd.DataFrame(
        encoder.transform(df_cat),
        columns=encoder.get_feature_names_out()
    )

    # 4️⃣ Combine numeric + encoded categorical
    X_input = pd.concat([df_num, df_cat_encoded], axis=1)

    # 5️⃣ Align features with crop model
    expected_features = crop_model.n_features_in_
    if X_input.shape[1] < expected_features:
        # Pad with zeros
        extra_cols = expected_features - X_input.shape[1]
        X_input = pd.concat([X_input, pd.DataFrame(np.zeros((1, extra_cols)))], axis=1)
    elif X_input.shape[1] > expected_features:
        # Drop extra columns
        X_input = X_input.iloc[:, :expected_features]

    X_input_array = X_input.values

    # 6️⃣ Predict crop
    pred_crop = crop_model.predict(X_input_array)[0]
    crop_probs = dict(zip(crop_model.classes_, crop_model.predict_proba(X_input_array)[0]))

    # 7️⃣ Prepare input for seed model
    crop_onehot = pd.get_dummies([pred_crop])
    missing_cols = seed_model.n_features_in_ - (X_input_array.shape[1] + crop_onehot.shape[1])
    if missing_cols > 0:
        crop_dummy_array = np.hstack([crop_onehot.values, np.zeros((1, missing_cols))])
    else:
        crop_dummy_array = crop_onehot.values[:, :seed_model.n_features_in_ - X_input_array.shape[1]]

    X_seed_input = np.hstack([X_input_array, crop_dummy_array])

    # 8️⃣ Predict seed varieties
    seed_probs = dict(zip(seed_model.classes_, seed_model.predict_proba(X_seed_input)[0]))
    top_seeds = sorted(seed_probs.items(), key=lambda x: x[1], reverse=True)[:3]

    return pred_crop, top_seeds, crop_probs

# ----------------------------
# Example usage
# ----------------------------
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
        # Remove extra columns not used in training
    }

    crop, top_seeds, crop_probs = recommend_seeds(farmer_input)

    print(f"\nPredicted Crop: {crop}")
    print("Crop Probabilities:")
    for k, v in crop_probs.items():
        print(f"{k} → {v:.2f}")

    print(f"\nTop 3 Recommended Seed Varieties for {crop}:")
    for seed, prob in top_seeds:
        print(f"{seed} → {prob:.2f}")
