"""FastAPI routes for authentication — sign up, sign in, OAuth."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Lazy-init to avoid circular imports at module level
_user_manager = None


def _get_manager():
    global _user_manager
    if _user_manager is None:
        from backend.core.auth_manager import UserManager
        _user_manager = UserManager()
    return _user_manager


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""


class SendOtpRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class ResendOtpRequest(BaseModel):
    email: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str


class ResendResetOtpRequest(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class OAuthRequest(BaseModel):
    email: str
    name: str
    provider: str  # "google" or "github"


class TokenRequest(BaseModel):
    token: str


@router.post("/send-otp")
async def send_otp(req: SendOtpRequest):
    result = _get_manager().initiate_registration(req.email, req.password, req.name or "")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/verify-otp")
async def verify_otp(req: VerifyOtpRequest):
    result = _get_manager().verify_otp_and_register(req.email, req.otp)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/resend-otp")
async def resend_otp(req: ResendOtpRequest):
    result = _get_manager().resend_otp(req.email)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    result = _get_manager().initiate_password_reset(req.email)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    result = _get_manager().verify_and_reset_password(req.email, req.otp, req.new_password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/resend-reset-otp")
async def resend_reset_otp(req: ResendResetOtpRequest):
    result = _get_manager().resend_password_reset_otp(req.email)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/register")
async def register(req: RegisterRequest):
    result = _get_manager().register(req.email, req.password, req.name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/login")
async def login(req: LoginRequest):
    result = _get_manager().login(req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@router.post("/oauth")
async def oauth_login(req: OAuthRequest):
    result = _get_manager().oauth_login(req.email, req.name, req.provider)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/verify")
async def verify_token(req: TokenRequest):
    email = _get_manager().verify_token(req.token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user = _get_manager()._users.get(email, {})
    return {"valid": True, "user": {"email": email, "name": user.get("name", "")}}


@router.post("/usage")
async def check_usage(req: TokenRequest):
    email = _get_manager().verify_token(req.token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return _get_manager().check_usage(email)
