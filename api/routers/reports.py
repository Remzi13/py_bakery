from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from typing import List, Optional, Dict, Any
from api.dependencies import get_model
from sql_model.model import SQLAlchemyModel
from sql_model.entities import Sale, ExpenseDocument, ExpenseCategory, ExpenseItem, ExpenseType, Product, StockItem, WriteOff, Unit
from sqlalchemy import func, Float
from datetime import datetime, timedelta
from api.templates_config import templates

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("", response_class=HTMLResponse)
async def get_reports_page(
    request: Request,
    period: str = "month",
    model: SQLAlchemyModel = Depends(get_model)
):
    now = datetime.now()
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_label_len = 13 # YYYY-MM-DD HH
    elif period == "week":
        start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_label_len = 10 # YYYY-MM-DD
    elif period == "year":
        start_date = (now - timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_label_len = 7 # YYYY-MM
    else: # month
        period = "month"
        start_date = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_label_len = 10 # YYYY-MM-DD
        
    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

    # Summary Stats for selected period
    total_revenue = model.db.query(
        func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100))
    ).filter(Sale.date >= start_date_str).scalar() or 0
    
    total_expenses = model.db.query(
        func.sum(ExpenseDocument.total_amount)
    ).filter(ExpenseDocument.date >= start_date_str).scalar() or 0
    
    net_profit = total_revenue - total_expenses
    
    sale_count = model.db.query(Sale).filter(Sale.date >= start_date_str).count()
    avg_order_value = total_revenue / sale_count if sale_count > 0 else 0
    
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    summary = {
        "total_revenue": round(float(total_revenue), 2),
        "total_expenses": round(float(total_expenses), 2),
        "net_profit": round(float(net_profit), 2),
        "avg_order_value": round(float(avg_order_value), 2),
        "profit_margin": round(float(profit_margin), 2)
    }
    
    # Sales Trend
    sales_trend = model.db.query(
        func.substr(Sale.date, 1, date_label_len).label('label'),
        func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100)).label('revenue')
    ).filter(Sale.date >= start_date_str).group_by('label').order_by('label').all()
    
    # Top Products
    top_products = model.db.query(
        Sale.product_name,
        func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100)).label('revenue')
    ).filter(Sale.date >= start_date_str).group_by(Sale.product_name).order_by(func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100)).desc()).limit(10).all()
    
    expenses_by_category = model.db.query(
        ExpenseCategory.name,
        func.sum(ExpenseItem.price).label('total')
    ).join(ExpenseType, ExpenseType.category_id == ExpenseCategory.id)\
     .join(ExpenseItem, ExpenseItem.expense_type_id == ExpenseType.id)\
     .join(ExpenseDocument, ExpenseDocument.id == ExpenseItem.document_id)\
     .filter(ExpenseDocument.date >= start_date_str)\
     .group_by(ExpenseCategory.name).all()

    # Stock Status (always current state, not filtered by period)
    low_stock = model.db.query(StockItem).filter(StockItem.quantity < 10).order_by(StockItem.quantity.asc()).limit(10).all()
    
    # Recent Write-offs
    recent_writeoffs = model.db.query(WriteOff).filter(WriteOff.date >= start_date_str).order_by(WriteOff.date.desc()).limit(10).all()
    
    return templates.TemplateResponse(request, "reports.html", {
        "summary": summary,
        "sales_trend": [{"label": row.label, "revenue": float(row.revenue)} for row in sales_trend],
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
        } for item in recent_writeoffs],
        "current_period": period
    })
