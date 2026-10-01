"""
ExpenseFlow - Transactions Controller
RESTful API endpoints for recording and retrieving financial transactions.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    PaginatedTransactions
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=PaginatedTransactions)
def get_transactions(
    search: Optional[str] = Query(None, description="Search description or category name"),
    type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category_id: Optional[int] = Query(None, description="Filter by specific category"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    min_amount: Optional[Decimal] = Query(None, ge=0, description="Minimum amount filter"),
    max_amount: Optional[Decimal] = Query(None, ge=0, description="Maximum amount filter"),
    sort_by: str = Query("date", pattern="^(date|amount)$", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List transactions with rich filtering, search, sorting, and pagination.
    Includes aggregate totals matching the filtered query scope.
    """
    return TransactionService.get_transactions(
        db=db,
        user_id=current_user.id,
        search=search,
        tx_type=type,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a new income or expense transaction."""
    return TransactionService.create_transaction(db=db, user_id=current_user.id, tx_in=tx_in)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve details of a specific transaction."""
    return TransactionService.get_transaction(db=db, user_id=current_user.id, transaction_id=transaction_id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    tx_in: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing transaction."""
    return TransactionService.update_transaction(
        db=db,
        user_id=current_user.id,
        transaction_id=transaction_id,
        tx_in=tx_in
    )


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction."""
    return TransactionService.delete_transaction(db=db, user_id=current_user.id, transaction_id=transaction_id)
