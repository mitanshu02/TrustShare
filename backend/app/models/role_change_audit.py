import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RoleChangeAudit(Base):
    """
    Immutable audit trail of every role change on the platform. Rows are
    never updated or deleted — only inserted. See docs/security-design.md
    (audit logging requirement for permission changes).
    """

    __tablename__ = "role_change_audits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    old_role: Mapped[str] = mapped_column(String(20), nullable=False)
    new_role: Mapped[str] = mapped_column(String(20), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    changer: Mapped["User"] = relationship(foreign_keys=[changed_by])
    target_user: Mapped["User"] = relationship(foreign_keys=[target_user_id])

    def __repr__(self) -> str:
        return (
            f"<RoleChangeAudit target={self.target_user_id} "
            f"{self.old_role}->{self.new_role} by={self.changed_by}>"
        )