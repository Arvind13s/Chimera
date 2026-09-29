"""User authentication manager — PBKDF2 hashing, OAuth support, rate limiting."""

import hashlib
import json
import logging
import os
import secrets
import threading
import time
from datetime import datetime
from typing import Dict, Optional

from backend.core.config import (
    AUTH_SECRET_KEY,
    DAILY_LIMIT,
    DATA_DIR,
    OTP_EXPIRY_SECONDS,
    OTP_RESEND_COOLDOWN,
)
from backend.core.email_service import send_otp_email, send_password_reset_email

logger = logging.getLogger(__name__)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
USAGE_FILE = os.path.join(DATA_DIR, "usage.json")

_HASH_ITERATIONS = 310_000
_SALT_LENGTH = 32


class UserManager:
    """Thread-safe user store with password hashing, email OTP verification, and rate limiting."""

    def __init__(self):
        self._lock = threading.Lock()
        self._users: Dict[str, dict] = {}
        self._usage: Dict[str, dict] = {}
        self._login_attempts: Dict[str, list] = {}
        self._pending_verifications: Dict[str, dict] = {}
        self._pending_password_resets: Dict[str, dict] = {}
        self._load()

    # ── Public Auth API ─────────────────────────────────────

    def initiate_registration(
        self,
        email: str,
        password: str,
        name: str = "",
    ) -> dict:
        """Validate input, generate OTP, and dispatch verification email."""
        email = email.strip().lower()

        if not email or "@" not in email:
            return {"success": False, "error": "Invalid email address."}
        if len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters."}

        with self._lock:
            if email in self._users:
                return {"success": False, "error": "Email is already registered. Please sign in."}

            now = time.time()
            existing_pending = self._pending_verifications.get(email)
            if existing_pending:
                last_sent = existing_pending.get("last_sent_at", 0)
                if now - last_sent < OTP_RESEND_COOLDOWN:
                    wait_sec = int(OTP_RESEND_COOLDOWN - (now - last_sent))
                    return {
                        "success": False,
                        "error": f"Please wait {wait_sec}s before requesting another verification code.",
                    }

            # Generate 6-digit numeric OTP
            otp = f"{secrets.randbelow(900000) + 100000:06d}"
            salt = secrets.token_hex(_SALT_LENGTH)
            pwd_hash = self._hash_password(password, salt)

            self._pending_verifications[email] = {
                "name": name.strip() or email.split("@")[0],
                "email": email,
                "salt": salt,
                "password_hash": pwd_hash,
                "otp": otp,
                "created_at": now,
                "expires_at": now + OTP_EXPIRY_SECONDS,
                "last_sent_at": now,
                "attempts": 0,
            }

        # Dispatch verification email
        send_otp_email(to_email=email, otp_code=otp, name=name)

        return {
            "success": True,
            "message": "Verification code sent to your email.",
            "email": email,
        }

    def verify_otp_and_register(self, email: str, otp: str) -> dict:
        """Verify OTP, create user record, and return session token."""
        email = email.strip().lower()
        otp = otp.strip()

        if not email or not otp:
            return {"success": False, "error": "Email and verification code are required."}

        with self._lock:
            pending = self._pending_verifications.get(email)
            if not pending:
                return {
                    "success": False,
                    "error": "No pending verification found or code expired. Please register again.",
                }

            now = time.time()
            if now > pending.get("expires_at", 0):
                self._pending_verifications.pop(email, None)
                return {
                    "success": False,
                    "error": "Verification code has expired. Please request a new code.",
                }

            pending["attempts"] = pending.get("attempts", 0) + 1
            if pending["attempts"] > 5:
                self._pending_verifications.pop(email, None)
                return {
                    "success": False,
                    "error": "Too many failed attempts. Please register again.",
                }

            stored_otp = pending.get("otp", "")
            if not secrets.compare_digest(stored_otp, otp):
                attempts_left = max(0, 5 - pending["attempts"])
                return {
                    "success": False,
                    "error": f"Invalid verification code. {attempts_left} attempts remaining.",
                }

            # OTP matched: create verified user
            user_data = {
                "name": pending["name"],
                "email": email,
                "salt": pending["salt"],
                "password_hash": pending["password_hash"],
                "provider": "email",
                "email_verified": True,
                "verified_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }
            self._users[email] = user_data
            self._save()
            self._pending_verifications.pop(email, None)

        token = self._generate_token(email)
        return {
            "success": True,
            "token": token,
            "user": {"email": email, "name": user_data["name"]},
        }

    def resend_otp(self, email: str) -> dict:
        """Resend a new OTP to a pending registration email with cooldown check."""
        email = email.strip().lower()
        now = time.time()

        with self._lock:
            pending = self._pending_verifications.get(email)
            if not pending:
                return {
                    "success": False,
                    "error": "Registration session expired. Please start registration again.",
                }

            last_sent = pending.get("last_sent_at", 0)
            if now - last_sent < OTP_RESEND_COOLDOWN:
                wait_sec = int(OTP_RESEND_COOLDOWN - (now - last_sent))
                return {
                    "success": False,
                    "error": f"Please wait {wait_sec}s before requesting another verification code.",
                }

            new_otp = f"{secrets.randbelow(900000) + 100000:06d}"
            pending["otp"] = new_otp
            pending["expires_at"] = now + OTP_EXPIRY_SECONDS
            pending["last_sent_at"] = now
            pending["attempts"] = 0
            name = pending.get("name", "")

        send_otp_email(to_email=email, otp_code=new_otp, name=name)

        return {
            "success": True,
            "message": "A new verification code has been sent.",
        }

    def initiate_password_reset(self, email: str) -> dict:
        """Validate account, generate reset OTP, and send password reset email."""
        email = email.strip().lower()

        if not email or "@" not in email:
            return {"success": False, "error": "Invalid email address."}

        with self._lock:
            user = self._users.get(email)
            if not user:
                return {"success": False, "error": "No account found with this email address."}

            if user.get("provider") != "email":
                provider_title = user.get("provider", "social").capitalize()
                return {
                    "success": False,
                    "error": f"This account signs in with {provider_title}. Please use {provider_title} to sign in.",
                }

            now = time.time()
            existing_reset = self._pending_password_resets.get(email)
            if existing_reset:
                last_sent = existing_reset.get("last_sent_at", 0)
                if now - last_sent < OTP_RESEND_COOLDOWN:
                    wait_sec = int(OTP_RESEND_COOLDOWN - (now - last_sent))
                    return {
                        "success": False,
                        "error": f"Please wait {wait_sec}s before requesting another reset code.",
                    }

            otp = f"{secrets.randbelow(900000) + 100000:06d}"
            self._pending_password_resets[email] = {
                "otp": otp,
                "created_at": now,
                "expires_at": now + OTP_EXPIRY_SECONDS,
                "last_sent_at": now,
                "attempts": 0,
            }
            user_name = user.get("name", "")

        send_password_reset_email(to_email=email, otp_code=otp, name=user_name)

        return {
            "success": True,
            "message": "Password reset code sent to your email.",
            "email": email,
        }

    def verify_and_reset_password(self, email: str, otp: str, new_password: str) -> dict:
        """Verify reset OTP, update password, and issue new session token."""
        email = email.strip().lower()
        otp = otp.strip()

        if not email or not otp:
            return {"success": False, "error": "Email and verification code are required."}
        if len(new_password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters."}

        with self._lock:
            user = self._users.get(email)
            if not user:
                return {"success": False, "error": "Account not found."}

            pending = self._pending_password_resets.get(email)
            if not pending:
                return {
                    "success": False,
                    "error": "No pending reset request found or code expired. Please request a new code.",
                }

            now = time.time()
            if now > pending.get("expires_at", 0):
                self._pending_password_resets.pop(email, None)
                return {
                    "success": False,
                    "error": "Reset code has expired. Please request a new code.",
                }

            pending["attempts"] = pending.get("attempts", 0) + 1
            if pending["attempts"] > 5:
                self._pending_password_resets.pop(email, None)
                return {
                    "success": False,
                    "error": "Too many failed attempts. Please request a new reset code.",
                }

            stored_otp = pending.get("otp", "")
            if not secrets.compare_digest(stored_otp, otp):
                attempts_left = max(0, 5 - pending["attempts"])
                return {
                    "success": False,
                    "error": f"Invalid verification code. {attempts_left} attempts remaining.",
                }

            # OTP verified: update password
            salt = secrets.token_hex(_SALT_LENGTH)
            pwd_hash = self._hash_password(new_password, salt)
            user["salt"] = salt
            user["password_hash"] = pwd_hash
            user["updated_at"] = datetime.utcnow().isoformat()
            self._save()
            self._pending_password_resets.pop(email, None)

        token = self._generate_token(email)
        return {
            "success": True,
            "message": "Password updated successfully.",
            "token": token,
            "user": {"email": email, "name": user.get("name", "")},
        }

    def resend_password_reset_otp(self, email: str) -> dict:
        """Resend password reset OTP with cooldown enforcement."""
        email = email.strip().lower()
        now = time.time()

        with self._lock:
            user = self._users.get(email)
            if not user:
                return {"success": False, "error": "Account not found."}

            pending = self._pending_password_resets.get(email)
            if not pending:
                return {
                    "success": False,
                    "error": "Reset session expired. Please request password reset again.",
                }

            last_sent = pending.get("last_sent_at", 0)
            if now - last_sent < OTP_RESEND_COOLDOWN:
                wait_sec = int(OTP_RESEND_COOLDOWN - (now - last_sent))
                return {
                    "success": False,
                    "error": f"Please wait {wait_sec}s before requesting another reset code.",
                }

            new_otp = f"{secrets.randbelow(900000) + 100000:06d}"
            pending["otp"] = new_otp
            pending["expires_at"] = now + OTP_EXPIRY_SECONDS
            pending["last_sent_at"] = now
            pending["attempts"] = 0
            user_name = user.get("name", "")

        send_password_reset_email(to_email=email, otp_code=new_otp, name=user_name)

        return {
            "success": True,
            "message": "A new password reset code has been sent.",
        }

    def register(
        self,
        email: str,
        password: str,
        name: str = "",
    ) -> dict:
        """Register a new user directly (legacy / direct API)."""
        email = email.strip().lower()

        if not email or "@" not in email:
            return {"success": False, "error": "Invalid email address."}
        if len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters."}

        with self._lock:
            if email in self._users:
                return {"success": False, "error": "Email already registered."}

            salt = secrets.token_hex(_SALT_LENGTH)
            pwd_hash = self._hash_password(password, salt)

            self._users[email] = {
                "name": name or email.split("@")[0],
                "email": email,
                "salt": salt,
                "password_hash": pwd_hash,
                "provider": "email",
                "email_verified": True,
                "created_at": datetime.utcnow().isoformat(),
            }
            self._save()

        token = self._generate_token(email)
        return {
            "success": True,
            "token": token,
            "user": {"email": email, "name": self._users[email]["name"]},
        }

    def login(self, email: str, password: str) -> dict:
        """Authenticate user with email/password."""
        email = email.strip().lower()

        if self._is_rate_limited(email):
            return {"success": False, "error": "Too many attempts. Try again later."}

        with self._lock:
            user = self._users.get(email)

        if not user:
            self._record_attempt(email)
            return {"success": False, "error": "Invalid email or password."}

        if user.get("provider") != "email":
            return {"success": False, "error": f"Please sign in with {user.get('provider', 'OAuth')}."}

        stored_hash = user["password_hash"]
        salt = user["salt"]
        check_hash = self._hash_password(password, salt)

        if not secrets.compare_digest(stored_hash, check_hash):
            self._record_attempt(email)
            return {"success": False, "error": "Invalid email or password."}

        token = self._generate_token(email)
        return {
            "success": True,
            "token": token,
            "user": {"email": email, "name": user.get("name", "")},
        }

    def oauth_login(self, email: str, name: str, provider: str) -> dict:
        """Register or login via OAuth provider (Google/GitHub)."""
        email = email.strip().lower()

        with self._lock:
            if email not in self._users:
                self._users[email] = {
                    "name": name,
                    "email": email,
                    "provider": provider,
                    "created_at": datetime.utcnow().isoformat(),
                }
                self._save()

        token = self._generate_token(email)
        user_data = self._users.get(email, {})
        return {
            "success": True,
            "token": token,
            "user": {"email": email, "name": user_data.get("name", name)},
        }

    def verify_token(self, token: str) -> Optional[str]:
        """Verify a session token and return the email, or None."""
        try:
            parts = token.split(":", 1)
            if len(parts) != 2:
                return None
            email = parts[0]
            expected = self._generate_token(email)
            if secrets.compare_digest(token, expected):
                return email
            return None
        except Exception:
            return None

    def check_usage(self, email: str) -> dict:
        """Check if user can generate today."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        with self._lock:
            user_usage = self._usage.get(email, {})
            if user_usage.get("date") != today:
                user_usage = {"date": today, "count": 0}
                self._usage[email] = user_usage
            remaining = max(0, DAILY_LIMIT - user_usage["count"])
        return {"can_generate": remaining > 0, "remaining": remaining, "limit": DAILY_LIMIT}

    def record_usage(self, email: str):
        """Record a generation for today."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        with self._lock:
            user_usage = self._usage.get(email, {"date": today, "count": 0})
            if user_usage.get("date") != today:
                user_usage = {"date": today, "count": 0}
            user_usage["count"] += 1
            self._usage[email] = user_usage
            self._save_usage()

    # ── Internal ────────────────────────────────────────────

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            _HASH_ITERATIONS,
        ).hex()

    def _generate_token(self, email: str) -> str:
        sig = hashlib.sha256(f"{email}:{AUTH_SECRET_KEY}".encode()).hexdigest()[:32]
        return f"{email}:{sig}"

    def _is_rate_limited(self, email: str) -> bool:
        now = time.time()
        attempts = self._login_attempts.get(email, [])
        recent = [t for t in attempts if now - t < 300]
        self._login_attempts[email] = recent
        return len(recent) >= 5

    def _record_attempt(self, email: str):
        if email not in self._login_attempts:
            self._login_attempts[email] = []
        self._login_attempts[email].append(time.time())

    def _load(self):
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r") as f:
                    self._users = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load users: {e}")

        try:
            if os.path.exists(USAGE_FILE):
                with open(USAGE_FILE, "r") as f:
                    self._usage = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load usage: {e}")

    def _save(self):
        try:
            with open(USERS_FILE, "w") as f:
                json.dump(self._users, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save users: {e}")

    def _save_usage(self):
        try:
            with open(USAGE_FILE, "w") as f:
                json.dump(self._usage, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save usage: {e}")
