from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
from datetime import datetime
from api.dependencies import get_model
from api.models import (
    ExpenseType, ExpenseTypeCreate, 
    ExpenseCategoryCreate, ExpenseDocumentCreate, ExpenseDocumentResponse 
)
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/expenses", tags=["expenses"])
templates = Jinja2Templates(directory="templates")

# --- Documents API (New System) ---

@router.get("/documents", response_model=List[ExpenseDocumentResponse])
async def get_expense_documents(
    request: Request,
    search: Optional[str] = None,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    accept: Optional[str] = Header(None, alias="Accept"),
    model: SQLiteModel = Depends(get_model)
):
    try:
        docs = model.expense_documents().get_documents_with_details()
        
        # Filter if search
        if search:
            s = search.lower()
            docs = [d for d in docs if (d.supplier_name and s in d.supplier_name.lower()) or (d.comment and s in d.comment.lower())]

        if hx_request or (accept and "text/html" in accept):
            if hx_target == "expenses-table-body":
                 return templates.TemplateResponse(request, "expenses/rows_only.html", {"documents": docs})
            return templates.TemplateResponse(request, "expenses/list.html", {"documents": docs})

        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/new", response_class=HTMLResponse)
async def get_new_expense_document_form(request: Request, model: SQLiteModel = Depends(get_model)):
    suppliers = model.suppliers().data()
    categories = model.utils().get_expense_category_names()
    types = model.expense_types().data()
    current_date = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    return templates.TemplateResponse(request, "expenses/document_form.html", {
        "doc": None, 
        "suppliers": suppliers,
        "categories": categories,
        "types": types,
        "current_date": current_date
    })

@router.get("/documents/{id}", response_class=HTMLResponse)
async def get_expense_document_details(id: int, request: Request, model: SQLiteModel = Depends(get_model)):
    """Display expense document details in read-only view"""
    all_docs = model.expense_documents().get_documents_with_details()
    doc = next((d for d in all_docs if d['id'] == id), None)
    if not doc:
        return HTMLResponse("Document not found", status_code=404)
        
    items = model.expense_documents().get_document_items(id)

    return templates.TemplateResponse(request, "expenses/document_detail.html", {
        "doc": doc, 
        "items": items
    })

