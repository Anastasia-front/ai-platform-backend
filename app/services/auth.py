from uuid import uuid4

import httpx
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    settings,
    verify_password,
)
from app.models import User
from app.schemas import TokenResponse


class GoogleAuthError(Exception):
    pass


class AuthTokenError(Exception):
    pass


class AuthService:
    @staticmethod
    def token_response_for_user(user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token({"sub": str(user.id)}),
            refresh_token=create_refresh_token({"sub": str(user.id)}),
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_refresh_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> User:
        try:
            payload = decode_access_token(refresh_token)
            if payload.get("typ") != "refresh":
                raise AuthTokenError("Invalid refresh token")
            user_id = int(payload.get("sub"))
        except (JWTError, TypeError, ValueError) as exc:
            raise AuthTokenError("Invalid refresh token") from exc

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise AuthTokenError("User not found")

        return user

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> TokenResponse:
        user = await AuthService.get_user_by_refresh_token(db, refresh_token)
        return AuthService.token_response_for_user(user)

    @staticmethod
    async def create_user(db: AsyncSession, email: str, password: str):
        user = User(
            email=email,
            hashed_password=hash_password(password),
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_or_create_google_user(db: AsyncSession, credential: str):
        google_user = await AuthService.verify_google_credential(credential)
        email = google_user.get("email")

        if not email:
            raise GoogleAuthError("Google token did not include an email address.")

        user = await AuthService.get_user_by_email(db, email)
        if user:
            return user

        random_password = f"Google-{uuid4()}!"
        return await AuthService.create_user(db, email, random_password)

    @staticmethod
    async def verify_google_credential(credential: str):
        if not settings.GOOGLE_CLIENT_ID:
            raise GoogleAuthError("Backend GOOGLE_CLIENT_ID is not configured.")

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential},
            )

        if response.status_code != 200:
            try:
                detail = response.json().get("error_description") or response.text
            except ValueError:
                detail = response.text
            raise GoogleAuthError(f"Google token verification failed: {detail}")

        payload = response.json()
        if payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise GoogleAuthError(
                "Google token audience does not match backend GOOGLE_CLIENT_ID."
            )

        if payload.get("email_verified") not in (True, "true", "True", "1"):
            raise GoogleAuthError("Google account email is not verified.")

        return payload

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str):
        user = await AuthService.get_user_by_email(db, email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user
