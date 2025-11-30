import pytest
from datetime import datetime, timedelta
import time


class TestCacheService:
    """Test caching functionality"""

    def test_price_cached_on_second_request(self, client, sample_product_data):
        """Test that price calculation is cached"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Test Promo",
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

        # First request - should not be cached
        response1 = client.post("/engine/compute", json=request_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cached"] is False

        # Second request - should be cached
        response2 = client.post("/engine/compute", json=request_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] is True

        # Results should be identical
        assert data1["final_price"] == data2["final_price"]
        assert data1["discount_amount"] == data2["discount_amount"]

    def test_cache_invalidation_on_product_update(self, client, sample_product_data):
        """Test that cache is invalidated when product is updated"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        # First request
        response1 = client.post("/engine/compute", json=request_data)
        original_price = response1.json()["final_price"]

        # Update product price
        update_data = {"base_price": 1500.00}
        client.put(f"/products/{product_id}", json=update_data)

        # Request again - should use new price (cache invalidated)
        response2 = client.post("/engine/compute", json=request_data)
        new_price = response2.json()["final_price"]

        # Prices should be different
        assert new_price != original_price

    def test_cache_invalidation_on_promotion_update(self, client, sample_product_data):
        """Test that cache is invalidated when promotion is updated"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        promo_data = {
            "name": "Test Promo",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        promo_response = client.post("/promotions/", json=promo_data)
        promo_id = promo_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        # First request
        response1 = client.post("/engine/compute", json=request_data)
        original_discount = response1.json()["discount_amount"]

        # Update promotion
        update_data = {"discount_value": 20.0}
        client.put(f"/promotions/{promo_id}", json=update_data)

        # Request again - should use new discount
        response2 = client.post("/engine/compute", json=request_data)
        new_discount = response2.json()["discount_amount"]

        # Discounts should be different
        assert new_discount != original_discount
        assert new_discount > original_discount

    def test_clear_product_cache_endpoint(self, client, sample_product_data):
        """Test manual cache clearing for specific product"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        # Make request to cache it
        client.post("/engine/compute", json=request_data)

        # Clear cache
        clear_response = client.delete(f"/engine/cache/product/{product_id}")
        assert clear_response.status_code == 200
        assert "cleared" in clear_response.json()["message"].lower()

        # Next request should not be cached
        response = client.post("/engine/compute", json=request_data)
        assert response.json()["cached"] is False

    def test_clear_all_cache_endpoint(self, client, sample_product_data):
        """Test clearing all cache"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        # Make request to cache it
        client.post("/engine/compute", json=request_data)

        # Clear all cache
        clear_response = client.delete("/engine/cache/all")
        assert clear_response.status_code == 200

        # Next request should not be cached
        response = client.post("/engine/compute", json=request_data)
        assert response.json()["cached"] is False

    def test_different_quantities_cached_separately(self, client, sample_product_data):
        """Test that different quantities are cached separately"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        # Request for quantity 1
        request1 = {"product_id": product_id, "quantity": 1}
        response1 = client.post("/engine/compute", json=request1)
        assert response1.json()["cached"] is False

        # Request for quantity 5
        request2 = {"product_id": product_id, "quantity": 5}
        response2 = client.post("/engine/compute", json=request2)
        assert response2.json()["cached"] is False

        # Both should be cached independently
        response1_cached = client.post("/engine/compute", json=request1)
        response2_cached = client.post("/engine/compute", json=request2)
        assert response1_cached.json()["cached"] is True
        assert response2_cached.json()["cached"] is True


class TestCurrencyConversion:
    """Test currency conversion functionality"""

    def test_price_in_original_currency(self, client, sample_product_data):
        """Test price calculation in product's original currency"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "INR"  # Original currency

    def test_price_conversion_to_usd(self, client, sample_product_data):
        """Test converting price to USD"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1,
            "target_currency": "USD"
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "USD"

        # USD price should be lower than INR (approx 83 INR = 1 USD)
        # Original is 1000 INR, so USD should be around 12
        assert data["final_price"] < 100  # Much less than original

    def test_price_conversion_to_eur(self, client, sample_product_data):
        """Test converting price to EUR"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1,
            "target_currency": "EUR"
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "EUR"

    def test_price_conversion_to_gbp(self, client, sample_product_data):
        """Test converting price to GBP"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1,
            "target_currency": "GBP"
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "GBP"

    def test_supported_currencies(self, client, sample_product_data):
        """Test all supported currencies"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        currencies = ["INR", "USD", "EUR", "GBP", "AED", "SAR"]

        for currency in currencies:
            request_data = {
                "product_id": product_id,
                "quantity": 1,
                "target_currency": currency
            }

            response = client.post("/engine/compute", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["currency"] == currency

    def test_currency_conversion_with_discount(self, client, sample_product_data):
        """Test that discounts are correctly applied before currency conversion"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

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
            "quantity": 1,
            "target_currency": "USD"
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Discount should be converted to USD as well
        assert data["currency"] == "USD"
        assert data["discount_amount"] > 0


