from fastapi import FastAPI
from tasks import router as tasks_router
from products import router as products_router
from auth import router as auth_router  # Import auth routes
from category import category_router
from upload import router as upload_router  # Import the upload router

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

# List of origins that are allowed to make requests to the API
origins = [
    "http://localhost:3000",  # React app running on localhost:3000
    "http://127.0.0.1:3000",  # React app running on 127.0.0.1:3000 (if needed)
]

# Add CORSMiddleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows these origins to access the API
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include routers from tasks and products
app.include_router(category_router, prefix="/category", tags=["category"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])  # Use /auth for authentication
app.include_router(upload_router, prefix="/files", tags=["files"])  # Include upload router


# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the task and product API!"}
