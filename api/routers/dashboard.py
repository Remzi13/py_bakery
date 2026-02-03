from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from api.dependencies import get_model
from sql_model.model import SQLAlchemyModel
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
from api.templates_config import templates

@router.get("/")
async def get_dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard/index.html", {})

@router.get("/stats")
async def get_dashboard_stats(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    # Calculate daily revenue
    today = datetime.now().strftime("%Y-%m-%d")
    sales = model.sales().data()    
    monthly_revenue = sum(s.price * s.quantity * (1 - s.discount / 100) for s in sales if s.date.startswith(today[:7]))
    
    monthly_expenses = sum(e.total_amount for e in model.expense_documents().data() if e.date.startswith(today[:7]))
    
    if monthly_revenue > 0:
        profit_margin = (monthly_revenue - monthly_expenses) / monthly_revenue * 100
    else:
        profit_margin = 0
    
    return templates.TemplateResponse(request, "dashboard/stats.html", {
        "monthly_revenue": monthly_revenue,
        "monthly_expenses": monthly_expenses,    
        "profit_margin": round(profit_margin, 2)
    })

@router.get("/chart")
async def get_dashboard_chart(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    now = datetime.now()
    sales = model.sales().data()
    
    weekly_sales = [0] * 7
    weekday_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    labels = []
    
    for i in range(7):
        date = now - timedelta(days=6-i)
        date_str = date.strftime("%Y-%m-%d")
        day_sales = sum(s.price * s.quantity * (1 - s.discount / 100) for s in sales if s.date.startswith(date_str))
        weekly_sales[i] = day_sales
        labels.append(weekday_names[date.weekday()])

    max_val = max(weekly_sales) if weekly_sales and max(weekly_sales) > 0 else 1
    
    chart_data = []
    for i in range(7):
        chart_data.append({
            "value": weekly_sales[i],
            "height": (weekly_sales[i] / max_val) * 100,
            "label": labels[i]
        })
        
    return templates.TemplateResponse(request, "dashboard/chart.html", {"chart_data": chart_data})

@router.get("/recent-activity")
async def get_recent_activity(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    sales = model.sales().data()
    # Sort by date descending and take top 5
    recent_sales = sorted(sales, key=lambda x: x.date, reverse=True)[:5]
    
    activities = []
    for s in recent_sales:
        time_part = s.date.split(' ')[1] if ' ' in s.date else ''
        activities.append({
            "type": "sale",
            "text": f"Sold: {s.product_name} x {s.quantity}",
            "time": time_part
        })
    
    return templates.TemplateResponse(request, "dashboard/recent_activity.html", {"activities": activities})

@router.get("/pending-orders")
async def get_pending_orders(request: Request, model: SQLAlchemyModel = Depends(get_model)):
    orders = model.orders().get_pending()
    
    order_data = []
    for order in orders:
        subtotal = sum(item['price'] * item['quantity'] for item in order.items)
        total = subtotal * (1 - (order.discount or 0) / 100)
        order_data.append({
            "id": order.id,
            "completion_date": order.completion_date,
            "items_text": ", ".join([f"{i['product_name']} x {i['quantity']}" for i in order.items]),
            "total": total
        })
        
    return templates.TemplateResponse(request, "dashboard/pending_orders.html", {"orders": order_data})
