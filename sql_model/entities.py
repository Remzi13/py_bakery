"""SQLAlchemy ORM models for the bakery management system."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sql_model.database import Base


# Association table for Product-Stock relationship (many-to-many)
product_stock_association = Table(
    'product_stock',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('stock_id', Integer, ForeignKey('stock.id', ondelete='RESTRICT'), primary_key=True),
    Column('quantity', Float, nullable=False),
)


class Unit(Base):
    """Единица измерения (kg, g, l, pc)."""
    __tablename__ = "units"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    # Relationships
    stock_items: Mapped[List["StockItem"]] = relationship("StockItem", back_populates="unit")
    write_offs: Mapped[List["WriteOff"]] = relationship("WriteOff", back_populates="unit")
    expense_items: Mapped[List["ExpenseItem"]] = relationship("ExpenseItem", back_populates="unit")
    expense_types: Mapped[List["ExpenseType"]] = relationship("ExpenseType", back_populates="unit")
    
    def __repr__(self):
        return f"<Unit(id={self.id}, name={self.name})>"


class StockCategory(Base):
    """Категория запасов (Materials, Packaging, Equipment)."""
    __tablename__ = "stock_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    # Relationships
    stock_items: Mapped[List["StockItem"]] = relationship("StockItem", back_populates="category")
    
    def __repr__(self):
        return f"<StockCategory(id={self.id}, name={self.name})>"


class ExpenseCategory(Base):
    """Категория финансовых расходов."""
    __tablename__ = "expense_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    # Relationships
    expense_types: Mapped[List["ExpenseType"]] = relationship("ExpenseType", back_populates="category")
    
    def __repr__(self):
        return f"<ExpenseCategory(id={self.id}, name={self.name})>"


class Product(Base):
    """Готовый продукт для продажи."""
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Integer, nullable=False)
    
    # Relationships
    sales: Mapped[List["Sale"]] = relationship("Sale", back_populates="product")
    write_offs: Mapped[List["WriteOff"]] = relationship("WriteOff", back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

    materials: Mapped[List["StockItem"]] = relationship(
        "StockItem", 
        secondary=product_stock_association,
        backref="products"
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"


class StockItem(Base):
    """Инвентарь/Запас."""
    __tablename__ = "stock"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('stock_categories.id'), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    
    # Relationships
    category: Mapped["StockCategory"] = relationship("StockCategory", back_populates="stock_items")
    unit: Mapped["Unit"] = relationship("Unit", back_populates="stock_items")
    write_offs: Mapped[List["WriteOff"]] = relationship("WriteOff", back_populates="stock_item")
    expense_items: Mapped[List["ExpenseItem"]] = relationship("ExpenseItem", back_populates="stock_item")
    
    def __repr__(self):
        return f"<StockItem(id={self.id}, name={self.name}, quantity={self.quantity})>"


class Sale(Base):
    """Проданный продукт."""
    __tablename__ = "sales"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="sales")
    
    def __repr__(self):
        return f"<Sale(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


class ExpenseType(Base):
    """Тип расхода (например, 'Аренда', 'Мука')."""
    __tablename__ = "expense_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    default_price: Mapped[float] = mapped_column(Integer, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('expense_categories.id'), nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)    
    
    # Relationships
    category: Mapped["ExpenseCategory"] = relationship("ExpenseCategory", back_populates="expense_types")
    unit: Mapped["Unit"] = relationship("Unit", back_populates="expense_types")
    expense_items: Mapped[List["ExpenseItem"]] = relationship("ExpenseItem", back_populates="expense_type")
    
    def __repr__(self):
        return f"<ExpenseType(id={self.id}, name={self.name}, default_price={self.default_price})>"


class Supplier(Base):
    """Поставщик сырья или услуг."""
    __tablename__ = "suppliers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships
    expense_documents: Mapped[List["ExpenseDocument"]] = relationship("ExpenseDocument", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name={self.name})>"


class WriteOff(Base):
    """Запись о списании (готового продукта или сырья/запаса)."""
    __tablename__ = "writeoffs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('products.id'), nullable=True)
    stock_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('stock.id'), nullable=True)
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('units.id'), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="write_offs")
    stock_item: Mapped[Optional["StockItem"]] = relationship("StockItem", back_populates="write_offs")
    unit: Mapped[Optional["Unit"]] = relationship("Unit", back_populates="write_offs")
    
    def __repr__(self):
        return f"<WriteOff(id={self.id}, quantity={self.quantity}, reason={self.reason})>"


class Order(Base):
    """Заказ с отложенным выполнением."""
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_date: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # 'pending' or 'completed'
    completion_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    additional_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, status={self.status}, created_date={self.created_date})>"


class OrderItem(Base):
    """Позиция в заказе."""
    __tablename__ = "order_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Integer, nullable=False)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"


class ExpenseDocument(Base):
    """Документ о закупке (чек/накладная)."""
    __tablename__ = "expense_documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String, nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=False)
    total_amount: Mapped[float] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="expense_documents")
    items: Mapped[List["ExpenseItem"]] = relationship("ExpenseItem", back_populates="document")
    
    def __repr__(self):
        return f"<ExpenseDocument(id={self.id}, supplier_id={self.supplier_id}, total_amount={self.total_amount})>"


class ExpenseItem(Base):
    """Позиция в документе о закупке."""
    __tablename__ = "expense_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey('expense_documents.id', ondelete='CASCADE'), nullable=False)
    expense_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('expense_types.id'), nullable=False)
    stock_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('stock.id'), nullable=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)    
    
    # Relationships
    document: Mapped["ExpenseDocument"] = relationship("ExpenseDocument", back_populates="items")
    expense_type: Mapped["ExpenseType"] = relationship("ExpenseType", back_populates="expense_items")
    stock_item: Mapped[Optional["StockItem"]] = relationship("StockItem", back_populates="expense_items")
    unit: Mapped["Unit"] = relationship("Unit", back_populates="expense_items")
    
    def __repr__(self):
        return f"<ExpenseItem(id={self.id}, document_id={self.document_id}, quantity={self.quantity})>"
