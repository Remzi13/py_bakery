"""Repository for managing products."""

from typing import Optional, List, Dict, Any
from types import SimpleNamespace
from sqlalchemy.orm import Session
from sqlalchemy import and_

from sql_model.entities import Product, StockItem, ProductRecipe


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
        from sql_model.entities import Unit
        from sqlalchemy.orm import aliased

        RecipeUnit = aliased(Unit)

        rows = (
            self.db.query(
                StockItem.id,
                StockItem.name,
                ProductRecipe.quantity,
                ProductRecipe.conversion_factor,
                ProductRecipe.recipe_unit_id,
                Unit.name.label("unit_name"),
                RecipeUnit.name.label("recipe_unit_name")
            )
            .join(ProductRecipe, StockItem.id == ProductRecipe.stock_id)
            .join(Unit, StockItem.unit_id == Unit.id)
            .outerjoin(RecipeUnit, ProductRecipe.recipe_unit_id == RecipeUnit.id)
            .filter(ProductRecipe.product_id == product_id)
            .all()
        )

        return [
            {
                "stock_id": row.id,
                "name": row.name,
                "quantity": row.quantity,
                "unit_name": row.unit_name,
                "recipe_unit_name": row.recipe_unit_name or row.unit_name,
                "recipe_unit_id": row.recipe_unit_id,
                "conversion_factor": row.conversion_factor
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

                # Use ORM delete
                self.db.query(ProductRecipe).filter(
                    ProductRecipe.product_id == product_id
                ).delete()

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
            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']
                mat_conversion = item.get('conversion_factor', 1.0)
                mat_recipe_unit_id = item.get('recipe_unit_id')

                # Find material by name
                stock_item = self.db.query(StockItem).filter(
                    StockItem.name == mat_name
                ).first()

                if not stock_item:
                    raise ValueError(f"Material '{mat_name}' not found. Product not saved.")

                recipe = ProductRecipe(
                    product_id=product_id,
                    stock_id=stock_item.id,
                    quantity=mat_quantity,
                    conversion_factor=mat_conversion,
                    recipe_unit_id=mat_recipe_unit_id
                )
                self.db.add(recipe)

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

    def delete(self, product_id: int):
        """Delete product and all related recipes."""
        product = self.by_id(product_id)
        if not product:
            return
        
        name = product.name

        try:
            # Check for related items (prevent IntegrityError)
            if len(product.sales) > 0:
                raise ValueError(f"Product '{name}' has been sold and cannot be deleted.")
            
            if len(product.write_offs) > 0:
                raise ValueError(f"Product '{name}' has write-off records and cannot be deleted.")
            
            if len(product.order_items) > 0:
                raise ValueError(f"Product '{name}' is part of existing orders and cannot be deleted.")

            # Delete from association table (cascade) using ORM
            self.db.query(ProductRecipe).filter(
                ProductRecipe.product_id == product.id
            ).delete()

            # Delete product
            self.db.delete(product)
            self.db.commit()

        except ValueError as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Error deleting product with ID {product_id} and its recipes: {e}")

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
            self.db.query(ProductRecipe).filter(
                ProductRecipe.product_id == product_id
            ).delete()
            self.db.flush()  # Ensure deletion is committed before inserting new materials

            # Add new recipe using ORM
            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']
                mat_conversion = item.get('conversion_factor', 1.0)
                mat_recipe_unit_id = item.get('recipe_unit_id')

                stock_item = self.db.query(StockItem).filter(
                    StockItem.name == mat_name
                ).first()

                if not stock_item:
                    raise ValueError(f"Material '{mat_name}' not found. Product not saved.")

                recipe = ProductRecipe(
                    product_id=product_id,
                    stock_id=stock_item.id,
                    quantity=mat_quantity,
                    conversion_factor=mat_conversion,
                    recipe_unit_id=mat_recipe_unit_id
                )
                self.db.add(recipe)

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
