import sqlite3
from typing import Optional, List, Any

from sql_model.entities import Expense
from repositories.expense_types import ExpenseTypesRepository
from datetime import datetime

class ExpensesRepository:

    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance # Ссылка на Model для доступа к ExpenseTypes

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Optional[Expense]:
        """Преобразует строку из БД в объект Expense."""
        if row is None:
            return None
        return Expense(
            id=row['id'],
            type_id=row['type_id'],
            name=row['name'],
            price=row['price'],
            category_id=row['category_id'],
            quantity=row['quantity'],
            date=row['date']
        )

    # --- CRUD Методы ---

    def add(self, name: str, price: int, quantity: float):
        """
        Регистрирует расход по имени типа расхода.
        """
        cursor = self._conn.cursor()
        
        # Получаем тип расхода по имени
        expense_type = self._model.expense_types().get(name)
        if not expense_type:
            raise ValueError(f"Тип расхода '{name}' не найден.")
            
        try:
            cursor.execute(
                """
                INSERT INTO expenses (type_id, name, price, category_id, quantity, date) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    expense_type.id, 
                    name, 
                    price, 
                    expense_type.category_id, 
                    quantity, 
                    datetime.now().strftime("%Y-%m-%d %H:%M"),                    
                )
            )
            self._conn.commit()

        except Exception as e:
            self._conn.rollback()
            raise e

    def data(self) -> List[Expense]:
        """Возвращает список всех расходов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def len(self) -> int:
        """Возвращает количество расходов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses")
        return cursor.fetchone()[0]
    
    def empty(self) -> bool:
        """Проверяет, пуст ли репозиторий."""
        return self.len() == 0