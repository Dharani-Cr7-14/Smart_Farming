import requests
import sqlite3
import os

session = requests.Session()

login_data = {
    "username": "dharani_disease_e2e",
    "password": "testpass123",
    "region": "South"
}

print("Running E2E Production Disease Tests...")

# 1. Register
reg_res = session.post("http://127.0.0.1:8000/auth/register", data=login_data)
print("1. Registration status:", reg_res.status_code)

# 2. Login
login_res = session.post("http://127.0.0.1:8000/auth/login", data=login_data)
print("2. Login status:", login_res.status_code)

# 3. Post Disease upload
test_image_path = "data/plant_disease/test/Apple___Apple_scab/1f6abf22-93fa-48f0-a509-cc3e210f75f0___FREC_Scab 3172.JPG"
if not os.path.exists(test_image_path):
    print("❌ Error: Test image missing at:", test_image_path)
    exit(1)

with open(test_image_path, "rb") as f:
    files = {
        "file": (os.path.basename(test_image_path), f, "image/jpeg")
    }
    disease_res = session.post("http://127.0.0.1:8000/disease_dashboard", files=files)

print("3. Upload POST status:", disease_res.status_code)

# Scan output HTML
text = disease_res.text
if "Disease Diagnosis" in text or "Predicted Class" in text or "Confidence" in text:
    print("✅ Success: Result page contains prediction outputs.")
    for line in text.split("\n"):
        if "Confidence:" in line or "Diagnosis:" in line:
            print("   Row found:", line.strip())
else:
    print("❌ Failed: HTML doesn't contain prediction elements.")

# 4. Check SQLite DB to confirm prediction logged
conn = sqlite3.connect("uzhavan_saathee.db")
cursor = conn.cursor()

# Get user id
cursor.execute("SELECT id FROM users WHERE username = 'dharani_disease_e2e';")
user = cursor.fetchone()
if user:
    user_id = user[0]
    cursor.execute("SELECT * FROM disease_predictions WHERE user_id = ? ORDER BY id DESC LIMIT 1;", (user_id,))
    row = cursor.fetchone()
    print("\n4. SQLite Stored Disease Prediction Row:", row)
    if row:
        print("✅ DB verified! Row created successfully.")
    else:
        print("❌ DB check failed!")
else:
    print("❌ User not found in DB.")

conn.close()
