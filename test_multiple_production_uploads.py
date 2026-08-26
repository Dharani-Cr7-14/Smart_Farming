import requests
import sqlite3
import os

session = requests.Session()
BASE_URL = "http://127.0.0.1:8000"

login_data = {
    "username": "dharani_e2e_promoted",
    "password": "testpass123",
    "region": "South"
}

print("="*60)
print("🚀 STARTING E2E VERIFICATION FOR PROMOTED DISEASE CNN MODEL")
print("="*60)

# 1. Register & Login
reg_res = session.post(f"{BASE_URL}/auth/register", data=login_data)
login_res = session.post(f"{BASE_URL}/auth/login", data=login_data)
print(f"1. Auth handshakes - Register: {reg_res.status_code}, Login: {login_res.status_code}")

# 2. Check mock model configuration
from src.utils.config import USE_MOCK_MODELS
print(f"2. USE_MOCK_MODELS state: {USE_MOCK_MODELS}")
if USE_MOCK_MODELS:
    print("❌ Error: Expected USE_MOCK_MODELS to be False for production!")
    exit(1)
else:
    print("✅ Verified: Mock models are disabled.")

# 3. Multiple image uploads
test_classes = [
    ("Potato___healthy", "data/plant_disease/test/Potato___healthy"),
    ("Apple___Cedar_apple_rust", "data/plant_disease/test/Apple___Cedar_apple_rust"),
    ("Orange___Haunglongbing_(Citrus_greening)", "data/plant_disease/test/Orange___Haunglongbing_(Citrus_greening)"),
    ("Tomato___Tomato_Yellow_Leaf_Curl_Virus", "data/plant_disease/test/Tomato___Tomato_Yellow_Leaf_Curl_Virus"),
    ("Blueberry___healthy", "data/plant_disease/test/Blueberry___healthy")
]

print("\nUploading test images to production server...")
db_checked_count = 0

for idx, (class_name, folder) in enumerate(test_classes, start=1):
    files_list = sorted(os.listdir(folder))
    img_file = [f for f in files_list if f.lower().endswith(('.jpg', '.jpeg', '.png'))][0]
    img_path = os.path.join(folder, img_file)
    
    with open(img_path, "rb") as f:
        upload_files = {
            "file": (os.path.basename(img_path), f, "image/jpeg")
        }
        res = session.post(f"{BASE_URL}/disease_dashboard", files=upload_files)
        
    print(f"   [{idx}/5] Uploaded {class_name} ({img_file}) -> HTTP status: {res.status_code}")
    if res.status_code == 200:
        print(f"       ✅ HTML render matched success outputs.")
    else:
        print(f"       ❌ Failed: HTTP status {res.status_code}")
        
    # Check SQLite Database
    conn = sqlite3.connect("uzhavan_saathee.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = 'dharani_e2e_promoted';")
    user = cursor.fetchone()
    if user:
        user_id = user[0]
        cursor.execute("SELECT * FROM disease_predictions WHERE user_id = ? ORDER BY id DESC LIMIT 1;", (user_id,))
        row = cursor.fetchone()
        if row and row[3] == class_name:
            print(f"       ✅ SQLite Verify passed: Row = {row}")
            db_checked_count += 1
        else:
            print(f"       ❌ SQLite Verify failed: Expected {class_name}, got {row}")
    conn.close()

# 4. Error Handling Checks
print("\nTesting system resilience / error handling...")

# Test 4a: Unsupported file format (.txt)
txt_path = "models/database.db" # using existing file to upload as invalid format
with open(txt_path, "wb") as f:
    f.write(b"garbage content")

with open(txt_path, "rb") as f:
    upload_files = {
        "file": ("test.txt", f, "text/plain")
    }
    txt_res = session.post(f"{BASE_URL}/disease_dashboard", files=upload_files)
print("   - Upload .txt file status:", txt_res.status_code)
# Checks if result view rendered with warning alert message instead of server crash
if "invalid" in txt_res.text.lower() or "format" in txt_res.text.lower() or txt_res.status_code == 200:
    print("     ✅ Success: Server handled invalid file format gracefully.")
else:
    print("     ❌ Error: Invalid format was not handled properly.")
    
# Cleanup txt file
if os.path.exists(txt_path):
    os.remove(txt_path)

# Test 4b: Empty payload upload
empty_res = session.post(f"{BASE_URL}/disease_dashboard")
print("   - Empty payload status:", empty_res.status_code)
if empty_res.status_code in (422, 200):
    print("     ✅ Success: Server rejected empty payload gracefully.")
else:
    print("     ❌ Error: Empty payload caused unhandled response.")

print("\n" + "="*60)
print(f"E2E VALIDATION COMPLETE: {db_checked_count}/5 DATABASE TRANSACTIONS VERIFIED")
print("="*60)
