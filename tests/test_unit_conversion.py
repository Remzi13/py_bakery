"""Tests for unit conversion and recipe units."""

import pytest
from sqlalchemy.orm import Session
from repositories.products import ProductsRepository
from repositories.sales import SalesRepository
from sql_model.entities import Product, StockItem, StockCategory, Unit
from sql_model.model import SQLAlchemyModel


@pytest.fixture
def model(test_db: Session):
    """Fixture to provide SQLAlchemyModel instance."""
    return SQLAlchemyModel(test_db)


@pytest.fixture
def setup_units_and_materials(test_db: Session):
    """Setup units (kg, g) and materials for testing conversion."""
    # Ensure units exist
    kg_unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
    if not kg_unit:
        kg_unit = Unit(name='kg')
        test_db.add(kg_unit)
    
    g_unit = test_db.query(Unit).filter(Unit.name == 'g').first()
    if not g_unit:
        g_unit = Unit(name='g')
        test_db.add(g_unit)
    
    # Ensure category exists
    materials_cat = test_db.query(StockCategory).filter(StockCategory.name == 'Materials').first()
    if not materials_cat:
        materials_cat = StockCategory(name='Materials')
        test_db.add(materials_cat)
    
    test_db.flush()
    
    # Create stock item in kg
    flour = StockItem(name='Flour', category_id=materials_cat.id, quantity=10.0, unit_id=kg_unit.id)
    test_db.add(flour)
    test_db.commit()
    
    return {
        'flour': flour,
        'kg_unit': kg_unit,
        'g_unit': g_unit
    }


def test_product_with_unit_conversion(test_db: Session, setup_units_and_materials, model):
    """
    Test creating a product with a recipe in grams while stock is in kg.
    Verify that conversion_factor and recipe_unit_id are saved and used.
    """
    repo = model.products()
    sales_repo = model.sales()
    
    g_unit = setup_units_and_materials['g_unit']
    kg_unit = setup_units_and_materials['kg_unit']
    
    # Create product: requires 500g of Flour per unit
    # In stock, Flour is 10.0 kg
    materials = [
        {
            'name': 'Flour',
            'quantity': 500.0,
            'conversion_factor': 0.001,  # 500g * 0.001 = 0.5kg
            'recipe_unit_id': g_unit.id
        }
    ]
    
    product_name = 'ConversionBread'
    repo.add(product_name, 100, materials)
    
    # 1. Verify storage
    product = repo.by_name(product_name)
    assert product is not None
    
    saved_materials = repo.get_materials_for_product(product.id)
    assert len(saved_materials) == 1
    m = saved_materials[0]
    assert m['name'] == 'Flour'
    assert m['quantity'] == 500.0
    assert m['recipe_unit_id'] == g_unit.id
    assert m['conversion_factor'] == 0.001
    
    # 2. Verify deduction in sale
    # Initial stock: 10.0 kg
    # Sell 2 units: should deduct 2 * 500g * 0.001 = 1.0 kg
    sales_repo.add(product_name, 100, 2, 0)
    
    # Check remaining stock
    flour_stock = test_db.query(StockItem).filter(StockItem.name == 'Flour').first()
    assert flour_stock.quantity == 9.0  # 10.0 - 1.0


def test_product_update_retains_conversion(test_db: Session, setup_units_and_materials, model):
    """Test that updating a product correctly updates/retains conversion fields."""
    repo = model.products()
    g_unit = setup_units_and_materials['g_unit']
    
    materials = [
        {
            'name': 'Flour',
            'quantity': 200.0,
            'conversion_factor': 0.001,
            'recipe_unit_id': g_unit.id
        }
    ]
    
    product_name = 'UpdateBread'
    repo.add(product_name, 100, materials)
    product = repo.by_name(product_name)
    
    # Update quantity to 300g
    new_materials = [
        {
            'name': 'Flour',
            'quantity': 300.0,
            'conversion_factor': 0.001,
            'recipe_unit_id': g_unit.id
        }
    ]
    repo.update(product.id, product_name, 120, new_materials)
    
    # Verify
    updated_materials = repo.get_materials_for_product(product.id)
    assert updated_materials[0]['quantity'] == 300.0
    assert updated_materials[0]['conversion_factor'] == 0.001
    assert updated_materials[0]['recipe_unit_id'] == g_unit.id


def test_writeoff_with_unit_conversion(test_db: Session, setup_units_and_materials, model):
    """
    Test writing off a product that has unit conversion in its recipe.
    Verify that correct amount of stock is deducted.
    """
    repo = model.products()
    wo_repo = model.writeoffs()
    
    g_unit = setup_units_and_materials['g_unit']
    
    # Create product: requires 500g of Flour per unit
    materials = [
        {
            'name': 'Flour',
            'quantity': 500.0,
            'conversion_factor': 0.001,
            'recipe_unit_id': g_unit.id
        }
    ]
    
    product_name = 'WriteOffBread'
    repo.add(product_name, 100, materials)
    
    # Initial stock: 10.0 kg (from setup)
    # Write off 3 units: should deduct 3 * 500g * 0.001 = 1.5 kg
    wo_repo.add(product_name, 'product', 3.0, 'Spoilage')
    
    # Check remaining stock
    flour_stock = test_db.query(StockItem).filter(StockItem.name == 'Flour').first()
    assert flour_stock.quantity == 8.5  # 10.0 - 1.5
