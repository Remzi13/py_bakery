from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.dependencies import get_model
from api.models import Supplier
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])

@router.get("/", response_model=List[Supplier])
def get_suppliers(model: SQLiteModel = Depends(get_model)):
    try:
        return model.suppliers().data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Supplier)
def create_supplier(supplier: Supplier, model: SQLiteModel = Depends(get_model)):
    try:
        # Since ID is ignored in creation, we just pass other fields
        return model.suppliers().add(supplier.name, supplier.contact_person, supplier.phone, supplier.email, supplier.address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{name}")
def delete_supplier(name: str, model: SQLiteModel = Depends(get_model)):
    try:
        model.suppliers().delete(name)
        return {"message": f"Supplier '{name}' deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
