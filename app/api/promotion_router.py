from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.database import get_db
from app.schemas.promotion import PromotionCreate, PromotionUpdate, PromotionResponse
from app.services.promotion_service import (
    create_promotion, update_promotion, delete_promotion,
    get_all_promotions, get_promotion
)

router = APIRouter(prefix="/promotions", tags=["Promotions"])

@router.post("/", response_model=PromotionResponse)
def create(data: PromotionCreate, db: Session = Depends(get_db)):
    try:
        return create_promotion(db, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Invalid product_id or promotion constraint violation")

@router.get("/", response_model=list[PromotionResponse])
def all(db: Session = Depends(get_db)):
    return get_all_promotions(db)

@router.get("/{promo_id}", response_model=PromotionResponse)
def get(promo_id: int, db: Session = Depends(get_db)):
    promo = get_promotion(db, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promo

@router.put("/{promo_id}", response_model=PromotionResponse)
def update(promo_id: int, data: PromotionUpdate, db: Session = Depends(get_db)):
    promo = update_promotion(db, promo_id, data)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promo

@router.delete("/{promo_id}")
def delete(promo_id: int, db: Session = Depends(get_db)):
    success = delete_promotion(db, promo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return {"message": "Promotion deleted successfully"}
