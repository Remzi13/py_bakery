from fastapi.testclient import TestClient
from main import app
import urllib.parse

client = TestClient(app)

def test_read_stock_json():
    response = client.get("/api/stock/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert isinstance(data, list)

def test_read_stock_htmx():
    response = client.get("/api/stock/", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<table" in response.text 

def test_read_stock_browser():
    response = client.get("/api/stock/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text
    assert "<table" in response.text

def test_get_new_stock_form():
    response = client.get("/api/stock/new")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<form" in response.text

def test_create_stock_item_json():
    # Setup
    item_name = "JSON Stock Item"
    
    payload = {
        "name": item_name,
        "category_name": "Materials",
        "quantity": 10.0,
        "unit_name": "kg"
    }
    response = client.post("/api/stock/", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == item_name
    
    # Cleanup
    client.delete(f"/api/stock/{item_name}")

def test_create_stock_item_form():
    item_name = "HTML Stock Item"
    form_data = {
        "name": item_name,
        "category_name": "Materials",
        "quantity": "5.5",
        "unit_name": "l"
    }
    response = client.post("/api/stock/", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert item_name in response.text
    assert "<tr" in response.text
    
    # Cleanup
    client.delete(f"/api/stock/{item_name}")

def test_update_stock_quantity_set_form():
    # Setup
    item_name = "Update Stock Item"
    payload = {
        "name": item_name,
        "category_name": "Materials",
        "quantity": 10.0,
        "unit_name": "kg"
    }
    client.post("/api/stock/", json=payload)
    
    # Update via Form
    encoded_name = urllib.parse.quote(item_name) # Ensure URL safe
    form_data = {
        "quantity": "15.5"
    }
    response = client.put(f"/api/stock/{item_name}/set", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "15.5" in response.text # Should see new quantity in row
    
    # Cleanup
    client.delete(f"/api/stock/{item_name}")
