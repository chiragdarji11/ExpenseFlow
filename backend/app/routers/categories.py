"""
ExpenseFlow - Categories Controller
RESTful API endpoints for organizing income and expense classifications.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    type: Optional[str] = Query(None, description="Filter by type: income, expense, or both"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all categories belonging to the authenticated user."""
    return CategoryService.get_categories(db=db, user_id=current_user.id, type_filter=type)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new custom category for the user."""
    return CategoryService.create_category(db=db, user_id=current_user.id, category_in=category_in)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update category properties (name, type, icon, color)."""
    return CategoryService.update_category(
        db=db,
        user_id=current_user.id,
        category_id=category_id,
        category_in=category_in
    )


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Safely delete a category.
    Prevents deletion if there are transactions linked to this category.
    """
    return CategoryService.delete_category(db=db, user_id=current_user.id, category_id=category_id)
