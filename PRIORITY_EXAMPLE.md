# Priority System Example

## Scenario: Multiple Promotions with Priority, Stacking, and Discount Cap

### Setup

**Product:**
```json
{
  "sku": "LAPTOP001",
  "title": "Gaming Laptop",
  "base_price": 50000.00,
  "max_discount_cap": 15000.00,  // Maximum ₹15,000 discount allowed
  "currency": "INR",
  "tax_rate": 18.0,
  "tax_inclusive": false
}
```

**Promotions:**
1. **VIP Discount** - Priority 0 (highest), Stacking: Yes
2. **Seasonal Sale** - Priority 1, Stacking: No
3. **Flash Sale** - Priority 2, Stacking: Yes
4. **Bulk Discount** - Priority 3, Stacking: No

---

## Example 1: Priority-Based Selection (No Stacking)

### Promotions:
```json
[
  {
    "name": "VIP Discount",
    "discount_type": "percentage",
    "discount_value": 10.0,
    "priority": 0,  // Highest priority
    "stacking_enabled": false
  },
  {
    "name": "Seasonal Sale",
    "discount_type": "percentage",
    "discount_value": 15.0,  // Better discount
    "priority": 1,  // Lower priority
    "stacking_enabled": false
  }
]
```

### Calculation:
- Base Price: ₹50,000
- VIP Discount (Priority 0): 10% = ₹5,000 discount
- Seasonal Sale (Priority 1): 15% = ₹7,500 discount

**Result:** VIP Discount applies (Priority 0 is evaluated first, and since stacking is disabled, it wins even though Seasonal Sale has a better discount)

**Final Price:** ₹50,000 - ₹5,000 = ₹45,000

---

## Example 2: Stacking Enabled

### Promotions:
```json
[
  {
    "name": "VIP Discount",
    "discount_type": "percentage",
    "discount_value": 10.0,
    "priority": 0,  // Evaluated first
    "stacking_enabled": true
  },
  {
    "name": "Flash Sale",
    "discount_type": "flat",
    "discount_value": 2000.0,  // ₹2,000 flat discount
    "priority": 2,  // Evaluated third
    "stacking_enabled": true
  },
  {
    "name": "Seasonal Sale",
    "discount_type": "percentage",
    "discount_value": 5.0,
    "priority": 1,  // Evaluated second
    "stacking_enabled": true
  }
]
```

### Calculation (Quantity: 1):
1. **Priority 0 - VIP Discount (10%)**: 
   - Discount: ₹50,000 × 10% = ₹5,000
   - Current Price: ₹50,000 - ₹5,000 = ₹45,000
   - **Applied** (stacking enabled)

2. **Priority 1 - Seasonal Sale (5%)**:
   - Discount: ₹45,000 × 5% = ₹2,250 (applied to current price)
   - Current Price: ₹45,000 - ₹2,250 = ₹42,750
   - **Applied** (stacking enabled)

3. **Priority 2 - Flash Sale (₹2,000 flat)**:
   - Discount: ₹2,000
   - Current Price: ₹42,750 - ₹2,000 = ₹40,750
   - **Applied** (stacking enabled)

**Total Discount:** ₹5,000 + ₹2,250 + ₹2,000 = ₹9,250

**Final Price:** ₹50,000 - ₹9,250 = ₹40,750

---

## Example 3: Discount Cap Enforcement

### Promotions:
```json
[
  {
    "name": "VIP Discount",
    "discount_type": "percentage",
    "discount_value": 20.0,  // 20% = ₹10,000
    "priority": 0,
    "stacking_enabled": true
  },
  {
    "name": "Flash Sale",
    "discount_type": "percentage",
    "discount_value": 15.0,  // 15% = ₹7,500
    "priority": 1,
    "stacking_enabled": true
  }
]
```

### Calculation:
- Base Price: ₹50,000
- Max Discount Cap: ₹15,000

