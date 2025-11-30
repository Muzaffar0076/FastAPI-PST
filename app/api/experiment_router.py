from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import experiment_service
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse
)
from typing import List, Optional

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post("/", response_model=ExperimentResponse)
def create_experiment(data: ExperimentCreate, db: Session = Depends(get_db)):
    existing = experiment_service.get_experiment_by_name(db, data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Experiment with this name already exists")

    experiment = experiment_service.create_experiment(db, data)
    return experiment


@router.get("/", response_model=List[ExperimentResponse])
def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    experiments = experiment_service.get_all_experiments(db, skip, limit)
    return experiments


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = experiment_service.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.put("/{experiment_id}", response_model=ExperimentResponse)
def update_experiment(
    experiment_id: int,
    data: ExperimentUpdate,
    db: Session = Depends(get_db)
):
    experiment = experiment_service.update_experiment(db, experiment_id, data)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    success = experiment_service.delete_experiment(db, experiment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"message": "Experiment deleted successfully"}


@router.post("/{experiment_id}/start", response_model=ExperimentResponse)
def start_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = experiment_service.start_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.post("/{experiment_id}/stop", response_model=ExperimentResponse)
def stop_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = experiment_service.stop_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.post("/{experiment_id}/run")
def run_experiment(
    experiment_id: int,
    product_id: int,
    quantity: int = 1,
    target_currency: Optional[str] = None,
    include_tax: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    result = experiment_service.run_experiment(
        db, experiment_id, product_id, quantity,
        target_currency, include_tax
    )

    if not result:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{experiment_id}/results")
def get_experiment_results(experiment_id: int, db: Session = Depends(get_db)):
    results = experiment_service.get_experiment_results(db, experiment_id)
    if not results:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return results


@router.get("/health/check")
def experiment_health():
    return {
        "service": "Experiment Engine",
        "status": "operational",
        "features": [
            "A/B Testing",
            "Shadow Evaluation",
            "Traffic Splitting",
            "Result Analysis"
        ]
    }
