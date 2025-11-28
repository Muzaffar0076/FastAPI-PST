from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.promotion import PromotionCreate, PromotionUpdate, PromotionResponse
from app.services.promotion_service import (
    create_promotion, update_promotion, delete_promotion,
    get_all_promotions, get_promotion
)

router = APIRouter(prefix="/promotions", tags=["Promotions"])

@router.post("/", response_model=PromotionResponse)
def create(data: PromotionCreate, db: Session = Depends(get_db)):
    return create_promotion(db, data)

@router.get("/", response_model=list[PromotionResponse])
def all(db: Session = Depends(get_db)):
    return get_all_promotions(db)

@router.get("/{promo_id}", response_model=PromotionResponse)
def get(promo_id: int, db: Session = Depends(get_db)):
    return get_promotion(db, promo_id)

@router.put("/{promo_id}", response_model=PromotionResponse)
def update(promo_id: int, data: PromotionUpdate, db: Session = Depends(get_db)):
    return update_promotion(db, promo_id, data)

@router.delete("/{promo_id}")
def delete(promo_id: int, db: Session = Depends(get_db)):
    return delete_promotion(db, promo_id)
