from sqlalchemy.orm import Session
from datetime import datetime
from app.models.product import Product
from app.models.promotion import Promotion



class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self):
        today = datetime.utcnow()

        total_products = self.db.query(Product).count()
        active_promotions = self.db.query(Promotion).filter(
            Promotion.is_active == True,
            Promotion.start_date <= today,
            Promotion.end_date >= today
        ).count()

        expired_promotions = self.db.query(Promotion).filter(
            Promotion.end_date < today
        ).count()

        upcoming_promotions = self.db.query(Promotion).filter(
            Promotion.start_date > today
        ).count()

        # Optional: If pricing requests table exists
        try:
            total_pricing_requests = self.db.query(PricingRequest).count()
        except Exception:
            total_pricing_requests = None

        return {
            "total_products": total_products,
            "active_promotions": active_promotions,
            "expired_promotions": expired_promotions,
            "upcoming_promotions": upcoming_promotions,
            "total_pricing_requests": total_pricing_requests,
        }
