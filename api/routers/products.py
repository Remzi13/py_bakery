from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from api.dependencies import get_model
from api.models import ProductCreate, ProductResponse
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("/", response_model=List[ProductResponse])
def get_products(model: SQLiteModel = Depends(get_model)):
    try:
        # The repository returns objects with dynamic attributes (SimpleNamespace-like for 'products.data()') 
        # but we need to match Pydantic model. 
        # repositories/products.py data() returns list of SimpleNamespace with .ingredients as list of dicts.
        
        products_data = model.products().data()
        results = []
        for p in products_data:
            # We need to manually map because SimpleNamespace isn't a dict
            results.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "ingredients": p.ingredients
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, model: SQLiteModel = Depends(get_model)):
    try:
        # Convert Pydantic ingredients list to list of dicts expected by repo
        ingredients_list = [i.dict() for i in product.ingredients]
        
        new_product = model.products().add(product.name, product.price, ingredients_list)
        
        # Get ingredients again to populate response
        ingredients = model.products().get_materials_for_product(new_product.id)
        
        return {
            "id": new_product.id,
            "name": new_product.name,
            "price": new_product.price,
            "ingredients": ingredients
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, model: SQLiteModel = Depends(get_model)):
    try:
        p = model.products().by_id(product_id)
        if not p:
            raise HTTPException(status_code=404, detail="Product not found")
        ingredients = model.products().get_materials_for_product(p.id)
        return {"id": p.id, "name": p.name, "price": p.price, "ingredients": ingredients}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate, model: SQLiteModel = Depends(get_model)):
    try:
        ingredients_list = [i.dict() for i in product.ingredients]
        updated = model.products().update(product_id, product.name, product.price, ingredients_list)
        ingredients = model.products().get_materials_for_product(updated.id)
        return {"id": updated.id, "name": updated.name, "price": updated.price, "ingredients": ingredients}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_name}")
def delete_product(product_name: str, model: SQLiteModel = Depends(get_model)):
    try:
        model.products().delete(product_name)
        return {"message": f"Product '{product_name}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
