from fastapi import FastAPI
from app.api import product_routes
from app.db.database import Base, engine
from app.api import promotion_router
from app.api.engine_router import router as engine_router
from app.db.database import SessionLocal
from app.services.promotion_scheduler import update_promotion_status
from app.api.dashboard_router import router as dashboard_router
from app.api.simulation_router import router as simulation_router
from app.api.experiment_router import router as experiment_router







# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Price Promotions Engine")

app.include_router(product_routes.router)
app.include_router(promotion_router.router)
app.include_router(engine_router)
app.include_router(dashboard_router)
app.include_router(simulation_router)
app.include_router(experiment_router)

@app.get("/")
def root():
    return {"message": "Welcome to Promotions Engine!"}

@app.on_event("startup")
def activate_promotion_scheduler():
    db = SessionLocal()
    update_promotion_status(db)
    db.close()