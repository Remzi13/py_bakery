from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.dependencies import get_model
from api.models import Sale, SaleCreate
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/sales", tags=["sales"])

@router.get("/", response_model=List[Sale])
def get_sales(model: SQLiteModel = Depends(get_model)):
    try:
        return model.sales().data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def create_sale(sale: SaleCreate, model: SQLiteModel = Depends(get_model)):
    try:
        # Get product name from ID
        product = model.products().by_id(sale.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        model.sales().add(product.name, product.price, sale.quantity, sale.discount)
        return {"message": "Sale created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
