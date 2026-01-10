import sqlite3
from typing import Optional, List, Any

from sql_model.entities import StockItem
from sql_model.database import create_connection, get_unit_by_name
from sql_model.database import INITIAL_STOCK_CATEGORIES # Для получения имен категорий


class StockRepository:

    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance # Ссылка на Model для доступа к Stock и Products

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Optional[StockItem]:
        """Преобразует строку из БД в объект StockItem."""
        if row is None:
            return None
        return StockItem(
            id=row['id'],
            name=row['name'],
            category_id=row['category_id'],
            quantity=row['quantity'],
            unit_id=row['unit_id']
        )
        
    def _get_category_id(self, category_name: str) -> Optional[int]:
        """Получает ID категории запасов по имени."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id FROM stock_categories WHERE name = ?", 
            (category_name,)
        )
        row = cursor.fetchone()
        return row['id'] if row else None


    # --- CRUD/Логические Методы ---

    def add(self, name: str, category_name: str, quantity: float, unit_name: str):
        """Добавляет новый элемент в инвентарь."""
        cursor = self._conn.cursor()
        
        unit_id = get_unit_by_name(self._conn, unit_name)
        category_id = self._get_category_id(category_name)
        
        if unit_id is None:
            raise ValueError(f"Единица измерения '{unit_name}' не найдена.")
        if category_id is None:
            raise ValueError(f"Категория '{category_name}' не найдена.")
       
        try:
            cursor.execute(
                """
                INSERT INTO stock (name, category_id, quantity, unit_id) 
                VALUES (?, ?, ?, ?)
                """,
                (name, category_id, quantity, unit_id)
            )
            # Также создаем запись в ExpenseTypes для этого элемента запаса
            self._model.expense_types().add(
                name=name, 
                default_price=100, 
                category_name="Materials"
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            self._conn.rollback()
            raise ValueError(f"Элемент инвентаря с именем '{name}' уже существует.")
        except Exception as e:
            self._conn.rollback()
            raise e


    def get(self, name: str) -> Optional[StockItem]:
        """Получает элемент инвентаря по имени."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM stock WHERE name = ?", (name,))
        row = cursor.fetchone()
        return self._row_to_entity(row)
        

    def by_id(self, id: int) -> Optional[StockItem]:
        """Получает продукт по ID (без рецепта)."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM stock WHERE id = ?", (id,))
        row = cursor.fetchone()
        return self._row_to_entity(row)
    
    def data(self) -> List[StockItem]:
        """Возвращает список всех элементов инвентаря."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM stock")
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def update(self, name: str, quantity_delta: float):
        """
        Изменяет количество элемента запаса на указанную величину (quantity_delta).
        
        Args:
            name (str): Имя элемента запаса.
            quantity_delta (float): Разница, на которую нужно изменить количество 
                                    (положительная для прихода, отрицательная для расхода).
                                    
        Raises:
            ValueError: Если в результате операции остаток становится отрицательным.
            KeyError: Если элемент с таким именем не найден.
        """
        conn = self._conn
        cursor = conn.cursor()
        
        # 1. Проверяем наличие и получаем текущее количество (для проверки остатка)
        current_item = self.get(name) 
        if current_item is None:
            raise KeyError(f"Элемент '{name}' не найден в инвентаре")
    
        new_quantity = current_item.quantity + quantity_delta
        
        # 2. Проверка бизнес-логики: Запрещаем отрицательный остаток
        if new_quantity < 0:
            raise ValueError(
                f"Недостаточно запаса для '{name}'. Требуется списание {abs(quantity_delta):.2f}, "
                f"текущий остаток {current_item.quantity:.2f}."
            )
    
        try:
            # 3. Атомарное обновление (SET quantity = quantity + delta)
            cursor.execute("""
                UPDATE stock
                SET quantity = quantity + ?
                WHERE name = ?
            """, (quantity_delta, name))
            
            conn.commit()
            
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Ошибка при обновлении запаса для '{name}': {e}")
        
    def set(self, name: str, new_quantity: float):
        """
        Устанавливает новое конкретное значение количества для элемента запаса.
        
        Args:
            name (str): Имя элемента запаса (например, 'Мука', 'Packaging 100г').
            new_quantity (float): Новое количество.
        
        Raises:
            KeyError: Если элемент с таким именем не найден.
        """
        conn = self._conn
        cursor = conn.cursor()
        
        # 1. Проверяем, существует ли элемент, чтобы избежать "слепого" UPDATE
        item = self.get(name) 
        if item is None:
            # Воспроизводим поведение старого класса (KeyError)
            raise KeyError(f"Элемент '{name}' не найден в инвентаре")

        try:
            # 2. Обновляем поле quantity
            cursor.execute("""
                UPDATE stock
                SET quantity = ?
                WHERE name = ?
            """, (new_quantity, name))
            
            conn.commit()
            
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Ошибка при обновлении запаса для '{name}': {e}")

    def can_delete(self, name: str) -> bool:
        stock = self.get(name)
        if not stock:
            return True # Если ингредиента нет, его можно "удалить" (т.е. нет проблем)

        # Проверяем наличие записей в таблице product_stock
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM product_stock WHERE stock_id = ?", 
            (stock.id,)
        )
        count = cursor.fetchone()[0]
        return count == 0

    def delete(self, name: str):
        """Удаляет элемент из инвентаря по имени."""
        if not self.can_delete(name):
            raise ValueError(f"Материал '{name}' используется в продукте. Удаление невозможно.")
        cursor = self._conn.cursor()
        try:
            self._model.expense_types().delete(name)

            cursor.execute("DELETE FROM stock WHERE name = ?", (name,))
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            raise e
            
    def len(self) -> int:
        """Возвращает количество элементов в инвентаре."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stock")
        return cursor.fetchone()[0]

    def empty(self) -> bool:
        """Проверяет, пуст ли инвентарь."""
        return self.len() == 0