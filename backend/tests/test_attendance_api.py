import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from app.services.auth import create_access_token, hash_password
from app.services.session import generate_dynamic_qr_token

class AttendanceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.student_token = create_access_token(
            data={"sub": "student-test-01", "role": "STUDENT"}
        )
        self.headers = {"Authorization": f"Bearer {self.student_token}"}

    def test_scan_qr_endpoint_requires_authentication(self) -> None:
        response = self.client.post(
            "/api/v1/attendance/scan",
            json={"qr_token": "invalid_token_str"}
        )
        self.assertEqual(response.status_code, 401)

    def test_scan_qr_invalid_payload_returns_400(self) -> None:
        response = self.client.post(
            "/api/v1/attendance/scan",
            json={"qr_token": "malformed_or_expired_qr_data"},
            headers=self.headers
        )
        self.assertTrue(response.status_code in [400, 404, 422])

if __name__ == "__main__":
    unittest.main()
