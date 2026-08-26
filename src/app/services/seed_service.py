import os
import re
import pandas as pd
from pathlib import Path

# Root directory
ROOT_DIR = Path(__file__).resolve().parents[3]
CATALOG_PATH = os.path.join(ROOT_DIR, "data", "processed", "seed_catalog.csv")

# Region mapping to Indian states (lowercased)
REGION_STATES = {
    "south": ["tamil nadu", "andhra pradesh", "telangana", "karnataka", "kerala", "pondicherry", "pondicherry"],
    "north": ["punjab", "haryana", "himachal pradesh", "jammu", "kashmir", "uttar pradesh", "uttarakhand", "delhi"],
    "east": ["west bengal", "orissa", "odisha", "bihar", "jharkhand", "assam", "tripura", "meghalaya", "manipur", "nagaland", "mizoram", "arunachal pradesh", "sikkim"],
    "west": ["maharashtra", "gujarat", "rajasthan", "goa"],
    "central": ["madhya pradesh", "chhattisgarh"]
}

def parse_duration_match(duration_str: str, target_days: float) -> bool:
    """Parses duration string and returns True if target_days fits the description."""
    text = str(duration_str).lower().strip()
    
    # 1. Range match (e.g. "115-120")
    range_match = re.search(r'(\d+)\s*-\s*(\d+)', text)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return low <= target_days <= high
        
    # 2. Single number match (e.g. "120 days")
    num_match = re.search(r'\b(\d+)\b', text)
    if num_match:
        val = float(num_match.group(1))
        return abs(val - target_days) <= 10  # within 10 days tolerance
        
    # 3. Text classifications
    if "early" in text:
        return target_days < 110
    if "medium" in text:
        return 110 <= target_days <= 130
    if "late" in text:
        return target_days > 130
        
    return False

def get_seed_recommendations(predicted_crop: str, farmer_region: str, season_duration: float):
    """
    Looks up matching seed varieties deterministically from the catalog.
    Returns: list of (variety, match_description) up to 3 recommendations.
    """
    if not os.path.exists(CATALOG_PATH):
        print(f"⚠️ Seed catalog not found at {CATALOG_PATH}")
        return []
        
    df = pd.read_csv(CATALOG_PATH)
    
    crop = predicted_crop.lower().strip()
    region = farmer_region.lower().strip()
    
    # Filter by crop
    crop_df = df[df["Normalized Crop"] == crop].copy()
    if crop_df.empty:
        # Fallback partial matching
        crop_df = df[df["Normalized Crop"].str.contains(crop, na=False)].copy()
        
    if crop_df.empty:
        return []
        
    states_to_match = REGION_STATES.get(region, [])
    
    results = []
    for _, row in crop_df.iterrows():
        recommended_zone = str(row.get("Recommended Zone", "")).lower()
        duration_str = str(row.get("Season/ duration in days", ""))
        variety = row.get("Variety", "")
        
        # Check Region Match
        region_match = False
        for state in states_to_match:
            if state in recommended_zone:
                region_match = True
                break
                
        # Check Duration Match
        duration_match = parse_duration_match(duration_str, season_duration)
        
        # Determine status score
        if region_match and duration_match:
            score = 3
            status = "Exact Match (Crop + Region + Duration)"
        elif region_match:
            score = 2
            status = "Crop + Region Match"
        elif duration_match:
            score = 1
            status = "Crop + Duration Match"
        else:
            score = 0
            status = "Crop Match (Fallback)"
            
        results.append({
            "variety": variety,
            "score": score,
            "status": status
        })
        
    # Sort by score descending and select top 3 unique varieties
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    
    final_seeds = []
    seen_varieties = set()
    for item in results:
        v = item["variety"]
        if v not in seen_varieties:
            seen_varieties.add(v)
            final_seeds.append((v, item["status"]))
            if len(final_seeds) >= 3:
                break
                
    return final_seeds
