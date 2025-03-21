from fastapi import FastAPI
from tasks import router as tasks_router
from products import router as products_router
from auth import router as auth_router  # Import auth routes

app = FastAPI()

# Include routers from tasks and products
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])  # Use /auth for authentication

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the task and product API!"}