1. **Priority 0 - VIP Discount (20%)**:
   - Discount: ₹50,000 × 20% = ₹10,000
   - Current Price: ₹50,000 - ₹10,000 = ₹40,000
   - **Applied**

2. **Priority 1 - Flash Sale (15%)**:
   - Discount: ₹40,000 × 15% = ₹6,000
   - Total Discount: ₹10,000 + ₹6,000 = ₹16,000
   - **Capped:** ₹16,000 > ₹15,000 cap → Discount reduced to ₹15,000
   - **Applied** (but capped)

**Total Discount:** ₹15,000 (capped from ₹16,000)

**Final Price:** ₹50,000 - ₹15,000 = ₹35,000

---

## Example 4: Mixed Stacking (Some Stack, Some Don't)

### Promotions:
```json
[
  {
    "name": "VIP Discount",
    "discount_type": "percentage",
    "discount_value": 10.0,
    "priority": 0,
    "stacking_enabled": true
  },
  {
    "name": "Seasonal Sale",
    "discount_type": "percentage",
    "discount_value": 15.0,
    "priority": 1,
    "stacking_enabled": false  // Cannot stack
  },
  {
    "name": "Flash Sale",
    "discount_type": "flat",
    "discount_value": 3000.0,
    "priority": 2,
    "stacking_enabled": true
  }
]
```

### Calculation:
1. **Priority 0 - VIP Discount (10%)**:
   - Discount: ₹5,000
   - Current Price: ₹45,000
   - **Applied** (stacking enabled)

2. **Priority 1 - Seasonal Sale (15%)**:
   - Discount: ₹45,000 × 15% = ₹6,750
   - Current Total: ₹5,000
   - Since ₹6,750 > ₹5,000 and stacking is disabled, **replaces** VIP Discount
   - Current Price: ₹50,000 - ₹6,750 = ₹43,250
   - **Applied** (replaces previous)

3. **Priority 2 - Flash Sale (₹3,000 flat)**:
   - Discount: ₹3,000
   - Current Total: ₹6,750
   - Since stacking is enabled, **adds** to total
   - Total Discount: ₹6,750 + ₹3,000 = ₹9,750
   - **Applied** (stacked)

**Total Discount:** ₹9,750

**Final Price:** ₹50,000 - ₹9,750 = ₹40,250

---

## API Request Example

```bash
POST /engine/compute
{
  "product_id": 1,
  "quantity": 2,
  "target_currency": "INR",
  "include_tax": false,
  "rounding_strategy": "half_up"
}
```

## API Response Example

```json
{
  "original_price": 100000.0,
  "base_price_after_discount": 80500.0,
  "tax_amount": 14490.0,
  "final_price": 94990.0,
  "discount_amount": 19500.0,
  "applied_promotion": "VIP Discount",
  "applied_promotions": [
    {
      "name": "VIP Discount",
      "discount": 10000.0,
      "reason": "Applied 10.0% discount",
      "priority": 0
    },
    {
      "name": "Flash Sale",
      "discount": 9500.0,
      "reason": "Applied flat discount of 2000.0 per item",
      "priority": 2
    }
  ],
  "currency": "INR",
  "tax_rate": 18.0,
  "tax_inclusive": false,
  "explanation": [
    "Rule Applied (Stacked): VIP Discount - Applied 10.0% discount (Priority: 0)",
    "Rule Skipped: Seasonal Sale - lower discount than current best (Priority: 1)",
    "Rule Applied (Stacked): Flash Sale - Applied flat discount of 2000.0 per item (Priority: 2)",
    "Discount capped: Original discount 20000.0 capped to 15000.0"
  ],
  "cached": false
}
```

---

## Key Takeaways

1. **Priority 0 = Highest Priority** (evaluated first)
2. **Lower number = Higher priority**
3. **Stacking Enabled**: Discounts combine/add together
4. **Stacking Disabled**: Only the best discount applies (can replace previous)
5. **Discount Cap**: Total discount cannot exceed the cap
6. **Evaluation Order**: Promotions are evaluated in priority order (0, 1, 2, 3...)




