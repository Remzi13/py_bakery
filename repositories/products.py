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
        Get list of ingredients and quantities for a given product ID.
        Returns list of dicts: [{'name': 'Flour', 'quantity': 500.0, 'unit': 'kg'}]
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []
        
        result = []
        # Query the association table through product_stock relationship
        # Since we're using direct SQL relationship, we need to query the raw data
        from sqlalchemy import text
        cursor_result = self.db.execute(
            text("""
            SELECT i.name AS material_name, pi.quantity AS qty, u.name AS unit_name
            FROM product_stock pi
            JOIN stock i ON pi.stock_id = i.id
            LEFT JOIN units u ON i.unit_id = u.id
            WHERE pi.product_id = :product_id
            """),
            {"product_id": product_id}
        )
        
        for row in cursor_result:
            result.append({
                'name': row.material_name,
                'quantity': row.qty,
                'unit': row.unit_name
            })
        
        return result

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
                from sqlalchemy import delete, text
                self.db.execute(
                    delete(text("product_stock")).where(
                        text("product_stock.product_id = :product_id")
                    ),
                    {"product_id": product_id}
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
            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']

                # Find material by name
                stock_item = self.db.query(StockItem).filter(
                    StockItem.name == mat_name
                ).first()
                
                if not stock_item:
                    raise ValueError(f"Material '{mat_name}' not found. Product not saved.")
                
                # Add to association table
                self.db.execute(
                    text("""
                    INSERT INTO product_stock (product_id, stock_id, quantity)
                    VALUES (:product_id, :stock_id, :quantity)
                    """),
                    {"product_id": product_id, "stock_id": stock_item.id, "quantity": mat_quantity}
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
            
            # Delete from association table (cascade)
            from sqlalchemy import text, delete
            self.db.execute(
                text("DELETE FROM product_stock WHERE product_id = :product_id"),
                {"product_id": product.id}
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

            # Delete old recipe
            from sqlalchemy import text
            self.db.execute(
                text("DELETE FROM product_stock WHERE product_id = :product_id"),
                {"product_id": product_id}
            )

            # Add new recipe
            for item in materials:
                mat_name = item['name']
                mat_quantity = item['quantity']
                
                stock_item = self.db.query(StockItem).filter(
                    StockItem.name == mat_name
                ).first()
                
                if not stock_item:
                    raise ValueError(f"Material '{mat_name}' not found. Product not saved.")

                self.db.execute(
                    text("""
                    INSERT INTO product_stock (product_id, stock_id, quantity)
                    VALUES (:product_id, :stock_id, :quantity)
                    """),
                    {"product_id": product_id, "stock_id": stock_item.id, "quantity": mat_quantity}
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