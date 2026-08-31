import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True, index=True
    )

    original_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Reference to the encrypted object in cloud storage (S3/Azure Blob key),
    # never the file content itself.
    storage_key: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True
    )
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Reference to the file's unique AES-256 key in the key-management
    # system. The actual key is NEVER stored here or exposed to users.
    encryption_key_reference: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="files", foreign_keys=[owner_id])
    folder: Mapped["Folder | None"] = relationship(back_populates="files")
    versions: Mapped[list["FileVersion"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )
    permissions: Mapped[list["FilePermission"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )
    share_links: Mapped[list["ShareLink"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )
    downloads: Mapped[list["Download"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<File id={self.id} name={self.original_name!r} owner_id={self.owner_id}>"