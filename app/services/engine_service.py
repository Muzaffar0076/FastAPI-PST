from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.promotion import Promotion
from decimal import Decimal
from datetime import datetime

def calculate_price_with_explanation(db: Session, product_id: int, quantity: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    base_price = Decimal(product.price) * quantity
    best_discount = Decimal(0)
    best_promo = None
    explanation = []

    promos = db.query(Promotion).filter(
        Promotion.product_id == product_id,
        Promotion.is_active == True
    ).all()

    for promo in promos:
        discount = Decimal(0)
        reason = ""

        # Check if promotion is active within dates
        now = datetime.utcnow()
        if promo.start_date and promo.start_date > now:
            explanation.append(f"Rule Skipped: {promo.name} - not started yet")
            continue
        if promo.end_date and promo.end_date < now:
            explanation.append(f"Rule Skipped: {promo.name} - expired")
            continue

        # Percentage discount
        if promo.discount_type == "percentage":
            discount = (base_price * Decimal(promo.discount_value / 100))
            reason = f"Applied {promo.discount_value}% discount"

        # Flat discount
        elif promo.discount_type == "flat":
            discount = Decimal(promo.discount_value) * quantity
            reason = f"Applied flat discount of {promo.discount_value} per item"

        # BOGO / Buy X Get Y
        elif promo.discount_type == "bogo":
            if promo.buy_quantity and promo.get_quantity:
                free_items = (quantity // promo.buy_quantity) * promo.get_quantity
                discount = Decimal(product.price) * free_items
                reason = f"Applied BOGO: buy {promo.buy_quantity} get {promo.get_quantity} free"

        # Track best discount
        if discount > best_discount:
            best_discount = discount
            best_promo = promo
            explanation.append(f"Rule Applied: {promo.name} - {reason}")
        else:
            explanation.append(f"Rule Skipped: {promo.name} - lower discount than best applied")

    final_price = base_price - best_discount

    return {
        "original_price": float(base_price),
        "final_price": float(final_price),
        "discount_amount": float(best_discount),
        "applied_promotion": best_promo.name if best_promo else None,
        "explanation": explanation
    }
