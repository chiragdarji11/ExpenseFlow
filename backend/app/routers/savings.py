"""
ExpenseFlow - Savings Goals Controller
RESTful API endpoints for goal tracking, funding, and progress monitoring.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.savings_goal import (
    GoalCreate,
    GoalUpdate,
    GoalDepositRequest,
    GoalResponse
)
from app.services.savings_service import SavingsService

router = APIRouter(prefix="/goals", tags=["Savings Goals"])


@router.get("", response_model=List[GoalResponse])
def get_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all savings goals for the current user."""
    return SavingsService.get_goals(db=db, user_id=current_user.id)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_in: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new savings goal."""
    return SavingsService.create_goal(db=db, user_id=current_user.id, goal_in=goal_in)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single savings goal."""
    return SavingsService._build_goal_response(
        SavingsService.get_goal(db=db, user_id=current_user.id, goal_id=goal_id)
    )


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_in: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update goal properties."""
    return SavingsService.update_goal(
        db=db,
        user_id=current_user.id,
        goal_id=goal_id,
        goal_in=goal_in
    )


@router.post("/{goal_id}/deposit", response_model=GoalResponse)
def adjust_funds(
    goal_id: int,
    deposit_in: GoalDepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add or withdraw funds from a savings goal."""
    return SavingsService.deposit_or_withdraw(
        db=db,
        user_id=current_user.id,
        goal_id=goal_id,
        deposit_in=deposit_in
    )


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a savings goal."""
    return SavingsService.delete_goal(db=db, user_id=current_user.id, goal_id=goal_id)
