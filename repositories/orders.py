import sqlite3
from typing import List, Optional
from datetime import datetime
from sql_model.entities import Order, OrderItem
from types import SimpleNamespace

class OrdersRepository:
    """Repository for managing orders."""
    
    def __init__(self, conn: sqlite3.Connection, model):
        self.conn = conn
        self.model = model
    
    def add(self, items: List[dict], completion_date: Optional[str] = None, additional_info: Optional[str] = None, complete_now: bool = False) -> Order:
        """
        Create a new order with items.
        
        Args:
            items: List of dicts with 'product_id' and 'quantity'
            completion_date: Optional completion date/time
            additional_info: Optional additional information
        
        Returns:
            Created Order object
        """
        cursor = self.conn.cursor()
        
        # Determine status. If complete_now is True, we start as pending so complete() can do its work.
        if complete_now:
            status = 'pending'
        else:
            status = 'pending'
            
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Insert order
        cursor.execute(
            """
            INSERT INTO orders (created_date, completion_date, status, additional_info)
            VALUES (?, ?, ?, ?)
            """,
            (created_date, completion_date, status, additional_info)
        )
        order_id = cursor.lastrowid
        
        # Insert order items
        for item in items:
            product = self.model.products().by_id(item['product_id'])
            if not product:
                raise ValueError(f"Product with ID {item['product_id']} not found")
            
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, product.id, product.name, item['quantity'], product.price)
            )
        
        self.conn.commit()
        
        if complete_now:
            self.complete(order_id)
            # Re-fetch order to get updated status and completion_date
            return self.by_id(order_id)
            
        return Order(
            id=order_id,
            created_date=created_date,
            completion_date=completion_date,
            status=status,
            additional_info=additional_info
        )
    
    def data(self) -> List[SimpleNamespace]:
        """Get all orders with their items."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, created_date, completion_date, status, additional_info
            FROM orders
            ORDER BY created_date DESC
            """
        )
        
        orders = []
        for row in cursor.fetchall():
            order_dict = dict(row)
            order_dict['items'] = self._get_order_items(order_dict['id'])
            orders.append(SimpleNamespace(**order_dict))
        
        return orders
    
    def get_pending(self) -> List[SimpleNamespace]:
        """Get all pending orders."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, created_date, completion_date, status, additional_info
            FROM orders
            WHERE status = 'pending'
            ORDER BY completion_date ASC
            """
        )
        
        orders = []
        for row in cursor.fetchall():
            order_dict = dict(row)
            order_dict['items'] = self._get_order_items(order_dict['id'])
            orders.append(SimpleNamespace(**order_dict))
        
        return orders
    
    def by_id(self, order_id: int) -> Optional[SimpleNamespace]:
        """Get order by ID with items."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, created_date, completion_date, status, additional_info
            FROM orders
            WHERE id = ?
            """,
            (order_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        order_dict = dict(row)
        order_dict['items'] = self._get_order_items(order_dict['id'])
        return SimpleNamespace(**order_dict)
    
    def _get_order_items(self, order_id: int) -> List[dict]:
        """Get items for a specific order."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, product_id, product_name, quantity, price
            FROM order_items
            WHERE order_id = ?
            """,
            (order_id,)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def complete(self, order_id: int) -> bool:
        """
        Mark order as completed, create sales records, and deduct inventory.
        
        Args:
            order_id: ID of the order to complete
        
        Returns:
            True if successful
        """
        # Get order
        order = self.by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status == 'completed':
            raise ValueError(f"Order {order_id} is already completed")
        
        cursor = self.conn.cursor()
        try:
            # For each item in order:
            # 1. Create sale record
            # 2. Deduct ingredients from stock
            for item in order.items:
                # Create sale
                self.model.sales().add(
                    name=item['product_name'],
                    price=item['price'],
                    quantity=item['quantity'],
                    discount=0
                )
            
            # Update order status
            completion_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(
                """
                UPDATE orders
                SET status = 'completed', completion_date = ?
                WHERE id = ?
                """,
                (completion_date, order_id)
            )
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def delete(self, order_id: int) -> bool:
        """Delete an order."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_status(self, order_id: int, status: str) -> bool:
        """Update order status."""
        if status not in ['pending', 'completed']:
            raise ValueError("Status must be 'pending' or 'completed'")
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE orders
            SET status = ?
            WHERE id = ?
            """,
            (status, order_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0
