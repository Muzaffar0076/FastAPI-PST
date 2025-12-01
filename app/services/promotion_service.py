from sqlalchemy.orm import Session
from app.models.promotion import Promotion
from app.models.product import Product
from app.schemas.promotion import PromotionCreate, PromotionUpdate
from app.core.cache import CacheService
from app.services.validation_service import PromotionValidator

def create_promotion(db: Session, data: PromotionCreate):
    validation_result = PromotionValidator.validate_promotion(db, data)
    if not validation_result['valid']:
        raise ValueError('; '.join(validation_result['errors']))
    if data.product_id is not None:
        product = db.query(Product).filter(Product.id == data.product_id).first()
        if not product:
            raise ValueError(f'Product with id {data.product_id} does not exist')
    promo = Promotion(**data.model_dump())
    db.add(promo)
    db.commit()
    db.refresh(promo)
    if promo.product_id:
        CacheService.invalidate_product(promo.product_id)
    return promo

def update_promotion(db: Session, promo_id: int, data: PromotionUpdate):
    promo = db.query(Promotion).filter(Promotion.id == promo_id).first()
    if not promo:
        return None
    validation_result = PromotionValidator.validate_promotion(db, data, exclude_id=promo_id)
    if not validation_result['valid']:
        raise ValueError('; '.join(validation_result['errors']))
    product_id = promo.product_id
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(promo, key, value)
    db.commit()
    db.refresh(promo)
    if product_id:
        CacheService.invalidate_product(product_id)
    return promo

def delete_promotion(db: Session, promo_id: int):
    promo = db.query(Promotion).filter(Promotion.id == promo_id).first()
    if not promo:
        return False
    product_id = promo.product_id
    db.delete(promo)
    db.commit()
    if product_id:
        CacheService.invalidate_product(product_id)
    return True

def get_all_promotions(db: Session):
    return db.query(Promotion).all()

def get_promotion(db: Session, promo_id: int):
    return db.query(Promotion).filter(Promotion.id == promo_id).first()