import os
import sys
import unittest
from pathlib import Path

# Add src and src/app to python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR / "src"))
sys.path.append(str(ROOT_DIR / "src" / "app"))

from fastapi.testclient import TestClient
from main import app
from services.auth_service import SESSIONS, sign_value, unsign_value
import sqlite3

class TestCookiesHardening(unittest.TestCase):
    
    def setUp(self):
        # Create a fresh TestClient for each test to isolate session states
        self.client = TestClient(app)
        SESSIONS.clear()
        
        self.username = "secure_farmer_test"
        self.password = "pass12345"
        
        # Pre-cleanup user
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (self.username,))
        conn.commit()
        conn.close()

    def tearDown(self):
        # Cleanup
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (self.username,))
        conn.commit()
        conn.close()
        SESSIONS.clear()

    def test_complete_auth_and_hardening_lifecycle(self):
        # 1. Registration Test
        reg_res = self.client.post(
            "/auth/register",
            data={"username": self.username, "password": self.password, "region": "South"}
        )
        self.assertEqual(reg_res.status_code, 200) # Returns 200 and login page view
        
        # 2. Login with incorrect credentials
        bad_login_res = self.client.post(
            "/auth/login",
            data={"username": self.username, "password": "wrong_password"}
        )
        self.assertEqual(bad_login_res.status_code, 200)
        self.assertIn("Invalid username or password", bad_login_res.text)
        self.assertNotIn("session_id", self.client.cookies)
        
        # 3. Login with correct credentials
        good_login_res = self.client.post(
            "/auth/login",
            data={"username": self.username, "password": self.password}
        )
        self.assertEqual(good_login_res.status_code, 200) # standardRedirectResponse returns 200 template
        
        # Verify signed session_id cookie is dropped
        self.assertIn("session_id", self.client.cookies)
        signed_cookie_val = self.client.cookies["session_id"]
        self.assertIn(".", signed_cookie_val) # Contains value.signature
        
        # 4. Access dashboard after login
        dash_res = self.client.get("/")
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(self.username, dash_res.text)
        
        # 5. Access crop prediction (GET)
        crop_get = self.client.get("/seed_dashboard")
        self.assertEqual(crop_get.status_code, 200)
        self.assertIn("Soil", crop_get.text)

        # 6. Access disease prediction (GET)
        disease_get = self.client.get("/disease_dashboard")
        self.assertEqual(disease_get.status_code, 200)
        
        # 7. Access chatbot (GET)
        chatbot_get = self.client.get("/chatbot")
        self.assertEqual(chatbot_get.status_code, 200)
        
        # 8. Access history (GET)
        history_get = self.client.get("/history")
        self.assertEqual(history_get.status_code, 200)

        # 9. Test Access protected page without login (using a fresh client instance)
        unauth_client = TestClient(app)
        unauth_res = unauth_client.get("/")
        self.assertEqual(unauth_res.status_code, 200)
        self.assertIn("Login / Register", unauth_res.text) # Redirected to login page content

        # 10. Tampered session cookie test
        tampered_client = TestClient(app)
        # Setup cookie containing valid UUID but modified/tampered signature suffix
        uuid_part = signed_cookie_val.split(".")[0]
        tampered_cookie = f"{uuid_part}.invalid_sig_value_123"
        tampered_client.cookies.set("session_id", tampered_cookie)
        
        tampered_res = tampered_client.get("/")
        self.assertEqual(tampered_res.status_code, 200)
        # Should be treated as unauthenticated and served the Login page view
        self.assertIn("Login / Register", tampered_res.text)
        
        # 11. Logout Test
        logout_res = self.client.get("/auth/logout")
        self.assertEqual(logout_res.status_code, 200)
        # Verify cookie cleared from client side
        self.assertNotIn("session_id", self.client.cookies)
        
        # 12. Access protected page after logout
        post_logout_res = self.client.get("/")
        self.assertEqual(post_logout_res.status_code, 200)
        self.assertIn("Login / Register", post_logout_res.text)

if __name__ == "__main__":
    unittest.main()
