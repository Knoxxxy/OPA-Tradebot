# app/main.py

from fastapi import FastAPI
from .routers import items


app = FastAPI()

# Include the items router
app.include_router(items.router, prefix="/items", tags=["items"])

# Root route
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI MongoDB API!"}