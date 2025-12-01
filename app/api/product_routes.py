from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import create_product, update_product, delete_product, get_all_products, get_product as get_product_service
router = APIRouter(prefix='/products', tags=['Products'])

@router.post('/', response_model=ProductResponse)
def create(product: ProductCreate, db: Session=Depends(get_db)):
    try:
        return create_product(db, product)
    except IntegrityError:
        raise HTTPException(status_code=400, detail='Product with this SKU already exists')

@router.get('/', response_model=list[ProductResponse])
def list_all(db: Session=Depends(get_db)):
    return get_all_products(db)

@router.get('/{product_id}', response_model=ProductResponse)
def get(product_id: int, db: Session=Depends(get_db)):
    product = get_product_service(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return product

@router.put('/{product_id}', response_model=ProductResponse)
def update(product_id: int, product: ProductUpdate, db: Session=Depends(get_db)):
    updated = update_product(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail='Product not found')
    return updated

@router.delete('/{product_id}')
def delete(product_id: int, db: Session=Depends(get_db)):
    success = delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail='Product not found')
    return {'message': 'Product deleted successfully'}