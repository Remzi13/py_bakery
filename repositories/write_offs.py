from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy.orm import Session

from sql_model.entities import WriteOff


class WriteOffsRepository:
    """Repository for WriteOff entities using SQLAlchemy ORM."""

    def __init__(self, db: Session, model_instance: Any):
        self.db = db
        self._model = model_instance  # Reference to Model for Stock, Products and Utils

    # --- Main method: Register write-off ---

    def add(self, item_name: str, item_type: str, quantity: float, reason: str):
        """
        Register a write-off (finished product or stock/raw material).

        Write-off of finished product (item_type='product') is registered and
        deducts ingredients from stock according to recipe.
        Write-off of stock/raw material (item_type='stock') is registered and
        deducts from Stock.

        Args:
            item_name: Item name
            item_type: Type of item ('product' or 'stock')
            quantity: Quantity to write off
            reason: Reason for write-off

        Raises:
            ValueError: If item not found, quantity invalid, or insufficient stock
        """
        if item_type not in ['product', 'stock']:
            raise ValueError("Invalid item type. Use 'product' or 'stock'.")

        if quantity <= 0:
            raise ValueError("Write-off quantity must be positive.")

        stock_repo = self._model.stock()
        
        # Variables for write-offs table
        product_id = None
        stock_item_id = None
        unit_id = None

        try:
            if item_type == 'product':
                # --- LOGIC FOR WRITING OFF FINISHED PRODUCT ---
                product_repo = self._model.products()
                
                # 1. Find product and recipe
                product_entity = product_repo.by_name(item_name)
                if product_entity is None:
                    raise ValueError(f"Product '{item_name}' not found.")
                
                mats_needed = product_repo.get_materials_for_product(product_entity.id)
                product_id = product_entity.id
                
                # 2. Deduct ingredients from stock
                for ing in mats_needed:
                    ing_name = ing['name']
                    conversion = ing.get('conversion_factor', 1.0)
                    ing_quantity_needed = ing['quantity'] * quantity * conversion
                    
                    current_stock = stock_repo.get(ing_name)
                    if current_stock is None:
                        raise ValueError(f"Ingredient '{ing_name}' for product '{item_name}' not found in stock.")
                    
                    new_quantity = current_stock.quantity - ing_quantity_needed
                    if new_quantity < 0:
                        raise ValueError(
                            f"Insufficient ingredient '{ing_name}' to write off {quantity} "
                            f"of '{item_name}'. Need {ing_quantity_needed}, have {current_stock.quantity}."
                        )
                    
                    stock_repo.set(ing_name, new_quantity)
                
            elif item_type == 'stock':
                # --- LOGIC FOR WRITING OFF STOCK/RAW MATERIAL ---
                current_stock_item = stock_repo.get(item_name)
                
                if current_stock_item is None:
                    raise ValueError(f"Item '{item_name}' not found in stock.")
                
                stock_item_id = current_stock_item.id
                unit_id = current_stock_item.unit_id
                
                # 1. Check stock before write-off
                if current_stock_item.quantity < quantity:
                    raise ValueError(
                        f"Insufficient stock '{item_name}' to write off "
                        f"({current_stock_item.quantity} < {quantity})."
                    )
                
                # 2. Decrease stock quantity
                new_quantity = current_stock_item.quantity - quantity
                stock_repo.set(item_name, new_quantity)
            
            # 3. Record write-off in log (for both types)
            writeoff = WriteOff(
                product_id=product_id,
                stock_item_id=stock_item_id,
                unit_id=unit_id,
                quantity=quantity,
                reason=reason,
                date=datetime.now().strftime("%Y-%m-%d %H:%M")
            )
            self.db.add(writeoff)
            self.db.commit()

        except ValueError as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            raise e
    
    def by_id(self, writeoff_id: int) -> Optional[WriteOff]:
        """Get write-off record by ID."""
        return self.db.query(WriteOff).filter(WriteOff.id == writeoff_id).first()

    def delete(self, writeoff_id: int):
        """Delete a write-off record."""
        wo = self.by_id(writeoff_id)
        if wo:
            try:
                self.db.delete(wo)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e

    def get_by_date_range(self, start_date: str, end_date: str) -> List[WriteOff]:
        """Get write-offs within a date range."""
        return self.db.query(WriteOff).filter(
            WriteOff.date >= start_date,
            WriteOff.date <= end_date + " 23:59"
        ).order_by(WriteOff.date.desc()).all()

    def get_by_stock_item(self, stock_item_id: int) -> List[WriteOff]:
        """Get write-offs for a specific stock item."""
        return self.db.query(WriteOff).filter(WriteOff.stock_item_id == stock_item_id).all()

    def data(self) -> List[WriteOff]:
        """Return list of all write-offs (for display in table)."""
        return self.db.query(WriteOff).order_by(WriteOff.date.desc()).all()

    def len(self) -> int:
        """Return count of write-off records."""
        return self.db.query(WriteOff).count()