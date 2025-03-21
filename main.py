from fastapi import FastAPI
from tasks import router as tasks_router
from products import router as products_router

app = FastAPI()

# Include routers from tasks and products
app.include_router(tasks_router)
app.include_router(products_router, prefix="/products", tags=["products"])

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the task and product API!"}
