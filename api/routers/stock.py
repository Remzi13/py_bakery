from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from api.dependencies import get_model
from api.models import StockItem, StockCreate, StockUpdate, StockSet
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/stock", tags=["stock"])
templates = Jinja2Templates(directory="templates")

@router.get("/categories", response_model=List[str])
def get_categories(model: SQLiteModel = Depends(get_model)):
    try:
        return model.utils().get_stock_category_names()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/materials", response_model=List[StockItem])
def get_materials(model: SQLiteModel = Depends(get_model)):
    try:
        items = model.stock().data()
        results = []
        utils = model.utils()
        for item in items:
            cat_name = utils.get_stock_category_name_by_id(item.category_id)
            unit_name = utils.get_unit_name_by_id(item.unit_id)

            # Using dict mapping to fill Pydantic model
            item_dict = item.__dict__.copy()
            item_dict['category_name'] = cat_name
            item_dict['unit_name'] = unit_name
            results.append(item_dict)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[StockItem])
async def get_stock(
    request: Request,
    search: Optional[str] = None,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    accept: Optional[str] = Header(None, alias="Accept"),
    model: SQLiteModel = Depends(get_model)
):
    try:
        items = model.stock().data()
        results = []
        
        # Filter if search
        if search:
            s = search.lower()
            items = [i for i in items if s in i.name.lower()]

        utils = model.utils()
        for item in items:
            cat_name = utils.get_stock_category_name_by_id(item.category_id)
            unit_name = utils.get_unit_name_by_id(item.unit_id)
            
            # Using dict mapping to fill Pydantic model
            item_dict = item.__dict__.copy()
            item_dict['category_name'] = cat_name
            item_dict['unit_name'] = unit_name
            results.append(item_dict)
            
        if hx_request or (accept and "text/html" in accept):
            if hx_target == "stock-table-body":
                 return templates.TemplateResponse(request, "stock/rows_only.html", {"stock": results})
            return templates.TemplateResponse(request, "stock/list.html", {"stock": results})

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new", response_class=HTMLResponse)
async def get_new_stock_form(request: Request, model: SQLiteModel = Depends(get_model)):
    categories = model.utils().get_stock_category_names()
    return templates.TemplateResponse(request, "stock/form.html", {"item": None, "categories": categories})

@router.get("/{stock_id}/edit", response_class=HTMLResponse)
async def get_edit_stock_form(stock_id: int, request: Request, model: SQLiteModel = Depends(get_model)):
    p = model.stock().by_id(stock_id)
    if not p:
         return HTMLResponse("Stock item not found", status_code=404)
    
    cat_name = model.utils().get_stock_category_name_by_id(p.category_id)
    unit_name = model.utils().get_unit_name_by_id(p.unit_id)
    
    item_dict = p.__dict__.copy()
    item_dict['category_name'] = cat_name
    item_dict['unit_name'] = unit_name

    categories = model.utils().get_stock_category_names()

    return templates.TemplateResponse(request, "stock/form.html", {"item": item_dict, "categories": categories})


@router.get("/{stock_id}", response_model=StockItem)
def get_stock_id(stock_id: int, model: SQLiteModel = Depends(get_model)):
    try:
        p = model.stock().by_id(stock_id)
        if not p:
            raise HTTPException(status_code=404, detail="Stock not found")

        return {
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
            "category_name": model.utils().get_stock_category_name_by_id(p.category_id),
            "quantity": p.quantity,
            "unit_name": model.utils().get_unit_name_by_id(p.unit_id),
            "unit_id": p.unit_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=StockItem)
async def add_stock(
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        # JSON Support
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            item = StockCreate(**data)
            model.stock().add(item.name, item.category_name, item.quantity, item.unit_name)
            return model.stock().get(item.name)

        # Form Support
        form = await request.form()
        name = form.get("name")
        category_name = form.get("category_name")
        quantity = float(form.get("quantity"))
        unit_name = form.get("unit_name")
        
        model.stock().add(name, category_name, quantity, unit_name)
        new_item = model.stock().get(name)

        # Enrich with names for template
        item_dict = new_item.__dict__.copy()
        item_dict['category_name'] = category_name
        item_dict['unit_name'] = unit_name
        
        return templates.TemplateResponse(request, "stock/row.html", {"item": item_dict})

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{name}/delta")
def update_stock_quantity(name: str, update: StockUpdate, model: SQLiteModel = Depends(get_model)):
    try:
        model.stock().update(name, update.quantity_delta)
        return model.stock().get(name)
    except KeyError as e:
         raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{name}/set")
async def set_stock_quantity(
    name: str, 
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        # JSON Support
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            update = StockSet(**data)
            model.stock().set(name, update.quantity)
            return model.stock().get(name)

        # Form Support
        form = await request.form()
        quantity = float(form.get("quantity"))
        
        model.stock().set(name, quantity)
        updated = model.stock().get(name)
        
        # We need category and unit names for the row template
        # Ideally repo.get() returns them or we fetch them
        # repo.get() returns StockItem Entity which has ids.
        
        cat_name = model.utils().get_stock_category_name_by_id(updated.category_id)
        unit_name = model.utils().get_unit_name_by_id(updated.unit_id)
        
        item_dict = updated.__dict__.copy()
        item_dict['category_name'] = cat_name
        item_dict['unit_name'] = unit_name

        return templates.TemplateResponse(request, "stock/row.html", {"item": item_dict})

    except KeyError as e:
         raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{name}")
def delete_stock(name: str, model: SQLiteModel = Depends(get_model)):
    try:
        model.stock().delete(name)
        return HTMLResponse("") # Remove row
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

