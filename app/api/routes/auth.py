
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import create_access_token, get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import RegisterRequest, UserResponse
from app.services import AuthService

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
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
    }

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