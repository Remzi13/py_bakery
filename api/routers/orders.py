from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from api.dependencies import get_model
from api.models import OrderCreate, OrderResponse, OrderItemResponse
from sql_model.model import SQLAlchemyModel

router = APIRouter(prefix="/api/orders", tags=["orders"])
from api.utils import get_resource_path
templates = Jinja2Templates(directory=get_resource_path("templates"))

@router.get("/", response_model=List[OrderResponse])
def get_orders(
    request: Request,
    search: Optional[str] = None,
    format: Optional[str] = None, 
    hx_request: Optional[str] = Header(None, alias="HX-Request"),
    hx_target: Optional[str] = Header(None, alias="HX-Target"),
    accept: Optional[str] = Header(None, alias="Accept"),
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        orders_data = model.orders().data()
       

        if search:
            s = search.lower()
            orders_data = [o for o in orders_data if s in str(o.id) or (o.additional_info and s in o.additional_info.lower())]

        orders_data.sort(key=lambda x: x.status, reverse=True)

        if format == "options":
            options = ""
            for o in orders_data:
                info = o.additional_info[:20] + "..." if o.additional_info else "No info"
                options += f'<option value="{o.id}">Order #{o.id} ({info})</option>'
            return HTMLResponse(content=options)

        results = []
        for order in orders_data:
            items_list = list(order.items) if order.items else []
            results.append({
                "id": order.id,
                "created_date": order.created_date,
                "completion_date": order.completion_date,
                "status": order.status,
                "additional_info": order.additional_info,
                "order_items": items_list
            })
        
        if hx_request or (accept and "text/html" in accept):
            if hx_target == "orders-table-body":
                return templates.TemplateResponse(request, "orders/rows.html", {"orders": results})
            
            if not hx_request and accept and "text/html" in accept:
                content = templates.get_template("orders/list.html").render({"request": request, "orders": results})
                return HTMLResponse(f"<!DOCTYPE html><html><body>{content}</body></html>")
                
            return templates.TemplateResponse(request, "orders/list.html", {"orders": results})
               
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new", response_class=HTMLResponse)
def get_new_order_form(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    try:
        products_data = model.products().data()
        
        products = []
        for p in products_data:
            products.append({
                "id": p.id,
                "name": p.name,
                "price": p.price
            })
        
        return templates.TemplateResponse(request, "orders/form.html", {
            "request": request,
            "products": products,
            "currency": "₽"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        
@router.get("/pending", response_model=List[OrderResponse])
def get_pending_orders(model: SQLAlchemyModel = Depends(get_model)):
    try:
        orders_data = model.orders().get_pending()
        results = []
        for order in orders_data:
            results.append({
                "id": order.id,
                "created_date": order.created_date,
                "completion_date": order.completion_date,
                "status": order.status,
                "additional_info": order.additional_info,
                "order_items": order.items
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, model: SQLAlchemyModel = Depends(get_model)):
    try:
        order = model.orders().by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "id": order.id,
            "created_date": order.created_date,
            "completion_date": order.completion_date,
            "status": order.status,
            "additional_info": order.additional_info,
            "items": order.items
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=OrderResponse)
async def create_order(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        # JSON Support
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
            order_data = OrderCreate(**data)
            items = [{"product_id": item.product_id, "quantity": item.quantity} for item in order_data.items]
            completion_date = order_data.completion_date
            additional_info = order_data.additional_info
            complete_now = order_data.complete_now
        else:            
            
            form = await request.form()
            products_list = []
            parsed_products = {}
            for key, value in form.items():
                if key.startswith("items["):
                    parts = key.split("][")
                    index = parts[0].replace("items[", "")
                    field = parts[1].replace("]", "")
                    if index not in parsed_products:
                        parsed_products[index] = {}
                    parsed_products[index][field] = value
            
            for idx in sorted(parsed_products.keys()):
                m = parsed_products[idx]
                products_list.append({
                    "product_id" : m["product_id"],
                    "quantity" : m["quantity"]
                })                
                

            items = products_list
            completion_date = form.get("completion_date")
            additional_info = form.get("additional_info")
            complete_now = form.get("complete_now") == "true"

        new_order = model.orders().add(
            items=items,
            completion_date=completion_date,
            additional_info=additional_info,
            complete_now=complete_now
        )
        
        # Get full order with items
        full_order = model.orders().by_id(new_order.id)
        
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(request, "orders/row.html", {"order": full_order, "hx_oob_swap": "afterbegin:#orders-table-body"})

        return {
            "id": full_order.id,
            "created_date": full_order.created_date,
            "completion_date": full_order.completion_date,
            "status": full_order.status,
            "additional_info": full_order.additional_info,
            "items": full_order.items
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/complete")
async def complete_order(
    request: Request,
    order_id: int, 
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        success = model.orders().complete(order_id)
        if success:
            if request.headers.get("HX-Request"):
                order = model.orders().by_id(order_id)
                return templates.TemplateResponse(request, "orders/row.html", {"order": order})
            return {"message": f"Order {order_id} completed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to complete order")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/info", response_class=HTMLResponse)
def get_order_info(request: Request, order_id: int, model: SQLAlchemyModel = Depends(get_model)):
    try:
        order = model.orders().by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return templates.TemplateResponse(request, "orders/info.html", {
            "order": order,
            "currency": "₽" 
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{order_id}")
async def delete_order(
    request: Request,
    order_id: int, 
    model: SQLAlchemyModel = Depends(get_model)
):
    try:
        success = model.orders().delete(order_id)
        if success:
            if request.headers.get("HX-Request"):
                return HTMLResponse("")
            return {"message": f"Order {order_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
