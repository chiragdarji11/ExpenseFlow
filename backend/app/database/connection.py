import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Normalize DATABASE_URL for PyMySQL or SQLite
db_url = settings.DATABASE_URL
if db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
elif db_url.startswith("sqlite"):
    if not db_url.startswith("sqlite:////") and ":\\" not in db_url and ":/" not in db_url:
        db_name = db_url.replace("sqlite:///", "")
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), db_name).replace("\\", "/")
        db_url = f"sqlite:///{db_path}"



def build_engine(url: str):
    """Builds a SQLAlchemy engine configured for either MySQL or SQLite."""
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    return create_engine(
        url,
        connect_args={"connect_timeout": 3} if "pymysql" in url else {},
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=False
    )


engine = build_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy database session
    and guarantees closure after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_db_connection() -> bool:
    """Utility function to test database connectivity with automatic SQLite fallback."""
    global engine, SessionLocal
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[Database Connection Notice] MySQL not reachable on port 3306: {e}")
        # If MySQL is not available, gracefully fallback to local SQLite
        if not str(engine.url).startswith("sqlite"):
            print("[Database] Automatically switching to local SQLite database (expense_flow.db)...")
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            fallback_path = os.path.join(base_dir, "expense_flow.db").replace("\\", "/")
            fallback_url = f"sqlite:///{fallback_path}"
            engine = build_engine(fallback_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print("[Database] SQLite database connected successfully!")
                return True
            except Exception as e2:
                print(f"[Database Error] SQLite fallback failed: {e2}")
        return False


def sync_database_schema():
    """Ensures all new tables and columns are created additively without data loss."""
    from app.database.base import Base
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Check and add recurring_transaction_id column to transactions if missing (MySQL only)
    if "mysql" in str(engine.url):
        try:
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_schema = DATABASE() AND table_name = 'transactions' AND column_name = 'recurring_transaction_id'"
                ))
                exists = result.scalar()
                if not exists:
                    conn.execute(text(
                        "ALTER TABLE transactions ADD COLUMN recurring_transaction_id INT NULL"
                    ))
                    try:
                        conn.execute(text(
                            "ALTER TABLE transactions ADD CONSTRAINT fk_transactions_recurring "
                            "FOREIGN KEY (recurring_transaction_id) REFERENCES recurring_transactions(id) ON DELETE SET NULL"
                        ))
                    except Exception:
                        pass
                    conn.commit()
                    print("[Database Migration] Added recurring_transaction_id column to transactions table.")
        except Exception as e:
            print(f"[Database Migration Warning] Error running additive migrations: {e}")


