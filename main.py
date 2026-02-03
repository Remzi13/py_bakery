from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from api.routers import (
    products, stock, sales, expenses, suppliers, 
    writeoffs, orders, dashboard, reports, pos, pages
)
from sql_model.database import init_db
from api.version import APP_VERSION
from api.utils import get_resource_path
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database once at startup unless skipped (for tests)
    if not getattr(app.state, "skip_init_db", False):
        init_db()
    yield

app = FastAPI(title="Bakery Manager API", lifespan=lifespan)

# Include Routers
app.include_router(pages.router)
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(sales.router)
app.include_router(expenses.router)
app.include_router(suppliers.router)
app.include_router(writeoffs.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(pos.router)

# Mount Static Files
app.mount("/static", StaticFiles(directory=get_resource_path("static")), name="static")
