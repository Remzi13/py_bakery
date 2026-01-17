
def test_read_products_json(client):
    response = client.get("/api/products/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert isinstance(data, list)

def test_read_products_htmx(client):
    response = client.get("/api/products/", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<table" in response.text # Should contain table from list.html

def test_read_products_htmx_row_only(client):
    response = client.get("/api/products/", headers={"HX-Request": "true", "HX-Target": "products-table-body"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<thead>" not in response.text # Should not contain table header

def test_read_products_browser(client):
    response = client.get("/api/products/", headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text # Should render full page (base.html)
    assert "<table" in response.text
    # It might be empty if no products, but shouldn't be full page

def test_get_new_product_form(client):
    response = client.get("/api/products/new")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<form" in response.text

def test_create_product_json(client):
    # Setup: ensure materials exist if validated?
    # The current create_product allows blank materials?
    
    payload = {
        "name": "JSON Product",
        "price": 10.5,
        "materials": []
    }
    response = client.post("/api/products/", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "JSON Product"
    
    # Cleanup
    client.delete(f"/api/products/JSON Product")

def test_create_product_form(client):
    form_data = {
        "name": "HTML Product",
        "price": "20.0"
    }
    response = client.post("/api/products/", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "HTML Product" in response.text
    assert "<tr" in response.text
    
    # Cleanup
    client.delete(f"/api/products/HTML Product")
