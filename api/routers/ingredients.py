from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from api.dependencies import get_model
from api.models import Ingredient, Unit
from pydantic import BaseModel
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/ingredients", tags=["ingredients"])

class IngredientCreate(BaseModel):
    name: str
    unit_name: str

class IngredientResponse(BaseModel):
    id: int
    name: str
    unit_id: int
    unit_name: Optional[str] = None

@router.get("/", response_model=List[IngredientResponse])
def get_ingredients(model: SQLiteModel = Depends(get_model)):
    try:
        # We need to join with units to get unit name ideally, but repo might not return it
        # The repo returns Ingredient entity which has unit_id.
        ingredients = model.ingredients().data()
        results = []
        for ing in ingredients:
            # Helper to get unit name if possible, or we fetch units once
            # For efficiency in this simple app, we can fetch unit name per item or just return IDs
            # Let's try to get unit name.
            # We can use model.utils() or just a raw query if needed
            # But wait, entities.Ingredient has unit_id.
            
            # Let's simple return what we have, we might need to fetch units to map names in frontend
            # Or we can do a quick lookup here
            unit_name = "Unknown"
            # This is N+1 but acceptable for small scale
            # A better way would be to fetch all units and map
            # or update the repository to do a JOIN.
            # Let's assume frontend can load units and map IDs or we expand here.
            
            # Let's expand here for "Convenience"
            conn = model._conn
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM units WHERE id = ?", (ing.unit_id,))
            row = cursor.fetchone()
            if row:
                unit_name = row[0]

            results.append({
                "id": ing.id,
                "name": ing.name,
                "unit_id": ing.unit_id,
                "unit_name": unit_name
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=IngredientResponse)
def create_ingredient(ingredient: IngredientCreate, model: SQLiteModel = Depends(get_model)):
    try:
        new_ing = model.ingredients().add(ingredient.name, ingredient.unit_name)
        return {
            "id": new_ing.id,
            "name": new_ing.name,
            "unit_id": new_ing.unit_id,
            "unit_name": ingredient.unit_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # logging.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/units", response_model=List[Unit])
def get_units(model: SQLiteModel = Depends(get_model)):
    try:
        # Utils repo? Or just manual query
        # There isn't a dedicated Units repo exposed typically, but we can query table
        cursor = model._conn.cursor()
        cursor.execute("SELECT * FROM units")
        rows = cursor.fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
