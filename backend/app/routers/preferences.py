"""
ExpenseFlow - User Preferences Controller
RESTful API endpoints for user notification and alert configurations.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user_preference import UserPreferenceUpdate, UserPreferenceResponse
from app.services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["User Preferences"])


@router.get("", response_model=UserPreferenceResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve notification and alert preferences for the authenticated user."""
    return PreferenceService.get_preferences(db=db, user_id=current_user.id)


@router.put("", response_model=UserPreferenceResponse)
def update_user_preferences(
    data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences for the authenticated user."""
    return PreferenceService.update_preferences(db=db, user_id=current_user.id, data=data)
