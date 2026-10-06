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


@router.get("")
def list_audit_log(
    event_type: str | None = None,
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
        q=q,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/export")
def export_audit_log(
    event_type: str | None = None,
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