class TestTaxCalculations:
    """Test tax calculation functionality"""

    def test_tax_exclusive_calculation(self, client, sample_product_data):
        """Test tax-exclusive price calculation"""
        sample_product_data["tax_inclusive"] = False
        sample_product_data["tax_rate"] = 18.0

        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]
        base_price = sample_product_data["base_price"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Tax should be added on top
        expected_tax = base_price * 0.18
        assert data["tax_inclusive"] is False
        assert abs(data["tax_amount"] - expected_tax) < 0.01
        assert data["final_price"] > base_price

    def test_tax_inclusive_calculation(self, client, sample_product_data):
        """Test tax-inclusive price calculation"""
        sample_product_data["tax_inclusive"] = True
        sample_product_data["tax_rate"] = 18.0

        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Tax is already included in base price
        assert data["tax_inclusive"] is True
        assert data["tax_amount"] > 0

    def test_zero_tax_rate(self, client, sample_product_data):
        """Test product with zero tax rate"""
        sample_product_data["tax_rate"] = 0.0

        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert data["tax_amount"] == 0.0

    def test_tax_with_discount(self, client, sample_product_data):
        """Test that tax is calculated after discount"""
        sample_product_data["tax_rate"] = 18.0
        sample_product_data["tax_inclusive"] = False

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

        request_data = {
            "product_id": product_id,
            "quantity": 1
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Tax should be on discounted price
        price_after_discount = base_price * 0.80
        expected_tax = price_after_discount * 0.18
        assert abs(data["tax_amount"] - expected_tax) < 0.01

    def test_override_tax_inclusive_flag(self, client, sample_product_data):
        """Test overriding product's tax_inclusive setting"""
        sample_product_data["tax_inclusive"] = False

        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        # Override to tax_inclusive = True
        request_data = {
            "product_id": product_id,
            "quantity": 1,
            "include_tax": True
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert data["tax_inclusive"] is True


class TestRoundingStrategies:
    """Test different rounding strategies"""

    def test_half_up_rounding(self, client, sample_product_data):
        """Test half_up rounding strategy (default)"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1,
            "rounding_strategy": "half_up"
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200
        # Prices should be rounded to 2 decimal places

    def test_down_rounding(self, client, sample_product_data):
        """Test down rounding strategy"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1,
            "rounding_strategy": "down"
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200

    def test_up_rounding(self, client, sample_product_data):
        """Test up rounding strategy"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        request_data = {
            "product_id": product_id,
            "quantity": 1,
            "rounding_strategy": "up"
        }

        response = client.post("/engine/compute", json=request_data)
        assert response.status_code == 200

    def test_all_rounding_strategies(self, client, sample_product_data):
        """Test all supported rounding strategies"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        strategies = ["half_up", "half_down", "up", "down", "nearest"]

        for strategy in strategies:
            request_data = {
                "product_id": product_id,
                "quantity": 1,
                "rounding_strategy": strategy
            }

            response = client.post("/engine/compute", json=request_data)
            assert response.status_code == 200
            data = response.json()
            # All should return valid prices
            assert data["final_price"] > 0


class TestDashboardEndpoint:
    """Test dashboard summary endpoint"""

    def test_dashboard_summary(self, client, sample_product_data):
        """Test getting dashboard summary"""
        # Create some products
        client.post("/products/", json=sample_product_data)

        product_2 = sample_product_data.copy()
        product_2["sku"] = "TEST-002"
        client.post("/products/", json=product_2)

        response = client.get("/dashboard/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_products" in data
        assert data["total_products"] >= 2
        assert "active_promotions" in data
        assert "expired_promotions" in data
        assert "upcoming_promotions" in data

    def test_dashboard_counts_active_promotions(self, client, sample_product_data):
        """Test dashboard counts active promotions correctly"""
        product_response = client.post("/products/", json=sample_product_data)
        product_id = product_response.json()["id"]

        # Create active promotion
        promo_data = {
            "name": "Active Promo",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "priority": 1,
            "stacking_enabled": False,
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True,
            "product_id": product_id
        }
        client.post("/promotions/", json=promo_data)

        response = client.get("/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["active_promotions"] >= 1
