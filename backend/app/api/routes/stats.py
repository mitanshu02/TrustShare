from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.stats import get_stats
from app.db.session import get_db
from app.models.user import User
from app.schemas.file import StatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def get_stats_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatsOut:
    return StatsOut(**get_stats(db, current_user.id))