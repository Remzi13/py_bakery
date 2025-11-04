import sqlite3
import uuid
from typing import Optional, List

from sql_model.entities import ExpenseType
from sql_model.database import get_expense_category_by_name


class ExpenseTypesRepository:

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Optional[ExpenseType]:
        """Преобразует строку из БД в объект ExpenseType."""
        if row is None:
            return None
        return ExpenseType(
            id=row['id'],
            name=row['name'],
            default_price=row['default_price'],
            category_id=row['category_id'],
            uid=uuid.UUID(row['uid'])
        )

    # --- CRUD Методы ---

    def add(self, name: str, default_price: int, category_name: str):
        """Добавляет новый тип расхода."""
        cursor = self._conn.cursor()
        
        category_id = get_expense_category_by_name(self._conn, category_name)
        if category_id is None:
            raise ValueError(f"Категория расходов '{category_name}' не найдена.")
        
        new_uuid = uuid.uuid4()
        
        try:
            cursor.execute(
                """
                INSERT INTO expense_types (name, default_price, category_id, uid) 
                VALUES (?, ?, ?, ?)
                """,
                (name, default_price, category_id, str(new_uuid))
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            self._conn.rollback()
            # Интегральность (UNIQUE) нарушена, тип расхода уже есть
            pass 
        except Exception as e:
            self._conn.rollback()
            raise e


    def get(self, name: str) -> Optional[ExpenseType]:
        """Получает тип расхода по имени."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM expense_types WHERE name = ?", (name,))
        row = cursor.fetchone()
        return self._row_to_entity(row)

    def delete(self, name: str):
        """
        Удаляет тип расхода по имени. 
        (Должен использоваться только в связке с удалением Ингредиента)
        """
        # Мы не проверяем, используется ли ExpenseType в таблице expenses,
        # так как это будет нарушать исторические данные о расходах.
        # Просто удаляем сам тип, если он не нужен.
        cursor = self._conn.cursor()
        try:
            cursor.execute("DELETE FROM expense_types WHERE name = ?", (name,))
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            raise e
            
    def data(self) -> List[ExpenseType]:
        """Возвращает список всех типов расходов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM expense_types")
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def len(self) -> int:
        """Возвращает количество типов расходов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expense_types")
        return cursor.fetchone()[0]

    def empty(self) -> bool:
        """Проверяет, пуст ли репозиторий."""
        return self.len() == 0