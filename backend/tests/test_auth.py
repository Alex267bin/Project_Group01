import os
import unittest
from datetime import datetime, timezone

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret")

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, login, require_role
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.base import Base
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)

    def setUp(self) -> None:
        self.db = Session(self.engine)
        self.user = User(
            user_id="user-1",
            username="student1",
            password_hash=hash_password("correct-password"),
            full_name="Test Student",
            email="student1@example.com",
            role=UserRole.STUDENT,
        )
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    def test_password_hashing(self) -> None:
        password_hash = hash_password("secret")
        self.assertNotEqual(password_hash, "secret")
        self.assertTrue(verify_password("secret", password_hash))
        self.assertFalse(verify_password("wrong", password_hash))

    def test_jwt_claims_and_expiration(self) -> None:
        token, expires_in = create_access_token(
            user_id=self.user.user_id,
            username=self.user.username,
            role=self.user.role,
        )
        claims = decode_access_token(token)
        self.assertEqual(expires_in, 1800)
        self.assertEqual(claims["sub"], "user-1")
        self.assertEqual(claims["role"], UserRole.STUDENT.value)
        expiration = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        self.assertAlmostEqual((expiration - datetime.now(timezone.utc)).total_seconds(), 1800, delta=5)

    def test_login_rejects_invalid_credentials(self) -> None:
        with self.assertRaises(HTTPException) as context:
            login(LoginRequest(username="student1", password="wrong"), self.db)
        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Incorrect username or password")

    def test_login_returns_token(self) -> None:
        response = login(
            LoginRequest(username="student1", password="correct-password"),
            self.db,
        )
        self.assertTrue(response.authenticated)
        self.assertEqual(response.token_type, "bearer")
        self.assertEqual(decode_access_token(response.access_token)["sub"], "user-1")

    def test_invalid_token_is_rejected(self) -> None:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")
        with self.assertRaises(HTTPException) as context:
            get_current_user(credentials, self.db)
        self.assertEqual(context.exception.status_code, 401)

    def test_role_authorization(self) -> None:
        for role in UserRole:
            self.user.role = role
            self.db.commit()
            self.assertIs(require_role(role)(self.user), self.user)
            denied_role = next(candidate for candidate in UserRole if candidate is not role)
            with self.assertRaises(HTTPException) as context:
                require_role(denied_role)(self.user)
            self.assertEqual(context.exception.status_code, 403)

# BỔ SUNG CỦA NHÂN (TESTER)
    
    def test_login_non_existent_user(self) -> None:
        """Kiểm tra ngoại lệ khi đăng nhập bằng tài khoản không tồn tại."""
        with self.assertRaises(HTTPException) as context:
            login(LoginRequest(username="ghost_student", password="password123"), self.db)
        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Incorrect username or password")

    def test_verify_empty_password_fails(self) -> None:
        """Kiểm tra hệ thống từ chối xác thực nếu mật khẩu bị để rỗng."""
        password_hash = hash_password("valid-password")
        self.assertFalse(verify_password("", password_hash))
        self.assertFalse(verify_password("   ", password_hash))


if __name__ == "__main__":
    unittest.main()
