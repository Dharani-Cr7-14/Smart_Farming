import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src to python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR / "src"))
sys.path.append(str(ROOT_DIR / "src" / "app"))

from fastapi.testclient import TestClient
from main import app
from services.chatbot_service import CHAT_HISTORY_DB, SYSTEM_PROMPT_TEMPLATES
import services.chatbot_service as chatbot_service
import sqlite3

class TestChatbotSystem(unittest.TestCase):
    
    def setUp(self):
        self.client = TestClient(app)
        # Clear database and in-memory histories
        CHAT_HISTORY_DB.clear()
        
        # Build a temporary test user
        self.test_username = "chatbot_test_user_unique"
        self.test_password = "password123"
        
        # Register user in DB
        from models.database import register_user, get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (self.test_username,))
        cursor.execute("DELETE FROM users WHERE username = 'user_two';")
        conn.commit()
        conn.close()
        
        register_user(self.test_username, self.test_password, region="South", language="en")
        register_user("user_two", "password123", region="North", language="en")
        
        # Retrieve user IDs
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (self.test_username,))
        self.user_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM users WHERE username = 'user_two'")
        self.user_two_id = cursor.fetchone()[0]
        conn.close()
        
        # Log in the test user sessions via TestClient cookies
        # Authenticate first user
        res = self.client.post("/auth/login", data={"username": self.test_username, "password": self.test_password})
        self.cookies_user1 = res.cookies
        
    def tearDown(self):
        # Cleanup users
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (self.test_username,))
        cursor.execute("DELETE FROM users WHERE username = 'user_two';")
        cursor.execute("DELETE FROM chat_messages WHERE user_id IN (?, ?)", (self.user_id, self.user_two_id))
        conn.commit()
        conn.close()
        CHAT_HISTORY_DB.clear()

    @patch("services.chatbot_service.ollama_client")
    def test_authenticated_english_message(self, mock_client):
        # Setup mock chat return response
        mock_msg = MagicMock()
        mock_msg.message.content = "This is a response in English advising on soil nutrients."
        mock_client.chat.return_value = mock_msg
        
        res = self.client.post(
            "/chatbot_message",
            data={"user_message": "What fertilizer should I use for rice?", "lang": "en"},
            cookies=self.cookies_user1
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["reply"], "This is a response in English advising on soil nutrients.")
        
        # Check system prompt matched language
        args, kwargs = mock_client.chat.call_args
        messages = kwargs["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Answer strictly in English.", messages[0]["content"])

    @patch("services.chatbot_service.ollama_client")
    def test_authenticated_tamil_message(self, mock_client):
        mock_msg = MagicMock()
        mock_msg.message.content = "நெல் சாகுபடிக்கு யூரியா தேவைப்படுகிறது."
        mock_client.chat.return_value = mock_msg
        
        res = self.client.post(
            "/chatbot_message",
            data={"user_message": "நெல் சாகுபடி?", "lang": "ta"},
            cookies=self.cookies_user1
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["reply"], "நெல் சாகுபடிக்கு யூரியா தேவைப்படுகிறது.")
        
        # Verify system prompt targets Tamil
        args, kwargs = mock_client.chat.call_args
        messages = kwargs["messages"]
        self.assertIn("Answer strictly in Tamil (தமிழ்).", messages[0]["content"])

    @patch("services.chatbot_service.ollama_client")
    def test_authenticated_hindi_message(self, mock_client):
        mock_msg = MagicMock()
        mock_msg.message.content = "धान की खेती के लिए खाद जरूरी है।"
        mock_client.chat.return_value = mock_msg
        
        res = self.client.post(
            "/chatbot_message",
            data={"user_message": "धान की खेती?", "lang": "hi"},
            cookies=self.cookies_user1
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["reply"], "धान की खेती के लिए खाद जरूरी है।")
        
        # Verify system prompt targets Hindi
        args, kwargs = mock_client.chat.call_args
        messages = kwargs["messages"]
        self.assertIn("Answer strictly in Hindi (हिंदी).", messages[0]["content"])

    @patch("services.chatbot_service.ollama_client")
    def test_conversation_follow_up_and_six_message_limit(self, mock_client):
        mock_msg = MagicMock()
        mock_msg.message.content = "Mock response"
        mock_client.chat.return_value = mock_msg
        
        # Send multiple queries to populate history
        for i in range(5):
            res = self.client.post(
                "/chatbot_message",
                data={"user_message": f"Query {i}", "lang": "en"},
                cookies=self.cookies_user1
            )
            self.assertEqual(res.status_code, 200)
            
        # Verify memory contains max 6 messages (3 user, 3 assistant turns)
        history = CHAT_HISTORY_DB[self.user_id]
        self.assertEqual(len(history), 6)
        
        # Verify role turn alternates
        for idx, entry in enumerate(history):
            expected_role = "user" if idx % 2 == 0 else "assistant"
            self.assertEqual(entry["role"], expected_role)

    @patch("services.chatbot_service.ollama_client")
    def test_multiple_users_separate_histories(self, mock_client):
        mock_msg = MagicMock()
        mock_msg.message.content = "Reply"
        mock_client.chat.return_value = mock_msg
        
        # User 1 sends message
        self.client.post("/chatbot_message", data={"user_message": "User 1 query", "lang": "en"}, cookies=self.cookies_user1)
        
        # Log in User 2
        res2 = self.client.post("/auth/login", data={"username": "user_two", "password": "password123"})
        cookies_user2 = res2.cookies
        
        # User 2 sends message
        self.client.post("/chatbot_message", data={"user_message": "User 2 query", "lang": "en"}, cookies=cookies_user2)
        
        # Confirm separate histories
        self.assertEqual(len(CHAT_HISTORY_DB[self.user_id]), 2)
        self.assertEqual(len(CHAT_HISTORY_DB[self.user_two_id]), 2)
        self.assertEqual(CHAT_HISTORY_DB[self.user_id][0]["content"], "User 1 query")
        self.assertEqual(CHAT_HISTORY_DB[self.user_two_id][0]["content"], "User 2 query")

    @patch("services.chatbot_service.ollama_client", None)
    def test_ollama_offline_handling(self):
        # ollama_client is set to None (offline)
        res = self.client.post(
            "/chatbot_message",
            data={"user_message": "Farming query", "lang": "en"},
            cookies=self.cookies_user1
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["reply"], "Error: Chatbot daemon is offline.")
        
        # Verify no database entry logged for offline error response
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_messages WHERE user_id = ?", (self.user_id,))
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows), 0)

    def test_empty_message(self):
        res = self.client.post(
            "/chatbot_message",
            data={"user_message": "", "lang": "en"},
            cookies=self.cookies_user1
        )
        self.assertEqual(res.status_code, 422) # Fastapi validation error

    def test_unauthenticated_request(self):
        fresh_client = TestClient(app)
        res = fresh_client.post(
            "/chatbot_message",
            data={"user_message": "Soil advice?", "lang": "en"}
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["reply"], "Session expired. Please log in again.")

    @patch("services.chatbot_service.ollama_client")
    def test_database_persistence(self, mock_client):
        mock_msg = MagicMock()
        mock_msg.message.content = "Persistence AI reply"
        mock_client.chat.return_value = mock_msg
        
        res = self.client.post(
            "/chatbot_message",
            data={"user_message": "Database persistence check", "lang": "en"},
            cookies=self.cookies_user1
        )
        self.assertEqual(res.status_code, 200)
        
        # Verify SQLite entries logged
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, message, language FROM chat_messages WHERE user_id = ? ORDER BY id ASC", (self.user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "user")
        self.assertEqual(rows[0][1], "Database persistence check")
        self.assertEqual(rows[0][2], "en")
        
        self.assertEqual(rows[1][0], "assistant")
        self.assertEqual(rows[1][1], "Persistence AI reply")
        self.assertEqual(rows[1][2], "en")

if __name__ == "__main__":
    unittest.main()
