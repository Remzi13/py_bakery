"""API dependencies for FastAPI routes."""

from typing import Generator
from sqlalchemy.orm import Session
from sql_model.database import SessionLocal
from sql_model.model import SQLAlchemyModel


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from fastapi import Depends

def get_model(db: Session = Depends(get_db)) -> Generator[SQLAlchemyModel, None, None]:
    """
    Creates a new SQLAlchemyModel instance for each request
    using the provided database session.
    """
    model = SQLAlchemyModel(db=db)
    try:
        yield model
    finally:
        # Note: we don't call model.close() here because it would close the db session
        # which is managed by get_db.
        pass
