"""
ExpenseFlow - Savings Goals Domain Service
Encapsulates business logic, balance adjustments, auto-completion, and persistence for Savings Goals.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from decimal import Decimal
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.savings_goal import SavingsGoal, GoalStatus
from app.schemas.savings_goal import (
    GoalCreate,
    GoalUpdate,
    GoalDepositRequest,
    GoalResponse
)


class SavingsService:
    @staticmethod
    def _build_goal_response(goal: SavingsGoal) -> GoalResponse:
        """Helper to transform ORM SavingsGoal to rich GoalResponse with calculated metrics."""
        target = Decimal(str(goal.target_amount))
        current = Decimal(str(goal.current_amount))
        remaining = max(Decimal("0.00"), target - current)
        pct = float(round((current / target) * 100, 1)) if target > 0 else 0.0

        return GoalResponse(
            id=goal.id,
            user_id=goal.user_id,
            name=goal.name,
            target_amount=target,
            current_amount=current,
            remaining_amount=remaining,
            progress_percentage=pct,
            target_date=goal.target_date,
            description=goal.description,
            status=goal.status,
            created_at=goal.created_at,
            updated_at=goal.updated_at
        )

    @staticmethod
    def get_goals(db: Session, user_id: int) -> List[GoalResponse]:
        """Retrieves all savings goals for the tenant ordered by recency."""
        goals = (
            db.query(SavingsGoal)
            .filter(SavingsGoal.user_id == user_id)
            .order_by(SavingsGoal.created_at.desc())
            .all()
        )
        return [SavingsService._build_goal_response(g) for g in goals]

    @staticmethod
    def create_goal(db: Session, user_id: int, goal_in: GoalCreate) -> GoalResponse:
        """Creates a new savings goal with initial funding status calculation."""
        initial = goal_in.initial_amount or Decimal("0.00")
        status_val = GoalStatus.COMPLETED if initial >= goal_in.target_amount else GoalStatus.IN_PROGRESS

        new_goal = SavingsGoal(
            user_id=user_id,
            name=goal_in.name.strip(),
            target_amount=goal_in.target_amount,
            current_amount=initial,
            target_date=goal_in.target_date,
            description=goal_in.description.strip() if goal_in.description else None,
            status=status_val
        )
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        return SavingsService._build_goal_response(new_goal)

    @staticmethod
    def get_goal(db: Session, user_id: int, goal_id: int) -> SavingsGoal:
        """Retrieves a single savings goal by ID."""
        goal = db.query(SavingsGoal).filter(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user_id
        ).first()

        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Savings goal not found."
            )
        return goal

    @staticmethod
    def update_goal(
        db: Session,
        user_id: int,
        goal_id: int,
        goal_in: GoalUpdate
    ) -> GoalResponse:
        """Updates goal details and recalibrates progress status."""
        goal = SavingsService.get_goal(db, user_id, goal_id)

        if goal_in.name is not None:
            goal.name = goal_in.name.strip()
        if goal_in.target_amount is not None:
            goal.target_amount = goal_in.target_amount
        if goal_in.target_date is not None:
            goal.target_date = goal_in.target_date
        if goal_in.description is not None:
            goal.description = goal_in.description.strip()
        if goal_in.status is not None:
            goal.status = goal_in.status
        else:
            if goal.current_amount >= goal.target_amount:
                goal.status = GoalStatus.COMPLETED
            else:
                goal.status = GoalStatus.IN_PROGRESS

        db.commit()
        db.refresh(goal)
        return SavingsService._build_goal_response(goal)

    @staticmethod
    def deposit_or_withdraw(
        db: Session,
        user_id: int,
        goal_id: int,
        deposit_in: GoalDepositRequest
    ) -> GoalResponse:
        """Safely credits or debits a goal's funds with negative balance guards."""
        goal = SavingsService.get_goal(db, user_id, goal_id)

        current = Decimal(str(goal.current_amount))
        amount = deposit_in.amount

        if deposit_in.action == "withdraw":
            if amount > current:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot withdraw {amount}. Current savings balance is {current}."
                )
            goal.current_amount = current - amount
        else:  # deposit
            goal.current_amount = current + amount

        # Automatically adjust completion status
        if goal.current_amount >= goal.target_amount:
            goal.status = GoalStatus.COMPLETED
        else:
            goal.status = GoalStatus.IN_PROGRESS

        db.commit()
        db.refresh(goal)
        return SavingsService._build_goal_response(goal)

    @staticmethod
    def delete_goal(db: Session, user_id: int, goal_id: int) -> dict:
        """Deletes a savings goal scoped to current user."""
        goal = SavingsService.get_goal(db, user_id, goal_id)
        db.delete(goal)
        db.commit()
        return {"message": "Savings goal deleted successfully."}
