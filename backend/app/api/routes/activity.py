from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.activity import get_activity_feed
from app.db.session import get_db
from app.models.user import User
from app.schemas.file import ActivityEvent

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("", response_model=list[ActivityEvent])
def get_activity_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ActivityEvent]:
    return get_activity_feed(db, current_user.id)