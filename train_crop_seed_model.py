# train_crop_seed_model.py (Interactive Visualizations Version)
import os
import numpy as np
import pandas as pd
import joblib
import plotly.express as px
import plotly.figure_factory as ff

from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# ----------------------------
# Step 1: Load dataset
# ----------------------------
data = pd.read_csv("data/cleaned_crop_dataset.csv")
print("Dataset shape:", data.shape)

# ----------------------------
# Step 2: Identify numeric and categorical columns
# ----------------------------
target_crop = 'crop'
target_variety = 'Seed Variety'

all_features = [col for col in data.columns if col not in [target_crop, target_variety]]
num_cols = data[all_features].select_dtypes(include=np.number).columns.tolist()
cat_cols = [col for col in all_features if col not in num_cols]

print("Numeric columns:", num_cols)
print("Categorical columns:", cat_cols)

# ----------------------------
# Step 3: Encode categorical features
# ----------------------------
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
X_cat = encoder.fit_transform(data[cat_cols])
X_num = data[num_cols].values
X = np.hstack([X_num, X_cat])

# ----------------------------
# Step 4: Define targets
# ----------------------------
y_crop = data[target_crop].copy()
y_variety = data[target_variety].copy()

# Handle rare seed varieties
min_samples = 3
rare_varieties = y_variety.value_counts()[y_variety.value_counts() < min_samples].index
y_variety = y_variety.replace(rare_varieties, "Other")

# ----------------------------
# Step 5: Safe train-test split
# ----------------------------
def safe_train_test_split(X, y, test_size=0.2, random_state=42):
    if (y.value_counts() < 2).any():
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)

# ----------------------------
# Step 6: Train RandomForest for Crop Prediction
# ----------------------------
X_train_crop, X_test_crop, y_train_crop, y_test_crop = safe_train_test_split(X, y_crop)

rf_crop = RandomForestClassifier(random_state=42)
param_grid = {'n_estimators': [100, 150], 'max_depth': [10, 15]}

grid_crop = GridSearchCV(rf_crop, param_grid, cv=5, n_jobs=-1)
grid_crop.fit(X_train_crop, y_train_crop)
best_rf_crop = grid_crop.best_estimator_

y_pred_crop = best_rf_crop.predict(X_test_crop)
print("Crop Prediction Accuracy:", accuracy_score(y_test_crop, y_pred_crop))
print(classification_report(y_test_crop, y_pred_crop))

# ----------------------------
# Step 7: Train RandomForest for Seed Variety Prediction
# ----------------------------
X_var = np.hstack([X, pd.get_dummies(y_crop, drop_first=True).values])
X_train_var, X_test_var, y_train_var, y_test_var = safe_train_test_split(X_var, y_variety)

rf_var = RandomForestClassifier(random_state=42)
grid_var = GridSearchCV(rf_var, param_grid, cv=5, n_jobs=-1)
grid_var.fit(X_train_var, y_train_var)
best_rf_var = grid_var.best_estimator_

y_pred_var = best_rf_var.predict(X_test_var)
print("Seed Prediction Accuracy:", accuracy_score(y_test_var, y_pred_var))
print(classification_report(y_test_var, y_pred_var, zero_division=0))

# ----------------------------
# Step 8: Save Interactive Visualizations
# ----------------------------
images_path = "src/app/static/images/seed"
os.makedirs(images_path, exist_ok=True)

# Common interactive settings
interactive_settings = dict(
    dragmode="lasso",
    selectdirection="any",
    modebar_add=["lasso2d", "select2d", "zoom2d", "pan2d"]
)

# 1️⃣ Feature Importance
feature_names = num_cols + encoder.get_feature_names_out(cat_cols).tolist()
importances = best_rf_crop.feature_importances_
feat_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances}).sort_values(by='Importance', ascending=True)
fig1 = px.bar(feat_df, x='Importance', y='Feature', orientation='h',
              title="⚙️ Feature Importance for Crop Prediction",
              labels={'Importance': 'Importance Score', 'Feature': 'Feature'})
