from typing import Generator
from sql_model.model import SQLiteModel

def get_model() -> Generator[SQLiteModel, None, None]:
    """
    Creates a new SQLiteModel instance for each request
    and ensures the connection is closed after the request is processed.
    """
    model = SQLiteModel()
    try:
        yield model
    finally:
        model.close()
