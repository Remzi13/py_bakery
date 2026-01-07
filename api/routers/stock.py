from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.dependencies import get_model
from api.models import StockItem, StockCreate, StockUpdate, StockSet
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/stock", tags=["stock"])

@router.get("/", response_model=List[StockItem])
def get_stock(model: SQLiteModel = Depends(get_model)):
    try:
        return model.stock().data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=StockItem)
def add_stock(item: StockCreate, model: SQLiteModel = Depends(get_model)):
    try:
        model.stock().add(item.name, item.category_name, item.quantity, item.unit_name)
        return model.stock().get(item.name)
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
def set_stock_quantity(name: str, update: StockSet, model: SQLiteModel = Depends(get_model)):
    try:
        model.stock().set(name, update.quantity)
        return model.stock().get(name)
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
        return {"message": f"Stock item '{name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
