from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import hash_password, settings, verify_password
from app.models import User


class AuthService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

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
        email = google_user.get("email") if google_user else None

        if not email:
            return None

        user = await AuthService.get_user_by_email(db, email)
        if user:
            return user

        random_password = f"Google-{uuid4()}!"
        return await AuthService.create_user(db, email, random_password)

    @staticmethod
    async def verify_google_credential(credential: str):
        if not settings.GOOGLE_CLIENT_ID:
            return None

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential},
            )

        if response.status_code != 200:
            return None

        payload = response.json()
        if payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            return None

        if payload.get("email_verified") not in (True, "true", "True", "1"):
            return None

        return payload

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str):
        user = await AuthService.get_user_by_email(db, email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user
