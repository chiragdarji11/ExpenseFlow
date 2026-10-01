"""
ExpenseFlow - Budgets Controller
RESTful API endpoints for managing monthly category budgets and spending limits.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetMonthlySummary
)
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=BudgetMonthlySummary)
def get_budgets(
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all category budgets for the specified month and year,
    including real-time spent amount, remaining balance, and usage percentage.
    """
    return BudgetService.get_monthly_budgets(
        db=db,
        user_id=current_user.id,
        month=month,
        year=year
    )


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a monthly budget for an expense category."""
    return BudgetService.create_budget(db=db, user_id=current_user.id, budget_in=budget_in)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_in: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the budget amount for an existing monthly budget."""
    return BudgetService.update_budget(
        db=db,
        user_id=current_user.id,
        budget_id=budget_id,
        budget_in=budget_in
    )


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a monthly budget."""
    return BudgetService.delete_budget(db=db, user_id=current_user.id, budget_id=budget_id)
