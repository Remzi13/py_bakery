import sqlite3
from typing import Optional, List, Any

# Импортируем обновленные сущности
from sql_model.entities import Ingredient
from sql_model.database import create_connection, get_unit_by_name, get_expense_category_by_name
# Импортируем классы для Stock и Expense, чтобы получить ID категорий

class IngredientsRepository:

    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance # Ссылка на Model для доступа к Stock и Products

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Ingredient:
        """Преобразует строку из БД в объект Ingredient."""
        if row is None:
            return None
        return Ingredient(
            id=row['id'],
            name=row['name'],
            unit_id=row['unit_id']
        )

    # --- CRUD Методы ---

    def add(self, name: str, unit_name: str) -> Ingredient:
        """
        Добавляет новый ингредиент, а также создает связанный StockItem 
        и ExpenseType.
        """
        cursor = self._conn.cursor()
        
        # 1. Получаем ID единицы измерения
        unit_id = get_unit_by_name(self._conn, unit_name)
        if unit_id is None:
            raise ValueError(f"Единица измерения '{unit_name}' не найдена.")

        # 2. Создаем ингредиент
        try:
            cursor.execute(
                "INSERT INTO ingredients (name, unit_id) VALUES (?, ?)",
                (name, unit_id)
            )
            ingredient_id = cursor.lastrowid
            self._conn.commit()
            
            # 3. Добавляем связанный StockItem (используем репозиторий Stock)
            # Мы используем строковое имя категории 'Materials', чтобы найти ее ID в БД.
            self._model.stock().add(
                name=name, 
                category_name='Materials', 
                quantity=0, # Изначально 0
                unit_name=unit_name 
            )

            # 4. Добавляем связанный ExpenseType (используем репозиторий ExpenseTypes)
            # Изначальная цена 100, категория 'Сырьё'
            self._model.expense_types().add(
                name=name, 
                default_price=100, 
                category_name='Materials'
            )
            
            return Ingredient(id=ingredient_id, name=name, unit_id=unit_id)

        except sqlite3.IntegrityError:
            self._conn.rollback()
            raise ValueError(f"Ингредиент с именем '{name}' уже существует.")
        except Exception as e:
            self._conn.rollback()
            raise e

    def by_name(self, name: str) -> Optional[Ingredient]:
        """Получает ингредиент по имени."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM ingredients WHERE name = ?", (name,))
        row = cursor.fetchone()
        return self._row_to_entity(row)

    def by_id(self, id: int) -> Optional[Ingredient]:
        """Получает ингредиент по ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM ingredients WHERE id = ?", (id,))
        row = cursor.fetchone()
        return self._row_to_entity(row)
    
    def data(self) -> List[Ingredient]:
        """Возвращает список всех ингредиентов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM ingredients")
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def can_delete(self, name: str) -> bool:
        """Проверяет, используется ли ингредиент в продуктах."""
        ingredient = self.by_name(name)
        if not ingredient:
            return True # Если ингредиента нет, его можно "удалить" (т.е. нет проблем)

        # Проверяем наличие записей в таблице product_ingredients
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM product_ingredients WHERE ingredient_id = ?", 
            (ingredient.id,)
        )
        count = cursor.fetchone()[0]
        return count == 0

    def delete(self, name: str):
        """
        Удаляет ингредиент и связанные с ним StockItem и ExpenseType, 
        если он не используется в продуктах.
        """
        ingredient = self.by_name(name)
        if not ingredient:
            return # Ничего удалять не надо

        if not self.can_delete(name):
            raise ValueError(f"Ингредиент '{name}' используется в продукте. Удаление невозможно.")
        
        cursor = self._conn.cursor()
        try:
            # 1. Удаляем связанные записи из Stock и ExpenseTypes
            self._model.stock().delete(name)
            self._model.expense_types().delete(name)

            # 2. Удаляем сам ингредиент
            cursor.execute("DELETE FROM ingredients WHERE id = ?", (ingredient.id,))
            self._conn.commit()

        except Exception as e:
            self._conn.rollback()
            raise e

    def len(self) -> int:
        """Возвращает количество ингредиентов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        return cursor.fetchone()[0]

    def names(self) -> List[str]:
        """Возвращает список имен всех ингредиентов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM ingredients")
        return [row[0] for row in cursor.fetchall()]
    
    def has(self, name: str) -> bool:
        """Проверяет наличие ингредиента по имени."""
        return self.by_name(name) is not None
    
    def empty(self) -> bool:
        """Проверяет, пуст ли репозиторий."""
        return self.len() == 0