import sqlite3
from typing import Optional, List, Any

from sql_model.entities import Sale
from repositories.products import ProductsRepository
from repositories.stock import StockRepository

from datetime import datetime

class SalesRepository:

    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance # Ссылка на Model для доступа к Products и Stock

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Optional[Sale]:
        """Преобразует строку из БД в объект Sale."""
        if row is None:
            return None
        return Sale(
            id=row['id'],
            product_id=row['product_id'],
            product_name=row['product_name'],
            price=row['price'],
            quantity=row['quantity'],
            discount=row['discount'],
            date=row['date']
        )

    # --- CRUD/Логические Методы ---

    def add(self, name: str, price: int, quantity: float, discount: int):
        """
        Регистрирует продажу и списывает необходимые ингредиенты со склада.
        """
        cursor = self._conn.cursor()
        
        # 1. Получаем продукт и его рецепт
        product = self._model.products().by_name(name)
        if not product:
            raise ValueError(f"Продукт '{name}' не найден.")
            
        # 2. Получаем рецепт (словарь ингредиентов с количеством)
        # Мы используем ProductsRepository.get_materials_for_product для получения рецепта
        recipe = self._model.products().get_materials_for_product(product.id)
        if not recipe:
            raise ValueError(f"Продукт '{name}' не имеет рецепта, продажа невозможна.")

        try:
            # 3. Списываем ингредиенты со склада
            stock_repo = self._model.stock()
            
            for item in recipe:
                ing_name = item['name']
                ing_quantity_needed = item['quantity'] * quantity # Общее количество на всю продажу
                
                # Обновляем запас (отрицательное изменение)
                # StockRepository.update() содержит проверку на отрицательный остаток
                stock_repo.update(ing_name, -ing_quantity_needed)

            # 4. Записываем факт продажи
            cursor.execute(
                """
                INSERT INTO sales (product_id, product_name, price, quantity, discount, date) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (product.id, name, price, quantity, discount, datetime.now().strftime("%Y-%m-%d %H:%M")) # Sale.date использует default_factory в dataclass
            )
            self._conn.commit()

        except ValueError as e:
            # Откат транзакции, если не хватило запасов (проверка в stock_repo.update)
            self._conn.rollback()
            raise e
        except Exception as e:
            self._conn.rollback()
            raise e

    def data(self) -> List[Sale]:
        """Возвращает список всех продаж."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM sales ORDER BY date DESC")
        return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def search(self, query: str) -> List[Sale]:
        """Поиск продаж по названию продукта или дате."""
        cursor = self._conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute(
            """
            SELECT * FROM sales 
            WHERE product_name LIKE ? 
               OR date LIKE ?
            ORDER BY date DESC
            """,
            (search_pattern, search_pattern)
        )
        return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def salesByProduct(self):
        cursor = self._conn.cursor()
        cursor.execute("SELECT product_id, product_name, SUM(price * quantity) AS total_price FROM sales GROUP BY product_id, product_name;")
        return cursor.fetchall()
        
    def len(self) -> int:
        """Возвращает количество продаж."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sales")
        return cursor.fetchone()[0]
    
    def empty(self) -> bool:
        """Проверяет, пуст ли репозиторий."""
        return self.len() == 0