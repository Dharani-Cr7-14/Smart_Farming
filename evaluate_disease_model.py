import os
import sys
import numpy as np
import json
from pathlib import Path

# Add src to python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR / "src"))

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.resnet50 import preprocess_input
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

print("="*60)
print("🔬 PLANT DISEASE CNN EVALUATION ON HELD-OUT TEST SPLIT")
print("="*60)

# Load dataset generators using preprocess_input
print("Loading generators...")
base_dir = os.path.join(ROOT_DIR, "data", "plant_disease")
test_dir = os.path.join(base_dir, "test")
class_indices_path = os.path.join(base_dir, "class_indices.json")

with open(class_indices_path, 'r') as f:
    class_indices = json.load(f)
inverse_class_indices = {v: k for k, v in class_indices.items()}
class_names = [inverse_class_indices[i] for i in range(len(inverse_class_indices))]

test_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    shuffle=False
)

# Load saved model (defaulting to the experimental finetuned best checkpoint)
model_path = os.path.join(ROOT_DIR, "models", "plant_disease_finetuned_best.h5")
if not os.path.exists(model_path):
    # Fallback to current production model
    model_path = os.path.join(ROOT_DIR, "models", "plant_disease_model.h5")
    
print(f"Loading model from: {model_path} ...")
model = load_model(model_path)

# 1. Evaluate generator loss & accuracy
print("Evaluating on test generator...")
test_loss, test_acc = model.evaluate(test_generator)
print(f"\n📈 Test Loss: {test_loss:.4f}")
print(f"📈 Test Accuracy: {test_acc:.4f}")

# 2. Get detailed predictions
print("\nGenerating classification predictions...")
test_generator.reset()
y_true = test_generator.classes

preds = model.predict(test_generator)
y_pred = np.argmax(preds, axis=1)

# Report metrics
print("\n" + "="*50)
print("📊 DETAILED METRICS REPORT:")
print("="*50)
prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)
print(f"Macro Precision: {prec:.4f}")
print(f"Macro Recall: {rec:.4f}")
print(f"Macro F1-score: {f1:.4f}")

print("\nClassification Report:")
print(classification_report(y_true, y_pred, target_names=class_names, zero_division=0))

print("\nConfusion Matrix:")
cm = confusion_matrix(y_true, y_pred)
print(cm.tolist())

print("="*60)
