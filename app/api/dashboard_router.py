from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.services.dashboard_service import DashboardService
router = APIRouter(prefix='/dashboard', tags=['Dashboard'])

@router.get('/summary', summary='Dashboard summary of products and promotions')
def get_dashboard_summary(db: Session=Depends(get_db)):
    service = DashboardService(db)
    return service.get_summary()