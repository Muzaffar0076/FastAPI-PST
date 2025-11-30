import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


class TestPromotionValidation:

    def test_validate_bogo_without_quantities(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "VAL-001",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        response = client.post("/promotions/", json={
            "name": "Invalid BOGO",
            "discount_type": "bogo",
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "buy_quantity" in response.json()["detail"] or "get_quantity" in response.json()["detail"]

    def test_validate_percentage_without_value(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "VAL-002",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        response = client.post("/promotions/", json={
            "name": "Invalid Percentage",
            "discount_type": "percentage",
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "discount_value" in response.json()["detail"]

    def test_validate_percentage_over_100(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "VAL-003",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        response = client.post("/promotions/", json={
            "name": "Invalid High Percentage",
            "discount_type": "percentage",
            "discount_value": 150.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "100" in response.json()["detail"]

    def test_validate_category_without_filter(self, client: TestClient):
        response = client.post("/promotions/", json={
            "name": "Invalid Category",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "applies_to_category": True,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "category_filter" in response.json()["detail"]

    def test_validate_non_category_without_product(self, client: TestClient):
        response = client.post("/promotions/", json={
            "name": "Invalid Non-Category",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "product_id" in response.json()["detail"]

    def test_validate_duplicate_name(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "VAL-004",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Duplicate Name",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/promotions/", json={
            "name": "Duplicate Name",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_validate_invalid_date_range(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "VAL-005",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        end_date = datetime.utcnow()
        start_date = end_date + timedelta(days=7)

        response = client.post("/promotions/", json={
            "name": "Invalid Date Range",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "before" in response.json()["detail"]

    def test_validation_endpoint(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "VAL-006",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        response = client.post("/promotions/validate", json={
            "name": "Valid Promotion",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert data["valid"] is True

    def test_validation_endpoint_with_errors(self, client: TestClient):
        response = client.post("/promotions/validate", json={
            "name": "Invalid Promotion",
            "discount_type": "percentage",
            "discount_value": 150.0,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


class TestOverlappingPromotions:

    def test_overlapping_promotions_same_priority(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "OVERLAP-001",
            "title": "Test Product",
            "base_price": 1000.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        start1 = datetime.utcnow()
        end1 = start1 + timedelta(days=10)

        client.post("/promotions/", json={
            "name": "First Promotion",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "priority": 1,
            "start_date": start1.isoformat(),
            "end_date": end1.isoformat(),
            "is_active": True
        })

        start2 = start1 + timedelta(days=5)
        end2 = start2 + timedelta(days=10)

        validation_response = client.post("/promotions/validate", json={
            "name": "Second Promotion",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "product_id": product_id,
            "priority": 1,
            "start_date": start2.isoformat(),
            "end_date": end2.isoformat(),
            "is_active": True
        })

        data = validation_response.json()
        assert len(data["warnings"]) > 0
        assert "Overlapping" in data["warnings"][0]

    def test_overlapping_promotions_different_priority(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "OVERLAP-002",
            "title": "Test Product",
            "base_price": 1000.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        start1 = datetime.utcnow()
        end1 = start1 + timedelta(days=10)

        client.post("/promotions/", json={
            "name": "First Promotion Priority 1",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "priority": 1,
            "start_date": start1.isoformat(),
            "end_date": end1.isoformat(),
            "is_active": True
        })

        start2 = start1 + timedelta(days=5)
        end2 = start2 + timedelta(days=10)

        validation_response = client.post("/promotions/validate", json={
            "name": "Second Promotion Priority 0",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "product_id": product_id,
            "priority": 0,
            "start_date": start2.isoformat(),
            "end_date": end2.isoformat(),
            "is_active": True
        })

        data = validation_response.json()
        assert data["valid"] is True


class TestStackingConflicts:

    def test_stackable_with_non_stackable(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "STACK-001",
            "title": "Test Product",
            "base_price": 1000.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        start = datetime.utcnow()
        end = start + timedelta(days=10)

        client.post("/promotions/", json={
            "name": "Non-Stackable Promotion",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "stacking_enabled": False,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "is_active": True
        })

        validation_response = client.post("/promotions/validate", json={
            "name": "Stackable Promotion",
            "discount_type": "percentage",
            "discount_value": 5.0,
            "product_id": product_id,
            "stacking_enabled": True,
            "priority": 1,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "is_active": True
        })

        data = validation_response.json()
        assert len(data["warnings"]) > 0
        assert "non-stackable" in data["warnings"][0].lower()


class TestCategoryValidation:

    def test_overlapping_category_promotions(self, client: TestClient):
        start = datetime.utcnow()
        end = start + timedelta(days=10)

        client.post("/promotions/", json={
            "name": "First Electronics Promo",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "applies_to_category": True,
            "category_filter": "electronics",
            "priority": 1,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "is_active": True
        })

        validation_response = client.post("/promotions/validate", json={
            "name": "Second Electronics Promo",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "applies_to_category": True,
            "category_filter": "electronics",
            "priority": 1,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "is_active": True
        })

        data = validation_response.json()
        assert len(data["warnings"]) > 0


class TestUpdateValidation:

    def test_update_with_duplicate_name(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "UPDATE-001",
            "title": "Test Product",
            "base_price": 1000.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        promo1 = client.post("/promotions/", json={
            "name": "Original Promotion",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        promo2 = client.post("/promotions/", json={
            "name": "Second Promotion",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        promo2_id = promo2.json()["id"]

        response = client.put(f"/promotions/{promo2_id}", json={
            "name": "Original Promotion"
        })

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_own_name_allowed(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "UPDATE-002",
            "title": "Test Product",
            "base_price": 1000.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        promo = client.post("/promotions/", json={
            "name": "My Promotion",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        promo_id = promo.json()["id"]

        response = client.put(f"/promotions/{promo_id}", json={
            "discount_value": 20.0
        })

        assert response.status_code == 200
        assert response.json()["discount_value"] == 20.0


class TestValidationEdgeCases:

    def test_negative_discount_value(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "EDGE-001",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        response = client.post("/promotions/", json={
            "name": "Negative Discount",
            "discount_type": "percentage",
            "discount_value": -10.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
        assert "greater than 0" in response.json()["detail"]

    def test_zero_buy_quantity(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "EDGE-002",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        response = client.post("/promotions/", json={
            "name": "Zero Buy Quantity",
            "discount_type": "bogo",
            "buy_quantity": 0,
            "get_quantity": 1,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400

    def test_negative_min_quantity(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "EDGE-003",
            "title": "Test Product",
            "base_price": 100.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        response = client.post("/promotions/", json={
            "name": "Negative Min Quantity",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "min_quantity": -5,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        assert response.status_code == 400
