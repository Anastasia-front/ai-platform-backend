from fastapi import Header, HTTPException, status

from app.core.database import AsyncSessionLocal


async def get_current_user(
    authorization: str | None = Header(default=None),
):
    """
    Fake auth dependency.
    Later this will decode JWT token.
    """

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return {
        "id": 1,
        "email": "user@example.com",
    }



async def get_db():
    async with AsyncSessionLocal() as session:
        yield session