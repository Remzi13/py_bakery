from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from api.dependencies import get_model
from api.models import Supplier
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_model=List[Supplier])
async def get_suppliers(
    request: Request,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    search: Optional[str] = Query(None),
    model: SQLiteModel = Depends(get_model)
):
    try:
        if search:
            suppliers = model.suppliers().search(search)
        else:
            suppliers = model.suppliers().data()
        
        if hx_request:
            if hx_target == "suppliers-table-body":
                 return templates.TemplateResponse(request, "suppliers/rows_only.html", {"suppliers": suppliers})
            return templates.TemplateResponse(request, "suppliers/list.html", {"suppliers": suppliers})

        return suppliers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new", response_class=HTMLResponse)
async def get_new_supplier_form(request: Request):
    return templates.TemplateResponse(request, "suppliers/form.html", {"supplier": None})

@router.get("/{supplier_id}/edit", response_class=HTMLResponse)
async def get_edit_supplier_form(supplier_id: int, request: Request, model: SQLiteModel = Depends(get_model)):
    supplier = model.suppliers().by_id(supplier_id)
    if not supplier:
         return HTMLResponse("Supplier not found", status_code=404)
    return templates.TemplateResponse(request, "suppliers/form.html", {"supplier": supplier})

@router.post("/", response_model=Supplier)
async def create_supplier(
    request: Request,
    supplier: Optional[Supplier] = None, # For JSON body
    model: SQLiteModel = Depends(get_model)
):
    try:
        # JSON Support
        if request.headers.get("content-type") == "application/json":
            if not supplier:
                raise HTTPException(status_code=400, detail="Invalid JSON body")
            return model.suppliers().add(supplier.name, supplier.contact_person, supplier.phone, supplier.email, supplier.address)

        # Form Support
        form = await request.form()
        name = form.get("name")
        contact_person = form.get("contact_person")
        phone = form.get("phone")
        email = form.get("email")
        address = form.get("address")
        
        new_supplier = model.suppliers().add(name, contact_person, phone, email, address)
        
        return templates.TemplateResponse(request, "suppliers/row.html", {"supplier": new_supplier})

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{supplier_id}", response_class=HTMLResponse)
async def update_supplier(
    supplier_id: int,
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        form = await request.form()
        name = form.get("name")
        contact_person = form.get("contact_person")
        phone = form.get("phone")
        email = form.get("email")
        address = form.get("address")

        updated_supplier = model.suppliers().update(supplier_id, name, contact_person, phone, email, address)
        return templates.TemplateResponse(request, "suppliers/row.html", {"supplier": updated_supplier})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, model: SQLiteModel = Depends(get_model)):
    try:
        model.suppliers().delete_by_id(supplier_id)
        return HTMLResponse("")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
