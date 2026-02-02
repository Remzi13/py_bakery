from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
from api.dependencies import get_model
from sql_model.model import SQLAlchemyModel
from sql_model.entities import Sale, ExpenseDocument, ExpenseCategory, ExpenseItem, ExpenseType, Product, StockItem, WriteOff, Unit
from sqlalchemy import func, Float
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/reports", tags=["reports"])
from api.utils import get_resource_path
templates = Jinja2Templates(directory=get_resource_path("templates"))

from api.version import APP_VERSION
def get_db_version():
    from sql_model.database import SessionLocal
    from sql_model.entities import SystemSettings
    db = SessionLocal()
    try:
        version = db.query(SystemSettings).filter(SystemSettings.key == 'db_version').first()
        return version.value if version else "unknown"
    except Exception:
        return "error"
    finally:
        db.close()

templates.env.globals["app_version"] = APP_VERSION
templates.env.globals["get_db_version"] = get_db_version

@router.get("/", response_class=HTMLResponse)
async def get_reports_page(
    request: Request,
    model: SQLAlchemyModel = Depends(get_model)
):
    # Summary Stats
    total_revenue = model.calculate_income()
    total_expenses = model.calculate_expenses()
    net_profit = total_revenue - total_expenses
    
    sale_count = model.db.query(Sale).count()
    avg_order_value = total_revenue / sale_count if sale_count > 0 else 0
    
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    summary = {
        "total_revenue": round(total_revenue, 2),
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2),
        "avg_order_value": round(avg_order_value, 2),
        "profit_margin": round(profit_margin, 2)
    }
    
    # Sales by Day (Last 30 days)
    today = datetime.now()
    thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    
    sales_by_day = model.db.query(
        func.substr(Sale.date, 1, 10).label('day'),
        func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100)).label('revenue')
    ).filter(Sale.date >= thirty_days_ago).group_by('day').order_by('day').all()
    
    # Top Products
    top_products = model.db.query(
        Sale.product_name,
        func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100)).label('revenue')
    ).group_by(Sale.product_name).order_by(func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100)).desc()).limit(10).all()
    
    # Expenses by Category
    expenses_by_category = model.db.query(
        ExpenseCategory.name,
        func.sum(ExpenseDocument.total_amount).label('total')
    ).join(ExpenseType, ExpenseType.category_id == ExpenseCategory.id)\
     .join(ExpenseItem, ExpenseItem.expense_type_id == ExpenseType.id)\
     .join(ExpenseDocument, ExpenseDocument.id == ExpenseItem.document_id)\
     .group_by(ExpenseCategory.name).all()

    # Stock Status
    low_stock = model.db.query(StockItem).filter(StockItem.quantity < 10).order_by(StockItem.quantity.asc()).limit(10).all()
    
    # Recent Write-offs
    recent_writeoffs = model.db.query(WriteOff).order_by(WriteOff.date.desc()).limit(10).all()
    
    return templates.TemplateResponse(request, "reports.html", {
        "summary": summary,
        "sales_by_day": [{"day": row.day, "revenue": float(row.revenue)} for row in sales_by_day],
        "top_products": [{"name": row.product_name, "revenue": float(row.revenue)} for row in top_products],
        "expenses_by_category": [{"name": row.name, "total": float(row.total)} for row in expenses_by_category],
        "low_stock": [{
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit.name if item.unit else ""
        } for item in low_stock],
        "recent_writeoffs": [{
            "item_name": (item.stock_item.name if item.stock_item else (item.product.name if item.product else "Unknown")),
            "quantity": item.quantity,
            "reason": item.reason,
            "date": item.date,
            "unit": item.unit.name if item.unit else ""
        } for item in recent_writeoffs]
    })
