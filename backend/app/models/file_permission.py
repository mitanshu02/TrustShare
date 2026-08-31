import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FilePermission(Base):
    __tablename__ = "file_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    access_level: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    file: Mapped["File"] = relationship(back_populates="permissions")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    granter: Mapped["User"] = relationship(foreign_keys=[granted_by])

    __table_args__ = (
        UniqueConstraint("file_id", "user_id", name="uq_file_permissions_file_user"),
        CheckConstraint(
            "access_level IN ('view', 'download')",
            name="ck_file_permissions_access_level",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FilePermission file_id={self.file_id} user_id={self.user_id} "
            f"level={self.access_level!r}>"
        )