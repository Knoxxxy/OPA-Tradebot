# app/main.py

from fastapi import FastAPI
import items


app = FastAPI(
    title="OPA Tradebot API",  # Application name
    description="This is an API to access the OPA Tradebot",  # Application description
    version="1.0.0",  # Application version
)

# Include the items router
app.include_router(items.router, tags=["items"])

# Root route
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI MongoDB API!"}