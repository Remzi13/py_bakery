import sqlite3
from typing import Optional, List

from sql_model.entities import Supplier

class SuppliersRepository:
    """Репозиторий для управления Поставщиками (suppliers)."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # --- Вспомогательные методы ---

    def _row_to_entity(self, row: sqlite3.Row) -> Optional[Supplier]:
        """Преобразует строку из БД в объект Supplier."""
        if row is None:
            return None
        return Supplier(
            id=row['id'],
            name=row['name'],
            contact_person=row['contact_person'],
            phone=row['phone'],
            email=row['email'],
            address=row['address']
        )

    # --- CRUD Методы ---

    def add(self, name: str, contact_person: Optional[str] = None, phone: Optional[str] = None, email: Optional[str] = None, address: Optional[str] = None) -> Supplier:
        """Добавляет нового поставщика."""
        cursor = self._conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO suppliers (name, contact_person, phone, email, address) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, contact_person, phone, email, address)
            )
            self._conn.commit()
            return self.by_id(cursor.lastrowid) # Возвращаем созданный объект
        except sqlite3.IntegrityError as e:
            self._conn.rollback()
            raise ValueError(f"Поставщик с именем '{name}' уже существует.")
        except Exception as e:
            self._conn.rollback()
            raise e

    def by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Возвращает поставщика по ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        return self._row_to_entity(cursor.fetchone())

    def by_name(self, name: str) -> Optional[Supplier]:
        """Возвращает поставщика по имени."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE name = ?", (name,))
        return self._row_to_entity(cursor.fetchone())

    def data(self) -> List[Supplier]:
        """Возвращает список всех поставщиков."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def names(self) -> List[str]:
        """Возвращает список имен всех поставщиков."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM suppliers ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    def len(self) -> int:
        """Возвращает количество поставщиков."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        return cursor.fetchone()[0]

    def search(self, query: str) -> List[Supplier]:
        """Поиск поставщиков по имени, контакту, телефону или email."""
        cursor = self._conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute(
            """
            SELECT * FROM suppliers 
            WHERE name LIKE ? 
               OR contact_person LIKE ? 
               OR phone LIKE ? 
               OR email LIKE ?
            ORDER BY name
            """,
            (search_pattern, search_pattern, search_pattern, search_pattern)
        )
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def update(self, supplier_id: int, name: str, contact_person: Optional[str] = None, phone: Optional[str] = None, email: Optional[str] = None, address: Optional[str] = None) -> Supplier:
        """
        Обновляет существующего поставщика по ID.
        Возвращает обновленный объект Supplier.
        
        Args:
            supplier_id (int): ID поставщика для обновления.
            name (str): Новое имя поставщика (обязательно).
            contact_person (Optional[str]): Новое контактное лицо.
            phone (Optional[str]): Новый телефон.
            email (Optional[str]): Новый email.
            address (Optional[str]): Новый адрес.
            
        Raises:
            ValueError: Если поставщик с ID не найден или новое имя уже занято.
        """
        cursor = self._conn.cursor()
        
        # Если контактные данные переданы как пустые строки, преобразуем их в None
        contact_person = contact_person.strip() if contact_person else None
        phone = phone.strip() if phone else None
        email = email.strip() if email else None
        address = address.strip() if address else None

        if not name:
            raise ValueError("Имя поставщика не может быть пустым.")
        
        try:
            cursor.execute(
                """
                UPDATE suppliers 
                SET name = ?, contact_person = ?, phone = ?, email = ?, address = ?
                WHERE id = ?
                """,
                (name, contact_person, phone, email, address, supplier_id)
            )
            self._conn.commit()
            
            if cursor.rowcount == 0:
                raise ValueError(f"Поставщик с ID {supplier_id} не найден.")
            
            return self.by_id(supplier_id) # Возвращаем обновленный объект
            
        except sqlite3.IntegrityError as e:
            self._conn.rollback()
            # Ошибка возникнет, если новое имя уже занято другим поставщиком
            raise ValueError(f"Поставщик с именем '{name}' уже существует.")
        except Exception as e:
            self._conn.rollback()
            raise e

    def can_delete_by_id(self, supplier_id: int) -> bool:
        """
        Проверяет, можно ли удалить поставщика по ID. 
        Нельзя удалить, если он связан с расходами (таблица expense_documents).
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT 1 FROM expense_documents WHERE supplier_id = ? LIMIT 1", 
            (supplier_id,)
        )
        return cursor.fetchone() is None

    def can_delete(self, name: str) -> bool:
        """
        Проверяет, можно ли удалить поставщика по имени. 
        """
        supplier = self.by_name(name)
        if not supplier:
            return True
        return self.can_delete_by_id(supplier.id)
    
    def delete_by_id(self, supplier_id: int):
        """
        Удаляет поставщика по ID. 
        Вызывает ошибку, если поставщик связан с расходами.
        """
        if not self.can_delete_by_id(supplier_id):
            supplier = self.by_id(supplier_id)
            name = supplier.name if supplier else f"ID {supplier_id}"
            raise ValueError(f"Поставщик '{name}' связан с существующими расходами. Удаление невозможно.")
        
        cursor = self._conn.cursor()
        try:
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            raise e

    def delete(self, name: str):
        """
        Удаляет поставщика по имени. 
        """
        supplier = self.by_name(name)
        if not supplier:
            return
        self.delete_by_id(supplier.id)

