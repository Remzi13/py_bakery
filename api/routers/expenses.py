from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.dependencies import get_model
from api.models import Expense, ExpenseCreate, ExpenseType
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

@router.get("/", response_model=List[Expense])
def get_expenses(model: SQLiteModel = Depends(get_model)):
    try:
        data = model.expenses().data()
        results = []
        utils = model.utils()
        for exp in data:
            cat_name = utils.get_expense_category_name_by_id(exp.category_id)
            
            supplier_name = "None"
            if exp.supplier_id:
                supplier = model.suppliers().get_by_id(exp.supplier_id)
                if supplier:
                    supplier_name = supplier.name
            
            exp_dict = exp.__dict__.copy()
            exp_dict['category_name'] = cat_name
            exp_dict['supplier_name'] = supplier_name
            results.append(exp_dict)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def create_expense(expense: ExpenseCreate, model: SQLiteModel = Depends(get_model)):
    try:
        # We need to find the ExpenseType by ID to get its name
        cursor = model._conn.cursor()
        cursor.execute("SELECT name FROM expense_types WHERE id = ?", (expense.type_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Expense Type not found")
        type_name = row[0]
        
        supplier_name = None
        if expense.supplier_id:
            supplier = model.suppliers().get_by_id(expense.supplier_id)
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
        data = model.expense_types().data()
        results = []
        utils = model.utils()
        for et in data:
            cat_name = utils.get_expense_category_name_by_id(et.category_id)
            et_dict = et.__dict__.copy()
            et_dict['category_name'] = cat_name
            results.append(et_dict)
        return results
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=List[str])
def get_expense_categories(model: SQLiteModel = Depends(get_model)):
    try:
        return model.utils().get_expense_category_names()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
