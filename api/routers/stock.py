from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.dependencies import get_model
from api.models import StockItem, StockCreate, StockUpdate, StockSet
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/stock", tags=["stock"])

@router.get("/", response_model=List[StockItem])
def get_stock(model: SQLiteModel = Depends(get_model)):
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

@router.get("/categories", response_model=List[str])
def get_categories(model: SQLiteModel = Depends(get_model)):
    try:
        return model.utils().get_stock_category_names()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
