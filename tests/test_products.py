"""Tests for products router and repository."""

import pytest
from sqlalchemy.orm import Session
from repositories.products import ProductsRepository
from sql_model.entities import Product, StockItem, StockCategory, Unit


@pytest.fixture
def setup_stock_items(test_db: Session):
    """Setup stock items for testing product recipes."""
    # Create units and categories if not present
    kg_unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
    materials_cat = test_db.query(StockCategory).filter(StockCategory.name == 'Materials').first()
    
    if not kg_unit:
        kg_unit = Unit(name='kg')
        test_db.add(kg_unit)
        test_db.flush()
    
    if not materials_cat:
        materials_cat = StockCategory(name='Materials')
        test_db.add(materials_cat)
        test_db.flush()
    
    # Create stock items
    flour = StockItem(name='Flour', category_id=materials_cat.id, quantity=100.0, unit_id=kg_unit.id)
    sugar = StockItem(name='Sugar', category_id=materials_cat.id, quantity=50.0, unit_id=kg_unit.id)
    butter = StockItem(name='Butter', category_id=materials_cat.id, quantity=30.0, unit_id=kg_unit.id)
    
    test_db.add_all([flour, sugar, butter])
    test_db.commit()
    
    return {'flour': flour, 'sugar': sugar, 'butter': butter, 'unit': kg_unit, 'category': materials_cat}


class TestProductsRepository:
    """Test ProductsRepository methods."""
    
    def test_add_new_product(self, test_db: Session, setup_stock_items):
        """Test adding a new product."""
        repo = ProductsRepository(test_db)
        
        materials = [
            {'name': 'Flour', 'quantity': 500.0},
            {'name': 'Sugar', 'quantity': 200.0},
            {'name': 'Butter', 'quantity': 100.0}
        ]
        
        repo.add('Bread', 250, materials)
        
        product = repo.by_name('Bread')
        assert product is not None
        assert product.name == 'Bread'
        assert product.price == 250
    
    def test_add_product_with_invalid_material(self, test_db: Session, setup_stock_items):
        """Test adding product with non-existent material."""
        repo = ProductsRepository(test_db)
        
        materials = [
            {'name': 'NonExistentMaterial', 'quantity': 100.0}
        ]
        
        with pytest.raises(ValueError, match="Material 'NonExistentMaterial' not found"):
            repo.add('InvalidProduct', 100, materials)
    
    def test_update_product(self, test_db: Session, setup_stock_items):
        """Test updating an existing product."""
        repo = ProductsRepository(test_db)
        
        # Add initial product
        materials = [{'name': 'Flour', 'quantity': 400.0}]
        repo.add('Cake', 300, materials)
        
        # Update product
        new_materials = [
            {'name': 'Flour', 'quantity': 500.0},
            {'name': 'Sugar', 'quantity': 300.0}
        ]
        repo.add('Cake', 400, new_materials)
        
        product = repo.by_name('Cake')
        assert product.price == 400
        
        materials_list = repo.get_materials_for_product(product.id)
        assert len(materials_list) == 2
    
    def test_get_product_by_id(self, test_db: Session, setup_stock_items):
        """Test retrieving product by ID."""
        repo = ProductsRepository(test_db)
        
        materials = [{'name': 'Flour', 'quantity': 400.0}]
        repo.add('Donut', 50, materials)
        
        product = repo.by_name('Donut')
        assert product is not None
        
        retrieved = repo.by_id(product.id)
        assert retrieved is not None
        assert retrieved.name == 'Donut'
        assert retrieved.price == 50
    
    def test_get_materials_for_product(self, test_db: Session, setup_stock_items):
        """Test retrieving materials for a product."""
        repo = ProductsRepository(test_db)
        
        materials = [
            {'name': 'Flour', 'quantity': 400.0},
            {'name': 'Sugar', 'quantity': 150.0},
            {'name': 'Butter', 'quantity': 80.0}
        ]
        repo.add('Pastry', 150, materials)
        
        product = repo.by_name('Pastry')
        product_materials = repo.get_materials_for_product(product.id)
        
        assert len(product_materials) == 3
        assert any(m['name'] == 'Flour' and m['quantity'] == 400.0 for m in product_materials)
        assert any(m['name'] == 'Sugar' and m['quantity'] == 150.0 for m in product_materials)
        assert any(m['name'] == 'Butter' and m['quantity'] == 80.0 for m in product_materials)
    
    def test_delete_product(self, test_db: Session, setup_stock_items):
        """Test deleting a product."""
        repo = ProductsRepository(test_db)
        
        materials = [{'name': 'Flour', 'quantity': 400.0}]
        repo.add('TempProduct', 100, materials)
        
        product = repo.by_name('TempProduct')
        assert product is not None
        
        repo.delete('TempProduct')
        
        deleted = repo.by_name('TempProduct')
        assert deleted is None
    
    def test_get_all_products(self, test_db: Session, setup_stock_items):
        """Test retrieving all products."""
        repo = ProductsRepository(test_db)
        
        materials = [{'name': 'Flour', 'quantity': 400.0}]
        repo.add('Bread', 200, materials)
        repo.add('Cake', 300, materials)
        repo.add('Donut', 50, materials)
        
        all_products = repo.data()
        assert len(all_products) >= 3
        
        names = [p.name for p in all_products]
        assert 'Bread' in names
        assert 'Cake' in names
        assert 'Donut' in names


class TestProductsRouter:
    """Test products API router endpoints."""
    
    def test_get_products_empty(self, client, test_db: Session):
        """Test getting products when none exist."""
        response = client.get("/api/products/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_products_with_data(self, client, test_db: Session, setup_stock_items):
        """Test getting products list."""
        repo = ProductsRepository(test_db)
        materials = [{'name': 'Flour', 'quantity': 400.0}]
        repo.add('Bread', 200, materials)
        
        response = client.get("/api/products/")
        assert response.status_code == 200
        
        products = response.json()
        # Products should be returned as list
        assert isinstance(products, list)
    
    def test_get_products_with_search(self, client, test_db: Session, setup_stock_items):
        """Test searching products."""
        repo = ProductsRepository(test_db)
        materials = [{'name': 'Flour', 'quantity': 400.0}]
        repo.add('Bread', 200, materials)
        repo.add('Wheat Bread', 250, materials)
        repo.add('Cake', 300, materials)
        
        response = client.get("/api/products/?search=bread")
        assert response.status_code == 200
        
        products = response.json()
        # Should return products with 'bread' in the name
        for product in products:
            assert 'bread' in product['name'].lower()
    
    def test_get_new_product_form(self, client, test_db: Session, setup_stock_items):
        """Test getting new product form."""
        response = client.get("/api/products/new")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()
    
    def test_get_edit_product_form_existing(self, client, test_db: Session, setup_stock_items):
        """Test getting edit form for existing product."""
        repo = ProductsRepository(test_db)
        materials = [{'name': 'Flour', 'quantity': 400.0}]
        repo.add('Bread', 200, materials)
        
        product = repo.by_name('Bread')
        response = client.get(f"/api/products/{product.id}/edit")
        # Should return HTML response
        assert response.status_code in [200, 422]
    
    def test_get_edit_product_form_non_existing(self, client):
        """Test getting edit form for non-existent product."""
        response = client.get("/api/products/99999/edit")
        assert response.status_code == 404
