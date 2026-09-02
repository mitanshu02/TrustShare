import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class FileEncryptionKey(Base):
    """
    Stores the raw AES-256 key material for an encrypted file, kept in a
    separate table from `files` so file metadata queries never touch key
    material. `files.encryption_key_reference` stores this row's id as a
    string — the key itself is never returned in any API response.

    TODO (production): move key_material into a real KMS / secrets
    manager (see docs/architecture.md) instead of this table. This table
    is a local stand-in until that's wired up.
    """

    __tablename__ = "file_encryption_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key_material: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )