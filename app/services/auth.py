from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
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
    async def authenticate_user(db: AsyncSession, email: str, password: str):
        user = await AuthService.get_user_by_email(db, email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user