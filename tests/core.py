import pytest
import sqlite3

from sql_model.model import SQLiteModel
from sql_model.database import create_connection, initialize_db, get_unit_by_name

TEST_DB = ':memory:'

@pytest.fixture
def conn():
    """Предоставляет чистое, инициализированное соединение с БД в памяти."""
    conn = create_connection(TEST_DB)
    initialize_db(conn)
    yield conn
    conn.close()

@pytest.fixture
def model(conn: sqlite3.Connection):
    """Предоставляет экземпляр SQLiteModel, использующий то же соединение."""
    # Мы используем SQLiteModel, чтобы корректно инициализировать все зависимости
    # и иметь доступ к вспомогательным репозиториям.
    # Фактически, мы тестируем репозитории, используя Model как Фабрику.
    return SQLiteModel(db_file=TEST_DB)
