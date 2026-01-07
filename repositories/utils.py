import sqlite3
from typing import List, Dict, Any, Optional

class UtilsRepository:
    """Репозиторий для доступа к справочным таблицам (Units, Categories)."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get_unit_names(self) -> List[str]:
        """Возвращает список имен всех единиц измерения (например, ['кг', 'грамм'])."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM units ORDER BY id")
        # Извлекаем только первый элемент (имя) из каждой строки
        return [row[0] for row in cursor.fetchall()]

    def get_stock_category_names(self) -> List[str]:
        """Возвращает список имен всех категорий запасов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM stock_categories ORDER BY id")
        return [row[0] for row in cursor.fetchall()]

    def get_expense_category_names(self) -> List[str]:
        """Возвращает список имен всех категорий расходов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM expense_categories ORDER BY id")
        return [row[0] for row in cursor.fetchall()]
    
    def get_unit_name_by_id(self, unit_id: int) -> Optional[str]:
        """Преобразует ID единицы измерения в ее строковое имя."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM units WHERE id = ?", (unit_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_stock_category_name_by_id(self, category_id: int) -> Optional[str]:
        """Преобразует ID категории запаса в ее строковое имя."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM stock_categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_expense_category_name_by_id(self, category_id: int) -> Optional[str]:
        """Преобразует ID категории расхода в ее строковое имя."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM expense_categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_expense_category_id_by_name(self, name: str) -> Optional[int]:
        """
        Возвращает ID категории расхода по ее строковому имени (например, 'Сырьё').
        
        Args:
            name (str): Строковое имя категории.
            
        Returns:
            Optional[int]: ID категории или None, если категория не найдена.
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT id FROM expense_categories WHERE name = ?", (name,))
        row = cursor.fetchone()
                
        return row['id'] if row else None 
        