from sqlalchemy.orm import Session
from app.models.promotion import Promotion
from app.schemas.promotion import PromotionCreate, PromotionUpdate
from app.core.cache import CacheService

def create_promotion(db: Session, data: PromotionCreate):
    promo = Promotion(**data.dict())
    db.add(promo)
    db.commit()
    db.refresh(promo)
    # Invalidate cache for this product
    CacheService.invalidate_product(promo.product_id)
    return promo

def update_promotion(db: Session, promo_id: int, data: PromotionUpdate):
    promo = db.query(Promotion).filter(Promotion.id == promo_id).first()
    if not promo:
        return None
    product_id = promo.product_id  # Store before update
    for key, value in data.dict(exclude_unset=True).items():
        setattr(promo, key, value)
    db.commit()
    db.refresh(promo)
    # Invalidate cache for this product
    CacheService.invalidate_product(product_id)
    return promo

def delete_promotion(db: Session, promo_id: int):
    promo = db.query(Promotion).filter(Promotion.id == promo_id).first()
    if not promo:
        return False
    product_id = promo.product_id  # Store before delete
    db.delete(promo)
    db.commit()
    # Invalidate cache for this product
    CacheService.invalidate_product(product_id)
    return True

def get_all_promotions(db: Session):
    return db.query(Promotion).all()

def get_promotion(db: Session, promo_id: int):
    return db.query(Promotion).filter(Promotion.id == promo_id).first()
