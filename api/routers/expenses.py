from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.dependencies import get_model
from api.models import Expense, ExpenseCreate, ExpenseType
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

@router.get("/", response_model=List[Expense])
def get_expenses(model: SQLiteModel = Depends(get_model)):
    try:
        return model.expenses().data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def create_expense(expense: ExpenseCreate, model: SQLiteModel = Depends(get_model)):
    try:
        # We need to find the ExpenseType by ID to get its name
        # Since ExpenseTypesRepository doesn't have by_id, we do it manually via cursor
        # or we could iterate data() (less efficient but works for now)
        
        # Using raw SQL for efficiency since we have access to connection via model._conn if needed,
        # but model doesn't expose conn directly publicly, only via repos.
        # But actually model._conn is accessible.
        
        # Let's use a quick query
        cursor = model._conn.cursor()
        cursor.execute("SELECT name FROM expense_types WHERE id = ?", (expense.type_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Expense Type not found")
        type_name = row[0]
        
        supplier_name = None
        if expense.supplier_id:
            supplier = model.suppliers().get(expense.supplier_id)
            if supplier:
                supplier_name = supplier.name
        
        model.expenses().add(type_name, expense.price, expense.quantity, supplier_name)
        return {"message": "Expense created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types", response_model=List[ExpenseType])
def get_expense_types(model: SQLiteModel = Depends(get_model)):
    try:
        return model.expense_types().data()
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
