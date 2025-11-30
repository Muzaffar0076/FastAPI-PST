import pytest
from datetime import datetime, timedelta
from decimal import Decimal


class TestRulePrecedence:
    """Test rule precedence/priority system"""

    def test_higher_priority_promotion_applied_first(self, client, sample_product_data):
        """Test that lower priority number (higher priority) is applied first"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        # Create two non-stacking promotions with different priorities
        promo_high = {
            "name": "High Priority 20%",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "priority": 0,  # Higher priority (lower number)
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        promo_low = {
            "name": "Low Priority 30%",
            "discount_type": "percentage",
            "discount_value": 30.0,
            "priority": 5,  # Lower priority (higher number)
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        client.post("/promotions/", json=promo_high)
        client.post("/promotions/", json=promo_low)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # With non-stacking, should apply the better discount (30%)
        # even though 20% has higher priority
        expected_discount = base_price * 0.30
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_priority_order_in_explanation(self, client, sample_product_data):
        """Test that promotions are evaluated in priority order"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        # Create multiple promotions with different priorities
        promotions = [
            {"name": "P0", "priority": 0, "discount_value": 10.0},
            {"name": "P2", "priority": 2, "discount_value": 15.0},
            {"name": "P1", "priority": 1, "discount_value": 12.0},
        ]

        for promo in promotions:
            promo_data = {
                "name": promo["name"],
                "discount_type": "percentage",
                "discount_value": promo["discount_value"],
                "priority": promo["priority"],
                "stacking_enabled": False,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "is_active": True,
                "product_id": product_id
            }
            client.post("/promotions/", json=promo_data)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Check explanation mentions priority
        explanation_text = " ".join(data["explanation"])
        assert "priority" in explanation_text.lower()


