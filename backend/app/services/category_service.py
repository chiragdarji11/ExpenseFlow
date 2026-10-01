"""
ExpenseFlow - Category Domain Service
Encapsulates business logic, duplicate prevention, relational integrity checks, and persistence for Categories.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryType
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    @staticmethod
    def get_categories(
        db: Session,
        user_id: int,
        type_filter: Optional[str] = None
    ) -> List[Category]:
        """
        Retrieves all categories for the authenticated tenant with optional type filtering.
        """
        query = db.query(Category).filter(Category.user_id == user_id)

        if type_filter:
            type_lower = type_filter.lower()
            if type_lower in ["income", "expense"]:
                query = query.filter((Category.type == type_lower) | (Category.type == CategoryType.BOTH))
            elif type_lower == "both":
                query = query.filter(Category.type == CategoryType.BOTH)

        return query.order_by(Category.name.asc()).all()

    @staticmethod
    def create_category(
        db: Session,
        user_id: int,
        category_in: CategoryCreate
    ) -> Category:
        """
        Validates duplicate names per type and creates a user category.
        """
        existing = db.query(Category).filter(
            Category.user_id == user_id,
            Category.name.ilike(category_in.name.strip()),
            Category.type == category_in.type
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{category_in.name}' of type '{category_in.type.value}' already exists."
            )

        new_cat = Category(
            user_id=user_id,
            name=category_in.name.strip(),
            type=category_in.type,
            icon=category_in.icon or "tag",
            color=category_in.color or "#6366F1",
            is_default=False
        )
        db.add(new_cat)
        db.commit()
        db.refresh(new_cat)
        return new_cat

    @staticmethod
    def get_category(
        db: Session,
        user_id: int,
        category_id: int
    ) -> Category:
        """
        Retrieves a category by ID scoped to current user.
        """
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )
        return category

    @staticmethod
    def update_category(
        db: Session,
        user_id: int,
        category_id: int,
        category_in: CategoryUpdate
    ) -> Category:
        """
        Updates category attributes with duplicate verification.
        """
        category = CategoryService.get_category(db, user_id, category_id)

        if category_in.name is not None:
            target_name = category_in.name.strip()
            target_type = category_in.type if category_in.type is not None else category.type

            duplicate = db.query(Category).filter(
                Category.user_id == user_id,
                Category.id != category.id,
                Category.name.ilike(target_name),
                Category.type == target_type
            ).first()
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category '{target_name}' already exists."
                )
            category.name = target_name

        if category_in.type is not None:
            category.type = category_in.type
        if category_in.icon is not None:
            category.icon = category_in.icon
        if category_in.color is not None:
            category.color = category_in.color

        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete_category(
        db: Session,
        user_id: int,
        category_id: int
    ) -> dict:
        """
        Deletes a category ensuring relational integrity is preserved.
        Rejects deletion if active transactions are associated.
        """
        category = CategoryService.get_category(db, user_id, category_id)

        linked_tx_count = db.query(Transaction).filter(
            Transaction.category_id == category_id,
            Transaction.user_id == user_id
        ).count()

        if linked_tx_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot delete category '{category.name}' because {linked_tx_count} transaction(s) "
                    "are linked to it. Please reassign or delete these transactions first."
                )
            )

        db.delete(category)
        db.commit()
        return {"message": f"Category '{category.name}' deleted successfully."}
