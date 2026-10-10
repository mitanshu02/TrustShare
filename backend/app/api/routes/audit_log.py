import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.monitoring import get_audit_log_for_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/api/audit-log", tags=["audit-log"])

# Groupings used by the Activity page's category tabs (All / Uploads /
# Downloads / Shares / Security). Kept here rather than in the crud
# layer since this is a presentation-level grouping, not a domain rule.
CATEGORY_EVENT_TYPES = {
    "uploads": ["file_uploaded"],
    "downloads": ["file_downloaded", "public_link_downloaded"],
    "shares": [
        "file_shared",
        "share_link_created",
        "share_link_revoked",
        "file_permission_updated",
        "file_permission_revoked",
    ],
    "security": [
        "login_success",
        "login_failed",
        "login_blocked",
        "suspicious_login_activity",
        "password_reset_requested",
        "password_reset_failed",
        "password_reset_success",
    ],
}


def _resolve_category(category: str | None) -> list[str] | None:
    if not category or category == "all":
        return None
    return CATEGORY_EVENT_TYPES.get(category)


@router.get("")
def list_audit_log(
    event_type: str | None = None,
    category: str | None = None,
    q: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return get_audit_log_for_user(
        db=db,
        user_id=current_user.id,
        event_type=event_type,
        event_types=_resolve_category(category),
        q=q,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/export")
def export_audit_log(
    event_type: str | None = None,
    category: str | None = None,
    q: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    CSV export of the same filtered view as list_audit_log, capped at
    5000 rows so a very active account can't produce an unbounded
    export in a single request.
    """
    report = get_audit_log_for_user(
        db=db,
        user_id=current_user.id,
        event_type=event_type,
        event_types=_resolve_category(category),
        q=q,
        date_from=date_from,
        date_to=date_to,
        limit=5000,
        offset=0,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Event", "Severity", "Actor", "File", "IP address", "Timestamp"])
    for event in report["events"]:
        writer.writerow(
            [
                event["event_type"],
                event["severity"],
                event["actor_email"] or "",
                event["file_name"] or "",
                event["ip_address"] or "",
                event["created_at"].isoformat() if event["created_at"] else "",
            ]
        )
    buffer.seek(0)

    filename = f"trustshare-audit-log-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
