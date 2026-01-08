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

    def can_delete(self, name: str) -> bool:
        """
        Проверяет, можно ли удалить поставщика. 
        Нельзя удалить, если он связан с расходами (таблица expenses).
        """
        supplier = self.by_name(name)
        if not supplier:
            return True # Если поставщика нет, его можно "удалить" (ничего не делать)
        
        cursor = self._conn.cursor()
        # Ищем расходы, у которых supplier_id совпадает с нашим ID.
        # Я предполагаю, что в вашей таблице expenses есть поле supplier_id.
        # Если такого поля нет, пожалуйста, сообщите, и мы изменим схему.
        cursor.execute(
            """
            SELECT 1 FROM expenses WHERE supplier_id = ? LIMIT 1
            """, 
            (supplier.id,)
        )
        # Если fetchone() возвращает что-то (например, 1), значит, связанные расходы есть.
        return cursor.fetchone() is None
    
    def delete(self, name: str):
        """
        Удаляет поставщика по имени. 
        Вызывает ошибку, если поставщик связан с расходами.
        """
        supplier = self.by_name(name)
        if not supplier:
            return # Ничего удалять не надо

        if not self.can_delete(name):
            # Используем понятное исключение
            raise ValueError(f"Поставщик '{name}' связан с существующими расходами. Удаление невозможно.")
        
        cursor = self._conn.cursor()
        try:
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier.id,))
            self._conn.commit()
            
        except Exception as e:
            self._conn.rollback()
            raise e

