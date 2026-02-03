from fastapi import APIRouter, Depends, Request, Response, HTTPException, Header, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, List
import uuid

from api.dependencies import get_model
from sql_model.model import SQLAlchemyModel
from api.utils import get_resource_path

router = APIRouter(prefix="/api/pos", tags=["pos"])
from api.templates_config import templates

# In-memory cart storage: {cart_id: {"items": {product_id: quantity}, "discount": 0}}
CARTS: Dict[str, dict] = {}

def get_cart_id(request: Request):
    """Retrieve cart_id from cookies or generate a new one."""
    cart_id = request.cookies.get("cart_id")
    is_new = False
    if not cart_id:
        cart_id = str(uuid.uuid4())
        is_new = True
    
    if cart_id not in CARTS:
        CARTS[cart_id] = {"items": {}, "discount": 0}
        
    return cart_id, is_new

@router.get("/products-grid", response_class=HTMLResponse)
async def get_products_grid(
    request: Request,
    search: Optional[str] = None,
    model: SQLAlchemyModel = Depends(get_model)
):
    products = model.products().data()
    if search:
        s = search.lower()
        products = [p for p in products if s in p.name.lower()]
    
    return templates.TemplateResponse(request, "pos/products_grid.html", {"products": products})

@router.get("/cart", response_class=HTMLResponse)
async def get_cart(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    cart_id, is_new = get_cart_id(request)
    cart = CARTS[cart_id]
    
    response = render_cart(request, cart, model)
    if is_new:
        response.set_cookie(key="cart_id", value=cart_id, max_age=3600*24)
    return response

@router.post("/cart/add/{product_id}", response_class=HTMLResponse)
async def add_to_cart(
    request: Request,
    product_id: int,
    model: SQLAlchemyModel = Depends(get_model)
):
    cart_id, is_new = get_cart_id(request)
    cart = CARTS[cart_id]
    
    product_id_str = str(product_id)
    if product_id_str in cart["items"]:
        cart["items"][product_id_str] += 1
    else:
        cart["items"][product_id_str] = 1
        
    response = render_cart(request, cart, model, toast=f"Added to cart")
    if is_new:
        response.set_cookie(key="cart_id", value=cart_id, max_age=3600*24)
    return response

@router.post("/cart/update/{product_id}", response_class=HTMLResponse)
async def update_cart_item(
    request: Request,
    product_id: int,
    change: Optional[int] = None,
    quantity: Optional[str] = Form(None),
    model: SQLAlchemyModel = Depends(get_model)
):
    cart_id, is_new = get_cart_id(request)
    cart = CARTS[cart_id]
    
    product_id_str = str(product_id)
    if product_id_str in cart["items"]:
        if quantity is not None and quantity.strip() != "":
            try:
                cart["items"][product_id_str] = int(quantity)
            except ValueError:
                pass
        elif change is not None:
            cart["items"][product_id_str] += change
            
        if cart["items"][product_id_str] <= 0:
            del cart["items"][product_id_str]
            
    response = render_cart(request, cart, model)
    if is_new:
        response.set_cookie(key="cart_id", value=cart_id, max_age=3600*24)
    return response

@router.delete("/cart/remove/{product_id}", response_class=HTMLResponse)
async def remove_from_cart(
    request: Request,
    product_id: int,
    model: SQLAlchemyModel = Depends(get_model)
):
    cart_id, is_new = get_cart_id(request)
    cart = CARTS[cart_id]
    
    product_id_str = str(product_id)
    if product_id_str in cart["items"]:
        del cart["items"][product_id_str]
        
    response = render_cart(request, cart, model, toast="Item removed")
    if is_new:
        response.set_cookie(key="cart_id", value=cart_id, max_age=3600*24)
    return response

@router.delete("/cart/clear", response_class=HTMLResponse)
async def clear_cart(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    cart_id, is_new = get_cart_id(request)
    CARTS[cart_id] = {"items": {}, "discount": 0}
    
    response = render_cart(request, cart=CARTS[cart_id], model=model, toast="Cart cleared")
    if is_new:
        response.set_cookie(key="cart_id", value=cart_id, max_age=3600*24)
    return response

@router.post("/cart/discount", response_class=HTMLResponse)
async def set_discount(
    request: Request,
    discount: int = Form(...),
    model: SQLAlchemyModel = Depends(get_model)
):
    cart_id, is_new = get_cart_id(request)
    CARTS[cart_id]["discount"] = max(0, min(100, discount))
    
    response = render_cart(request, cart=CARTS[cart_id], model=model)
    if is_new:
        response.set_cookie(key="cart_id", value=cart_id, max_age=3600*24)
    return response

@router.post("/checkout", response_class=HTMLResponse)
async def checkout(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    cart_id, is_new = get_cart_id(request)
    cart = CARTS[cart_id]
    
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    form = await request.form()
    complete_now = form.get("complete_now") == "true"
    completion_date = form.get("completion_date")
    additional_info = form.get("additional_info")
    
    # Robust discount parsing
    form_discount = form.get("discount")
    try:
        if form_discount is not None and form_discount.strip() != "":
            discount = int(form_discount)
        else:
            discount = cart["discount"]
    except (ValueError, TypeError):
        discount = cart["discount"]
    
    items = []
    for pid, qty in cart["items"].items():
        items.append({"product_id": int(pid), "quantity": qty})
        
    try:
        new_order = model.orders().add(
            items=items,
            completion_date=completion_date,
            additional_info=additional_info,
            complete_now=complete_now,
            discount=discount
        )
        
        # Clear cart after successful checkout
        CARTS[cart_id] = {"items": {}, "discount": 0}
        
        # Return empty cart with success toast
        response = render_cart(request, CARTS[cart_id], model, toast="Order created successfully!")
        response.headers["HX-Trigger"] = "dashboard-update"
        if is_new:
            response.set_cookie(key="cart_id", value=cart_id, max_age=3600*24)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def render_cart(request: Request, cart: dict, model: SQLAlchemyModel, toast: str = None):
    cart_items = []
    subtotal = 0
    
    for pid, qty in cart["items"].items():
        product = model.products().by_id(int(pid))
        if product:
            item_total = product.price * qty
            subtotal += item_total
            cart_items.append({
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": qty,
                "total": item_total
            })
            
    total = subtotal * (1 - cart["discount"] / 100)
    
    response = templates.TemplateResponse(request, "pos/cart_panel.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "discount": cart["discount"],
        "total": total
    })
    
    if toast:
        # Custom header for toast if needed, or just status update
        response.headers["HX-Trigger"] = f'{{"showToast": "{toast}"}}'
        
    return response