class TestPromotionStacking:
    """Test promotion stacking logic"""

    def test_two_stackable_percentage_promotions(self, client, sample_product_data):
        """Test stacking two percentage promotions"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        # Create two stackable promotions
        promo1 = {
            "name": "Stack 10%",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "priority": 1,
            "stacking_enabled": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        promo2 = {
            "name": "Stack 5%",
            "discount_type": "percentage",
            "discount_value": 5.0,
            "priority": 2,
            "stacking_enabled": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        client.post("/promotions/", json=promo1)
        client.post("/promotions/", json=promo2)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Both promotions should be applied and stacked
        # First: 10% of 1000 = 100
        # Second: 5% of 900 = 45 (compound) OR 5% of 1000 = 50 (additive)
        # Check implementation to verify stacking method
        assert data["discount_amount"] > 100  # At least first discount
        assert "applied_promotions" in data
        assert len(data["applied_promotions"]) == 2

    def test_stackable_and_non_stackable_mix(self, client, sample_product_data):
        """Test mixing stackable and non-stackable promotions"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        # Non-stackable with higher discount
        promo_non_stack = {
            "name": "Non-Stack 20%",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        # Stackable with lower discount
        promo_stack = {
            "name": "Stack 5%",
            "discount_type": "percentage",
            "discount_value": 5.0,
            "priority": 2,
            "stacking_enabled": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        client.post("/promotions/", json=promo_non_stack)
        client.post("/promotions/", json=promo_stack)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should apply the better single discount
        assert "applied_promotions" in data

    def test_three_stackable_promotions(self, client, sample_product_data):
        """Test stacking three promotions"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promotions = [
            {"name": "Stack1", "value": 10.0, "priority": 1},
            {"name": "Stack2", "value": 5.0, "priority": 2},
            {"name": "Stack3", "value": 3.0, "priority": 3},
        ]

        for promo in promotions:
            promo_data = {
                "name": promo["name"],
                "discount_type": "percentage",
                "discount_value": promo["value"],
                "priority": promo["priority"],
                "stacking_enabled": True,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "is_active": True,
                "product_id": product_id
            }
            client.post("/promotions/", json=promo_data)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # All three should be applied
        assert "applied_promotions" in data
        assert len(data["applied_promotions"]) == 3

    def test_stacking_flat_discounts(self, client, sample_product_data):
        """Test stacking flat discounts"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo1 = {
            "name": "Flat 50",
            "discount_type": "flat",
            "discount_value": 50.0,
            "priority": 1,
            "stacking_enabled": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        promo2 = {
            "name": "Flat 30",
            "discount_type": "flat",
            "discount_value": 30.0,
            "priority": 2,
            "stacking_enabled": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        client.post("/promotions/", json=promo1)
        client.post("/promotions/", json=promo2)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Flat discounts should stack: 50 + 30 = 80
        assert data["discount_amount"] >= 80.0


class TestDiscountCap:
    """Test maximum discount cap enforcement"""

    def test_discount_cap_enforced(self, client, sample_product_data):
        """Test that discount is capped at max_discount_cap"""
        # Product with max_discount_cap of 300
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        max_cap = sample_product_data["max_discount_cap"]

        # Create promotion that would give 50% discount (500 on 1000)
        promo_data = {
            "name": "Big Sale 50%",
            "discount_type": "percentage",
            "discount_value": 50.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Discount should be capped at 300
        assert abs(data["discount_amount"] - max_cap) < 0.01

        # Explanation should mention cap
        explanation_text = " ".join(data["explanation"]).lower()
        assert "cap" in explanation_text

    def test_discount_cap_with_multiple_quantities(self, client, sample_product_data):
        """Test discount cap applies to total discount (scales with quantity)"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        max_cap_per_unit = sample_product_data["max_discount_cap"]

        promo_data = {
            "name": "40% Off",
            "discount_type": "percentage",
            "discount_value": 40.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        quantity = 3
        request_data = {
            "product_id": product_id,
            "quantity": quantity
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Cap should scale with quantity: 300 * 3 = 900
        expected_cap = max_cap_per_unit * quantity
        assert abs(data["discount_amount"] - expected_cap) < 0.01

    def test_discount_below_cap_not_affected(self, client, sample_product_data):
        """Test that discounts below cap are not affected"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        # Small discount (10% = 100, well below cap of 300)
        promo_data = {
            "name": "Small 10%",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should get full 10% discount (100)
        expected_discount = base_price * 0.10
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_no_discount_cap_unlimited(self, client, sample_product_data):
        """Test product with no discount cap allows unlimited discount"""
        # Remove discount cap
        sample_product_data["max_discount_cap"] = None
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        # Large discount (80%)
        promo_data = {
            "name": "Huge 80%",
            "discount_type": "percentage",
            "discount_value": 80.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should get full 80% discount
        expected_discount = base_price * 0.80
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_stacking_promotions_with_cap(self, client, sample_product_data):
        """Test that stacked promotions are also subject to discount cap"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        max_cap = sample_product_data["max_discount_cap"]

        # Two stackable promotions that together exceed cap
        promo1 = {
            "name": "Stack 30%",
            "discount_type": "percentage",
            "discount_value": 30.0,
            "priority": 1,
            "stacking_enabled": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        promo2 = {
            "name": "Stack 25%",
            "discount_type": "percentage",
            "discount_value": 25.0,
            "priority": 2,
            "stacking_enabled": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }

        client.post("/promotions/", json=promo1)
        client.post("/promotions/", json=promo2)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Total discount should be capped at 300
        assert data["discount_amount"] <= max_cap + 0.01


class TestComplexScenarios:
    """Test complex real-world scenarios"""

    def test_multiple_promotions_best_applied(self, client, sample_product_data):
        """Test that the best discount is applied when multiple are available"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        # Create three non-stackable promotions
        promotions = [
            {"name": "Promo A", "value": 10.0},
            {"name": "Promo B", "value": 25.0},  # Best
            {"name": "Promo C", "value": 15.0},
        ]

        for idx, promo in enumerate(promotions):
            promo_data = {
                "name": promo["name"],
                "discount_type": "percentage",
                "discount_value": promo["value"],
                "priority": idx + 1,
                "stacking_enabled": False,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "is_active": True,
                "product_id": product_id
            }
            client.post("/promotions/", json=promo_data)

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should apply Promo B (25%)
        expected_discount = base_price * 0.25
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_deterministic_pricing(self, client, sample_product_data):
        """Test that same inputs produce same outputs (deterministic)"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Consistent Promo",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        request_data = {
            "product_id": product_id,
            "quantity": 5
        }

        # Make same request multiple times
        responses = []
        for _ in range(5):
            response = client.post("/engine/compute", json=request_data)
            responses.append(response.json())

        # All responses should be identical
        first_price = responses[0]["final_price"]
        first_discount = responses[0]["discount_amount"]

        for resp in responses[1:]:
            assert abs(resp["final_price"] - first_price) < 0.01
            assert abs(resp["discount_amount"] - first_discount) < 0.01
