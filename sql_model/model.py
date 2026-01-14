import sqlite3

# Импорт модулей
from sql_model.database import create_connection, initialize_db

from repositories.products import ProductsRepository
from repositories.stock import StockRepository
from repositories.sales import SalesRepository
from repositories.expense_types import ExpenseTypesRepository
from repositories.expenses import ExpensesRepository
from repositories.write_offs import WriteOffsRepository
from repositories.suppliers import SuppliersRepository
from repositories.orders import OrdersRepository
from repositories.utils import UtilsRepository

from repositories.expense_documents import ExpenseDocumentsRepository

class SQLiteModel:
    """
    Класс Модели для управления пекарней, использующий SQLite в качестве хранилища.
    Инкапсулирует соединения и предоставляет доступ к репозиториям.
    """
    
    def __init__(self, db_file: str = 'bakery_management.db'):
        """
        Инициализирует соединение с БД и репозитории.
        Если файл БД не существует, он будет создан и инициализирован.
        """
        self.db_file = db_file
        self._conn: sqlite3.Connection = create_connection(self.db_file)
        initialize_db(self._conn) # Создает таблицы и заполняет справочники
        
        # Инициализация репозиториев
        self._stock_repo = StockRepository(self._conn, self)
        self._expense_types_repo = ExpenseTypesRepository(self._conn)
        self._products_repo = ProductsRepository(self._conn, self)
        self._sales_repo = SalesRepository(self._conn, self)
        self._expenses_repo = ExpensesRepository(self._conn, self)
        self._utils_repo = UtilsRepository(self._conn)
        self._write_offs_repo = WriteOffsRepository(self._conn, self)
        self._suppliers_repo = SuppliersRepository(self._conn)
        self._orders_repo = OrdersRepository(self._conn, self)
        self._expense_documents_repo = ExpenseDocumentsRepository(self._conn, self)

    def close(self):
        """Закрывает соединение с базой данных."""
        if self._conn:
            self._conn.close()
            
    # --- Методы, возвращающие репозитории (интерфейс, как в старой модели) ---
    
    def utils(self) -> UtilsRepository:
       return self._utils_repo # <-- Новый метод

    def products(self) -> ProductsRepository:
        return self._products_repo
    
    def stock(self) -> StockRepository:
        return self._stock_repo

    def sales(self) -> SalesRepository:
        return self._sales_repo

    def expense_types(self) -> ExpenseTypesRepository:
        return self._expense_types_repo

    def expenses(self) -> ExpensesRepository:
        return self._expenses_repo

    def writeoffs(self) -> WriteOffsRepository:
        return self._write_offs_repo
    
    def suppliers(self) -> SuppliersRepository:
        return self._suppliers_repo
    
    def orders(self) -> OrdersRepository:
        return self._orders_repo

    def expense_documents(self) -> ExpenseDocumentsRepository:
        return self._expense_documents_repo
    
    def request(self, query):
        cursor = self._conn.cursor()
        cursor.execute(query)
        if query.lower().startswith("select"):
            rows = cursor.fetchall()
            headers = [d[0] for d in cursor.description]
            return rows, headers
        
        return None

    # --- Бизнес-логика (расчеты) ---

    def calculate_income(self) -> float:
        """Рассчитывает общий доход от продаж."""
        cursor = self._conn.cursor()        
        # Доход = Сумма (Цена * Количество * (1 - Скидка/100))
        cursor.execute(
            """
            SELECT SUM(price * quantity * (1 - CAST(discount AS REAL) / 100)) 
            FROM sales
            """
        )
        result = cursor.fetchone()[0]
        return result if result is not None else 0.0

    def calculate_expenses(self) -> float:
        """Рассчитывает общие расходы."""
        cursor = self._conn.cursor()
        # Расходы = Сумма (Цена * Количество)
        cursor.execute("SELECT SUM(price * quantity) FROM expenses")
        result = cursor.fetchone()[0]
        return result if result is not None else 0.0

    def calculate_profit(self) -> float:
        """Рассчитывает прибыль."""
        return self.calculate_income() - self.calculate_expenses()