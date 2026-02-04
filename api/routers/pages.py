from fastapi import APIRouter, Request, Depends
from api.dependencies import get_model
from sql_model.model import SQLAlchemyModel
from fastapi.responses import HTMLResponse
from api.templates_config import templates

router = APIRouter(tags=["pages"])

@router.get("/")
async def read_landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})

@router.get("/management")
async def read_management(request: Request):
    return templates.TemplateResponse(request, "management.html", {})

@router.get("/pos")
async def read_pos(request: Request):
    return templates.TemplateResponse(request, "pos.html", {})

@router.get("/pos-mobile")
async def read_pos_mobile(request: Request):
    return templates.TemplateResponse(request, "pos_mob.html", {})

@router.get("/expenses")
async def read_expenses_entry(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    suppliers = model.suppliers().data()
    categories = model.utils().get_expense_category_names()
    types = model.expense_types().data()
    
    all_types = []
    for item in types:
        all_types.append({
            "id" : item.id,
            "name": item.name,
            "unit_id" : item.unit_id,
            "unit_name": model.utils().get_unit_name_by_id(item.unit_id),
            "category_id": item.category_id,
            "category_name": model.utils().get_expense_category_name_by_id(item.category_id),
            "default_price": item.default_price
        })
        
    return templates.TemplateResponse(request, "expenses_entry.html", {
        "suppliers": suppliers,
        "categories": categories,
        "types": all_types
    })
