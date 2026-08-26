import requests

session = requests.Session()
BASE_URL = "http://127.0.0.1:8000"

login_data = {
    "username": "regression_farmer_check",
    "password": "password123",
    "region": "South"
}

print("Running Regression Check Across All FastAPI Endpoints...")

# 1. Register & Login
reg = session.post(f"{BASE_URL}/auth/register", data=login_data)
login = session.post(f"{BASE_URL}/auth/login", data=login_data)
print(f"1. Login Status: {login.status_code}")

# 2. GET Home Dashboard
home = session.get(f"{BASE_URL}/")
print(f"2. Dashboard Status: {home.status_code}")
assert home.status_code == 200, f"Expected 200, got {home.status_code}"
assert "Dashboard" in home.text or "Uzhavan" in home.text, "Dashboard context check failed"

# 3. GET Crop Recommendation Page
crop = session.get(f"{BASE_URL}/seed_dashboard")
print(f"3. Crop/Seed Page Status: {crop.status_code}")
assert crop.status_code == 200, f"Expected 200, got {crop.status_code}"
assert "Crop" in crop.text or "pH" in crop.text, "Crop page check failed"

# 4. GET Leaf Disease Scan Page
disease = session.get(f"{BASE_URL}/disease_dashboard")
print(f"4. Disease Page Status: {disease.status_code}")
assert disease.status_code == 200, f"Expected 200, got {disease.status_code}"
assert "Disease" in disease.text or "Leaf" in disease.text, "Disease page check failed"

# 5. GET Chatbot Page
chat = session.get(f"{BASE_URL}/chatbot")
print(f"5. Chatbot Page Status: {chat.status_code}")
assert chat.status_code == 200, f"Expected 200, got {chat.status_code}"
assert "Assistant" in chat.text or "Chat" in chat.text, "Chatbot page check failed"

# 6. GET History Page
history = session.get(f"{BASE_URL}/history")
print(f"6. History Page Status: {history.status_code}")
assert history.status_code == 200, f"Expected 200, got {history.status_code}"
assert "History" in history.text or "Disease" in history.text, "History page check failed"

# 7. GET Model Health Endpoint
health = session.get(f"{BASE_URL}/model_health")
print(f"7. Health API Status: {health.status_code} -> {health.json()}")
assert health.status_code == 200, f"Expected 200, got {health.status_code}"

print("\n✅ REGRESSION CHECK COMPLETED SUCCESSFULLY! ALL MODULES ARE FUNCTIONAL.")
