from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.audit_service import AuditService
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
router = APIRouter(prefix='/audit', tags=['Audit Logs'])

class AuditLogResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    original_price: float
    final_price: float
    discount_amount: float
    applied_promotions: List
    currency: str
    tax_amount: float
    tax_rate: float
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    extra_data: dict
    created_at: datetime

    class Config:
        orm_mode = True

@router.get('/logs', response_model=List[AuditLogResponse])
def get_logs(product_id: Optional[int]=Query(None), start_date: Optional[datetime]=Query(None), end_date: Optional[datetime]=Query(None), user_id: Optional[str]=Query(None), limit: int=Query(100, le=1000), offset: int=Query(0, ge=0), db: Session=Depends(get_db)):
    logs = AuditService.get_audit_logs(db, product_id, start_date, end_date, user_id, limit, offset)
    return logs

@router.get('/logs/{log_id}', response_model=AuditLogResponse)
def get_log(log_id: int, db: Session=Depends(get_db)):
    log = AuditService.get_audit_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail='Audit log not found')
    return log

@router.get('/statistics')
def get_statistics(product_id: Optional[int]=Query(None), start_date: Optional[datetime]=Query(None), end_date: Optional[datetime]=Query(None), db: Session=Depends(get_db)):
    stats = AuditService.get_audit_statistics(db, product_id, start_date, end_date)
    return stats

@router.delete('/cleanup')
def cleanup_logs(days: int=Query(90, ge=1, le=365), db: Session=Depends(get_db)):
    deleted = AuditService.cleanup_old_logs(db, days)
    return {'message': f'Deleted {deleted} old audit logs', 'deleted_count': deleted}