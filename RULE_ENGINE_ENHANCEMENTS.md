# Rule Engine Enhancements

## ✅ Implemented Features (Per PRD Requirements)

### 1. Rule Precedence/Priority ✅
- **Field Added**: `priority` (Integer) in Promotion model
- **Default**: 0
- **Behavior**: Lower number = higher priority (0 is highest priority)
- **Implementation**: Promotions are sorted by priority (ascending) before evaluation
- **Usage**: Promotions with lower priority numbers are evaluated first

### 2. Promotion Stacking ✅
- **Field Added**: `stacking_enabled` (Boolean) in Promotion model
- **Default**: False
- **Behavior**:
  - If `stacking_enabled = True`: Discount is added to total (can combine with other promotions)
  - If `stacking_enabled = False`: Only applies if it's better than current best (mutually exclusive)

### 3. Maximum Discount Caps ✅
- **Field Added**: `max_discount_cap` (Decimal) in Product model
- **Default**: None (no cap)
- **Behavior**: If set, total discount cannot exceed this amount
- **Calculation**: Cap is multiplied by quantity (per-order cap)

---

## 📊 How It Works

### Evaluation Flow:
1. **Fetch & Sort**: Get all active promotions, sort by priority (descending)
2. **Evaluate in Priority Order**:
   - Check date validity
   - Check minimum quantity
   - Calculate discount based on type
   - Apply based on stacking rules:
     - **Stacking enabled**: Add to total discount
     - **Stacking disabled**: Only apply if better than current
3. **Apply Cap**: If `max_discount_cap` is set, enforce it
4. **Calculate Final Price**: Apply tax and currency conversion

### Example Scenarios:

#### Scenario 1: Priority-Based Selection
```
Promotion A: 10% off, priority=5, stacking_enabled=False
Promotion B: 15% off, priority=3, stacking_enabled=False
Result: Promotion B applies (lower priority number = higher priority, even though A has better discount)
```

#### Scenario 2: Stacking
```
Promotion A: 10% off, priority=3, stacking_enabled=True
Promotion B: ₹100 flat, priority=5, stacking_enabled=True
Result: Both apply (10% + ₹100), evaluated in order: A first (priority 3), then B (priority 5)
```

#### Scenario 3: Discount Cap
```
Base Price: ₹1000
Promotion A: 20% off (₹200 discount)
Max Discount Cap: ₹150
Result: Discount capped at ₹150 (not ₹200)
```

---

## 🔧 Database Schema Changes

### Promotion Model:
```python
priority = Column(Integer, default=0, nullable=False)  # Lower number = higher priority (0 is highest)
stacking_enabled = Column(Boolean, default=False, nullable=False)
```

### Product Model:
```python
max_discount_cap = Column(Numeric(10, 2), nullable=True)  # None = no cap
```

---

## 📝 API Response Changes

The `/engine/compute` endpoint now returns:
```json
{
  "applied_promotion": "Primary Promotion Name",  // Highest priority
  "applied_promotions": [  // List of all applied promotions
    {
      "name": "Promotion A",
      "discount": 100.0,
      "reason": "Applied 10% discount",
      "priority": 5
    },
    {
      "name": "Promotion B",
      "discount": 50.0,
      "reason": "Applied flat discount",
      "priority": 3
    }
  ],
  "explanation": [
    "Rule Applied (Stacked): Promotion A - Applied 10% discount (Priority: 5)",
    "Rule Applied (Stacked): Promotion B - Applied flat discount (Priority: 3)",
    "Discount capped: Original discount 200.0 capped to 150.0"
  ]
}
```

---

## 🎯 Usage Examples

### Create Promotion with Priority and Stacking:
```json
POST /promotions/
{
  "name": "VIP Discount",
  "discount_type": "percentage",
  "discount_value": 15.0,
  "priority": 1,  // Lower number = higher priority (0 is highest, 1 is second highest)
  "stacking_enabled": true,
  "min_quantity": 1,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-12-31T23:59:59",
  "is_active": true,
  "product_id": 1
}
```

### Create Product with Discount Cap:
```json
POST /products/
{
  "sku": "PROD001",
  "title": "Laptop",
  "base_price": 50000.00,
  "max_discount_cap": 10000.00,  // Maximum ₹10,000 discount allowed
  "currency": "INR",
  "tax_rate": 18.0,
  "tax_inclusive": false,
  "category": "Electronics",
  "stock": 100
}
```

---

## ✅ PRD Requirements Met

- ✅ **Rule Precedence**: Implemented via `priority` field
- ✅ **Promotion Stacking**: Implemented via `stacking_enabled` field
- ✅ **Maximum Discount Caps**: Implemented via `max_discount_cap` field
- ✅ **Explanation**: Enhanced to show priority and stacking status
- ✅ **Multiple Promotions**: Can now apply multiple promotions when stacking is enabled

---

## 🔄 Migration Notes

**Important**: Existing promotions will have:
- `priority = 0` (default - highest priority)
- `stacking_enabled = False` (default)

Existing products will have:
- `max_discount_cap = None` (no cap)

To update existing data, use the update endpoints:
```bash
PUT /promotions/{id}  # Update priority and stacking
PUT /products/{id}    # Update max_discount_cap
```

---

## 📈 Benefits

1. **Flexibility**: Can combine multiple promotions when needed
2. **Control**: Priority ensures important promotions apply first (lower number = higher priority)
3. **Protection**: Discount caps prevent excessive discounts
4. **Transparency**: Clear explanation of which rules applied and why

## 📌 Priority System Details

- **Priority 0**: Highest priority (evaluated first)
- **Priority 1**: Second highest priority
- **Priority 2**: Third highest priority
- **And so on...**

Lower priority numbers are evaluated before higher priority numbers, ensuring critical promotions are applied first.

