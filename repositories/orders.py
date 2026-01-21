from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from types import SimpleNamespace

from sql_model.entities import Order, OrderItem


class OrdersRepository:
    """Repository for managing orders using SQLAlchemy ORM."""
    
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model
    
    def add(self, items: List[dict], completion_date: Optional[str] = None, additional_info: Optional[str] = None, complete_now: bool = False) -> Order:
        """
        Create a new order with items.
        
        Args:
            items: List of dicts with 'product_id' and 'quantity'
            completion_date: Optional completion date/time
            additional_info: Optional additional information
            complete_now: Whether to mark as completed immediately
        
        Returns:
            Created Order object
        """
        status = 'pending'
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Create order
        order = Order(
            created_date=created_date,
            completion_date=completion_date,
            status=status,
            additional_info=additional_info
        )
        self.db.add(order)
        self.db.flush()
        order_id = order.id
        
        # Add order items
        for item in items:
            product = self.model.products().by_id(item['product_id'])
            if not product:
                self.db.rollback()
                raise ValueError(f"Product with ID {item['product_id']} not found")
            
            order_item = OrderItem(
                order_id=order_id,
                product_id=product.id,
                product_name=product.name,
                quantity=item['quantity'],
                price=product.price
            )
            self.db.add(order_item)
        
        self.db.commit()
        
        if complete_now:
            self.complete(order_id)
            return self.by_id(order_id)
            
        return self.by_id(order_id)
    
    def data(self) -> List[SimpleNamespace]:
        """Get all orders with their items."""
        orders = self.db.query(Order).order_by(Order.created_date.desc()).all()
        result = []
        
        for order in orders:
            order_dict = {
                'id': order.id,
                'created_date': order.created_date,
                'completion_date': order.completion_date,
                'status': order.status,
                'additional_info': order.additional_info,
                'items': [self._item_to_dict(item) for item in order.items]
            }
            result.append(SimpleNamespace(**order_dict))
        
        return result
    
    def get_pending(self) -> List[SimpleNamespace]:
        """Get all pending orders."""
        orders = self.db.query(Order).filter(
            Order.status == 'pending'
        ).order_by(Order.completion_date.asc()).all()
        
        result = []
        for order in orders:
            order_dict = {
                'id': order.id,
                'created_date': order.created_date,
                'completion_date': order.completion_date,
                'status': order.status,
                'additional_info': order.additional_info,
                'items': [self._item_to_dict(item) for item in order.items]
            }
            result.append(SimpleNamespace(**order_dict))
        
        return result
    
    def by_id(self, order_id: int) -> Optional[SimpleNamespace]:
        """Get order by ID with items."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            return None
        
        order_dict = {
            'id': order.id,
            'created_date': order.created_date,
            'completion_date': order.completion_date,
            'status': order.status,
            'additional_info': order.additional_info,
            'items': [self._item_to_dict(item) for item in order.items]
        }
        return SimpleNamespace(**order_dict)
    
    def _item_to_dict(self, item: OrderItem) -> dict:
        """Convert OrderItem to dict."""
        return {
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product_name,
            'quantity': item.quantity,
            'price': item.price
        }
    
    def get_by_product(self, product_id: int) -> List[SimpleNamespace]:
        """Get orders containing a specific product."""
        orders = self.db.query(Order).join(OrderItem).filter(
            OrderItem.product_id == product_id
        ).order_by(Order.created_date.desc()).all()
        
        result = []
        for order in orders:
            order_dict = {
                'id': order.id,
                'created_date': order.created_date,
                'completion_date': order.completion_date,
                'status': order.status,
                'additional_info': order.additional_info,
                'items': [self._item_to_dict(item) for item in order.items]
            }
            result.append(SimpleNamespace(**order_dict))
        return result

    def complete(self, order_id: int) -> bool:
        """
        Mark order as completed, create sales records, and deduct inventory.
        
        Args:
            order_id: ID of the order to complete
        
        Returns:
            True if successful
        """
        # Get order
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status == 'completed':
            raise ValueError(f"Order {order_id} is already completed")
        
        try:
            # For each item in order create sale
            for item in order.items:
                self.model.sales().add(
                    name=item.product_name,
                    price=item.price,
                    quantity=item.quantity,
                    discount=0
                )
            
            # Update order status
            completion_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            order.status = 'completed'
            order.completion_date = completion_date
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete(self, order_id: int) -> bool:
        """Delete an order."""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if order:
                self.db.delete(order)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_status(self, order_id: int, status: str) -> bool:
        """Update order status."""
        if status not in ['pending', 'completed']:
            raise ValueError("Status must be 'pending' or 'completed'")
        
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return False
            
            order.status = status
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
