from sqlalchemy.orm import Session
from app.models.experiment import Experiment, ExperimentResult
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate, ExperimentResultCreate
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
from app.services.simulation_service import simulate_promotion
from app.services.engine_service import calculate_price_with_explanation

def create_experiment(db: Session, data: ExperimentCreate) -> Experiment:
    experiment = Experiment(**data.model_dump())
    experiment.status = 'draft'
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment

def get_experiment(db: Session, experiment_id: int) -> Optional[Experiment]:
    return db.query(Experiment).filter(Experiment.id == experiment_id).first()

def get_experiment_by_name(db: Session, name: str) -> Optional[Experiment]:
    return db.query(Experiment).filter(Experiment.name == name).first()

def get_all_experiments(db: Session, skip: int=0, limit: int=100) -> List[Experiment]:
    return db.query(Experiment).offset(skip).limit(limit).all()

def update_experiment(db: Session, experiment_id: int, data: ExperimentUpdate) -> Optional[Experiment]:
    experiment = get_experiment(db, experiment_id)
    if not experiment:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(experiment, key, value)
    experiment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(experiment)
    return experiment

def delete_experiment(db: Session, experiment_id: int) -> bool:
    experiment = get_experiment(db, experiment_id)
    if not experiment:
        return False
    db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment_id).delete()
    db.delete(experiment)
    db.commit()
    return True

def start_experiment(db: Session, experiment_id: int) -> Optional[Experiment]:
    experiment = get_experiment(db, experiment_id)
    if not experiment:
        return None
    experiment.status = 'running'
    experiment.is_active = True
    if not experiment.start_date:
        experiment.start_date = datetime.utcnow()
    db.commit()
    db.refresh(experiment)
    return experiment

def stop_experiment(db: Session, experiment_id: int) -> Optional[Experiment]:
    experiment = get_experiment(db, experiment_id)
    if not experiment:
        return None
    experiment.status = 'completed'
    experiment.is_active = False
    if not experiment.end_date:
        experiment.end_date = datetime.utcnow()
    db.commit()
    db.refresh(experiment)
    return experiment

def assign_variant(experiment: Experiment) -> str:
    random_value = random.random() * 100
    if random_value < experiment.traffic_split:
        return 'control'
    return 'variant'

def run_experiment(db: Session, experiment_id: int, product_id: int, quantity: int, target_currency: Optional[str]=None, include_tax: Optional[bool]=None) -> Dict[str, Any]:
    experiment = get_experiment(db, experiment_id)
    if not experiment:
        return None
    if not experiment.is_active:
        return {'error': 'Experiment is not active', 'experiment_id': experiment_id, 'status': experiment.status}
    assigned_variant = assign_variant(experiment)
    control_result = simulate_promotion(db, product_id, quantity, experiment.control_config, target_currency, include_tax)
    variant_result = simulate_promotion(db, product_id, quantity, experiment.variant_config, target_currency, include_tax)
    if assigned_variant == 'control':
        selected_result = control_result
    else:
        selected_result = variant_result
    result_record = ExperimentResult(experiment_id=experiment_id, variant=assigned_variant, product_id=product_id, quantity=quantity, original_price=selected_result['current_price']['final_price'], final_price=selected_result['simulated_price']['final_price'], discount_amount=selected_result['simulated_price']['discount_amount'], extra_data={'currency': target_currency, 'include_tax': include_tax, 'comparison': selected_result['comparison']})
    db.add(result_record)
    db.commit()
    return {'experiment_id': experiment_id, 'experiment_name': experiment.name, 'assigned_variant': assigned_variant, 'control_result': control_result, 'variant_result': variant_result, 'selected_result': selected_result, 'shadow_evaluation': {'control': control_result['simulated_price']['final_price'], 'variant': variant_result['simulated_price']['final_price'], 'difference': variant_result['simulated_price']['final_price'] - control_result['simulated_price']['final_price']}}

def get_experiment_results(db: Session, experiment_id: int) -> Dict[str, Any]:
    experiment = get_experiment(db, experiment_id)
    if not experiment:
        return None
    results = db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment_id).all()
    if not results:
        return {'experiment_id': experiment_id, 'experiment_name': experiment.name, 'total_observations': 0, 'control': {}, 'variant': {}, 'summary': 'No data collected yet'}
    control_results = [r for r in results if r.variant == 'control']
    variant_results = [r for r in results if r.variant == 'variant']
    control_stats = calculate_variant_stats(control_results)
    variant_stats = calculate_variant_stats(variant_results)
    improvement = 0
    if control_stats['avg_final_price'] > 0:
        improvement = (control_stats['avg_final_price'] - variant_stats['avg_final_price']) / control_stats['avg_final_price'] * 100
    winner = 'variant' if variant_stats['avg_final_price'] < control_stats['avg_final_price'] else 'control'
    return {'experiment_id': experiment_id, 'experiment_name': experiment.name, 'status': experiment.status, 'total_observations': len(results), 'control': {'observations': len(control_results), 'percentage': len(control_results) / len(results) * 100 if results else 0, **control_stats}, 'variant': {'observations': len(variant_results), 'percentage': len(variant_results) / len(results) * 100 if results else 0, **variant_stats}, 'comparison': {'winner': winner, 'improvement_percentage': improvement, 'price_difference': control_stats['avg_final_price'] - variant_stats['avg_final_price']}, 'recommendation': generate_recommendation(control_stats, variant_stats, improvement)}

def calculate_variant_stats(results: List[ExperimentResult]) -> Dict[str, float]:
    if not results:
        return {'avg_original_price': 0, 'avg_final_price': 0, 'avg_discount': 0, 'total_revenue': 0}
    total_original = sum((r.original_price for r in results))
    total_final = sum((r.final_price for r in results))
    total_discount = sum((r.discount_amount for r in results))
    return {'avg_original_price': total_original / len(results), 'avg_final_price': total_final / len(results), 'avg_discount': total_discount / len(results), 'total_revenue': total_final}

def generate_recommendation(control_stats: Dict, variant_stats: Dict, improvement: float) -> str:
    if abs(improvement) < 1:
        return 'No significant difference between variants. More data needed.'
    elif improvement > 0:
        return f'Variant performs {improvement:.2f}% better than control. Consider rolling out variant.'
    else:
        return f'Control performs {abs(improvement):.2f}% better than variant. Keep current setup.'