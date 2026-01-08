from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from api.dependencies import get_model
from sql_model.model import SQLiteModel
from sql_model.entities import WriteOff

router = APIRouter(prefix="/api/writeoffs", tags=["writeoffs"])

class WriteOffCreate(BaseModel):
    item_name: str
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
async def get_writeoffs(model: SQLiteModel = Depends(get_model)):
    try:
        data = model.writeoffs().data()
        results = []
        for wo in data:
            item_name = "Unknown"
            if wo.product_id:
                p = model.products().by_id(wo.product_id)
                item_name = p.name if p else f"Product #{wo.product_id}"
            elif wo.stock_item_id:
                # Need a method to get stock item by ID or name
                # Stock repository has get(name), let's check if there is get_by_id
                # Or just use model.utils() to get unit name etc.
                # Actually, WriteOff has stock_item_id.
                # Let's see if we can get it from DB directly if repo doesn't have it.
                cursor = model._conn.cursor()
                cursor.execute("SELECT name FROM stock WHERE id = ?", (wo.stock_item_id,))
                row = cursor.fetchone()
                if row:
                    item_name = row[0]
            
            wo_dict = wo.__dict__.copy()
            wo_dict['item_name'] = item_name
            results.append(wo_dict)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=WriteOffRead)
async def add_writeoff(data: WriteOffCreate, model: SQLiteModel = Depends(get_model)):
    try:
        model.writeoffs().add(
            item_name=data.item_name,
            item_type=data.item_type,
            quantity=data.quantity,
            reason=data.reason
        )
        # Get the latest record (since add doesn't return the object)
        latest = model.writeoffs().data()[0]
        return latest
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
