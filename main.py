from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routers import products, stock, sales, expenses, suppliers, writeoffs, orders, dashboard
from sql_model.database import init_db

from fastapi.templating import Jinja2Templates

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database once at startup
    init_db()
    yield

app = FastAPI(title="Bakery Manager API", lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

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
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})

@app.get("/management")
async def read_management(request: Request):
    return templates.TemplateResponse(request, "management.html", {})

@app.get("/pos")
async def read_pos(request: Request):
    return templates.TemplateResponse(request, "pos.html", {})
