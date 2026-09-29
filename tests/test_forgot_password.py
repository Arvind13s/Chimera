"""Unit and integration tests for forgot password and password reset system."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.core.auth_manager import UserManager
from backend.core.email_service import send_password_reset_email
from backend.server import app


@pytest.fixture
def clean_user_manager(tmp_path, monkeypatch):
    """Provide an isolated UserManager with temporary user storage."""
    users_file = str(tmp_path / "test_users.json")
    usage_file = str(tmp_path / "test_usage.json")
    monkeypatch.setattr("backend.core.auth_manager.USERS_FILE", users_file)
    monkeypatch.setattr("backend.core.auth_manager.USAGE_FILE", usage_file)
    manager = UserManager()
    return manager


def test_send_password_reset_email_dev_fallback():
    """When SMTP is not configured, reset email logs to dev console without failing."""
    with patch("backend.core.email_service.SMTP_HOST", ""):
        res = send_password_reset_email("user@example.com", "654321", "Test User")
        assert res["sent"] is True
        assert res["dev_mode"] is True
        assert res["otp"] == "654321"


def test_forgot_password_and_reset_success(clean_user_manager):
    """Full happy path: register -> forgot password -> receive OTP -> reset -> login with new password."""
    manager = clean_user_manager
    email = "forgot@example.com"
    old_pwd = "oldpassword123"
    new_pwd = "brandnewpassword456"

    # Create account
    reg = manager.register(email, old_pwd, "Forgot Tester")
    assert reg["success"] is True

    # Step 1: Initiate password reset
    forgot_res = manager.initiate_password_reset(email)
    assert forgot_res["success"] is True
    assert forgot_res["email"] == email

    assert email in manager._pending_password_resets
    otp = manager._pending_password_resets[email]["otp"]
    assert len(otp) == 6
    assert otp.isdigit()

    # Step 2: Reset password with OTP
    reset_res = manager.verify_and_reset_password(email=email, otp=otp, new_password=new_pwd)
    assert reset_res["success"] is True
    assert "token" in reset_res
    assert reset_res["user"]["email"] == email

    # Pending reset cleared
    assert email not in manager._pending_password_resets

    # Old password fails
    old_login = manager.login(email, old_pwd)
    assert old_login["success"] is False

    # New password succeeds
    new_login = manager.login(email, new_pwd)
    assert new_login["success"] is True


def test_forgot_password_invalid_email_or_oauth(clean_user_manager):
    """Non-existent email or OAuth accounts cannot use password reset."""
    manager = clean_user_manager

    # Non-existent email
    res1 = manager.initiate_password_reset("nonexistent@example.com")
    assert res1["success"] is False
    assert "No account found" in res1["error"]

    # OAuth account
    manager.oauth_login("oauthuser@example.com", "OAuth User", "google")
    res2 = manager.initiate_password_reset("oauthuser@example.com")
    assert res2["success"] is False
    assert "Google" in res2["error"]


def test_reset_password_invalid_otp_and_attempts(clean_user_manager):
    """Invalid OTP codes reduce attempts and eventually lock out."""
    manager = clean_user_manager
    email = "attempts@example.com"
    manager.register(email, "mypassword123", "Attempts User")
    manager.initiate_password_reset(email)

    # 1 bad attempt
    bad_res = manager.verify_and_reset_password(email, "000000", "newpassword123")
    assert bad_res["success"] is False
    assert "attempts remaining" in bad_res["error"]

    # 4 more bad attempts
    for _ in range(4):
        manager.verify_and_reset_password(email, "000000", "newpassword123")

    # 6th attempt locks out
    lock_res = manager.verify_and_reset_password(email, "000000", "newpassword123")
    assert lock_res["success"] is False
    assert "Too many failed attempts" in lock_res["error"]
    assert email not in manager._pending_password_resets


def test_resend_password_reset_cooldown(clean_user_manager):
    """Resend reset code enforces cooldown."""
    manager = clean_user_manager
    email = "cooldown_reset@example.com"
    manager.register(email, "mypassword123", "Cooldown User")
    manager.initiate_password_reset(email)

    # Immediate resend fails
    resend_fail = manager.resend_password_reset_otp(email)
    assert resend_fail["success"] is False
    assert "Please wait" in resend_fail["error"]

    # Advance time
    pending = manager._pending_password_resets[email]
    pending["last_sent_at"] -= 35

    # Resend succeeds
    resend_ok = manager.resend_password_reset_otp(email)
    assert resend_ok["success"] is True


def test_fastapi_password_reset_endpoints(tmp_path, monkeypatch):
    """Test the HTTP endpoints for forgot-password, reset-password, and resend-reset-otp."""
    users_file = str(tmp_path / "test_api_users.json")
    usage_file = str(tmp_path / "test_api_usage.json")
    monkeypatch.setattr("backend.core.auth_manager.USERS_FILE", users_file)
    monkeypatch.setattr("backend.core.auth_manager.USAGE_FILE", usage_file)

    mgr = UserManager()
    mgr.register("apipwd@example.com", "initialpassword123", "API Pwd")
    monkeypatch.setattr("backend.routes.auth._user_manager", mgr)

    client = TestClient(app)

    # 1. Request reset
    req_res = client.post("/api/auth/forgot-password", json={"email": "apipwd@example.com"})
    assert req_res.status_code == 200
    assert req_res.json()["success"] is True

    otp = mgr._pending_password_resets["apipwd@example.com"]["otp"]

    # 2. Reset with wrong OTP
    bad_res = client.post("/api/auth/reset-password", json={
        "email": "apipwd@example.com",
        "otp": "111111",
        "new_password": "changedsecret999",
    })
    assert bad_res.status_code == 400

    # 3. Reset with correct OTP
    good_res = client.post("/api/auth/reset-password", json={
        "email": "apipwd@example.com",
        "otp": otp,
        "new_password": "changedsecret999",
    })
    assert good_res.status_code == 200
    data = good_res.json()
    assert data["success"] is True
    assert "token" in data

    # 4. Login with new password
    login_res = client.post("/api/auth/login", json={
        "email": "apipwd@example.com",
        "password": "changedsecret999",
    })
    assert login_res.status_code == 200
    assert login_res.json()["success"] is True
