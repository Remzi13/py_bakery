from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from api.dependencies import get_model
from api.models import Sale, SaleCreate
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/sales", tags=["sales"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_model=List[Sale])
async def get_sales(
    request: Request,
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    search: Optional[str] = Query(None),
    model: SQLiteModel = Depends(get_model)
):
    try:
        if search:
            sales = model.sales().search(search)
        else:
            sales = model.sales().data()
        
        if hx_request:
            if hx_target == "sales-table-body":
                 return templates.TemplateResponse(request, "sales/rows_only.html", {"sales": sales})
            return templates.TemplateResponse(request, "sales/list.html", {"sales": sales})

        return sales
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new", response_class=HTMLResponse)
async def get_new_sale_form(request: Request, model: SQLiteModel = Depends(get_model)):
    products = model.products().data()
    return templates.TemplateResponse(request, "sales/form.html", {"products": products})

@router.post("/")
async def create_sale(
    request: Request,
    model: SQLiteModel = Depends(get_model)
):
    try:
        # Check if it's a JSON request (backward compatibility) or Form request (HTMX)
        if request.headers.get("content-type") == "application/json":
            body = await request.json()
            product_id = body.get("product_id")
            quantity = body.get("quantity")
            discount = body.get("discount", 0)
        else:
            form = await request.form()
            product_id = int(form.get("product_id"))
            quantity = float(form.get("quantity"))
            discount = int(form.get("discount", 0))

        product = model.products().by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        model.sales().add(product.name, product.price, quantity, discount)
        
        # Get the latest sale back for the row template
        new_sale = model.sales().data()[0] 
        
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(request, "sales/row.html", {"sale": new_sale})
            
        return {"message": "Sale created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log error in real app
        raise HTTPException(status_code=500, detail=str(e))
