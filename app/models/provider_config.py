from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ProviderConfig(TimestampMixin, Base):
    __tablename__ = "provider_configs"
    __table_args__ = (
        UniqueConstraint("kind", "provider", name="uq_provider_configs_kind_provider"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    kind: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    fallback_model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    base_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    encrypted_api_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    dimensions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
