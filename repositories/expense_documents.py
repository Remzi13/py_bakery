import sqlite3
from typing import List, Dict, Optional, Any
from sql_model.entities import ExpenseDocument, ExpenseItem

class ExpenseDocumentsRepository:
    def __init__(self, conn: sqlite3.Connection, model_instance: Any):
        self._conn = conn
        self._model = model_instance

    def add(self, date: str, supplier_id: int, total_amount: float, comment: str, items: List[Dict[str, Any]]) -> int:
        """
        Создает документ расхода и связанные позиции.
        Автоматически пополняет склад, если тип расхода помечен как 'stock'.
        
        Args:
            items: Список словарей [{'expense_type_id': int, 'quantity': float, 'price_per_unit': int, 'unit_id': int}]
        """
        cursor = self._conn.cursor()
        try:
             # 1. Создаем документ
             cursor.execute("""
                INSERT INTO expense_documents (date, supplier_id, total_amount, comment) 
                VALUES (?, ?, ?, ?)
             """, (date, supplier_id, total_amount, comment))
             
             doc_id = cursor.lastrowid
             
             # 2. Добавляем позиции
             for item in items:
                 self._add_item(cursor, doc_id, item)

             self._conn.commit()
             return doc_id
        except Exception as e:
            self._conn.rollback()
            raise e

    def _add_item(self, cursor: sqlite3.Cursor, doc_id: int, item_data: Dict[str, Any]):
        exp_type_id = item_data['expense_type_id']
        quantity = item_data['quantity']
        price = item_data['price_per_unit']
        unit_id = item_data['unit_id']
        
        # Получаем информацию о типе расхода
        cursor.execute("SELECT name, stock, category_id FROM expense_types WHERE id = ?", (exp_type_id,))
        et_row = cursor.fetchone()
        if not et_row:
             raise ValueError(f"Expense Type ID {exp_type_id} not found")
        
        et_name = et_row[0]
        et_stock = bool(et_row[1]) if et_row[1] is not None else False
        et_cat_id = et_row[2]

        stock_item_id = None
        
        # Логика пополнения склада
        if et_stock:
             # Ищем товар на складе по имени
             cursor.execute("SELECT id FROM stock WHERE name = ?", (et_name,))
             stock_row = cursor.fetchone()
             
             if stock_row:
                 # Обновляем существующий
                 stock_item_id = stock_row[0]
                 cursor.execute("UPDATE stock SET quantity = quantity + ? WHERE id = ?", (quantity, stock_item_id))
             else:
                 # Создаем новый товар на складе
                 # Пытаемся сопоставить категорию расхода с категорией склада по имени
                 cursor.execute("SELECT name FROM expense_categories WHERE id = ?", (et_cat_id,))
                 ec_name = cursor.fetchone()[0]
                 
                 cursor.execute("SELECT id FROM stock_categories WHERE name = ?", (ec_name,))
                 sc_row = cursor.fetchone()
                 
                 # Если категории совпадают (например 'Materials'), берем ID. 
                 # Если нет — берем первую попавшуюся (например Materials, id=1) или создаем ошибку?
                 # Для надежности используем ID=1 (Materials) как дефолт.
                 sc_id = sc_row[0] if sc_row else 1 
                 
                 cursor.execute("""
                    INSERT INTO stock (name, category_id, quantity, unit_id) 
                    VALUES (?, ?, ?, ?)
                 """, (et_name, sc_id, quantity, unit_id))
                 
                 stock_item_id = cursor.lastrowid
        
        # Добавляем запись в expense_items
        total_price = quantity * price
        cursor.execute("""
            INSERT INTO expense_items 
            (document_id, expense_type_id, stock_item_id, unit_id, quantity, price_per_unit, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, exp_type_id, stock_item_id, unit_id, quantity, price, total_price))

    def get_documents_with_details(self) -> List[Dict[str, Any]]:
        """Возвращает список документов с именем поставщика и количеством позиций."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT d.id, d.date, d.total_amount, d.comment, s.name as supplier_name, COUNT(i.id) as items_count
            FROM expense_documents d
            LEFT JOIN suppliers s ON d.supplier_id = s.id
            LEFT JOIN expense_items i ON d.id = i.document_id
            GROUP BY d.id
            ORDER BY d.date DESC
        """)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "date": row[1],
                "total_amount": row[2],
                "comment": row[3],
                "supplier_name": row[4],
                "items_count": row[5]
            })
        return result

    def get_document_items(self, document_id: int) -> List[Dict[str, Any]]:
        """Возвращает позиции конкретного документа."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT i.id, i.quantity, i.price_per_unit, i.total_price, et.name as expense_type_name, u.name as unit_name
            FROM expense_items i
            JOIN expense_types et ON i.expense_type_id = et.id
            JOIN units u ON i.unit_id = u.id
            WHERE i.document_id = ?
        """, (document_id,))
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "quantity": row[1],
                "price_per_unit": row[2],
                "total_price": row[3],
                "expense_type_name": row[4],
                "unit_name": row[5]
            })
        return result
