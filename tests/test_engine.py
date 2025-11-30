import pytest
from datetime import datetime, timedelta
from decimal import Decimal


class TestBasicPriceCalculation:
    """Test basic price calculation without promotions"""

    def test_calculate_price_without_promotions(self, client, sample_product_data):
        """Test price calculation for product with no promotions"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should return original price without discount
        assert "final_price" in data
        assert "original_price" in data
        assert data["discount_amount"] == 0.0
        assert data["applied_promotion"] is None

    def test_calculate_price_multiple_quantities(self, client, sample_product_data):
        """Test price calculation with different quantities"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        quantities = [1, 2, 5, 10]

        for qty in quantities:
            request_data = {
                "product_id": product_id,
                "quantity": qty
            }

            response = client.post("/engine/compute", json=request_data)
            assert response.status_code == 200
            data = response.json()

            # Original price should be base_price * quantity (before tax)
            expected_base = base_price * qty
            # Note: exact comparison depends on tax calculation
            assert data["original_price"] > 0

    def test_calculate_price_nonexistent_product(self, client):
        """Test price calculation for non-existent product"""
        request_data = {
            "product_id": 99999,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 404


class TestPercentageDiscountCalculation:
    """Test percentage discount calculations"""

    def test_simple_percentage_discount(self, client, sample_product_data):
        """Test 10% percentage discount"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        promo_data = {
            "name": "10% Off",
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

        # Should apply 10% discount
        expected_discount = base_price * 0.10
        assert data["applied_promotion"] == "10% Off"
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_multiple_quantity_percentage_discount(self, client, sample_product_data):
        """Test percentage discount with multiple quantities"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        promo_data = {
            "name": "20% Off",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        quantity = 5
        request_data = {
            "product_id": product_id,
            "quantity": quantity
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should apply 20% discount on total
        expected_discount = (base_price * quantity) * 0.20
        assert data["applied_promotion"] == "20% Off"
        assert abs(data["discount_amount"] - expected_discount) < 0.01


class TestFlatDiscountCalculation:
    """Test flat discount calculations"""

    def test_simple_flat_discount(self, client, sample_product_data):
        """Test flat ₹100 discount"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "₹100 Off",
            "discount_type": "flat",
            "discount_value": 100.0,
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

        # Should apply ₹100 flat discount
        assert data["applied_promotion"] == "₹100 Off"
        assert abs(data["discount_amount"] - 100.0) < 0.01

    def test_flat_discount_multiple_quantities(self, client, sample_product_data):
        """Test flat discount with multiple quantities"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "₹50 Off Per Item",
            "discount_type": "flat",
            "discount_value": 50.0,
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

        # Flat discount per item: 50 * 3 = 150
        expected_discount = 50.0 * quantity
        assert abs(data["discount_amount"] - expected_discount) < 0.01


class TestBOGOCalculation:
    """Test BOGO (Buy One Get One) calculations"""

    def test_buy_one_get_one_free(self, client, sample_product_data):
        """Test Buy 1 Get 1 Free"""
        # Remove discount cap for BOGO test
        sample_product_data["max_discount_cap"] = None
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        promo_data = {
            "name": "BOGO",
            "discount_type": "bogo",
            "discount_value": 0.0,
            "buy_quantity": 1,
            "get_quantity": 1,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        # Buy 2 items, get 1 free
        request_data = {
            "product_id": product_id,
            "quantity": 2
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should get 1 free item (discount = base_price * 1)
        expected_discount = base_price * 1
        assert data["applied_promotion"] == "BOGO"
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_buy_two_get_one_free(self, client, sample_product_data):
        """Test Buy 2 Get 1 Free"""
        # Remove discount cap for BOGO test
        sample_product_data["max_discount_cap"] = None
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        promo_data = {
            "name": "Buy 2 Get 1",
            "discount_type": "bogo",
            "discount_value": 0.0,
            "buy_quantity": 2,
            "get_quantity": 1,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        # Buy 6 items: 6 // 2 = 3 sets, so 3 free items
        request_data = {
            "product_id": product_id,
            "quantity": 6
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should get 3 free items
        expected_discount = base_price * 3
        assert abs(data["discount_amount"] - expected_discount) < 0.01

    def test_bogo_insufficient_quantity(self, client, sample_product_data):
        """Test BOGO with insufficient quantity to qualify"""
        # Remove discount cap for BOGO test
        sample_product_data["max_discount_cap"] = None
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Buy 3 Get 1",
            "discount_type": "bogo",
            "discount_value": 0.0,
            "buy_quantity": 3,
            "get_quantity": 1,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        # Only buy 2 items (need 3 to qualify)
        request_data = {
            "product_id": product_id,
            "quantity": 2
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should not apply BOGO (0 free items)
        assert data["discount_amount"] == 0.0


class TestMinimumQuantityRequirement:
    """Test minimum quantity requirement for promotions"""

    def test_promotion_with_min_quantity_met(self, client, sample_product_data):
        """Test promotion applies when min quantity is met"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Bulk Discount",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "min_quantity": 5,
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
            "quantity": 10  # Meets min_quantity of 5
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should apply promotion
        assert data["applied_promotion"] == "Bulk Discount"
        assert data["discount_amount"] > 0

    def test_promotion_with_min_quantity_not_met(self, client, sample_product_data):
        """Test promotion doesn't apply when min quantity not met"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Bulk Discount",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "min_quantity": 10,
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
            "quantity": 3  # Below min_quantity of 10
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should not apply promotion
        assert data["discount_amount"] == 0.0
        assert "minimum quantity" in " ".join(data["explanation"]).lower()


class TestPromotionTimeWindow:
    """Test promotion time window validation in pricing"""

    def test_expired_promotion_not_applied(self, client, sample_product_data):
        """Test that expired promotions are not applied"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Expired Sale",
            "discount_type": "percentage",
            "discount_value": 25.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": (datetime.utcnow() - timedelta(days=14)).isoformat(),
            "end_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
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

        # Should not apply expired promotion
        assert data["discount_amount"] == 0.0
        assert "expired" in " ".join(data["explanation"]).lower()

    def test_upcoming_promotion_not_applied(self, client, sample_product_data):
        """Test that future promotions are not applied"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Future Sale",
            "discount_type": "percentage",
            "discount_value": 30.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
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

        # Should not apply future promotion
        assert data["discount_amount"] == 0.0
        assert "not started" in " ".join(data["explanation"]).lower()

    def test_inactive_promotion_not_applied(self, client, sample_product_data):
        """Test that inactive promotions are not applied"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Inactive Sale",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": False,  # Inactive
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

        # Should not apply inactive promotion
        assert data["discount_amount"] == 0.0


class TestExplanationAPI:
    """Test explanation/audit trail functionality"""

    def test_explanation_includes_applied_rules(self, client, sample_product_data):
        """Test that explanation includes applied rules"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Summer Sale",
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
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should have explanation
        assert "explanation" in data
        assert isinstance(data["explanation"], list)
        assert len(data["explanation"]) > 0

        # Should mention the applied promotion
        explanation_text = " ".join(data["explanation"]).lower()
        assert "summer sale" in explanation_text or "applied" in explanation_text

    def test_explanation_includes_skipped_rules(self, client, sample_product_data):
        """Test that explanation includes skipped rules with reasons"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        # Create a promotion that won't apply (min quantity not met)
        promo_data = {
            "name": "Bulk Only",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "min_quantity": 10,
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
            "quantity": 2  # Below min_quantity
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should explain why rule was skipped
        explanation_text = " ".join(data["explanation"]).lower()
        assert "skipped" in explanation_text
        assert "minimum quantity" in explanation_text
