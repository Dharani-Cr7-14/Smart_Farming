import requests
import sqlite3

session = requests.Session()

login_data = {
    "username": "dharani_production_flow",
    "password": "testpass123",
    "region": "South"
}

print("Running E2E Production Tests...")

# 1. Register
reg_res = session.post("http://127.0.0.1:8000/auth/register", data=login_data)
print("1. Registration status:", reg_res.status_code)

# 2. Login
login_res = session.post("http://127.0.0.1:8000/auth/login", data=login_data)
print("2. Login status:", login_res.status_code)

# 3. Post Seed Recommendation soil/weather parameters (Medium duration, South region)
crop_data = {
    "pH": "6.5",
    "N": "90",
    "P": "42",
    "K": "43",
    "Temp": "25.0",
    "Rainfall": "200.0",
    "Humidity": "80.0",
    "Season_Duration": "120",
    "Soil_Type": "Loamy",
    "Region": "South"
}

crop_res = session.post("http://127.0.0.1:8000/seed_dashboard", data=crop_data)
print("3. Seed Recommendation status:", crop_res.status_code)

# Search output HTML text for predictions
text = crop_res.text
if "Predicted Crop:" in text:
    print("✅ Success: Result page contains Predicted Crop label.")
    # Extract prediction labels
    for line in text.split("\n"):
        if "Predicted Crop:" in line:
            print("   Row found:", line.strip())
else:
    print("❌ Failed: Result page crop labels missing.")

# Check seed recommendations listed in output HTML
print("\nScanning output for seed varieties and match status:")
for line in text.split("\n"):
    if "Exact Match" in line or "Region Match" in line or "Fallback" in line:
        print("   ->", line.strip())

# 4. Check SQLite DB to confirm prediction logged
conn = sqlite3.connect("uzhavan_saathee.db")
cursor = conn.cursor()

# Get user id
cursor.execute("SELECT id FROM users WHERE username = 'dharani_production_flow';")
user = cursor.fetchone()
if user:
    user_id = user[0]
    cursor.execute("SELECT * FROM crop_predictions WHERE user_id = ? ORDER BY id DESC LIMIT 1;", (user_id,))
    row = cursor.fetchone()
    print("\n4. SQLite Stored Prediction Row:", row)
    if row:
        print("✅ DB verified! Row created successfully.")
    else:
        print("❌ DB check failed!")
else:
    print("❌ User not found in DB.")

conn.close()
