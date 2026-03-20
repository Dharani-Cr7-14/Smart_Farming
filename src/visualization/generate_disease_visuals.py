import os
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ==============================
# CONFIGURATION
# ==============================
MODEL_PATH = "models/plant_disease_model.h5"
DATASET_PATH = "data/plant_disease/"
IMAGES_PATH = "src/app/static/images"
os.makedirs(IMAGES_PATH, exist_ok=True)

# ==============================
# ⿡ Load trained model
# ==============================
model = load_model(MODEL_PATH)

# ==============================
# ⿢ Load class indices
# ==============================
CLASS_INDICES_PATH = os.path.join(DATASET_PATH, "class_indices.json")
with open(CLASS_INDICES_PATH, "r") as f:
    class_indices = json.load(f)

inverse_class_indices = {int(v): k for k, v in class_indices.items()}

# ==============================
# ⿣ Load dataset
# ==============================
datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

test_generator = datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(224, 224),
    batch_size=32,
    class_mode="categorical",
    subset="validation",
    shuffle=False
)

# ==============================
# ⿤ Predictions & metrics
# ==============================
preds = model.predict(test_generator, verbose=1)
pred_labels = np.argmax(preds, axis=1)
true_labels = test_generator.classes

# Map predicted labels to names safely
pred_labels_names = [
    inverse_class_indices.get(int(i), "Unknown") for i in pred_labels
]
true_labels_names = [
    inverse_class_indices.get(int(i), "Unknown") for i in true_labels
]

# Accuracy
accuracy = np.mean(np.array(pred_labels_names) == np.array(true_labels_names)) * 100

# Healthy vs Diseased count
healthy_label = "Healthy"  # adjust if needed
status_counts = {
    "Healthy Leaves": sum(np.array(true_labels_names) == healthy_label),
    "Diseased Leaves": sum(np.array(true_labels_names) != healthy_label)
}

# Disease type counts
disease_counts = pd.Series(true_labels_names).value_counts()

# ==============================
# ⿥ Create Visualizations
# ==============================

# ----- Healthy vs Diseased Pie Chart -----
df_health = pd.DataFrame({
    "Status": list(status_counts.keys()),
    "Count": list(status_counts.values())
})
fig1 = px.pie(df_health, names="Status", values="Count",
              color="Status",
              color_discrete_map={"Healthy Leaves": "#2ecc71", "Diseased Leaves": "#e74c3c"},
              title="🌿 Overall Leaf Health")
fig1.update_traces(textinfo="label+percent", pull=[0, 0.1])
fig1.update_layout(dragmode="lasso")  # Enable lasso
fig1.write_html(os.path.join(IMAGES_PATH, "healthy_vs_diseased.html"), full_html=True)

# ----- Disease Type Distribution -----
df_disease = pd.DataFrame({
    "Disease": disease_counts.index,
    "Samples": disease_counts.values
})
fig2 = px.bar(df_disease, x="Disease", y="Samples", color="Disease",
              title="🍂 Disease Type Distribution", text="Samples")
fig2.update_layout(
    xaxis_title="Disease",
    yaxis_title="Number of Leaves",
    dragmode="select"
)
fig2.write_html(os.path.join(IMAGES_PATH, "disease_type_distribution.html"), full_html=True)

# ----- Model Accuracy Gauge -----
fig3 = go.Figure(go.Indicator(
    mode="gauge+number",
    value=accuracy,
    title={'text': "🤖 Model Accuracy (%)"},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': "#27ae60"},
        'steps': [
            {'range': [0, 50], 'color': "#e74c3c"},
            {'range': [50, 80], 'color': "#f1c40f"},
            {'range': [80, 100], 'color': "#2ecc71"}
        ],
    }
))
fig3.write_html(os.path.join(IMAGES_PATH, "model_accuracy_gauge.html"), full_html=True)

# ----- Top Predicted Diseases -----
top_disease_counts = pd.Series(pred_labels_names).value_counts().head(3)
df_top = pd.DataFrame({
    "Disease": top_disease_counts.index,
    "Confidence": (top_disease_counts.values / sum(top_disease_counts.values)) * 100
})
fig4 = px.bar(df_top, x="Disease", y="Confidence", color="Disease",
              title="🌱 Top Predicted Diseases", text="Confidence")
fig4.update_layout(dragmode="lasso")
fig4.write_html(os.path.join(IMAGES_PATH, "top_disease_predictions.html"), full_html=True)

print("✅ All disease visualizations generated with interactivity enabled.")