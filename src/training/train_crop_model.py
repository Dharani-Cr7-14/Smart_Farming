import os
import sys
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Add root directory to python path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

DATA_PATH = os.path.join(ROOT_DIR, "data", "raw", "Crop_recommendation.csv")
MODEL_OUTPUT_PATH = os.path.join(ROOT_DIR, "models", "crop_recommender.joblib")

def run_crop_training():
    print("="*60)
    print("🌱 SMART FARMING DECISION SUPPORT SYSTEM - CROP MODEL TRAINING PIPELINE")
    print("="*60)
    
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Missing training dataset at {DATA_PATH}")
        
    print(f"Loading dataset from: {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH)
    
    # 1. Validate Columns
    required_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 'label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    print("✅ Dataset columns validated.")
    
    # 2. Check Missing values & duplicates
    missing_sum = df[required_cols].isnull().sum().sum()
    duplicate_sum = df.duplicated().sum()
    print(f"   Missing values count: {missing_sum}")
    print(f"   Duplicate rows count: {duplicate_sum}")
    
    # 3. Class distribution
    print("\nClass distribution (Crop types):")
    print(df['label'].value_counts())
    
    # 4. Features & targets split
    # Standardize names: temperature -> Temp, humidity -> Humidity, ph -> pH, rainfall -> Rainfall
    X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']].values
    y = df['label'].values
    
    # 5. Train-test split (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain set size: {X_train.shape[0]} samples")
    print(f"Test set size: {X_test.shape[0]} samples")
    
    # 6. Train RandomForest model
    print("\nTraining RandomForestClassifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=12)
    clf.fit(X_train, y_train)
    
    # 7. Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n" + "="*50)
    print("📈 EVALUATION METRICS REPORT:")
    print("="*50)
    print(f"Overall Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # 8. Save model
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_OUTPUT_PATH)
    print(f"\n✅ Model binary saved to: {MODEL_OUTPUT_PATH}")
    print("="*60)

if __name__ == "__main__":
    run_crop_training()
