import secrets

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="管理员登录")
async def login(payload: LoginRequest) -> TokenResponse:
    username_valid = secrets.compare_digest(payload.username, settings.admin_username)
    password_valid = secrets.compare_digest(payload.password, settings.admin_password)
    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(payload.username))
