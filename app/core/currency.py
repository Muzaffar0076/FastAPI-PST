from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_UP, ROUND_DOWN, ROUND_HALF_EVEN
from typing import Dict

# Currency exchange rates (base: INR)
# In production, fetch from external API or database
EXCHANGE_RATES: Dict[str, Decimal] = {
    "INR": Decimal("1.0"),
    "USD": Decimal("0.012"),  # 1 INR = 0.012 USD (approximate)
    "EUR": Decimal("0.011"),  # 1 INR = 0.011 EUR (approximate)
    "GBP": Decimal("0.0095"),  # 1 INR = 0.0095 GBP (approximate)
    "AED": Decimal("0.044"),  # 1 INR = 0.044 AED (approximate)
    "SAR": Decimal("0.045"),  # 1 INR = 0.045 SAR (approximate)
}

# Supported currencies
SUPPORTED_CURRENCIES = list(EXCHANGE_RATES.keys())


def convert_currency(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """
    Convert amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (ISO)
        to_currency: Target currency code (ISO)
    
    Returns:
        Converted amount rounded to 2 decimal places
    """
    if from_currency == to_currency:
        return amount
    
    if from_currency not in EXCHANGE_RATES or to_currency not in EXCHANGE_RATES:
        raise ValueError(f"Unsupported currency: {from_currency} or {to_currency}")
    
    # Convert to base currency (INR) first, then to target
    if from_currency != "INR":
        # Convert to INR
        amount_inr = amount / EXCHANGE_RATES[from_currency]
    else:
        amount_inr = amount
    
    # Convert from INR to target
    if to_currency != "INR":
        converted = amount_inr * EXCHANGE_RATES[to_currency]
    else:
        converted = amount_inr
    
    # Round to 2 decimal places
    return converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_tax(amount: Decimal, tax_rate: Decimal, tax_inclusive: bool = False) -> Dict[str, Decimal]:
    """
    Calculate tax amount and final price.
    
    Args:
        amount: Base amount
        tax_rate: Tax rate as percentage (e.g., 18.0 for 18%)
        tax_inclusive: True if amount includes tax
    
    Returns:
        Dictionary with 'base_amount', 'tax_amount', 'total_amount'
    """
    tax_rate_decimal = tax_rate / Decimal("100")
    
    if tax_inclusive:
        # Price includes tax, extract base and tax
        base_amount = amount / (Decimal("1") + tax_rate_decimal)
        tax_amount = amount - base_amount
        total_amount = amount
    else:
        # Price excludes tax, add tax
        base_amount = amount
        tax_amount = amount * tax_rate_decimal
        total_amount = amount + tax_amount
    
    # Round all values to 2 decimal places
    base_amount = base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax_amount = tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_amount = total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    return {
        "base_amount": base_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount
    }


def round_price(amount: Decimal, rounding_strategy: str = "half_up") -> Decimal:
    """
    Round price based on strategy.
    
    Args:
        amount: Amount to round
        rounding_strategy: 'half_up', 'half_down', 'up', 'down', 'nearest'
    
    Returns:
        Rounded amount to 2 decimal places
    """
    rounding_map = {
        "half_up": ROUND_HALF_UP,
        "half_down": ROUND_HALF_DOWN,
        "up": ROUND_UP,
        "down": ROUND_DOWN,
        "nearest": ROUND_HALF_EVEN
    }
    
    rounding = rounding_map.get(rounding_strategy, ROUND_HALF_UP)
    return amount.quantize(Decimal("0.01"), rounding=rounding)




