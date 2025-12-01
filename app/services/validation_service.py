from sqlalchemy.orm import Session
from app.models.promotion import Promotion
from app.schemas.promotion import PromotionCreate, PromotionUpdate
from typing import List, Dict, Any
from datetime import datetime

class PromotionValidator:

    @staticmethod
    def validate_promotion_data(data: PromotionCreate | PromotionUpdate) -> List[str]:
        errors = []
        is_update = isinstance(data, PromotionUpdate)
        if hasattr(data, 'discount_type') and data.discount_type == 'bogo':
            if not data.buy_quantity or not data.get_quantity:
                errors.append('BOGO promotions require both buy_quantity and get_quantity')
            if data.buy_quantity and data.buy_quantity <= 0:
                errors.append('buy_quantity must be greater than 0')
            if data.get_quantity and data.get_quantity <= 0:
                errors.append('get_quantity must be greater than 0')
        if hasattr(data, 'discount_type') and data.discount_type in ['percentage', 'flat']:
            if data.discount_value is None and (not is_update):
                errors.append(f'{data.discount_type} promotions require discount_value')
            elif data.discount_value is not None and data.discount_value <= 0:
                errors.append('discount_value must be greater than 0')
            elif data.discount_value is not None and data.discount_type == 'percentage' and (data.discount_value > 100):
                errors.append('percentage discount cannot exceed 100%')
        if hasattr(data, 'applies_to_category') and data.applies_to_category and (not data.category_filter):
            errors.append('Category promotions require category_filter')
        if not is_update:
            if not data.applies_to_category and (not data.product_id):
                errors.append('Non-category promotions require product_id')
        if data.min_quantity and data.min_quantity <= 0:
            errors.append('min_quantity must be greater than 0')
        if data.min_amount and data.min_amount <= 0:
            errors.append('min_amount must be greater than 0')
        if hasattr(data, 'start_date') and hasattr(data, 'end_date'):
            if data.start_date and data.end_date and (data.start_date >= data.end_date):
                errors.append('start_date must be before end_date')
        return errors

    @staticmethod
    def check_overlapping_promotions(db: Session, data: PromotionCreate | PromotionUpdate, exclude_id: int | None=None) -> List[str]:
        warnings = []
        query = db.query(Promotion).filter(Promotion.is_active == True)
        if exclude_id:
            query = query.filter(Promotion.id != exclude_id)
        if hasattr(data, 'product_id') and data.product_id:
            query = query.filter(Promotion.product_id == data.product_id)
        elif hasattr(data, 'applies_to_category') and data.applies_to_category and hasattr(data, 'category_filter'):
            if data.category_filter:
                query = query.filter(Promotion.applies_to_category == True, Promotion.category_filter == data.category_filter)
        existing = query.all()
        for promo in existing:
            if hasattr(data, 'start_date') and hasattr(data, 'end_date'):
                if data.start_date and data.end_date:
                    if not (data.end_date < promo.start_date or data.start_date > promo.end_date):
                        if hasattr(data, 'priority') and data.priority == promo.priority:
                            warnings.append(f"Overlapping promotion '{promo.name}' with same priority {promo.priority} from {promo.start_date} to {promo.end_date}")
        return warnings

    @staticmethod
    def check_duplicate_name(db: Session, name: str, exclude_id: int | None=None) -> bool:
        query = db.query(Promotion).filter(Promotion.name == name)
        if exclude_id:
            query = query.filter(Promotion.id != exclude_id)
        return query.first() is not None

    @staticmethod
    def check_stacking_conflicts(db: Session, data: PromotionCreate | PromotionUpdate, exclude_id: int | None=None) -> List[str]:
        warnings = []
        if not hasattr(data, 'stacking_enabled') or not data.stacking_enabled:
            return warnings
        query = db.query(Promotion).filter(Promotion.is_active == True, Promotion.stacking_enabled == False)
        if exclude_id:
            query = query.filter(Promotion.id != exclude_id)
        if hasattr(data, 'product_id') and data.product_id:
            query = query.filter(Promotion.product_id == data.product_id)
        elif hasattr(data, 'applies_to_category') and data.applies_to_category and hasattr(data, 'category_filter'):
            if data.category_filter:
                query = query.filter(Promotion.applies_to_category == True, Promotion.category_filter == data.category_filter)
        non_stackable = query.all()
        if non_stackable:
            for promo in non_stackable:
                if hasattr(data, 'start_date') and hasattr(data, 'end_date'):
                    if data.start_date and data.end_date:
                        if not (data.end_date < promo.start_date or data.start_date > promo.end_date):
                            warnings.append(f"Stackable promotion conflicts with non-stackable promotion '{promo.name}'")
        return warnings

    @staticmethod
    def validate_promotion(db: Session, data: PromotionCreate | PromotionUpdate, exclude_id: int | None=None) -> Dict[str, Any]:
        errors = PromotionValidator.validate_promotion_data(data)
        if hasattr(data, 'name') and data.name:
            if PromotionValidator.check_duplicate_name(db, data.name, exclude_id):
                errors.append(f"Promotion with name '{data.name}' already exists")
        warnings = []
        warnings.extend(PromotionValidator.check_overlapping_promotions(db, data, exclude_id))
        warnings.extend(PromotionValidator.check_stacking_conflicts(db, data, exclude_id))
        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}