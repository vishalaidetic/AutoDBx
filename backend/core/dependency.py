"""
FastAPI Dependency Injection
----------------------------
Provides the DB session dependency for use in route handlers.
"""

from typing import Generator

from core.database import SessionLocal
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy DB session
    and guarantees it is closed after the request completes.

    Usage in routes:
        @router.get("/")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

