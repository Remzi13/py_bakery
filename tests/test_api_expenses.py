def test_read_expenses_json(client):
    response = client.get("/api/expenses/documents")
    assert response.status_code == 200
    # Response model is list of ExpenseDocumentResponse
    # Might default to JSON for unknown accept
    # But router specifically checks helper params or assume JSON if not matched?
    # Actually my implementation returns 'docs' object directly if no hx_request/accept match.
    # FastAPI converts this object to JSON by default.
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert isinstance(data, list)

def test_read_expenses_htmx(client):
    response = client.get("/api/expenses/documents", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<table" in response.text

def test_get_new_expense_form(client):
    response = client.get("/api/expenses/documents/new")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<form" in response.text
    assert "items[" in response.text # Check for inline JS or structure

import uuid

def test_create_expense_document_json(client):
    uid = str(uuid.uuid4())[:8]
    # Setup - need a supplier
    supplier_payload = {
        "name": f"JSON Supplier {uid}", 
        "contact_person": "J", 
        "phone": "1", 
        "email": "j@e.com", 
        "address": "A"
    }
    s_res = client.post("/api/suppliers/", json=supplier_payload)
    assert s_res.status_code == 200, f"Supplier creation failed: {s_res.text}"
    supplier_id = s_res.json()["id"]

    # Need expense type
    # First Category
    client.post("/api/expenses/categories", json={"name": f"JSON Cat {uid}"})
    # Expense Type
    type_payload = {
        "name": f"JSON Type {uid}",
        "default_price": 10.0,
        "category_name": f"JSON Cat {uid}",
        "stock": False
    }
    t_res = client.post("/api/expenses/types", json=type_payload)
    # create_expense_type returns message, we need ID...
    # get types to find ID
    types = client.get("/api/expenses/types").json()
    type_id = next(t["id"] for t in types if t["name"] == f"JSON Type {uid}")

    # Create Document
    doc_payload = {
        "date": "2023-01-01 10:00",
        "supplier_id": supplier_id,
        "comment": "JSON Doc",
        "items": [
            {
                "expense_type_id": type_id,
                "quantity": 5.0,
                "price": 10.0,
                "unit_id": 1
            }
        ]
    }
    response = client.post("/api/expenses/documents", json=doc_payload)
    assert response.status_code == 200, f"Doc creation failed: {response.text}"
    assert "success" in response.json()["message"]

def test_create_expense_document_form(client):
    uid = str(uuid.uuid4())[:8]
    # Create Supplier
    s_res = client.post("/api/suppliers/", json={
        "name": f"HTML Supplier {uid}",
        "contact_person": None,
        "phone": None,
        "email": None,
        "address": None
    })
    assert s_res.status_code == 200, f"Supplier creation failed: {s_res.text}"
    supplier_id = s_res.json()["id"]
    
    # Create Category & Type
    client.post("/api/expenses/categories", json={"name": f"HTML Cat {uid}"})
    client.post("/api/expenses/types", json={
        "name": f"HTML Type {uid}",
        "default_price": 20.0,
        "category_name": f"HTML Cat {uid}",
        "stock": False
    })
    types = client.get("/api/expenses/types").json()
    type_id = next(t["id"] for t in types if t["name"] == f"HTML Type {uid}")

    # Create Document via Form
    form_data = {
        "date": "2023-01-02T12:00",
        "supplier_id": str(supplier_id),
        "comment": "HTML Doc",
        # Nested items simulation
        "items[1][expense_type_id]": str(type_id),
        "items[1][quantity]": "2.0",
        "items[1][unit_id]": "1",
        "items[1][price]": "20.0"
    }
    response = client.post("/api/expenses/documents", data=form_data)
    assert response.status_code == 200, f"Form Doc creation failed: {response.text}"
    assert "text/html" in response.headers["content-type"]
    assert f"HTML Supplier {uid}" in response.text # Row returned with supplier name
    assert "<tr" in response.text

def test_category_and_type_forms(client):
    # Test Forms GET
    r_cat = client.get("/api/expenses/categories/new")
    assert r_cat.status_code == 200
    assert "<form" in r_cat.text
    
    r_type = client.get("/api/expenses/types/new")
    assert r_type.status_code == 200
    assert "<form" in r_type.text
    
    # Test POST Form Data
    uid = str(uuid.uuid4())[:8]
    cat_name = f"FormCat {uid}"
    
    # Add Category via form
    client.post("/api/expenses/categories", data={"name": cat_name})
    
    # Add Type via form
    type_data = {
        "name": f"FormType {uid}",
        "default_price": "15.0",
        "category_name": cat_name,
        "stock": "true"
    }
    r_post_type = client.post("/api/expenses/types", data=type_data)
    assert r_post_type.status_code == 200
    assert "Type added" in r_post_type.text or "successfully" in r_post_type.json()["message"]

