from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.promotion import Promotion
from decimal import Decimal
from datetime import datetime
from app.core.cache import CacheService
from app.core.currency import convert_currency, calculate_tax, round_price
from typing import Optional, Dict, Any, List

def calculate_price_with_explanation(
    db: Session, 
    product_id: int, 
    quantity: int,
    target_currency: Optional[str] = None,
    include_tax: Optional[bool] = None,
    rounding_strategy: str = "half_up"
) -> Optional[Dict[str, Any]]:
    """
    Calculate price with promotions, caching, currency conversion, and tax handling.
    Implements rule precedence, promotion stacking, and maximum discount caps.
    
    Args:
        db: Database session
        product_id: Product ID
        quantity: Quantity to purchase
        target_currency: Target currency for conversion (ISO code)
        include_tax: Override product tax_inclusive setting
        rounding_strategy: Rounding strategy for final price
    
    Returns:
        Dictionary with pricing details and explanation
    """
    # Generate cache key
    cache_key = CacheService._get_key(
        "price", 
        product_id, 
        quantity, 
        target_currency or "default",
        include_tax if include_tax is not None else "default",
        rounding_strategy
    )
    
    # Try to get from cache
    cached_result = CacheService.get(cache_key)
    if cached_result is not None:
        cached_result["cached"] = True
        return cached_result
    
    # Fetch product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    # Use base_price
    base_price_per_unit = Decimal(str(product.base_price))
    base_price = base_price_per_unit * quantity
    
    # Get max discount cap
    max_discount_cap = None
    if product.max_discount_cap is not None:
        max_discount_cap = Decimal(str(product.max_discount_cap)) * quantity
    
    # Get active promotions and sort by priority (lower number = higher priority, 0 is highest)
    promos = db.query(Promotion).filter(
        Promotion.product_id == product_id,
        Promotion.is_active == True
    ).order_by(Promotion.priority.asc()).all()
    
    explanation = []
    applied_promotions: List[Dict[str, Any]] = []
    total_discount = Decimal(0)
    current_price = base_price  # Price after each promotion is applied
    
    now = datetime.utcnow()
    
    # Evaluate promotions in priority order
    for promo in promos:
        discount = Decimal(0)
        reason = ""
        
        # Check if promotion is active within dates
        if promo.start_date and promo.start_date > now:
            explanation.append(f"Rule Skipped: {promo.name} - not started yet")
            continue
        if promo.end_date and promo.end_date < now:
            explanation.append(f"Rule Skipped: {promo.name} - expired")
            continue
        
        # Check min_quantity requirement
        if promo.min_quantity and quantity < promo.min_quantity:
            explanation.append(f"Rule Skipped: {promo.name} - minimum quantity {promo.min_quantity} required")
            continue
        
        # Calculate discount based on type
        if promo.discount_type == "percentage":
            # Percentage discount applied to current price (after previous discounts if stacking)
            discount = (current_price * Decimal(promo.discount_value / 100))
            reason = f"Applied {promo.discount_value}% discount"
        
        elif promo.discount_type == "flat":
            # Flat discount per item
            discount = Decimal(promo.discount_value) * quantity
            reason = f"Applied flat discount of {promo.discount_value} per item"
        
        elif promo.discount_type == "bogo":
            # BOGO / Buy X Get Y
            if promo.buy_quantity and promo.get_quantity:
                free_items = (quantity // promo.buy_quantity) * promo.get_quantity
                discount = base_price_per_unit * free_items
                reason = f"Applied BOGO: buy {promo.buy_quantity} get {promo.get_quantity} free"
        
        # Apply promotion based on stacking rules
        if discount > 0:
            if promo.stacking_enabled:
                # Stacking enabled: add to total discount
                total_discount += discount
                current_price = base_price - total_discount
                applied_promotions.append({
                    "name": promo.name,
                    "discount": float(discount),
                    "reason": reason,
                    "priority": promo.priority
                })
                explanation.append(f"Rule Applied (Stacked): {promo.name} - {reason} (Priority: {promo.priority})")
            else:
                # No stacking: only apply if this discount is better than current total
                if discount > total_discount:
                    total_discount = discount
                    current_price = base_price - total_discount
                    applied_promotions = [{
                        "name": promo.name,
                        "discount": float(discount),
                        "reason": reason,
                        "priority": promo.priority
                    }]
                    explanation.append(f"Rule Applied: {promo.name} - {reason} (Priority: {promo.priority})")
                else:
                    explanation.append(f"Rule Skipped: {promo.name} - lower discount than current best (Priority: {promo.priority})")
    
    # Apply maximum discount cap if set
    if max_discount_cap is not None and total_discount > max_discount_cap:
        original_discount = total_discount
        total_discount = max_discount_cap
        explanation.append(f"Discount capped: Original discount {float(original_discount)} capped to {float(max_discount_cap)}")
        current_price = base_price - total_discount
    
    # Calculate price after discount
    price_after_discount = base_price - total_discount
    
    # Handle tax
    tax_inclusive = include_tax if include_tax is not None else product.tax_inclusive
    tax_rate = Decimal(str(product.tax_rate))
    
    tax_details = calculate_tax(price_after_discount, tax_rate, tax_inclusive)
    
    # Currency conversion
    product_currency = product.currency or "INR"
    display_currency = target_currency or product_currency
    
    # Convert all amounts to target currency if needed
    if display_currency != product_currency:
        base_amount_converted = convert_currency(tax_details["base_amount"], product_currency, display_currency)
        tax_amount_converted = convert_currency(tax_details["tax_amount"], product_currency, display_currency)
        total_amount_converted = convert_currency(tax_details["total_amount"], product_currency, display_currency)
        discount_converted = convert_currency(total_discount, product_currency, display_currency)
        original_converted = convert_currency(base_price, product_currency, display_currency)
    else:
        base_amount_converted = tax_details["base_amount"]
        tax_amount_converted = tax_details["tax_amount"]
        total_amount_converted = tax_details["total_amount"]
        discount_converted = total_discount
        original_converted = base_price
    
    # Apply rounding strategy
    final_price = round_price(total_amount_converted, rounding_strategy)
    
    # Get primary promotion name (highest priority or first applied)
    primary_promotion = applied_promotions[0]["name"] if applied_promotions else None
    
    result = {
        "original_price": float(round_price(original_converted, rounding_strategy)),
        "base_price_after_discount": float(round_price(base_amount_converted, rounding_strategy)),
        "tax_amount": float(round_price(tax_amount_converted, rounding_strategy)),
        "final_price": float(final_price),
        "discount_amount": float(round_price(discount_converted, rounding_strategy)),
        "applied_promotion": primary_promotion,
        "applied_promotions": applied_promotions,  # List of all applied promotions
        "currency": display_currency,
        "tax_rate": float(tax_rate),
        "tax_inclusive": tax_inclusive,
        "explanation": explanation,
        "cached": False
    }
    
    # Cache the result (TTL: 1 hour)
    CacheService.set(cache_key, result, ttl=3600)
    
    return result
