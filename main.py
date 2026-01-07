from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routers import products, stock, sales, expenses, suppliers, ingredients

app = FastAPI(title="Bakery Manager API")

# Include Routers
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(sales.router)
app.include_router(expenses.router)
app.include_router(suppliers.router)
app.include_router(ingredients.router)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')
