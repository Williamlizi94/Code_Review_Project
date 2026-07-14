import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Full audit trail for all significant operations."""

    __tablename__ = "audit_logs"

    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # Action: review.submit | knowledge.upload | user.login | webhook.receive | ...
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # SHA-256 digest of input payload (for integrity verification)
    input_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # SHA-256 digest of output result
    output_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # OpenTelemetry trace ID
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Client IP for HTTP requests
    client_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Extra context
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    operator: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="audit_logs"
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by={self.operator_id}>"
