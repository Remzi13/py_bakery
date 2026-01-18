from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from sql_model.entities import Sale


class SalesRepository:
    """Repository for Sale entities using SQLAlchemy ORM."""

    def __init__(self, db: Session, model_instance: Any):
        self.db = db
        self._model = model_instance  # Reference to Model for accessing Products and Stock

    # --- CRUD/Logic Methods ---

    def add(self, name: str, price: int, quantity: float, discount: int):
        """
        Register a sale and deduct necessary ingredients from stock.
        """
        # Get product and recipe
        product = self._model.products().by_name(name)
        if not product:
            raise ValueError(f"Product '{name}' not found.")
            
        # Get recipe (list of ingredients with quantities)
        recipe = self._model.products().get_materials_for_product(product.id)
        if not recipe:
            raise ValueError(f"Product '{name}' has no recipe. Cannot sell.")

        try:
            # Deduct ingredients from stock
            stock_repo = self._model.stock()
            
            for item in recipe:
                ing_name = item['name']
                ing_quantity_needed = item['quantity'] * quantity  # Total for all sales
                
                # Update stock (negative change)
                stock_repo.update(ing_name, -ing_quantity_needed)

            # Record the sale
            sale = Sale(
                product_id=product.id,
                product_name=name,
                price=price,
                quantity=quantity,
                discount=discount,
                date=datetime.now().strftime("%Y-%m-%d %H:%M")
            )
            self.db.add(sale)
            self.db.commit()

        except ValueError as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            raise e

    def data(self) -> List[Sale]:
        """Return list of all sales."""
        return self.db.query(Sale).order_by(Sale.date.desc()).all()
    
    def search(self, query: str) -> List[Sale]:
        """Search sales by product name or date."""
        return self.db.query(Sale).filter(
            (Sale.product_name.ilike(f"%{query}%")) |
            (Sale.date.ilike(f"%{query}%"))
        ).order_by(Sale.date.desc()).all()
    
    def salesByProduct(self):
        """Get sales grouped by product with total price."""
        return self.db.query(
            Sale.product_id,
            Sale.product_name,
            func.sum(Sale.price * Sale.quantity).label('total_price')
        ).group_by(Sale.product_id, Sale.product_name).all()
        
    def len(self) -> int:
        """Return count of sales."""
        return self.db.query(Sale).count()
    
    def empty(self) -> bool:
        """Check if repository is empty."""
        return self.len() == 0