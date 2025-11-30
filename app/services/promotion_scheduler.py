from datetime import datetime
from sqlalchemy.orm import Session
from app.models.promotion import Promotion

def update_promotion_status(db: Session):
    now = datetime.now()

    promotions = db.query(Promotion).all()
    for promo in promotions:
        if promo.start_date <= now <= promo.end_date:
            promo.is_active = True
        else:
            promo.is_active = False

    db.commit()
