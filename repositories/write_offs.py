import sqlite3
from typing import Optional, List, Any
from datetime import datetime

# Предполагаем, что WriteOff Entity обновлен в sql_model.entities
from sql_model.entities import WriteOff 

class WriteOffsRepository:

    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance # Ссылка на Model для доступа к Stock, Products и Utils

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Optional[WriteOff]:
        """Преобразует строку из БД в объект WriteOff."""
        if row is None:
            return None
        return WriteOff(
            id=row['id'],
            # product_id и stock_item_id могут быть None
            product_id=row['product_id'],
            stock_item_id=row['stock_item_id'],
            quantity=row['quantity'],
            reason=row['reason'],
            unit_id=row['unit_id'],
            date=row['date']
        )

    # --- Основной метод: Регистрация списания ---

    def add(self, item_name: str, item_type: str, quantity: float, reason: str):
        """
        Регистрирует списание (готового продукта или запаса/сырья).

        Списание готового продукта (item_type='product') регистрируется в журнале И 
        уменьшает запасы ингредиентов на складе согласно рецепту.
        Списание запаса/сырья (item_type='stock') регистрируется в журнале И уменьшает Stock.

        Args:
            item_name (str): Название элемента.
            item_type (str): Тип элемента ('product' или 'stock').
            quantity (float): Количество для списания.
            reason (str): Причина списания.

        Raises:
            ValueError: Если элемент не найден, количество не положительно или не хватает запаса.
        """
        if item_type not in ['product', 'stock']:
            raise ValueError("Недопустимый тип элемента. Используйте 'product' или 'stock'.")

        if quantity <= 0:
            raise ValueError("Количество для списания должно быть положительным.")

        cursor = self._conn.cursor()
        stock_repo = self._model.stock()

        # Переменные для записи в таблицу write_offs
        product_id = None
        stock_item_id = None
        unit_id = None

        try:
            if item_type == 'product':
                # --- ЛОГИКА СПИСАНИЯ ГОТОВОГО ПРОДУКТА (списание ингредиентов) ---
            
                product_repo = self._model.products()
            
                # 1. Находим продукт и его рецепт
                product_entity = product_repo.by_name(item_name) # Получаем Product Entity
                if product_entity is None:
                    raise ValueError(f"Продукт '{item_name}' не найден в списке продуктов.")
            
                ingredients_needed = product_repo.get_ingredients_for_product(product_entity.id)
                if not ingredients_needed:
                    # Регистрируем факт списания продукта, даже если у него нет рецепта
                    pass 

                product_id = product_entity.id
            
                # 2. Списываем ингредиенты со склада (аналогично продаже)
                for ing in ingredients_needed:
                    ing_name = ing['name']
                    # Общее количество ингредиента, необходимое для списанных продуктов
                    ing_quantity_needed = ing['quantity'] * quantity 
                
                    # Обновляем запас (отрицательное изменение)
                    # StockRepository.update() содержит проверку на отрицательный остаток
                    # Мы используем 'set' вместо 'update', так как в StockRepository у нас был set.
                    # Если в StockRepository есть метод update, то лучше использовать его. 
                    # Исходя из предоставленных файлов, используем get/set:
                    current_stock = stock_repo.get(ing_name)
                    if current_stock is None:
                        raise ValueError(f"Ингредиент '{ing_name}' для продукта '{item_name}' не найден на складе.")
                
                    new_quantity = current_stock.quantity - ing_quantity_needed
                    if new_quantity < 0:
                        # Важно: Вызываем ошибку до коммита
                        raise ValueError(f"Не хватает ингредиента '{ing_name}' для списания {quantity} шт. продукта '{item_name}'. Недостаточно {ing_name}.")
                
                    stock_repo.set(ing_name, new_quantity)
                
                # После успешного списания всех ингредиентов, регистрируем списание продукта.
            
            elif item_type == 'stock':
                # --- ЛОГИКА СПИСАНИЯ СЫРЬЯ/ЗАПАСА (уменьшение Stock) ---
            
                current_stock_item = stock_repo.get(item_name)

                if current_stock_item is None:
                    raise ValueError(f"Элемент '{item_name}' не найден на складе для списания.")
            
                stock_item_id = current_stock_item.id
                unit_id = current_stock_item.unit_id
            
                # 1. Проверяем остаток перед списанием
                if current_stock_item.quantity < quantity:
                    raise ValueError(f"Недостаточно запаса '{item_name}' для списания ({current_stock_item.quantity} < {quantity}).")

                # 2. Уменьшаем количество на складе
                new_quantity = current_stock_item.quantity - quantity
                stock_repo.set(item_name, new_quantity)


            # 3. Записываем факт списания в журнал (для обоих типов)
            # Для product: product_id заполнен, stock_item_id и unit_id - None.
            # Для stock: stock_item_id и unit_id заполнены, product_id - None.
            cursor.execute(
                """
                INSERT INTO writeoffs (product_id, stock_item_id, unit_id, quantity, reason, date) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id, 
                    stock_item_id, 
                    unit_id,
                    quantity, 
                    reason, 
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                )
            )
            self._conn.commit()

        except ValueError as e:
            # Откат транзакции, если не хватило запасов (важно для product)
            self._conn.rollback()
            raise e
        except Exception as e:
            self._conn.rollback()
            raise e
    
    
    def data(self) -> List[WriteOff]:
        """Возвращает список всех списаний (для отображения в таблице)."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM writeoffs ORDER BY date DESC")
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def len(self) -> int:
        """Возвращает количество записей о списаниях."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM writeoffs")
        return cursor.fetchone()[0]