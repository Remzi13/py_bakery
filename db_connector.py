# db_connector.py (Теперь для SQLite)
import sqlite3
from sqlite3 import Error
import os

# Имя файла базы данных (будет создан в той же папке)
DB_FILE = 'bakery_data.db' 

class DBConnector:
    """
    Класс для управления подключением к базе данных SQLite.
    """
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.connection = None
        self.connect()

    def connect(self):
        """Устанавливает соединение с базой данных и создает файл, если он не существует."""
        try:
            # Создаст файл, если его нет
            self.connection = sqlite3.connect(self.db_file) 
            self.connection.row_factory = sqlite3.Row # Позволяет получать результаты как словари/объекты
            print(f"Успешное подключение к SQLite базе данных '{self.db_file}'")
            self.create_tables() # Убедимся, что таблицы созданы
        except Error as e:
            print(f"Ошибка при подключении к SQLite: {e}")
            self.connection = None
            
    def disconnect(self):
        """Закрывает соединение."""
        if self.connection:
            self.connection.close()
            print("Соединение с базой данных закрыто.")

    def create_tables(self):
        """Создает таблицы, если они еще не существуют."""
        if not self.connection:
            return

        cursor = self.connection.cursor()
        
        # Запросы для создания таблиц (адаптированные для синтаксиса SQLite)
        sql_commands = [
            # 1. Ingredients
            """
            CREATE TABLE IF NOT EXISTS Ingredients (
                ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                unit_of_measure TEXT NOT NULL,
                current_stock REAL NOT NULL DEFAULT 0.0
            )
            """,
            # 2. Ingredient_Purchases
            """
            CREATE TABLE IF NOT EXISTS Ingredient_Purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                purchase_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                quantity_bought REAL NOT NULL,
                price_per_unit REAL NOT NULL,
                total_cost REAL NOT NULL,
                FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id)
            )
            """,
            # 3. Products
            """
            CREATE TABLE IF NOT EXISTS Products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                selling_price REAL NOT NULL,
                unit_of_measure TEXT NOT NULL DEFAULT 'штуки'
            )
            """,
            # 4. Recipe
            """
            CREATE TABLE IF NOT EXISTS Recipe (
                recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity_needed REAL NOT NULL,
                UNIQUE (product_id, ingredient_id),
                FOREIGN KEY (product_id) REFERENCES Products(product_id),
                FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id)
            )
            """,
            # 5. Sales
            """
            CREATE TABLE IF NOT EXISTS Sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                product_id INTEGER NOT NULL,
                quantity_sold INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                total_amount REAL NOT NULL DEFAULT 0.00,
                FOREIGN KEY (product_id) REFERENCES Products(product_id)
            )
            """,
            # 6. Expenses
            """
            CREATE TABLE IF NOT EXISTS Expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date TEXT NOT NULL,
                amount REAL NOT NULL,
                comment TEXT
            )
            """
        ]
        
        try:
            for command in sql_commands:
                cursor.execute(command)
            self.connection.commit()
            print("Таблицы SQLite успешно проверены/созданы.")
        except Error as e:
            print(f"Ошибка при создании таблиц SQLite: {e}")

    def execute_query(self, query, params=None, fetch=False):
        """
        Выполняет SQL-запрос.
        
        :param query: SQL-запрос для выполнения.
        :param params: Кортеж или список параметров для запроса.
        :param fetch: Если True, возвращает результат (для SELECT запросов).
        :return: Результат запроса (если fetch=True), или True/None.
        """
        if not self.connection:
            print("Не удалось выполнить запрос: нет активного подключения.")
            return None

        cursor = self.connection.cursor()
        try:
            # Заменяем %s на ? для SQLite
            sqlite_query = query.replace('%s', '?') 
            cursor.execute(sqlite_query, params or ())
            
            if fetch:
                # В SQLite нет DATETIME/NOW(), используем strftime для форматирования
                return cursor.fetchall() 
            else:
                self.connection.commit()
                return True
        except Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()