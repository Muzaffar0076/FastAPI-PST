from fastapi import FastAPI
from app.api import product_routes
from app.db.database import Base, engine
from app.api import promotion_router


# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Price Promotions Engine")

app.include_router(product_routes.router)
app.include_router(promotion_router.router)

@app.get("/")
def root():
    return {"message": "Welcome to Promotions Engine!"}
