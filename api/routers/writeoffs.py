from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel
from api.dependencies import get_model
from sql_model.model import SQLAlchemyModel
from sql_model.entities import WriteOff

router = APIRouter(prefix="/api/writeoffs", tags=["writeoffs"])
from api.templates_config import templates

class WriteOffCreate(BaseModel):
    item_id: int
    item_type: str # 'product' or 'stock'
    quantity: float
    reason: str

class WriteOffRead(BaseModel):
    id: int
    product_id: Optional[int] = None
    stock_item_id: Optional[int] = None
    item_name: Optional[str] = None # Added for UI convenience
    quantity: float
    reason: str
    unit_id: Optional[int] = None
    date: str

@router.get("/", response_model=List[WriteOffRead])
async def get_writeoffs(
    request: Request,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    accept: Optional[str] = Header(None, alias="Accept"),
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        data = model.writeoffs().data()
        results = []
        for wo in data:
            item_name = "Unknown"
            if wo.product_id:
                p = model.products().by_id(wo.product_id)
                item_name = p.name if p else f"Product #{wo.product_id}"
            elif wo.stock_item_id:
                si = model.stock().by_id(wo.stock_item_id)
                item_name = si.name if si else f"Stock Item #{wo.stock_item_id}"
            
            wo_dict = wo.__dict__.copy()
            wo_dict['item_name'] = item_name
            results.append(wo_dict)
        
        if hx_request or (accept and "text/html" in accept):
            return templates.TemplateResponse(request, "writeoffs/list.html", {"writeoffs": results})
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new", response_class=HTMLResponse)
async def get_new_writeoff_form(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    categories = model.utils().get_stock_category_names()
    return templates.TemplateResponse(request, "writeoffs/form.html", {"categories": categories})

@router.post("/", response_model=WriteOffRead)
async def add_writeoff(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        # JSON Support
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            item_id = int(data.get("item_id"))
            item_type = data.get("item_type")
            quantity = float(data.get("quantity"))
            reason = data.get("reason")
        else:
            form = await request.form()
            item_id = int(form.get("item_id"))
            item_type = form.get("item_type")
            quantity = float(form.get("quantity"))
            reason = form.get("reason")

        model.writeoffs().add(
            item_id=item_id,
            item_type=item_type,
            quantity=quantity,
            reason=reason
        )
        
        # Get the item name for UI enrichment
        item_name = "Unknown"
        if item_type == 'product':
            p = model.products().by_id(item_id)
            item_name = p.name if p else f"Product #{item_id}"
        else:
            si = model.stock().by_id(item_id)
            item_name = si.name if si else f"Stock Item #{item_id}"
        
        # Get the latest record
        all_wo = model.writeoffs().data()
        latest = all_wo[0]
        
        # Enrich for template
        latest_dict = latest.__dict__.copy()
        latest_dict['item_name'] = item_name
        
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(request, "writeoffs/row.html", {"wo": latest_dict})
            
        return latest_dict
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{writeoff_id}")
async def delete_writeoff(writeoff_id: int, model: SQLAlchemyModel = Depends(get_model)):
    try:
        model.writeoffs().delete(writeoff_id)
        return HTMLResponse("")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
