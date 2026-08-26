import os
import pandas as pd
from pathlib import Path

# Root directory
ROOT_DIR = Path(__file__).resolve().parents[2]

def clean_seed_catalog():
    xls_path = os.path.join(ROOT_DIR, "data", "raw", "F_Central_Release__Field_crop_Varieties__released_1.xls")
    output_dir = os.path.join(ROOT_DIR, "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    output_csv = os.path.join(output_dir, "seed_catalog.csv")
    
    print("Reading Excel catalog...")
    df = pd.read_excel(xls_path)
    
    # Standardize columns
    df.columns = [col.strip() for col in df.columns]
    
    # Strip string values
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            
    print("Cleaning values...")
    # Normalize crop names to lowercase for comparison
    df["Normalized Crop"] = df["Crop"].str.lower().str.replace("paddy", "rice")
    
    # Save processed catalog
    df.to_csv(output_csv, index=False)
    print(f"✅ Processed catalog saved to: {output_csv}")

if __name__ == "__main__":
    clean_seed_catalog()
