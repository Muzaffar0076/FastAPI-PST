import pytest
from datetime import datetime, timedelta
from decimal import Decimal


class TestRulePrecedence:

    def test_higher_priority_promotion_applied_first(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        promo_high = {
            "name": "High Priority 20%",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "priority": 0,
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
            "priority": 5,
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

        expected_discount = base_price * 0.30
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_priority_order_in_explanation(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

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

        explanation_text = " ".join(data["explanation"])
        assert "priority" in explanation_text.lower()


class TestPromotionStacking:

    def test_two_stackable_percentage_promotions(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

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

        assert data["discount_amount"] > 100
        assert "applied_promotions" in data
        assert len(data["applied_promotions"]) == 2

    def test_stackable_and_non_stackable_mix(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

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

        assert "applied_promotions" in data

    def test_three_stackable_promotions(self, client, sample_product_data):
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

        assert "applied_promotions" in data
        assert len(data["applied_promotions"]) == 3

    def test_stacking_flat_discounts(self, client, sample_product_data):
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

        assert data["discount_amount"] >= 80.0


class TestDiscountCap:

    def test_discount_cap_enforced(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        max_cap = sample_product_data["max_discount_cap"]

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

        assert abs(data["discount_amount"] - max_cap) < 0.01

        explanation_text = " ".join(data["explanation"]).lower()
        assert "cap" in explanation_text

    def test_discount_cap_with_multiple_quantities(self, client, sample_product_data):
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

        expected_cap = max_cap_per_unit * quantity
        assert abs(data["discount_amount"] - expected_cap) < 0.01

    def test_discount_below_cap_not_affected(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

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

        expected_discount = base_price * 0.10
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_no_discount_cap_unlimited(self, client, sample_product_data):
        sample_product_data["max_discount_cap"] = None
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

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

        expected_discount = base_price * 0.80
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_stacking_promotions_with_cap(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        max_cap = sample_product_data["max_discount_cap"]

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

        assert data["discount_amount"] <= max_cap + 0.01


class TestComplexScenarios:

    def test_multiple_promotions_best_applied(self, client, sample_product_data):
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        promotions = [
            {"name": "Promo A", "value": 10.0},
            {"name": "Promo B", "value": 25.0},
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

        expected_discount = base_price * 0.25
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_deterministic_pricing(self, client, sample_product_data):
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

        responses = []
        for _ in range(5):
            response = client.post("/engine/compute", json=request_data)
            responses.append(response.json())

        first_price = responses[0]["final_price"]
        first_discount = responses[0]["discount_amount"]

        for resp in responses[1:]:
            assert abs(resp["final_price"] - first_price) < 0.01
            assert abs(resp["discount_amount"] - first_discount) < 0.01
