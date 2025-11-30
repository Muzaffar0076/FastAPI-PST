# Price & Promotions Engine

A FastAPI-based pricing and promotions engine with rule-based pricing, caching, multi-currency support, and tax handling.

## Features

### Core Features
- ✅ CRUD operations for Products and Promotions
- ✅ Rule-based pricing engine (percentage, flat, BOGO discounts)
- ✅ Real-time price calculation with explanations
- ✅ Time-window based promotions
- ✅ Minimum quantity validation

### Week 3 Features (Caching & Currency)
- ✅ **Redis Caching**: High-performance caching for price computations
- ✅ **In-Memory Fallback**: Automatic fallback if Redis is unavailable
- ✅ **Cache Invalidation**: Automatic cache clearing on product/promotion updates
- ✅ **Multi-Currency Support**: Support for INR, USD, EUR, GBP, AED, SAR
- ✅ **Currency Conversion**: Real-time currency conversion in price calculations
- ✅ **Tax Handling**: Support for tax-inclusive and tax-exclusive pricing
- ✅ **Rounding Strategies**: Multiple rounding strategies (half_up, half_down, up, down, nearest)

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: SQLite (default) / PostgreSQL
- **Caching**: Redis (with in-memory fallback)
- **Validation**: Pydantic
- **Currency**: Decimal for precise calculations

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Start Redis server:
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
redis-server
```

3. Set environment variables (optional):
```bash
export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/0"
export CACHE_TTL=3600  # Cache TTL in seconds (default: 1 hour)
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Products
- `POST /products/` - Create product
- `GET /products/` - List all products
- `GET /products/{product_id}` - Get product details
- `PUT /products/{product_id}` - Update product
- `DELETE /products/{product_id}` - Delete product

### Promotions
- `POST /promotions/` - Create promotion
- `GET /promotions/` - List all promotions
- `GET /promotions/{promo_id}` - Get promotion details
- `PUT /promotions/{promo_id}` - Update promotion
- `DELETE /promotions/{promo_id}` - Delete promotion

### Price Engine
- `POST /engine/compute` - Compute final price with promotions
- `DELETE /engine/cache/product/{product_id}` - Clear cache for a product
- `DELETE /engine/cache/all` - Clear all price computation cache

### Dashboard
- `GET /dashboard/summary` - Get summary statistics

## Usage Examples

### Create Product with Currency and Tax
```json
POST /products/
{
  "sku": "PROD001",
  "title": "Laptop",
  "base_price": 50000.00,
  "currency": "INR",
  "tax_rate": 18.0,
  "tax_inclusive": false,
  "category": "Electronics",
  "stock": 100
}
```

### Create Promotion
```json
POST /promotions/
{
  "name": "Summer Sale",
  "discount_type": "percentage",
  "discount_value": 10.0,
  "min_quantity": 1,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-12-31T23:59:59",
  "is_active": true,
  "product_id": 1
}
```

### Compute Price with Currency Conversion
```json
POST /engine/compute
{
  "product_id": 1,
  "quantity": 2,
  "target_currency": "USD",
  "include_tax": true,
  "rounding_strategy": "half_up"
}
```

Response:
```json
{
  "original_price": 100000.0,
  "base_price_after_discount": 90000.0,
  "tax_amount": 16200.0,
  "final_price": 106200.0,
  "discount_amount": 10000.0,
  "applied_promotion": "Summer Sale",
  "currency": "USD",
  "tax_rate": 18.0,
  "tax_inclusive": true,
  "explanation": [
    "Rule Applied: Summer Sale - Applied 10.0% discount"
  ],
  "cached": false
}
```

## Caching

The engine automatically caches price computation results for 1 hour (configurable via `CACHE_TTL`).

- **Cache Key Format**: `price:{product_id}:{quantity}:{currency}:{tax}:{rounding}`
- **Automatic Invalidation**: Cache is automatically cleared when:
  - Product is updated or deleted
  - Promotion is created, updated, or deleted
- **Manual Invalidation**: Use `/engine/cache/product/{product_id}` or `/engine/cache/all`

### Redis vs In-Memory
- If Redis is available, it's used for distributed caching
- If Redis is unavailable, the system automatically falls back to in-memory caching
- No code changes required - the system handles this automatically

## Currency Support

Supported currencies:
- INR (Indian Rupee) - Base currency
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- AED (UAE Dirham)
- SAR (Saudi Riyal)

Exchange rates are stored in `app/core/currency.py`. In production, these should be fetched from an external API or database.

## Tax Handling

Products can be configured with:
- `tax_rate`: Tax percentage (e.g., 18.0 for 18%)
- `tax_inclusive`: Boolean indicating if base_price includes tax

The engine calculates:
- Base amount (before/after tax depending on `tax_inclusive`)
- Tax amount
- Total amount (base + tax)

## Rounding Strategies

Available rounding strategies:
- `half_up`: Round half up (default)
- `half_down`: Round half down
- `up`: Always round up
- `down`: Always round down
- `nearest`: Round to nearest even (banker's rounding)

## Database Schema

### Product
- `id`: Primary key
- `sku`: Unique product identifier
- `title`: Product name
- `base_price`: Base price (Decimal)
- `currency`: ISO currency code (default: INR)
- `tax_rate`: Tax rate percentage (default: 0.0)
- `tax_inclusive`: Whether price includes tax (default: false)
- `category`: Product category
- `stock`: Available stock

### Promotion
- `id`: Primary key
- `name`: Promotion name
- `discount_type`: percentage | flat | bogo
- `discount_value`: Discount amount/percentage
- `buy_quantity`: For BOGO promotions
- `get_quantity`: For BOGO promotions
- `min_quantity`: Minimum quantity required
- `start_date`: Promotion start date
- `end_date`: Promotion end date
- `is_active`: Active status
- `product_id`: Foreign key to Product

## Performance

- **Caching**: Price computations are cached for 1 hour
- **Cache Invalidation**: Automatic on data updates
- **Target Latency**: P95 < 50ms (with caching)
- **Fallback**: In-memory cache if Redis unavailable

## Development

### Running Tests
```bash
pytest
```

### Code Structure
```
app/
├── api/          # API routes
├── core/         # Core utilities (cache, currency)
├── db/           # Database configuration
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic schemas
├── services/     # Business logic
└── tests/        # Test files
```

## Environment Variables

- `DATABASE_URL`: Database connection string (default: `sqlite:///./test.db`)
- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379/0`)
- `CACHE_TTL`: Cache time-to-live in seconds (default: `3600`)

## License

MIT




