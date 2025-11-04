import sqlite3
from typing import List, Dict, Tuple, Any, Optional

# Путь к файлу базы данных
DB_PATH = 'bakery_management.db'

# Начальные данные для справочников (Unit, Categories)
INITIAL_UNITS = [
    ('кг',), ('грамм',), ('литр',), ('штук',)
]

INITIAL_STOCK_CATEGORIES = [
    ('Сырье',), ('Упаковка',), ('Оборудование',)
]

INITIAL_EXPENSE_CATEGORIES = [
    ('Сырьё',), ('Оборудование',), ('Платежи',), ('Другое',)
]


def execute_scripts(conn: sqlite3.Connection, scripts: List[str]):
    """Выполняет список SQL скриптов."""
    cursor = conn.cursor()
    for script in scripts:
        cursor.execute(script)
    conn.commit()


def create_connection(db_file=DB_PATH) -> sqlite3.Connection:
    """Создает и возвращает соединение с базой данных SQLite."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Это позволит получать данные в виде словарей
    return conn


def initialize_db(conn: sqlite3.Connection):
    """Создает все необходимые таблицы и заполняет справочники."""

    # 1. Справочные таблицы
    scripts = [
        """
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS stock_categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """,
    ]

    # 2. Основные таблицы
    scripts += [
        """
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            unit_id INTEGER NOT NULL,
            uid TEXT NOT NULL UNIQUE,
            FOREIGN KEY (unit_id) REFERENCES units (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            price INTEGER NOT NULL,
            uid TEXT NOT NULL UNIQUE
        );
        """,
        # Таблица для связи Продукт-Ингредиент
        """
        CREATE TABLE IF NOT EXISTS product_ingredients (
            product_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            PRIMARY KEY (product_id, ingredient_id),
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            unit_id INTEGER NOT NULL,
            uid TEXT NOT NULL UNIQUE,
            FOREIGN KEY (category_id) REFERENCES stock_categories (id),
            FOREIGN KEY (unit_id) REFERENCES units (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS expense_types (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            default_price INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            uid TEXT NOT NULL UNIQUE,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            type_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (type_id) REFERENCES expense_types (id),
            FOREIGN KEY (category_id) REFERENCES expense_categories (id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity REAL NOT NULL,
            discount INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        """
    ]

    execute_scripts(conn, scripts)

    # 3. Заполнение справочных таблиц
    cursor = conn.cursor()
    
    # Заполнение Units
    cursor.executemany("INSERT OR IGNORE INTO units (name) VALUES (?)", INITIAL_UNITS)
    
    # Заполнение Stock Categories
    cursor.executemany("INSERT OR IGNORE INTO stock_categories (name) VALUES (?)", INITIAL_STOCK_CATEGORIES)
    
    # Заполнение Expense Categories
    cursor.executemany("INSERT OR IGNORE INTO expense_categories (name) VALUES (?)", INITIAL_EXPENSE_CATEGORIES)

    conn.commit()


def get_unit_by_name(conn: sqlite3.Connection, name: str) -> Optional[int]:
    """Вспомогательная функция для получения ID единицы измерения по имени."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM units WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    return None

def get_expense_category_by_name(conn: sqlite3.Connection, name: str) -> Optional[int]:
    """Вспомогательная функция для получения ID категории расходов по имени."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM expense_categories WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    return None

# Инициализация при первом импорте (для удобства)
#try:
#    conn = create_connection()
#    initialize_db(conn)
#    conn.close()
#except sqlite3.Error as e:
#    print(f"Ошибка при инициализации базы данных: {e}")