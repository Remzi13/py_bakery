from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from sql_model.entities import ExpenseDocument, ExpenseItem, ExpenseType, ExpenseCategory, StockItem, StockCategory, Unit, Supplier


class ExpenseDocumentsRepository:
    """Repository for ExpenseDocument entities using SQLAlchemy ORM."""
    
    def __init__(self, db: Session, model_instance: Any):
        self.db = db
        self._model = model_instance

    def by_id(self, document_id: int) -> Optional[ExpenseDocument]:
        """Get document by ID."""
        return self.db.query(ExpenseDocument).filter(ExpenseDocument.id == document_id).first()

    def data(self) -> List[ExpenseDocument]:
        """Return all documents."""
        return self.db.query(ExpenseDocument).order_by(ExpenseDocument.date.desc()).all()

    def add(self, date: str, supplier_id: int, total_amount: float, comment: str, items: List[Dict[str, Any]]) -> int:
        """
        Create an expense document and related items.
        Automatically replenishes stock if expense type is marked as 'stock'.
        
        Args:
            items: List of dicts [{'expense_type_id': int, 'quantity': float, 'price': int, 'unit_id': int}]
        """
        try:
            # 1. Create document
            document = ExpenseDocument(
                date=date,
                supplier_id=supplier_id,
                total_amount=total_amount,
                comment=comment
            )
            self.db.add(document)
            self.db.flush()
            doc_id = document.id
            
            # 2. Add items
            for item in items:
                self._add_item(doc_id, item)
            
            self.db.commit()
            return doc_id
        except Exception as e:
            self.db.rollback()
            raise e

    def _add_item(self, doc_id: int, item_data: Dict[str, Any]):
        """Add a single item to expense document."""
        exp_type_id = item_data['expense_type_id']
        quantity = item_data['quantity']
        price = item_data['price']
        unit_id = item_data['unit_id']
        
        # Get expense type info
        exp_type = self.db.query(ExpenseType).filter(ExpenseType.id == exp_type_id).first()
        if not exp_type:
            raise ValueError(f"Expense Type ID {exp_type_id} not found")
        
        stock_item_id = None
        
        # Logic for stock replenishment
        if exp_type.stock:
            # Search for item in stock by name
            stock_item = self.db.query(StockItem).filter(StockItem.name == exp_type.name).first()
            
            if stock_item:
                # Update existing
                stock_item_id = stock_item.id
                stock_item.quantity += quantity
            else:
                # Create new stock item
                category = self.db.query(ExpenseCategory).filter(
                    ExpenseCategory.id == exp_type.category_id
                ).first()
                
                # Try to match category names
                stock_category = self.db.query(StockCategory).filter(
                    StockCategory.name == (category.name if category else 'Materials')
                ).first()
                
                # Use Materials (id=1) as default if not found
                sc_id = stock_category.id if stock_category else 1
                
                unit = self.db.query(Unit).filter(Unit.id == unit_id).first()
                if not unit:
                    raise ValueError(f"Unit ID {unit_id} not found")
                
                new_stock = StockItem(
                    name=exp_type.name,
                    category_id=sc_id,
                    quantity=quantity,
                    unit_id=unit_id
                )
                self.db.add(new_stock)
                self.db.flush()
                stock_item_id = new_stock.id
        
        # Add expense item record
        expense_item = ExpenseItem(
            document_id=doc_id,
            expense_type_id=exp_type_id,
            stock_item_id=stock_item_id,
            unit_id=unit_id,
            quantity=quantity,
            price=price
        )
        self.db.add(expense_item)

    def get_documents_with_details(self) -> List[Dict[str, Any]]:
        """Return list of documents with supplier name and item count."""
        # Импортируйте модель Supplier, если она еще не импортирована
        results = self.db.query(
            ExpenseDocument.id,
            ExpenseDocument.date,
            ExpenseDocument.total_amount,
            ExpenseDocument.comment,
            Supplier.name.label('supplier_name'), # Выбираем сразу имя
            func.count(ExpenseItem.id).label('items_count')
        ).join(Supplier, ExpenseDocument.supplier_id == Supplier.id) \
         .outerjoin(ExpenseItem) \
         .group_by(ExpenseDocument.id, Supplier.name) \
         .order_by(ExpenseDocument.date.desc()).all()
        
        result = []
        for row in results:
            result.append({
                "id": row.id,
                "date": row.date,
                "total_amount": row.total_amount,
                "comment": row.comment,
                "supplier_name": row.supplier_name,
                "items_count": row.items_count
            })
        return result

    def get_document_items(self, document_id: int) -> List[Dict[str, Any]]:
        """Return items for a specific document."""
        items = self.db.query(ExpenseItem).filter(
            ExpenseItem.document_id == document_id
        ).all()
        
        result = []
        for item in items:
            result.append({
                "id": item.id,
                "quantity": item.quantity,
                "price": item.price,
                "expense_type_name": item.expense_type.name if item.expense_type else None,
                "unit_name": item.unit.name if item.unit else None
            })
        return result

    def delete(self, document_id: int) -> bool:
        """
        Delete expense document and rollback stock changes.
        For items with stock=true, deducts quantity from stock.
        """
        try:
            # 1. Get all items with stock info
            items = self.db.query(ExpenseItem).filter(
                ExpenseItem.document_id == document_id
            ).all()
            
            # 2. Rollback stock changes
            for item in items:
                if item.expense_type.stock and item.stock_item_id:
                    # Deduct from stock
                    stock_item = self.db.query(StockItem).filter(
                        StockItem.id == item.stock_item_id
                    ).first()
                    if stock_item:
                        stock_item.quantity -= item.quantity
                        
                        # Check for negative stock
                        if stock_item.quantity < 0:
                            raise ValueError(
                                f"Cannot delete document: would result in negative stock "
                                f"for '{stock_item.name}'"
                            )
            
            # 3. Delete expense items
            self.db.query(ExpenseItem).filter(
                ExpenseItem.document_id == document_id
            ).delete()
            
            # 4. Delete document
            document = self.db.query(ExpenseDocument).filter(
                ExpenseDocument.id == document_id
            ).first()
            if document:
                self.db.delete(document)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
