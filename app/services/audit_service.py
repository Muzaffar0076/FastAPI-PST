from sqlalchemy.orm import Session
from app.models.audit_log import PriceAuditLog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class AuditService:

    @staticmethod
    def log_price_calculation(db: Session, product_id: int, quantity: int, pricing_result: Dict[str, Any], user_id: Optional[str]=None, ip_address: Optional[str]=None, user_agent: Optional[str]=None, request_id: Optional[str]=None, extra_data: Optional[Dict[str, Any]]=None) -> PriceAuditLog:
        audit_log = PriceAuditLog(product_id=product_id, quantity=quantity, original_price=pricing_result.get('original_price', 0), final_price=pricing_result.get('final_price', 0), discount_amount=pricing_result.get('discount_amount', 0), applied_promotions=pricing_result.get('applied_promotions', []), currency=pricing_result.get('currency', 'INR'), tax_amount=pricing_result.get('tax_amount', 0), tax_rate=pricing_result.get('tax_rate', 0), user_id=user_id, ip_address=ip_address, user_agent=user_agent, request_id=request_id, extra_data=extra_data or {})
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def get_audit_logs(db: Session, product_id: Optional[int]=None, start_date: Optional[datetime]=None, end_date: Optional[datetime]=None, user_id: Optional[str]=None, limit: int=100, offset: int=0) -> List[PriceAuditLog]:
        query = db.query(PriceAuditLog)
        if product_id:
            query = query.filter(PriceAuditLog.product_id == product_id)
        if start_date:
            query = query.filter(PriceAuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(PriceAuditLog.created_at <= end_date)
        if user_id:
            query = query.filter(PriceAuditLog.user_id == user_id)
        query = query.order_by(PriceAuditLog.created_at.desc())
        query = query.offset(offset).limit(limit)
        return query.all()

    @staticmethod
    def get_audit_log(db: Session, log_id: int) -> Optional[PriceAuditLog]:
        return db.query(PriceAuditLog).filter(PriceAuditLog.id == log_id).first()

    @staticmethod
    def get_audit_statistics(db: Session, product_id: Optional[int]=None, start_date: Optional[datetime]=None, end_date: Optional[datetime]=None) -> Dict[str, Any]:
        query = db.query(PriceAuditLog)
        if product_id:
            query = query.filter(PriceAuditLog.product_id == product_id)
        if start_date:
            query = query.filter(PriceAuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(PriceAuditLog.created_at <= end_date)
        logs = query.all()
        if not logs:
            return {'total_calculations': 0, 'total_revenue': 0, 'total_discount': 0, 'avg_discount': 0, 'unique_products': 0, 'period_start': start_date.isoformat() if start_date else None, 'period_end': end_date.isoformat() if end_date else None}
        total_revenue = sum((log.final_price for log in logs))
        total_discount = sum((log.discount_amount for log in logs))
        unique_products = len(set((log.product_id for log in logs)))
        return {'total_calculations': len(logs), 'total_revenue': float(total_revenue), 'total_discount': float(total_discount), 'avg_discount': float(total_discount / len(logs)) if logs else 0, 'unique_products': unique_products, 'period_start': start_date.isoformat() if start_date else None, 'period_end': end_date.isoformat() if end_date else None}

    @staticmethod
    def cleanup_old_logs(db: Session, days: int=90) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(PriceAuditLog).filter(PriceAuditLog.created_at < cutoff_date).delete()
        db.commit()
        return deleted