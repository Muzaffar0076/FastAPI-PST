from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.promotion import Promotion
from app.schemas.promotion import PromotionCreate
from app.services.engine_service import calculate_price_with_explanation
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

def simulate_promotion(db: Session, product_id: int, quantity: int, test_promotion: Dict[str, Any], target_currency: Optional[str]=None, include_tax: Optional[bool]=None) -> Optional[Dict[str, Any]]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    current_result = calculate_price_with_explanation(db, product_id, quantity, target_currency, include_tax)
    from datetime import timedelta
    now = datetime.utcnow()
    temp_promotion = Promotion(name=test_promotion.get('name', 'Test Promotion'), discount_type=test_promotion.get('discount_type', 'percentage'), discount_value=test_promotion.get('discount_value', 0), buy_quantity=test_promotion.get('buy_quantity'), get_quantity=test_promotion.get('get_quantity'), min_quantity=test_promotion.get('min_quantity'), priority=test_promotion.get('priority', 999), stacking_enabled=test_promotion.get('stacking_enabled', False), start_date=now - timedelta(days=1), end_date=now + timedelta(days=7), is_active=True, product_id=product_id)
    original_promotions = product.promotions if hasattr(product, 'promotions') else []
    db.add(temp_promotion)
    db.flush()
    simulated_result = calculate_price_with_explanation(db, product_id, quantity, target_currency, include_tax)
    db.rollback()
    price_difference = current_result['final_price'] - simulated_result['final_price']
    discount_difference = simulated_result['discount_amount'] - current_result['discount_amount']
    return {'simulation': True, 'product_id': product_id, 'quantity': quantity, 'test_promotion': test_promotion, 'current_price': current_result, 'simulated_price': simulated_result, 'comparison': {'price_difference': float(price_difference), 'discount_difference': float(discount_difference), 'savings_percentage': float(price_difference / current_result['final_price'] * 100) if current_result['final_price'] > 0 else 0, 'is_better': price_difference > 0}}

def simulate_multiple_promotions(db: Session, product_id: int, quantity: int, test_promotions: List[Dict[str, Any]], target_currency: Optional[str]=None, include_tax: Optional[bool]=None) -> Optional[Dict[str, Any]]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    baseline = calculate_price_with_explanation(db, product_id, quantity, target_currency, include_tax)
    results = []
    best_option = None
    max_savings = 0
    for idx, test_promo in enumerate(test_promotions):
        simulation = simulate_promotion(db, product_id, quantity, test_promo, target_currency, include_tax)
        if simulation:
            result = {'option_number': idx + 1, 'promotion': test_promo, 'final_price': simulation['simulated_price']['final_price'], 'discount_amount': simulation['simulated_price']['discount_amount'], 'savings': simulation['comparison']['price_difference'], 'savings_percentage': simulation['comparison']['savings_percentage']}
            results.append(result)
            if simulation['comparison']['price_difference'] > max_savings:
                max_savings = simulation['comparison']['price_difference']
                best_option = result
    return {'simulation': True, 'product_id': product_id, 'quantity': quantity, 'baseline_price': baseline['final_price'], 'baseline_discount': baseline['discount_amount'], 'tested_promotions': len(test_promotions), 'results': results, 'best_option': best_option, 'recommendation': f"Option {best_option['option_number']} saves ₹{best_option['savings']:.2f} ({best_option['savings_percentage']:.1f}%)" if best_option else 'No better option found'}

def compare_scenarios(db: Session, product_id: int, scenarios: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    results = []
    for idx, scenario in enumerate(scenarios):
        quantity = scenario.get('quantity', 1)
        currency = scenario.get('currency')
        include_tax = scenario.get('include_tax')
        price_result = calculate_price_with_explanation(db, product_id, quantity, currency, include_tax)
        results.append({'scenario_number': idx + 1, 'description': scenario.get('description', f'Scenario {idx + 1}'), 'quantity': quantity, 'currency': currency or product.currency, 'final_price': price_result['final_price'], 'price_per_unit': price_result['final_price'] / quantity if quantity > 0 else 0, 'discount_amount': price_result['discount_amount'], 'applied_promotions': price_result.get('applied_promotions', [])})
    best_value = min(results, key=lambda x: x['price_per_unit']) if results else None
    return {'product_id': product_id, 'scenarios_tested': len(scenarios), 'results': results, 'best_value_scenario': best_value, 'recommendation': f"{best_value['description']} offers best value at {best_value['currency']} {best_value['price_per_unit']:.2f} per unit" if best_value else 'No scenarios to compare'}