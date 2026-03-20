import pandas as pd

# Load Excel file
file_path = "data/merged_crop_dataset.xlsx"
data = pd.read_excel(file_path)

# Inspect basic info
print("Shape:", data.shape)  # rows x columns
print("Columns:", data.columns.tolist())
print("First 5 rows:\n", data.head())

# Check missing values
print("\nMissing values per column:\n", data.isnull().sum())

# Standardize categorical columns
cat_cols = ['crop', 'Soil Type', 'Region', 'Seed Variety']
for col in cat_cols:
    data[col] = data[col].str.strip().str.lower()

# Save cleaned dataset
data.to_csv("data/cleaned_crop_dataset.csv", index=False)
print("\nCleaned dataset saved to data/cleaned_crop_dataset.csv")