import sqlite3
from typing import Optional, List, Dict, Any
from types import SimpleNamespace


from sql_model.entities import Product
# Мы импортируем IngredientsRepository для получения ID ингредиента по имени
from repositories.ingredients import IngredientsRepository


class ProductsRepository:

    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance # Ссылка на Model для доступа к Ingredients

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row, ingredients_data: List[Dict[str, Any]]) -> Optional[Product]:
        """Преобразует строку из БД в объект Product."""
        if row is None:
            return None
        
        # В отличие от старой модели, новый Product entity не хранит список ингредиентов
        # напрямую, но мы его можем добавить для совместимости с бизнес-логикой.
        # Однако, для чистоты, мы будем возвращать его без списка, 
        # а рецепт получать отдельным методом get_ingredients_for_product.
        # Но чтобы сохранить логику, как в исходной модели, будем возвращать словарь.
        
        # ВНИМАНИЕ: Если бы Product Entity не был 'frozen', мы бы делали так:
        # p = Product(id=row['id'], name=row['name'], price=row['price']))
        # p.ingredients = ingredients_data # Но dataclass frozen=True не позволяет этого.
        
        # Возвращаем Product, но для дальнейшей работы с ним потребуется отдельный вызов
        # для получения рецепта.
        
        # Для простоты, оставим dataclass Product без поля ingredients, но будем 
        # возвращать данные о рецепте отдельно.
        
        return Product(
            id=row['id'], 
            name=row['name'], 
            price=row['price']
        )

    def get_ingredients_for_product(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Получает список ингредиентов и их количество для заданного ID продукта.
        Возвращает список словарей в формате: [{'name': 'Мука', 'quantity': 500.0}].
        """
        cursor = self._conn.cursor()
        # Соединяем product_ingredients с таблицей ingredients, чтобы получить имя
        cursor.execute(
            """
            SELECT i.name, pi.quantity
            FROM product_ingredients pi
            JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.product_id = ?
            """,
            (product_id,)
        )
        # Преобразуем результат в список словарей, как было в старой модели
        return [{'name': row['name'], 'quantity': row['quantity']} for row in cursor.fetchall()]

    # --- CRUD Методы ---

    def add(self, name: str, price: int, ingredients: List[Dict[str, Any]]):
        """
        Добавляет или обновляет продукт и его рецепт.
        ingredients: [{'name': 'Мука', 'quantity': 500.0}]
        """
        cursor = self._conn.cursor()
        
        # Проверяем, существует ли продукт
        existing_product = self.by_name(name)
        
        try:
            if existing_product:
                # 1. Обновление: Удаляем старый рецепт
                product_id = existing_product.id
                cursor.execute(
                    "DELETE FROM product_ingredients WHERE product_id = ?", 
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

            # 3. Добавляем новый/обновленный рецепт
            ingredient_repo = self._model.ingredients() # Получаем репозиторий ингредиентов
            
            for item in ingredients:
                ing_name = item['name']
                ing_quantity = item['quantity']
                
                # Находим ID ингредиента
                ingredient_entity = ingredient_repo.by_name(ing_name)
                if not ingredient_entity:
                    raise ValueError(f"Ингредиент '{ing_name}' не найден. Продукт не сохранен.")
                
                # Добавляем в связующую таблицу
                cursor.execute(
                    """
                    INSERT INTO product_ingredients (product_id, ingredient_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (product_id, ingredient_entity.id, ing_quantity)
                )

            self._conn.commit()
            
            # Возвращаем объект продукта (без списка ингредиентов, т.к. он в отдельной таблице)
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
        return self._row_to_entity(row, [])

    def by_id(self, id: int) -> Optional[Product]:
        """Получает продукт по ID (без рецепта)."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (id,))
        row = cursor.fetchone()
        return self._row_to_entity(row, [])

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
            cursor.execute("DELETE FROM product_ingredients WHERE product_id = ?", (product.id,))
            
            # 2. Удаляем сам продукт
            cursor.execute("DELETE FROM products WHERE id = ?", (product.id,))
            
            conn.commit()
            
        except sqlite3.Error as e:
            conn.rollback()
            # В реальном приложении здесь можно логировать ошибку
            raise RuntimeError(f"Ошибка при удалении продукта '{name}' и его рецептов: {e}")

    def data(self) -> List[Dict[str, SimpleNamespace]]:
        """
        Возвращает список всех продуктов в виде словарей, 
        включая их рецепты (для совместимости со старой моделью).
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = []
        for row in cursor.fetchall():
            product = self._row_to_entity(row, [])            
            # Создаем словарь, чтобы добавить поле 'ingredients'
            prod = SimpleNamespace()            
            setattr(prod, "id", product.id)
            setattr(prod, "name", product.name)
            setattr(prod, "price", product.price)
            setattr(prod, "ingredients", self.get_ingredients_for_product(product.id))            
            
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