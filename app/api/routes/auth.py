
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    GoogleLoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import AuthService, AuthTokenError
from app.services.auth import GoogleAuthError

router = APIRouter()


# -------------------------------------------------
# REGISTER USER
# -------------------------------------------------
@router.post(
    "/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED
    )
async def register(
    payload: RegisterRequest, 
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.create_user(db, payload.email, payload.password)

    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )

# -------------------------------------------------
# LOGIN USER
# -------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthService.token_response_for_user(user)

# -------------------------------------------------
# GOOGLE AUTH
# -------------------------------------------------
@router.post("/google", response_model=TokenResponse)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await AuthService.get_or_create_google_user(db, payload.credential)
    except GoogleAuthError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    return AuthService.token_response_for_user(user)

# -------------------------------------------------
# REFRESH TOKEN
# -------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await AuthService.refresh_token(db, payload.refresh_token)
    except AuthTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

# -------------------------------------------------
# GET CURRENT USER
# -------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )
