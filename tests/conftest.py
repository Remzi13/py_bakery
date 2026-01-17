import pytest
import sqlite3
from fastapi.testclient import TestClient
from main import app
from api.dependencies import get_model
from sql_model.model import SQLiteModel
from sql_model.database import initialize_db

# 1. Постоянное соединение остается на уровне модуля
mem_conn = sqlite3.connect(":memory:", check_same_thread=False)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Инициализирует структуру таблиц один раз на всю сессию."""
    initialize_db(mem_conn)
    yield
    mem_conn.close()

@pytest.fixture(scope="session")
def test_model():
    """Создает модель, привязанную к общему соединению в памяти."""
    model = SQLiteModel(db_file=':memory:')
    model.conn = mem_conn 
    return model

@pytest.fixture(scope="session", autouse=True)
def session_override_get_model(test_model):
    """
    Глобально подменяет модель для всех тестов сессии.
    Используем autouse=True и scope="session".
    """
    app.dependency_overrides[get_model] = lambda: test_model
    yield
    app.dependency_overrides.clear()

# 2. Создаем клиент как фикстуру, а не как глобальную переменную
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c