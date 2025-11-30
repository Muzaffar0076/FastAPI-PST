"""
Simulation API Router
Endpoints for testing promotions without affecting the database.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.simulation_service import (
    simulate_promotion,
    simulate_multiple_promotions,
    compare_scenarios
)
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/simulate", tags=["Simulation"])


class PromotionSimulationRequest(BaseModel):
    product_id: int
    quantity: int
    test_promotion: Dict[str, Any]
    target_currency: Optional[str] = None
    include_tax: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "quantity": 5,
                "test_promotion": {
                    "name": "Test 25% Off",
                    "discount_type": "percentage",
                    "discount_value": 25.0,
                    "min_quantity": 3,
                    "priority": 1,
                    "stacking_enabled": False
                },
                "target_currency": "USD",
                "include_tax": False
            }
        }


class MultiplePromotionSimulationRequest(BaseModel):
    product_id: int
    quantity: int
    test_promotions: List[Dict[str, Any]]
    target_currency: Optional[str] = None
    include_tax: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "quantity": 10,
                "test_promotions": [
                    {
                        "name": "Option A: 20% Off",
                        "discount_type": "percentage",
                        "discount_value": 20.0
                    },
                    {
                        "name": "Option B: Flat ₹500 Off",
                        "discount_type": "flat",
                        "discount_value": 500.0
                    },
                    {
                        "name": "Option C: Buy 3 Get 1",
                        "discount_type": "bogo",
                        "buy_quantity": 3,
                        "get_quantity": 1
                    }
                ]
            }
        }


class ScenarioComparisonRequest(BaseModel):
    product_id: int
    scenarios: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "scenarios": [
                    {
                        "description": "Buy 5 units in INR",
                        "quantity": 5,
                        "currency": "INR"
                    },
                    {
                        "description": "Buy 10 units in INR (bulk)",
                        "quantity": 10,
                        "currency": "INR"
                    },
                    {
                        "description": "Buy 5 units in USD",
                        "quantity": 5,
                        "currency": "USD"
                    }
                ]
            }
        }


@router.post("/promotion")
def simulate_single_promotion(
    data: PromotionSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate a single promotion on a product.

    Test how a promotion would affect pricing without saving it to the database.
    Useful for previewing price changes before creating actual promotions.

    Returns:
    - Current price (without test promotion)
    - Simulated price (with test promotion)
    - Comparison showing savings and percentage difference
    """
    result = simulate_promotion(
        db,
        data.product_id,
        data.quantity,
        data.test_promotion,
        data.target_currency,
        data.include_tax
    )

    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return result


@router.post("/promotion/compare")
def simulate_and_compare_promotions(
    data: MultiplePromotionSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate multiple promotions and find the best option.

    Test several promotion strategies and get a recommendation for which
    one provides the best value for customers.

    Returns:
    - Baseline price (current pricing)
    - Results for each test promotion
    - Best option with maximum savings
    - Recommendation
    """
    result = simulate_multiple_promotions(
        db,
        data.product_id,
        data.quantity,
        data.test_promotions,
        data.target_currency,
        data.include_tax
    )

    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return result


@router.post("/scenarios")
def compare_purchase_scenarios(
    data: ScenarioComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare different purchase scenarios.

    Test how different quantities, currencies, or tax settings affect
    the final price. Useful for bulk purchase analysis and pricing optimization.

    Returns:
    - Results for each scenario
    - Best value scenario (lowest price per unit)
    - Recommendation
    """
    result = compare_scenarios(db, data.product_id, data.scenarios)

    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return result


@router.get("/health")
def simulation_health_check():
    """Health check endpoint for simulation service"""
    return {
        "service": "Simulation Engine",
        "status": "operational",
        "capabilities": [
            "Single promotion simulation",
            "Multiple promotion comparison",
            "Scenario analysis",
            "What-if testing"
        ]
    }
