from typing import Optional, List
from sqlalchemy.orm import Session

from sql_model.entities import Supplier, ExpenseDocument


class SuppliersRepository:
    """Repository for managing Suppliers using SQLAlchemy ORM."""

    def __init__(self, db: Session):
        self.db = db

    # --- CRUD Methods ---

    def add(self, name: str, contact_person: Optional[str] = None, phone: Optional[str] = None, email: Optional[str] = None, address: Optional[str] = None) -> Supplier:
        """Add a new supplier."""
        try:
            supplier = Supplier(
                name=name,
                contact_person=contact_person,
                phone=phone,
                email=email,
                address=address
            )
            self.db.add(supplier)
            self.db.flush()
            supplier_id = supplier.id
            self.db.commit()
            return self.by_id(supplier_id)
        except Exception as e:
            self.db.rollback()
            if 'UNIQUE' in str(e):
                raise ValueError(f"Supplier with name '{name}' already exists.")
            raise e

    def by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Return supplier by ID."""
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Return supplier by ID (alias for by_id)."""
        return self.by_id(supplier_id)

    def by_name(self, name: str) -> Optional[Supplier]:
        """Return supplier by name."""
        return self.db.query(Supplier).filter(Supplier.name == name).first()

    def data(self) -> List[Supplier]:
        """Return list of all suppliers."""
        return self.db.query(Supplier).order_by(Supplier.name).all()

    def names(self) -> List[str]:
        """Return list of all supplier names."""
        return [s.name for s in self.db.query(Supplier).order_by(Supplier.name).all()]

    def len(self) -> int:
        """Return count of suppliers."""
        return self.db.query(Supplier).count()

    def search(self, query: str) -> List[Supplier]:
        """Search suppliers by name, contact, phone or email."""
        return self.db.query(Supplier).filter(
            (Supplier.name.ilike(f"%{query}%")) |
            (Supplier.contact_person.ilike(f"%{query}%")) |
            (Supplier.phone.ilike(f"%{query}%")) |
            (Supplier.email.ilike(f"%{query}%"))
        ).order_by(Supplier.name).all()

    def update(self, supplier_id: int, name: str, contact_person: Optional[str] = None, phone: Optional[str] = None, email: Optional[str] = None, address: Optional[str] = None) -> Supplier:
        """
        Update an existing supplier by ID.
        Returns updated Supplier object.
        
        Args:
            supplier_id: ID of supplier to update
            name: New supplier name (required)
            contact_person: New contact person
            phone: New phone
            email: New email
            address: New address
            
        Raises:
            ValueError: If supplier not found or new name already taken
        """
        # Convert empty strings to None
        contact_person = contact_person.strip() if contact_person else None
        phone = phone.strip() if phone else None
        email = email.strip() if email else None
        address = address.strip() if address else None

        if not name:
            raise ValueError("Supplier name cannot be empty.")
        
        try:
            supplier = self.by_id(supplier_id)
            if not supplier:
                raise ValueError(f"Supplier with ID {supplier_id} not found.")
            
            supplier.name = name
            supplier.contact_person = contact_person
            supplier.phone = phone
            supplier.email = email
            supplier.address = address
            
            self.db.commit()
            return self.by_id(supplier_id)
            
        except Exception as e:
            self.db.rollback()
            if 'UNIQUE' in str(e):
                raise ValueError(f"Supplier with name '{name}' already exists.")
            raise e

    def can_delete_by_id(self, supplier_id: int) -> bool:
        """
        Check if supplier can be deleted by ID.
        Cannot delete if linked to expense documents.
        """
        count = self.db.query(ExpenseDocument).filter(
            ExpenseDocument.supplier_id == supplier_id
        ).count()
        return count == 0

    def can_delete(self, name: str) -> bool:
        """
        Check if supplier can be deleted by name.
        """
        supplier = self.by_name(name)
        if not supplier:
            return True
        return self.can_delete_by_id(supplier.id)
    
    def delete_by_id(self, supplier_id: int):
        """
        Delete supplier by ID.
        Raises error if supplier is linked to expense documents.
        """
        if not self.can_delete_by_id(supplier_id):
            supplier = self.by_id(supplier_id)
            name = supplier.name if supplier else f"ID {supplier_id}"
            raise ValueError(f"Supplier '{name}' is linked to existing expenses. Cannot delete.")
        
        try:
            supplier = self.by_id(supplier_id)
            if supplier:
                self.db.delete(supplier)
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def delete(self, name: str):
        """
        Delete supplier by name.
        """
        supplier = self.by_name(name)
        if not supplier:
            return
        self.delete_by_id(supplier.id)

