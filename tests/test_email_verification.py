"""Unit and integration tests for email OTP verification system."""

import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.core.auth_manager import UserManager
from backend.core.email_service import is_smtp_configured, send_otp_email
from backend.server import app


@pytest.fixture
def clean_user_manager(tmp_path, monkeypatch):
    """Provide an isolated UserManager with temporary user storage."""
    users_file = str(tmp_path / "test_users.json")
    usage_file = str(tmp_path / "test_usage.json")
    monkeypatch.setattr("backend.core.auth_manager.USERS_FILE", users_file)
    monkeypatch.setattr("backend.core.auth_manager.USAGE_FILE", usage_file)
    # Ensure fresh instance
    manager = UserManager()
    return manager


def test_smtp_configured_check():
    """Verify is_smtp_configured checks presence of host, user, password."""
    with patch("backend.core.email_service.SMTP_HOST", ""), \
         patch("backend.core.email_service.SMTP_USER", ""), \
         patch("backend.core.email_service.SMTP_PASSWORD", ""):
        assert is_smtp_configured() is False

    with patch("backend.core.email_service.SMTP_HOST", "smtp.example.com"), \
         patch("backend.core.email_service.SMTP_USER", "user@example.com"), \
         patch("backend.core.email_service.SMTP_PASSWORD", "secret123"):
        assert is_smtp_configured() is True


def test_send_otp_email_dev_fallback():
    """When SMTP is not configured, send_otp_email falls back to dev mode without failing."""
    with patch("backend.core.email_service.SMTP_HOST", ""):
        res = send_otp_email("test@example.com", "123456", "Test User")
        assert res["sent"] is True
        assert res["dev_mode"] is True
        assert res["otp"] == "123456"


def test_initiate_registration_and_verify_success(clean_user_manager):
    """Test full happy path: initiate -> receive OTP -> verify -> login."""
    manager = clean_user_manager
    email = "newuser@example.com"
    pwd = "password123"
    name = "New User"

    # Step 1: Initiate
    init_res = manager.initiate_registration(email=email, password=pwd, name=name)
    assert init_res["success"] is True
    assert init_res["email"] == email

    # Verify pending state exists
    assert email in manager._pending_verifications
    otp = manager._pending_verifications[email]["otp"]
    assert len(otp) == 6
    assert otp.isdigit()

    # Step 2: Verify with correct OTP
    verify_res = manager.verify_otp_and_register(email=email, otp=otp)
    assert verify_res["success"] is True
    assert "token" in verify_res
    assert verify_res["user"]["email"] == email
    assert verify_res["user"]["name"] == name

    # Pending state cleaned up
    assert email not in manager._pending_verifications

    # User in store and marked verified
    user_record = manager._users[email]
    assert user_record["email_verified"] is True
    assert "verified_at" in user_record

    # User can now login with password
    login_res = manager.login(email, pwd)
    assert login_res["success"] is True


def test_verify_otp_invalid_code_and_rate_limit(clean_user_manager):
    """Invalid OTP codes should be rejected and track remaining attempts."""
    manager = clean_user_manager
    email = "failuser@example.com"
    manager.initiate_registration(email=email, password="password123", name="Fail User")

    # Attempt with wrong OTP
    bad_res = manager.verify_otp_and_register(email=email, otp="000000")
    assert bad_res["success"] is False
    assert "attempts remaining" in bad_res["error"]

    # 4 more failed attempts -> total 5 attempts
    for _ in range(4):
        manager.verify_otp_and_register(email=email, otp="000000")

    # 6th attempt -> locked out / cleared
    lock_res = manager.verify_otp_and_register(email=email, otp="000000")
    assert lock_res["success"] is False
    assert "Too many failed attempts" in lock_res["error"]
    assert email not in manager._pending_verifications


def test_duplicate_registration_rejected(clean_user_manager):
    """Cannot initiate registration if email already registered."""
    manager = clean_user_manager
    manager.register("existing@example.com", "password123", "Existing User")

    init_res = manager.initiate_registration("existing@example.com", "newpassword123", "New")
    assert init_res["success"] is False
    assert "already registered" in init_res["error"]


def test_resend_otp_cooldown(clean_user_manager, monkeypatch):
    """Resend OTP should enforce cooldown."""
    manager = clean_user_manager
    email = "cooldown@example.com"
    manager.initiate_registration(email=email, password="password123", name="Cooldown")

    # Immediate resend should fail with cooldown message
    resend_fail = manager.resend_otp(email)
    assert resend_fail["success"] is False
    assert "Please wait" in resend_fail["error"]

    # Simulate waiting past cooldown
    pending = manager._pending_verifications[email]
    pending["last_sent_at"] -= 35

    resend_ok = manager.resend_otp(email)
    assert resend_ok["success"] is True
    assert manager._pending_verifications[email]["otp"] is not None


def test_fastapi_otp_endpoints(tmp_path, monkeypatch):
    """Test the FastAPI HTTP endpoints for send-otp, verify-otp, and resend-otp."""
    users_file = str(tmp_path / "test_api_users.json")
    usage_file = str(tmp_path / "test_api_usage.json")
    monkeypatch.setattr("backend.core.auth_manager.USERS_FILE", users_file)
    monkeypatch.setattr("backend.core.auth_manager.USAGE_FILE", usage_file)

    # Force re-instantiation of manager
    mgr = UserManager()
    monkeypatch.setattr("backend.routes.auth._user_manager", mgr)

    client = TestClient(app)

    # 1. Send OTP
    send_res = client.post("/api/auth/send-otp", json={
        "email": "apitester@example.com",
        "password": "strongpassword123",
        "name": "API Tester",
    })
    assert send_res.status_code == 200
    data = send_res.json()
    assert data["success"] is True
    otp = mgr._pending_verifications["apitester@example.com"]["otp"]

    # 2. Verify with wrong OTP
    bad_verify = client.post("/api/auth/verify-otp", json={
        "email": "apitester@example.com",
        "otp": "999999",
    })
    assert bad_verify.status_code == 400
    assert "attempts remaining" in bad_verify.json()["detail"]

    # 3. Verify with correct OTP
    good_verify = client.post("/api/auth/verify-otp", json={
        "email": "apitester@example.com",
        "otp": otp,
    })
    assert good_verify.status_code == 200
    verify_data = good_verify.json()
    assert verify_data["success"] is True
    assert "token" in verify_data
    token = verify_data["token"]

    # 4. Check token validity
    check_res = client.post("/api/auth/verify", json={"token": token})
    assert check_res.status_code == 200
    assert check_res.json()["valid"] is True
