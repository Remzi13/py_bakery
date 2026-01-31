from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routers import products, stock, sales, expenses, suppliers, writeoffs, orders, dashboard
from sql_model.database import init_db, SessionLocal
from sql_model.entities import SystemSettings
from api.version import APP_VERSION

from fastapi.templating import Jinja2Templates

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database once at startup unless skipped (for tests)
    if not getattr(app.state, "skip_init_db", False):
        init_db()
    yield

app = FastAPI(title="Bakery Manager API", lifespan=lifespan)

from api.utils import get_resource_path
templates = Jinja2Templates(directory=get_resource_path("templates"))

def get_db_version():
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

# Include Routers
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(sales.router)
app.include_router(expenses.router)
app.include_router(suppliers.router)
app.include_router(writeoffs.router)
app.include_router(orders.router)
app.include_router(dashboard.router)

# Mount Static Files
app.mount("/static", StaticFiles(directory=get_resource_path("static")), name="static")

@app.get("/")
async def read_landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})

@app.get("/management")
async def read_management(request: Request):
    return templates.TemplateResponse(request, "management.html", {})

@app.get("/pos")
async def read_pos(request: Request):
    return templates.TemplateResponse(request, "pos.html", {})

@app.get("/expenses")
async def read_expenses_entry(request: Request):
    from sql_model.database import SessionLocal
    from sql_model.model import SQLAlchemyModel
    db = SessionLocal()
    try:
        model = SQLAlchemyModel(db)
        suppliers = model.suppliers().data()
        categories = model.utils().get_expense_category_names()
        types = model.expense_types().data()
        
        all_types = []
        for item in types:
            all_types.append({
                "id" : item.id,
                "name": item.name,
                "unit_id" : item.unit_id,
                "unit_name": model.utils().get_unit_name_by_id(item.unit_id),
                "category_id": item.category_id,
                "category_name": model.utils().get_expense_category_name_by_id(item.category_id),
                "default_price": item.default_price
            })
            
        return templates.TemplateResponse(request, "expenses_entry.html", {
            "suppliers": suppliers,
            "categories": categories,
            "types": all_types
        })
    finally:
        db.close()