@router.post("/documents")
async def create_expense_document(
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        # JSON Support
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            doc = ExpenseDocumentCreate(**data)
            # Logic duplication from original... refactor later
            total_amount = 0
            items_data = []
            for item in doc.items:
                total_amount += item.quantity * item.price_per_unit
                items_data.append(item.dict())
            
            doc_id = model.expense_documents().add(
                date=doc.date,
                supplier_id=doc.supplier_id,
                total_amount=total_amount,
                comment=doc.comment,
                items=items_data
            )
            return {"message": "Expense document created successfully", "id": doc_id}

        # Form Support
        form = await request.form()
        date = form.get("date")
        supplier_id = int(form.get("supplier_id"))
        comment = form.get("comment")
        
        # Parsing items from form text/hidden fields is tricky with flat FormData
        # expected format: items[0][expense_type_id], items[0][quantity]...
        # FastAPI/Starlette doesn't parse nested objects automatically from FormData
        
        items_data = []
        total_amount = 0
        
        # Manual parsing or regex?
        # Let's iterate keys
        parsed_items = {}
        for key, value in form.items():
            if key.startswith("items["):
                # items[123123][field]
                parts = key.split("][")
                index = parts[0].replace("items[", "")
                field = parts[1].replace("]", "")
                
                if index not in parsed_items:
                    parsed_items[index] = {}
                parsed_items[index][field] = value
        
        for idx in parsed_items:
            item = parsed_items[idx]
            qty = float(item['quantity'])
            price = float(item['price_per_unit'])
            total_amount += qty * price
            
            items_data.append({
                "expense_type_id": int(item['expense_type_id']),
                "quantity": qty,
                "price_per_unit": price,
                "unit_id": int(item['unit_id'])
            })
            
        doc_id = model.expense_documents().add(
            date=date.replace("T", " "), # Fix format
            supplier_id=supplier_id,
            total_amount=total_amount,
            comment=comment,
            items=items_data
        )

        # Return the new row
        # We need the inserted doc object. 
        # get_documents_with_details() fetches all. Inefficient but safe.
        all_docs = model.expense_documents().get_documents_with_details()
        new_doc = next((d for d in all_docs if d['id'] == doc_id), None)
        
        return templates.TemplateResponse(request, "expenses/document_row.html", {"doc": new_doc})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{id}/items")
def get_expense_document_items(id: int, model: SQLiteModel = Depends(get_model)):
    try:
        items = model.expense_documents().get_document_items(id)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{id}")
async def delete_expense_document(id: int, model: SQLiteModel = Depends(get_model)):
    """Delete expense document and rollback stock changes"""
    try:
        model.expense_documents().delete(id)
        # Return empty response - HTMX will remove the row
        return HTMLResponse(content="", status_code=200)
    except ValueError as e:
        # Stock validation error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Categories & Types API ---

@router.get("/categories/new", response_class=HTMLResponse)
async def get_new_category_form(request: Request):
    return templates.TemplateResponse(request, "expenses/category_form.html", {})

@router.get("/types/new", response_class=HTMLResponse)
async def get_new_type_form(request: Request, model: SQLiteModel = Depends(get_model)):
    categories = model.utils().get_expense_category_names()
    return templates.TemplateResponse(request, "expenses/type_form.html", {"categories": categories})

@router.post("/categories")
async def create_expense_category(
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        if request.headers.get("content-type") == "application/json":
             data = await request.json()
             name = data.get("name")
        else:
             form = await request.form()
             name = form.get("name")

        cursor = model._conn.cursor()
        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (name,))
        model._conn.commit()
        
        # If HTMX request, we might want to return something else or empty to close modal, 
        # but the template has hx-on::after-request handling.
        return {"message": "Category created successfully"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/types")
async def create_expense_type(
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            type_data = ExpenseTypeCreate(**data)
            model.expense_types().add(
                name=type_data.name,
                default_price=type_data.default_price,
                category_name=type_data.category_name,
                stock=type_data.stock
            )
        else:
            form = await request.form()
            name = form.get("name")
            default_price = float(form.get("default_price"))
            category_name = form.get("category_name")
            stock = form.get("stock") == "true"
            
            model.expense_types().add(
                name=name,
                default_price=default_price,
                category_name=category_name,
                stock=stock
            )
            
        return {"message": "Expense type created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types/options", response_class=HTMLResponse)
async def get_expense_type_options(
    request: Request,
    category_filter: Optional[str] = None,
    model: SQLiteModel = Depends(get_model)
):
    """Return HTML options for expense types, optionally filtered by category"""
    try:
        data = model.expense_types().data()
        utils = model.utils()
        
        # Filter by category if specified
        if category_filter:
            filtered_data = []
            for et in data:
                cat_name = utils.get_expense_category_name_by_id(et.category_id)
                if cat_name == category_filter:
                    filtered_data.append(et)
            data = filtered_data
        
        # Build HTML options
        options_html = '<option value="" data-i18n="selectExpenseType">Select Expense Type...</option>\n'
        for et in data:
            options_html += f'<option value="{et.id}" data-price="{et.default_price}">{et.name}</option>\n'
        
        return HTMLResponse(content=options_html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types", response_model=List[ExpenseType])
def get_expense_types(model: SQLiteModel = Depends(get_model)):
    try:
        data = model.expense_types().data()
        results = []
        utils = model.utils()
        for et in data:
            cat_name = utils.get_expense_category_name_by_id(et.category_id)
            et_dict = et.__dict__.copy()
            et_dict['category_name'] = cat_name
            results.append(et_dict)
        return results
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=List[str])
def get_expense_categories(model: SQLiteModel = Depends(get_model)):
    try:
        return model.utils().get_expense_category_names()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
