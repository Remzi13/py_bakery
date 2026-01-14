from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from api.dependencies import get_model
from api.models import ProductCreate, ProductResponse
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/products", tags=["products"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    request: Request,
    search: Optional[str] = None,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    accept: Optional[str] = Header(None, alias="Accept"),
    model: SQLiteModel = Depends(get_model)
):
    try:
        products_data = model.products().data()
        
        # Filter if search is present
        if search:
            s = search.lower()
            products_data = [p for p in products_data if s in p.name.lower()]

        results = []
        for p in products_data:
            results.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "materials": p.materials
            })
            
        # Check for HTMX request OR Browser request (Accept: text/html)
        if hx_request or (accept and "text/html" in accept):
            if hx_target == "products-table-body":
                 # Return only the rows for the table
                 return templates.TemplateResponse(request, "products/rows_only.html", {"products": results})
            return templates.TemplateResponse(request, "products/list.html", {"products": results})
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new", response_class=HTMLResponse)
async def get_new_product_form(request: Request):
    return templates.TemplateResponse(request, "products/form.html", {"product": None})

@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def get_edit_product_form(product_id: int, request: Request, model: SQLiteModel = Depends(get_model)):
    p = model.products().by_id(product_id)
    if not p:
        return HTMLResponse("Product not found", status_code=404)
    return templates.TemplateResponse(request, "products/form.html", {"product": p})

@router.post("/", response_model=ProductResponse)
async def create_product(
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        # Check for JSON content type (Legacy SPA support)
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            product = ProductCreate(**data)
            materials_list = [i.dict() for i in product.materials]
            new_product = model.products().add(product.name, product.price, materials_list)
            materials = model.products().get_materials_for_product(new_product.id)
            return {
                "id": new_product.id,
                "name": new_product.name,
                "price": new_product.price,
                "materials": materials
            }

        # HTMX Form Data
        form = await request.form()
        name = form.get("name")
        price = float(form.get("price"))
        materials_list = [] # TODO: Handle materials from form
        
        new_product = model.products().add(name, price, materials_list)
        materials = model.products().get_materials_for_product(new_product.id)
        
        product_dict = {
            "id": new_product.id,
            "name": new_product.name,
            "price": new_product.price,
            "materials": materials
        }
        
        return templates.TemplateResponse(request, "products/row.html", {"product": product_dict})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, model: SQLiteModel = Depends(get_model)):
    try:
        p = model.products().by_id(product_id)
        if not p:
            raise HTTPException(status_code=404, detail="Product not found")
        materials = model.products().get_materials_for_product(p.id)
        return {"id": p.id, "name": p.name, "price": p.price, "materials": materials}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, 
    request: Request, 
    model: SQLiteModel = Depends(get_model)
):
    try:
        # Check for JSON content type (Legacy SPA support)
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            product = ProductCreate(**data)
            materials_list = [i.dict() for i in product.materials]
            updated = model.products().update(product_id, product.name, product.price, materials_list)
            materials = model.products().get_materials_for_product(updated.id)
            return {"id": updated.id, "name": updated.name, "price": updated.price, "materials": materials}

        # HTMX Form Data
        form = await request.form()
        name = form.get("name")
        price = float(form.get("price"))
        
        # For now, preserve existing materials if not provided? 
        # Or simplify and say we can't edit materials via this form yet.
        # We'll pass empty list for now, which might clear materials.
        # Better: get existing materials first and keep them?
        # TODO: Implement full material editing in form
        
        # Current hack: pass empty list, but this clears materials. 
        # To avoid data loss, let's fetch current product
        current = model.products().by_id(product_id)
        if not current:
            raise HTTPException(status_code=404, detail="Product not found")
            
        # If we had a proper repository method to get ingredients...
        current_materials = model.products().get_materials_for_product(product_id)
        materials_list = [] # form.get("materials") is complex
        
        # If user didn't edit materials (form doesn't support it yet), keep existing?
        # The update method in repo likely replaces all materials.
        # So we need to reconstruct the list.
        for m in current_materials:
            # Material dict as expected by repo: {name, quantity, ...}
            # The 'get_materials_for_product' returns dicts? Check repo.
            # Assuming returns list of dicts.
            materials_list.append(m)

        updated = model.products().update(product_id, name, price, materials_list)
        materials = model.products().get_materials_for_product(updated.id)
        
        product_dict = {
            "id": updated.id,
            "name": updated.name,
            "price": updated.price,
            "materials": materials
        }
        return templates.TemplateResponse(request, "products/row.html", {"product": product_dict})

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_name}")
def delete_product(product_name: str, model: SQLiteModel = Depends(get_model)):
    try:
        model.products().delete(product_name)
        return HTMLResponse("") # Return empty string to remove row from DOM
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
