import sqlite3
from typing import Optional, List, Dict, Any
from types import SimpleNamespace


from sql_model.entities import Product


class ProductsRepository:

    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance # Ссылка на Model для доступа к Ingredients

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Optional[Product]:
        """Преобразует строку из БД в объект Product."""
        if row is None:
            return None

        return Product(
            id=row['id'], 
            name=row['name'], 
            price=row['price']
        )

    def get_materials_for_product(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Получает список ингредиентов и их количество для заданного ID продукта.
        Возвращает список словарей в формате: [{'name': 'Мука', 'quantity': 500.0}].
        """
        cursor = self._conn.cursor()
        # Явное указание алиасов защищает от конфликтов имён колонок
        cursor.execute(
            """
            SELECT i.name AS material_name, pi.quantity AS qty, u.name AS unit_name
            FROM product_stock pi
            JOIN stock i ON pi.stock_id = i.id
            LEFT JOIN units u ON i.unit_id = u.id
            WHERE pi.product_id = ?
            """,
            (product_id,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            # sqlite3.Row поддерживает доступ по имени
            name = row['material_name'] if 'material_name' in row.keys() else row[0]
            qty = row['qty'] if 'qty' in row.keys() else row[1]
            unit = row['unit_name'] if 'unit_name' in row.keys() else (row[2] if len(row) > 2 else None)
            result.append({'name': name, 'quantity': qty, 'unit': unit})
        return result

    # --- CRUD Методы ---

    def add(self, name: str, price: int, materials: List[Dict[str, Any]]):
        """
        Добавляет или обновляет продукт и его рецепт.
        materials: [{'name': 'Мука', 'quantity': 500.0}]
        """
        cursor = self._conn.cursor()
        
        # Проверяем, существует ли продукт
        existing_product = self.by_name(name)
        
        try:
            if existing_product:
                # 1. Обновление: Удаляем старый рецепт
                product_id = existing_product.id
                cursor.execute(
                    "DELETE FROM product_stock WHERE product_id = ?", 
                    (product_id,)
                )
                
                # Обновляем сам продукт
                cursor.execute(
                    "UPDATE products SET price = ? WHERE id = ?",
                    (price, product_id)
                )
            else:
                # 2. Добавление: Создаем новый продукт
                cursor.execute(
                    "INSERT INTO products (name, price) VALUES (?, ?)",
                    (name, price)
                )
                product_id = cursor.lastrowid


            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']

                # Находим ID материала
                entity = self._model.stock().get(mat_name)
                if not entity:
                    raise ValueError(f"Материал '{mat_name}' не найден. Продукт не сохранен.")
                
                # Добавляем в связующую таблицу
                cursor.execute(
                    """
                    INSERT INTO product_stock (product_id, stock_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (product_id, entity.id, mat_quantity)
                )

            self._conn.commit()
            
            # Возвращаем объект продукта (без списка материалов, т.к. он в отдельной таблице)
            return self.by_id(product_id) 

        except sqlite3.Error as e:
            self._conn.rollback()
            # Проверка на дубликат имени при первом добавлении
            if 'UNIQUE constraint failed: products.name' in str(e):
                 raise ValueError(f"Продукт с именем '{name}' уже существует.")
            raise e
        except Exception as e:
            self._conn.rollback()
            raise e


    def by_name(self, name: str) -> Optional[Product]:
        """Получает продукт по имени (без рецепта)."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        # Возвращаем просто объект Product
        return self._row_to_entity(row)

    def by_id(self, id: int) -> Optional[Product]:
        """Получает продукт по ID (без рецепта)."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (id,))
        row = cursor.fetchone()
        return self._row_to_entity(row)

    def delete(self, name: str):
        """Удаляет продукт и все его связанные рецепты."""
        product = self.by_name(name)
        if not product:
            return

        conn = self._conn
        cursor = conn.cursor()
        
        try:            
            cursor.execute("SELECT COUNT(*) FROM sales WHERE product_id = ?", (product.id,))
            if cursor.fetchone()[0] > 0:
                 raise ValueError(f"Продукт '{name}' был продан и не может быть удален.")
            # 1. Каскадное удаление: Удаляем все записи рецептов, связанные с этим product_id
            cursor.execute("DELETE FROM product_stock WHERE product_id = ?", (product.id,))
            
            # 2. Удаляем сам продукт
            cursor.execute("DELETE FROM products WHERE id = ?", (product.id,))
            
            conn.commit()
            
        except sqlite3.Error as e:
            conn.rollback()
            # В реальном приложении здесь можно логировать ошибку
            raise RuntimeError(f"Ошибка при удалении продукта '{name}' и его рецептов: {e}")

    def update(self, product_id: int, name: str, price: int, materials: List[Dict[str, Any]]):
        """
        Обновляет продукт по ID: изменяет имя/цену и пересоздаёт рецепт.
        Проверяет коллизию имени с другими продуктами.
        """
        cursor = self._conn.cursor()

        # Проверяем, существует ли продукт
        existing = self.by_id(product_id)
        if not existing:
            raise ValueError(f"Продукт с id={product_id} не найден.")

        try:
            # Проверка на дублирование имени у другого продукта
            cursor.execute("SELECT id FROM products WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row and row['id'] != product_id:
                raise ValueError(f"Продукт с именем '{name}' уже существует.")

            # Обновляем сам продукт
            cursor.execute(
                "UPDATE products SET name = ?, price = ? WHERE id = ?",
                (name, price, product_id)
            )

            # Удаляем старый рецепт
            cursor.execute("DELETE FROM product_stock WHERE product_id = ?", (product_id,))

            # Добавляем новый рецепт
            stock_repo = self._model.stock()
            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']
                mat_entity = stock_repo.get(mat_name)
                if not mat_entity:
                    raise ValueError(f"Материал '{mat_name}' не найден. Продукт не сохранен.")

                cursor.execute(
                    "INSERT INTO product_stock (product_id, stock_id, quantity) VALUES (?, ?, ?)",
                    (product_id, mat_entity.id, mat_quantity)
                )

            self._conn.commit()
            return self.by_id(product_id)
        except sqlite3.Error as e:
            self._conn.rollback()
            raise e
        except Exception:
            self._conn.rollback()
            raise

    def data(self) -> List[Dict[str, SimpleNamespace]]:
        """
        Возвращает список всех продуктов в виде словарей, 
        включая их рецепты (для совместимости со старой моделью).
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = []
        for row in cursor.fetchall():
            product = self._row_to_entity(row)
            # Создаем словарь, чтобы добавить поле 'materials'
            prod = SimpleNamespace()            
            setattr(prod, "id", product.id)
            setattr(prod, "name", product.name)
            setattr(prod, "price", product.price)
            setattr(prod, "materials", self.get_materials_for_product(product.id))            
            
            products.append(prod)
            
        return products
    
    def has(self, name : str) -> bool:
        """Проверяет наличие продукта по имени."""
        return self.by_name(name) is not None

    def empty(self) -> bool:
        """Проверяет, пуст ли репозиторий."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        return cursor.fetchone()[0] == 0

    def len(self) -> int:
        """Возвращает количество продуктов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        return cursor.fetchone()[0]
    
    def names(self) -> List[str]:
        """Возвращает список имен всех продуктов."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM products")
        return [row[0] for row in cursor.fetchall()]