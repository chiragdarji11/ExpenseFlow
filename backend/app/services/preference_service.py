"""
ExpenseFlow - User Preference Domain Service
Encapsulates retrieval and mutation of user notification preferences.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from sqlalchemy.orm import Session
from app.models.user_preference import UserPreference
from app.schemas.user_preference import UserPreferenceUpdate
from app.services.notification_service import NotificationService


class PreferenceService:
    @staticmethod
    def get_preferences(db: Session, user_id: int) -> UserPreference:
        """Retrieves or lazily provisions user notification preferences."""
        return NotificationService.get_user_preferences(db, user_id)

    @staticmethod
    def update_preferences(
        db: Session,
        user_id: int,
        data: UserPreferenceUpdate
    ) -> UserPreference:
        """Applies partial updates to user preferences and persists changes."""
        pref = NotificationService.get_user_preferences(db, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            setattr(pref, field, val)

        db.commit()
        db.refresh(pref)
        return pref
