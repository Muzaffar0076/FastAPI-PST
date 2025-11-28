from sqlalchemy.orm import Session
from app.models.promotion import Promotion
from app.schemas.promotion import PromotionCreate, PromotionUpdate

def create_promotion(db: Session, data: PromotionCreate):
    promo = Promotion(**data.dict())
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo

def update_promotion(db: Session, promo_id: int, data: PromotionUpdate):
    promo = db.query(Promotion).filter(Promotion.id == promo_id).first()
    if not promo:
        return None
    for key, value in data.dict().items():
        setattr(promo, key, value)
    db.commit()
    db.refresh(promo)
    return promo

def delete_promotion(db: Session, promo_id: int):
    promo = db.query(Promotion).filter(Promotion.id == promo_id).first()
    if not promo:
        return False
    db.delete(promo)
    db.commit()
    return True

def get_all_promotions(db: Session):
    return db.query(Promotion).all()

def get_promotion(db: Session, promo_id: int):
    return db.query(Promotion).filter(Promotion.id == promo_id).first()
