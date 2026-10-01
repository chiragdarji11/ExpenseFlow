"""
ExpenseFlow - Transaction Domain Service
Encapsulates business logic, search filtering, aggregation, and persistence for Transactions.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

import math
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, or_

from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    PaginatedTransactions
)


class TransactionService:
    @staticmethod
    def get_transactions(
        db: Session,
        user_id: int,
        search: Optional[str] = None,
        tx_type: Optional[TransactionType] = None,
        category_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 15
    ) -> PaginatedTransactions:
        """
        Queries transactions with multi-field filtering, search, sorting,
        pagination, and aggregate sums for the current tenant.
        """
        base_query = db.query(Transaction).join(Category).filter(Transaction.user_id == user_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            base_query = base_query.filter(
                or_(
                    Transaction.description.ilike(search_pattern),
                    Category.name.ilike(search_pattern)
                )
            )

        if tx_type:
            base_query = base_query.filter(Transaction.type == tx_type)

        if category_id:
            base_query = base_query.filter(Transaction.category_id == category_id)

        if start_date:
            base_query = base_query.filter(Transaction.transaction_date >= start_date)

        if end_date:
            base_query = base_query.filter(Transaction.transaction_date <= end_date)

        if min_amount is not None:
            base_query = base_query.filter(Transaction.amount >= min_amount)

        if max_amount is not None:
            base_query = base_query.filter(Transaction.amount <= max_amount)

        # Aggregate calculations for filtered scope
        aggregates = base_query.with_entities(
            func.count(Transaction.id).label("total_count"),
            func.coalesce(
                func.sum(case((Transaction.type == TransactionType.INCOME, Transaction.amount), else_=0)),
                0
            ).label("income_sum"),
            func.coalesce(
                func.sum(case((Transaction.type == TransactionType.EXPENSE, Transaction.amount), else_=0)),
                0
            ).label("expense_sum"),
        ).first()

        total_count = aggregates.total_count if aggregates else 0
        total_income = Decimal(str(aggregates.income_sum)) if aggregates else Decimal("0.00")
        total_expense = Decimal(str(aggregates.expense_sum)) if aggregates else Decimal("0.00")

        # Sorting strategy
        if sort_by == "amount":
            order_col = Transaction.amount.desc() if sort_order == "desc" else Transaction.amount.asc()
        else:
            order_col = Transaction.transaction_date.desc() if sort_order == "desc" else Transaction.transaction_date.asc()

        # Pagination window
        offset = (page - 1) * page_size
        items = (
            base_query
            .options(joinedload(Transaction.category))
            .order_by(order_col, Transaction.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return PaginatedTransactions(
            items=[TransactionResponse.model_validate(item) for item in items],
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_income=total_income,
            total_expense=total_expense
        )

    @staticmethod
    def create_transaction(
        db: Session,
        user_id: int,
        tx_in: TransactionCreate
    ) -> Transaction:
        """
        Validates category ownership and compatibility, then records a new transaction.
        """
        category = db.query(Category).filter(
            Category.id == tx_in.category_id,
            Category.user_id == user_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified category does not exist."
            )

        if category.type != CategoryType.BOTH and category.type.value != tx_in.type.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category.name}' is an {category.type.value} category and cannot be used for {tx_in.type.value} transactions."
            )

        new_tx = Transaction(
            user_id=user_id,
            category_id=tx_in.category_id,
            type=tx_in.type,
            amount=tx_in.amount,
            description=tx_in.description.strip(),
            transaction_date=tx_in.transaction_date
        )
        db.add(new_tx)
        db.commit()
        db.refresh(new_tx)

        new_tx.category = category
        return new_tx

    @staticmethod
    def get_transaction(
        db: Session,
        user_id: int,
        transaction_id: int
    ) -> Transaction:
        """
        Retrieves a single transaction by ID scoped to current user.
        """
        tx = (
            db.query(Transaction)
            .options(joinedload(Transaction.category))
            .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
            .first()
        )
        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found."
            )
        return tx

    @staticmethod
    def update_transaction(
        db: Session,
        user_id: int,
        transaction_id: int,
        tx_in: TransactionUpdate
    ) -> Transaction:
        """
        Updates an existing transaction ensuring multi-tenant ownership and category rules.
        """
        tx = TransactionService.get_transaction(db, user_id, transaction_id)

        target_category_id = tx_in.category_id if tx_in.category_id is not None else tx.category_id
        target_type = tx_in.type if tx_in.type is not None else tx.type

        category = db.query(Category).filter(
            Category.id == target_category_id,
            Category.user_id == user_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified category does not exist."
            )

        if category.type != CategoryType.BOTH and category.type.value != target_type.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category.name}' is an {category.type.value} category and cannot be used for {target_type.value} transactions."
            )

        if tx_in.category_id is not None:
            tx.category_id = tx_in.category_id
            tx.category = category
        if tx_in.type is not None:
            tx.type = tx_in.type
        if tx_in.amount is not None:
            tx.amount = tx_in.amount
        if tx_in.description is not None:
            tx.description = tx_in.description.strip()
        if tx_in.transaction_date is not None:
            tx.transaction_date = tx_in.transaction_date

        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def delete_transaction(
        db: Session,
        user_id: int,
        transaction_id: int
    ) -> dict:
        """
        Deletes a transaction scoped to the current user.
        """
        tx = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()

        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found."
            )

        db.delete(tx)
        db.commit()
        return {"message": "Transaction deleted successfully."}
