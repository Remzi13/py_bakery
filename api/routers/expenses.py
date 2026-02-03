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
from sql_model.model import SQLAlchemyModel

router = APIRouter(prefix="/api/expenses", tags=["expenses"])
from api.templates_config import templates

# --- Documents API (New System) ---


@router.get("/documents", response_model=List[ExpenseDocumentResponse])
async def get_expense_documents(
    request: Request,
    search: Optional[str] = None,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    accept: Optional[str] = Header(None, alias="Accept"),
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        docs = model.expense_documents().get_documents_with_details()
        
        # Filter if search
        if search:
            s = search.lower()
            docs = [d for d in docs if (d['supplier_name'] and s in d['supplier_name'].lower()) or (d['comment'] and s in d['comment'].lower())]

        if hx_request or (accept and "text/html" in accept):
            if hx_target == "expenses-table-body":
                 return templates.TemplateResponse(request, "expenses/rows_only.html", {"documents": docs})
            return templates.TemplateResponse(request, "expenses/list.html", {"documents": docs})

        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/new", response_class=HTMLResponse)
async def get_new_expense_document_form(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    suppliers = model.suppliers().data()
    categories = model.utils().get_expense_category_names()
    types = model.expense_types().data()
    current_date = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    all_types = []
    for item in types:
        all_types.append({
            "id" : item.id,
            "name": item.name,
            "unit_id" : item.unit_id,
            "unit_name": model.utils().get_unit_name_by_id(item.unit_id)
        })
    
    return templates.TemplateResponse(request, "expenses/document_form.html", {
        "doc": None, 
        "suppliers": suppliers,
        "categories": categories,
        "types": all_types,
        "current_date": current_date
    })

@router.get("/documents/{id}", response_class=HTMLResponse)
async def get_expense_document_details(id: int, request: Request, model: SQLAlchemyModel = Depends(get_model)):
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
    model: SQLAlchemyModel = Depends(get_model)
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
                total_amount += item.price
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
            price = float(item['price'])
            total_amount += price
            
            items_data.append({
                "expense_type_id": int(item['expense_type_id']),
                "quantity": qty,
                "price": price,
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
        
        response = templates.TemplateResponse(request, "expenses/document_row.html", {"doc": new_doc, "hx_oob_swap": "beforeend:#expenses-table-body"})
        response.headers["HX-Trigger"] = "dashboard-update"
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{id}/items")
def get_expense_document_items(id: int, model: SQLAlchemyModel = Depends(get_model)):
    try:
        items = model.expense_documents().get_document_items(id)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{id}")
async def delete_expense_document(id: int, model: SQLAlchemyModel = Depends(get_model)):
    """Delete expense document and rollback stock changes"""
    try:
        model.expense_documents().delete(id)
        # Return empty response - HTMX will remove the row
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Trigger"] = "dashboard-update"
        return response
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
async def get_new_type_form(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    categories = model.utils().get_expense_category_names()
    units = model.utils().get_units()
    return templates.TemplateResponse(request, "expenses/type_form.html", {"categories": categories, "units": units})

@router.get("/types/{id}/edit", response_class=HTMLResponse)
async def get_edit_type_form(id: int, request: Request, model: SQLAlchemyModel = Depends(get_model)):
    et = model.expense_types().by_id(id)
    if not et:
        raise HTTPException(status_code=404, detail="Expense type not found")
    
    categories = model.utils().get_expense_category_names()
    units = model.utils().get_units()
    
    type_data = {
        "id": et.id,
        "name": et.name,
        "default_price": et.default_price,
        "category_id": et.category_id,
        "category_name": model.utils().get_expense_category_name_by_id(et.category_id),
        "unit_id": et.unit_id,
        "stock": et.stock
    }
    
    return templates.TemplateResponse(request, "expenses/type_edit_form.html", {
        "type": type_data, 
        "categories": categories, 
        "units": units
    })

@router.post("/categories")
async def create_expense_category(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        if request.headers.get("content-type") == "application/json":
             data = await request.json()
             name = data.get("name")
        else:
             form = await request.form()
             name = form.get("name")

        from sql_model.entities import ExpenseCategory
        new_cat = ExpenseCategory(name=name)
        model.db.add(new_cat)
        model.db.commit()
        
        return {"message": "Category created successfully"}
    except Exception as e:
         model.db.rollback()
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/types")
async def create_expense_type(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            type_data = ExpenseTypeCreate(**data)
            name = type_data.name
            default_price = type_data.default_price
            category_name = type_data.category_name
            unit_id = type_data.unit_id
            stock = type_data.stock
        else:
            form = await request.form()
            name = form.get("name")
            default_price = float(form.get("default_price"))
            category_name = form.get("category_name")
            unit_id = int(form.get("unit_id"))
            stock = form.get("stock") == "true"

        new_type_id = model.expense_types().add(
            name=name,
            default_price=default_price,
            category_name=category_name,
            unit_id=unit_id,
            stock=stock
        )
        
        if request.headers.get("HX-Request"):
            et = model.expense_types().by_id(new_type_id)
            type_data_dict = {
                "id": et.id,
                "name": et.name,
                "default_price": et.default_price,
                "category_id": et.category_id,
                "category_name": model.utils().get_expense_category_name_by_id(et.category_id),
                "unit_id": et.unit_id,
                "unit_name": model.utils().get_unit_name_by_id(et.unit_id),
                "stock": et.stock
            }
            return templates.TemplateResponse(request, "expenses/type_row.html", {"type": type_data_dict})
            
        return {"message": "Expense type created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types/options", response_class=HTMLResponse)
async def get_expense_type_options(
    request: Request,
    category_filter: Optional[str] = None,
    model: SQLAlchemyModel = Depends(get_model)
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
            options_html += f'<option value="{et.id}" data-price="{et.default_price}" data-unit-id="{et.unit_id}" >{et.name}</option>\n'
        
        return HTMLResponse(content=options_html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types", response_model=List[ExpenseType])
def get_expense_types(
    request: Request, 
    search: Optional[str] = None,
    category: Optional[str] = None,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    accept: Optional[str] = Header(None, alias="Accept"),
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        data = model.expense_types().data()
        results = []
        utils = model.utils()
        for et in data:
            cat_name = utils.get_expense_category_name_by_id(et.category_id)
            results.append({
                "id": et.id,
                "name": et.name,
                "default_price": et.default_price,
                "category_id": et.category_id,
                "category_name": cat_name,
                "unit_id": et.unit_id,
                "unit_name": utils.get_unit_name_by_id(et.unit_id),
                "stock": et.stock
            })
        
        if category and category != "":
            results = [r for r in results if r['category_name'] == category]

        if search:
            s = search.lower()
            results = [r for r in results if s in r['name'].lower()]

        if hx_request or (accept and "text/html" in accept):
            if hx_target == "types-table-body":
                return templates.TemplateResponse(request, "expenses/types_table_rows.html", {"types": results})
            
            categories = utils.get_expense_category_names()
            return templates.TemplateResponse(request, "expenses/types_list.html", {
                "types": results,
                "categories": categories,
                "selected_category": category
            })
            
        return results
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.put("/types/{id}", response_class=HTMLResponse)
async def update_expense_type(
    id: int,
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        form = await request.form()
        name = form.get("name")
        default_price = float(form.get("default_price"))
        category_name = form.get("category_name")
        unit_id = int(form.get("unit_id"))
        stock = form.get("stock") == "true"
        
        updated_et = model.expense_types().full_update(
            type_id=id,
            name=name,
            default_price=default_price,
            category_name=category_name,
            unit_id=unit_id,
            stock=stock
        )
        
        if not updated_et:
            raise HTTPException(status_code=404, detail="Expense type not found")
            
        type_data = {
            "id": updated_et.id,
            "name": updated_et.name,
            "default_price": updated_et.default_price,
            "category_id": updated_et.category_id,
            "category_name": model.utils().get_expense_category_name_by_id(updated_et.category_id),
            "unit_id": updated_et.unit_id,
            "unit_name": model.utils().get_unit_name_by_id(updated_et.unit_id),
            "stock": updated_et.stock
        }
        
        return templates.TemplateResponse(request, "expenses/type_row.html", {"type": type_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/types/{id}", response_class=HTMLResponse)
async def delete_expense_type(
    id: int,
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        model.expense_types().delete_by_id(id)
        return HTMLResponse(content="", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=List[str])
def get_expense_categories(model: SQLAlchemyModel = Depends(get_model)):
    try:
        return model.utils().get_expense_category_names()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


