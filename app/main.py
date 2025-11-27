from fastapi import FastAPI
from app.api import product_routes
from app.db.database import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Price Promotions Engine")

app.include_router(product_routes.router)

@app.get("/")
def root():
    return {"message": "Welcome to Promotions Engine!"}
