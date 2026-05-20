from datetime import datetime, timezone

from fastapi import APIRouter, status

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
):
    return {
        "id": 1,
        "email": payload.email,
        "created_at": datetime.now(timezone.utc),
    }


@router.post("/login")
async def login(
    payload: LoginRequest,
):
    return {
        "access_token": "fake-jwt-token",
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me():
    return {
        "id": 1,
        "email": "user@example.com",
        "created_at": datetime.now(timezone.utc),
    }