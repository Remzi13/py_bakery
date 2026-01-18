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


def get_model() -> Generator[SQLAlchemyModel, None, None]:
    """
    Creates a new SQLAlchemyModel instance for each request
    and ensures the connection is closed after the request is processed.
    """
    model = SQLAlchemyModel()
    try:
        yield model
    finally:
        model.close()