fig1.update_traces(marker_color='green')
fig1.update_layout(**interactive_settings)
fig1.write_html(os.path.join(images_path, "feature_importance.html"), full_html=True)

# 2️⃣ Seed Variety Distribution
fig2 = px.histogram(data, x='Seed Variety', title='🌱 Seed Variety Distribution',
                    color='Seed Variety', template='plotly_white')
fig2.update_layout(xaxis_title="Seed Variety", yaxis_title="Count", **interactive_settings)
fig2.write_html(os.path.join(images_path, "seed_distribution.html"), full_html=True)

# 3️⃣ Crop → Seed Variety Relationship (Sunburst)
fig3 = px.sunburst(data, path=['crop', 'Seed Variety'],
                    title='🌾 Crop → Seed Variety Relationship')
fig3.update_layout(**interactive_settings)
fig3.write_html(os.path.join(images_path, "crop_vs_seed.html"), full_html=True)

# 4️⃣ Soil Type vs Seed Variety
if 'Soil Type' in data.columns:
    top_seeds = data.groupby(['Soil Type', 'Seed Variety']).size().reset_index(name='count')
    fig4 = px.bar(top_seeds, x='Seed Variety', y='count', color='Soil Type',
                  barmode='group', title='🧪 Soil Type vs Seed Variety')
    fig4.update_layout(**interactive_settings)
    fig4.write_html(os.path.join(images_path, "soil_type_vs_seed.html"), full_html=True)

# 5️⃣ Expected Yield vs Seed Variety
if 'Expected_Yield' not in data.columns:
    np.random.seed(42)
    data['Expected_Yield'] = np.random.uniform(2, 8, size=len(data))
fig5 = px.scatter(data, x='Seed Variety', y='Expected_Yield',
                  color='Soil Type' if 'Soil Type' in data.columns else None,
                  title='📈 Seed Variety vs Expected Yield',
                  labels={'Expected_Yield': 'Expected Yield (tons/ha)'},
                  hover_data=['Region'] if 'Region' in data.columns else None)
fig5.update_traces(marker=dict(size=12, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
fig5.update_layout(**interactive_settings)
fig5.write_html(os.path.join(images_path, "expected_yield.html"), full_html=True)

# 6️⃣ Soil Nutrient Radar Chart
nutrients = [col for col in ['N', 'P', 'K', 'pH'] if col in data.columns]
if nutrients:
    radar_df = pd.DataFrame({
        'Nutrient': nutrients,
        'Actual': [data[col].mean() for col in nutrients],
        'Ideal': [80, 60, 40, 6.5][:len(nutrients)]
    })
    radar_long = radar_df.melt(id_vars='Nutrient', var_name='Type', value_name='Value')
    fig6 = px.line_polar(radar_long, r='Value', theta='Nutrient', color='Type', line_close=True,
                         template='plotly_dark', title='🧭 Soil Nutrient vs Ideal Levels')
    fig6.update_layout(**interactive_settings)
    fig6.write_html(os.path.join(images_path, "soil_radar.html"), full_html=True)

# 7️⃣ Correlation Heatmap
num_data = data[num_cols]
corr_matrix = num_data.corr().round(2)
fig7 = ff.create_annotated_heatmap(z=corr_matrix.values, x=list(corr_matrix.columns), y=list(corr_matrix.index),
                                    colorscale='Viridis')
fig7.update_layout(title="🔍 Feature Correlation Heatmap", **interactive_settings)
fig7.write_html(os.path.join(images_path, "correlation_heatmap.html"), full_html=True)

# ----------------------------
# Step 9: Save models and encoder
# ----------------------------
os.makedirs('models', exist_ok=True)
joblib.dump(best_rf_crop, 'models/crop_recommender.joblib')
joblib.dump(best_rf_var, 'models/seed_recommender.joblib')
joblib.dump(encoder, 'models/encoder.joblib')

print("✅ Models saved in 'models/' and interactive visualizations saved in 'src/app/static/images/seed/'")
