from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_UP, ROUND_DOWN, ROUND_HALF_EVEN
from typing import Dict
EXCHANGE_RATES: Dict[str, Decimal] = {'INR': Decimal('1.0'), 'USD': Decimal('0.012'), 'EUR': Decimal('0.011'), 'GBP': Decimal('0.0095'), 'AED': Decimal('0.044'), 'SAR': Decimal('0.045')}
SUPPORTED_CURRENCIES = list(EXCHANGE_RATES.keys())

def convert_currency(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    if from_currency == to_currency:
        return amount
    if from_currency not in EXCHANGE_RATES or to_currency not in EXCHANGE_RATES:
        raise ValueError(f'Unsupported currency: {from_currency} or {to_currency}')
    if from_currency != 'INR':
        amount_inr = amount / EXCHANGE_RATES[from_currency]
    else:
        amount_inr = amount
    if to_currency != 'INR':
        converted = amount_inr * EXCHANGE_RATES[to_currency]
    else:
        converted = amount_inr
    return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_tax(amount: Decimal, tax_rate: Decimal, tax_inclusive: bool=False) -> Dict[str, Decimal]:
    tax_rate_decimal = tax_rate / Decimal('100')
    if tax_inclusive:
        base_amount = amount / (Decimal('1') + tax_rate_decimal)
        tax_amount = amount - base_amount
        total_amount = amount
    else:
        base_amount = amount
        tax_amount = amount * tax_rate_decimal
        total_amount = amount + tax_amount
    base_amount = base_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    tax_amount = tax_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return {'base_amount': base_amount, 'tax_amount': tax_amount, 'total_amount': total_amount}

def round_price(amount: Decimal, rounding_strategy: str='half_up') -> Decimal:
    rounding_map = {'half_up': ROUND_HALF_UP, 'half_down': ROUND_HALF_DOWN, 'up': ROUND_UP, 'down': ROUND_DOWN, 'nearest': ROUND_HALF_EVEN}
    rounding = rounding_map.get(rounding_strategy, ROUND_HALF_UP)
    return amount.quantize(Decimal('0.01'), rounding=rounding)