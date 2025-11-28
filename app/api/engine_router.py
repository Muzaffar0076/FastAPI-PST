from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.engine import PriceRequest
from app.services.engine_service import calculate_price_with_explanation

router = APIRouter(prefix="/engine", tags=["Price Engine"])

@router.post("/compute")
def compute(data: PriceRequest, db: Session = Depends(get_db)):
    result = calculate_price_with_explanation(db, data.product_id, data.quantity)
    if not result:
        return {"error": "Product not found"}
    return result
