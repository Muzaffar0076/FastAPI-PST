from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.engine import PriceRequest
from app.services.engine_service import calculate_price_with_explanation
from app.core.cache import CacheService
import uuid
router = APIRouter(prefix='/engine', tags=['Price Engine'])

@router.post('/compute')
def compute(data: PriceRequest, request: Request, db: Session=Depends(get_db)):
    request_id = str(uuid.uuid4())
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get('user-agent')
    result = calculate_price_with_explanation(db, data.product_id, data.quantity, target_currency=data.target_currency, include_tax=data.include_tax, rounding_strategy=data.rounding_strategy, enable_audit=True, ip_address=client_host, user_agent=user_agent, request_id=request_id)
    if not result:
        raise HTTPException(status_code=404, detail='Product not found')
    return result

@router.delete('/cache/product/{product_id}')
def clear_product_cache(product_id: int):
    count = CacheService.invalidate_product(product_id)
    return {'message': f'Cache cleared for product {product_id}', 'keys_deleted': count}

@router.delete('/cache/all')
def clear_all_cache():
    from app.core.cache import REDIS_AVAILABLE, redis_client, _memory_cache
    try:
        if REDIS_AVAILABLE:
            count = 0
            for key in redis_client.scan_iter(match='price:*'):
                redis_client.delete(key)
                count += 1
            return {'message': 'All cache cleared', 'keys_deleted': count}
        else:
            keys = [k for k in _memory_cache.keys() if k.startswith('price:')]
            for key in keys:
                _memory_cache.pop(key, None)
            return {'message': 'All cache cleared', 'keys_deleted': len(keys)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error clearing cache: {str(e)}')