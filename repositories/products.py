"""Repository for managing products."""

from typing import Optional, List, Dict, Any
from types import SimpleNamespace
from sqlalchemy.orm import Session
from sqlalchemy import and_

from sql_model.entities import Product, StockItem


class ProductsRepository:
    """Repository for Product entities using SQLAlchemy ORM."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    # --- Helper methods ---
    def get_materials_for_product(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Получает список ингредиентов для продукта, используя ORM-связи.
        """
        from sql_model.entities import StockItem, Unit, product_stock_association

        # Делаем один запрос, который сразу подгружает связанные данные (Eager Loading)
        # Это предотвращает проблему N+1 запросов
        rows = (
            self.db.query(
                StockItem.name,
                product_stock_association.c.quantity,
                Unit.name.label("unit_name")
            )
            .join(product_stock_association, StockItem.id == product_stock_association.c.stock_id)
            .join(Unit, StockItem.unit_id == Unit.id)
            .filter(product_stock_association.c.product_id == product_id)
            .all()
        )

        return [
            {
                "name": row.name,
                "quantity": row.quantity,
                "unit_name": row.unit_name # Теперь здесь будет 'kg', 'g' и т.д.
            }
            for row in rows
        ]

    # --- CRUD Methods ---

    def add(self, name: str, price: int, materials: List[Dict[str, Any]]):
        """
        Add or update product and its recipe.
        materials: [{'name': 'Flour', 'quantity': 500.0}]
        """
        # Check if product exists
        existing_product = self.by_name(name)
        
        try:
            if existing_product:
                # Update: Delete old recipe
                product_id = existing_product.id
                from sqlalchemy import delete
                from sql_model.entities import product_stock_association
                
                # Use ORM delete instead of raw SQL text()
                self.db.execute(
                    delete(product_stock_association).where(
                        product_stock_association.c.product_id == product_id
                    )
                )
                
                # Update product
                existing_product.price = price
                self.db.commit()
            else:
                # Add: Create new product
                new_product = Product(name=name, price=price)
                self.db.add(new_product)
                self.db.flush()
                product_id = new_product.id

            # Add materials
            from sql_model.entities import product_stock_association
            from sqlalchemy import insert
            
            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']

                # Find material by name
                stock_item = self.db.query(StockItem).filter(
                    StockItem.name == mat_name
                ).first()
                
                if not stock_item:
                    raise ValueError(f"Material '{mat_name}' not found. Product not saved.")
                
                self.db.execute(
                    insert(product_stock_association).values(
                        product_id=product_id,
                        stock_id=stock_item.id,
                        quantity=mat_quantity
                    )
                )

            self.db.commit()
            return self.by_id(product_id)

        except Exception as e:
            self.db.rollback()
            if 'UNIQUE' in str(e):
                raise ValueError(f"Product with name '{name}' already exists.")
            raise e

    def by_name(self, name: str) -> Optional[Product]:
        """Get product by name (without recipe)."""
        return self.db.query(Product).filter(Product.name == name).first()

    def by_id(self, id: int) -> Optional[Product]:
        """Get product by ID (without recipe)."""
        return self.db.query(Product).filter(Product.id == id).first()

    def delete(self, name: str):
        """Delete product and all related recipes."""
        product = self.by_name(name)
        if not product:
            return

        try:
            # Check if product has sales
            sales_count = len(product.sales)
            if sales_count > 0:
                raise ValueError(f"Product '{name}' has been sold and cannot be deleted.")
            
            # Delete from association table (cascade) using ORM
            from sqlalchemy import delete
            from sql_model.entities import product_stock_association
            
            self.db.execute(
                delete(product_stock_association).where(
                    product_stock_association.c.product_id == product.id
                )
            )
            
            # Delete product
            self.db.delete(product)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Error deleting product '{name}' and its recipes: {e}")

    def update(self, product_id: int, name: str, price: int, materials: List[Dict[str, Any]]):
        """
        Update product by ID: change name/price and recreate recipe.
        Check for name collision with other products.
        """
        # Check if product exists
        existing = self.by_id(product_id)
        if not existing:
            raise ValueError(f"Product with id={product_id} not found.")

        try:
            # Check for duplicate name with other products
            other_product = self.db.query(Product).filter(
                and_(Product.name == name, Product.id != product_id)
            ).first()
            
            if other_product:
                raise ValueError(f"Product with name '{name}' already exists.")

            # Update product
            existing.name = name
            existing.price = price

            # Delete old recipe using ORM
            from sqlalchemy import delete
            from sql_model.entities import product_stock_association
            
            self.db.execute(
                delete(product_stock_association).where(
                    product_stock_association.c.product_id == product_id
                )
            )
            self.db.flush()  # Ensure deletion is committed before inserting new materials

            # Add new recipe using ORM insert
            from sqlalchemy import insert
            
            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']
                
                stock_item = self.db.query(StockItem).filter(
                    StockItem.name == mat_name
                ).first()
                
                if not stock_item:
                    raise ValueError(f"Material '{mat_name}' not found. Product not saved.")

                self.db.execute(
                    insert(product_stock_association).values(
                        product_id=product_id,
                        stock_id=stock_item.id,
                        quantity=mat_quantity
                    )
                )

            self.db.commit()
            return self.by_id(product_id)

        except Exception as e:
            self.db.rollback()
            raise e

    def data(self) -> List[SimpleNamespace]:
        """
        Return list of all products as SimpleNamespace objects,
        including their recipes (for compatibility with old model).
        """
        products = self.db.query(Product).all()
        result = []
        
        for product in products:
            prod = SimpleNamespace()
            prod.id = product.id
            prod.name = product.name
            prod.price = product.price
            prod.materials = self.get_materials_for_product(product.id)
            result.append(prod)
        
        return result
    
    def has(self, name: str) -> bool:
        """Check if product exists by name."""
        return self.by_name(name) is not None

    def empty(self) -> bool:
        """Check if repository is empty."""
        return self.db.query(Product).count() == 0

    def len(self) -> int:
        """Return count of products."""
        return self.db.query(Product).count()
    
    def names(self) -> List[str]:
        """Return list of all product names."""
        return [p.name for p in self.db.query(Product.name).all()]