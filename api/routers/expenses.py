from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from api.dependencies import get_model
from api.models import (
    ExpenseType, ExpenseTypeCreate, 
    ExpenseCategoryCreate, ExpenseDocumentCreate, ExpenseDocumentResponse 
)
from sql_model.model import SQLiteModel

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

# --- Documents API (New System) ---

@router.post("/documents")
def create_expense_document(doc: ExpenseDocumentCreate, model: SQLiteModel = Depends(get_model)):
    try:
        # Calculate total amount
        total_amount = 0
        items_data = []
        for item in doc.items:
            total_amount += item.quantity * item.price_per_unit
            items_data.append(item.dict())
        
        doc_id = model.expense_documents().add(
            date=doc.date,
            supplier_id=doc.supplier_id,
            total_amount=total_amount,
            comment=doc.comment,
            items=items_data
        )
        return {"message": "Expense document created successfully", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=List[ExpenseDocumentResponse])
def get_expense_documents(model: SQLiteModel = Depends(get_model)):
    try:
        docs = model.expense_documents().get_documents_with_details()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{id}/items")
def get_expense_document_items(id: int, model: SQLiteModel = Depends(get_model)):
    try:
        items = model.expense_documents().get_document_items(id)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Categories & Types API ---

@router.post("/categories")
def create_expense_category(category: ExpenseCategoryCreate, model: SQLiteModel = Depends(get_model)):
    try:
        # We need to access underlying DB to add category, as there is no dedicated repo method explicitly exposed yet for simple insert
        # Or we can add method to UtilsRepository or ExpenseTypesRepository?
        # UtilsRepository has 'get_expense_category_names'.
        # Let's direct execute for now to save time, or better, add to Utils.
        # But wait, we don't have Utils add method.
        # Let's just execute SQL here or add a helper in Utils.
        cursor = model._conn.cursor()
        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (category.name,))
        model._conn.commit()
        return {"message": "Category created successfully"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/types")
def create_expense_type(type_data: ExpenseTypeCreate, model: SQLiteModel = Depends(get_model)):
    try:
        model.expense_types().add(
            name=type_data.name,
            default_price=type_data.default_price,
            category_name=type_data.category_name,
            stock=type_data.stock
        )
        return {"message": "Expense type created successfully"}
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
