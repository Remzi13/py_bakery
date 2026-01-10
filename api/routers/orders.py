from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.dependencies import get_model
from api.models import OrderCreate, OrderResponse, OrderItemResponse
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.get("/", response_model=List[OrderResponse])
def get_orders(model: SQLiteModel = Depends(get_model)):
    try:
        orders_data = model.orders().data()
        results = []
        for order in orders_data:
            results.append({
                "id": order.id,
                "created_date": order.created_date,
                "completion_date": order.completion_date,
                "status": order.status,
                "additional_info": order.additional_info,
                "items": order.items
            })
        results.sort(key=lambda x: x["status"], reverse=True)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending", response_model=List[OrderResponse])
def get_pending_orders(model: SQLiteModel = Depends(get_model)):
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
                "items": order.items
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, model: SQLiteModel = Depends(get_model)):
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
def create_order(order: OrderCreate, model: SQLiteModel = Depends(get_model)):
    try:
        items = [{"product_id": item.product_id, "quantity": item.quantity} for item in order.items]
        new_order = model.orders().add(
            items=items,
            completion_date=order.completion_date,
            additional_info=order.additional_info,
            complete_now=order.complete_now
        )
        
        # Get full order with items
        full_order = model.orders().by_id(new_order.id)
        
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
def complete_order(order_id: int, model: SQLiteModel = Depends(get_model)):
    try:
        success = model.orders().complete(order_id)
        if success:
            return {"message": f"Order {order_id} completed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to complete order")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{order_id}")
def delete_order(order_id: int, model: SQLiteModel = Depends(get_model)):
    try:
        success = model.orders().delete(order_id)
        if success:
            return {"message": f"Order {order_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
