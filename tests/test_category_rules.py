"""
Tests for Category-Based Rules
Test promotions that apply to product categories with minimum amount conditions.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


class TestCategoryPromotions:
    """Test category-based promotion rules"""

    def test_category_promotion_applies_to_category(self, client: TestClient):
        """Test that category promotions apply to matching category products"""
        product1 = client.post("/products/", json={
            "sku": "ELEC-001",
            "title": "Laptop",
            "base_price": 50000.0,
            "category": "electronics",
            "stock": 10,
            "tax_rate": 18.0
        })
        product1_id = product1.json()["id"]

        product2 = client.post("/products/", json={
            "sku": "FASH-001",
            "title": "T-Shirt",
            "base_price": 500.0,
            "category": "fashion",
            "stock": 50,
            "tax_rate": 12.0
        })
        product2_id = product2.json()["id"]

        promo_response = client.post("/promotions/", json={
            "name": "Electronics 10% Off",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "applies_to_category": True,
            "category_filter": "electronics",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })
        assert promo_response.status_code == 200

        response1 = client.post("/engine/compute", json={
            "product_id": product1_id,
            "quantity": 1
        })
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["discount_amount"] > 0
        assert len(data1["applied_promotions"]) == 1

        response2 = client.post("/engine/compute", json={
            "product_id": product2_id,
            "quantity": 1
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["discount_amount"] == 0
        assert len(data2["applied_promotions"]) == 0

    def test_category_promotion_with_min_amount(self, client: TestClient):
        """Test category promotion with minimum amount requirement"""
        product1 = client.post("/products/", json={
            "sku": "ELEC-PHONE",
            "title": "Smartphone",
            "base_price": 30000.0,
            "category": "electronics",
            "stock": 20,
            "tax_rate": 18.0
        })
        product1_id = product1.json()["id"]

        product2 = client.post("/products/", json={
            "sku": "ELEC-CHARGER",
            "title": "Phone Charger",
            "base_price": 500.0,
            "category": "electronics",
            "stock": 100,
            "tax_rate": 18.0
        })
        product2_id = product2.json()["id"]

        client.post("/promotions/", json={
            "name": "Electronics Above 5000",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "applies_to_category": True,
            "category_filter": "electronics",
            "min_amount": 5000.0,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response1 = client.post("/engine/compute", json={
            "product_id": product1_id,
            "quantity": 1
        })
        data1 = response1.json()
        assert data1["discount_amount"] > 0

        response2 = client.post("/engine/compute", json={
            "product_id": product2_id,
            "quantity": 1
        })
        data2 = response2.json()
        assert data2["discount_amount"] == 0

    def test_multiple_category_promotions(self, client: TestClient):
        """Test multiple category promotions on same product"""
        product = client.post("/products/", json={
            "sku": "ELEC-TV",
            "title": "Smart TV",
            "base_price": 60000.0,
            "category": "electronics",
            "stock": 5,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Electronics 10% Off",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "applies_to_category": True,
            "category_filter": "electronics",
            "priority": 1,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        client.post("/promotions/", json={
            "name": "Electronics Above 50k - 20% Off",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "applies_to_category": True,
            "category_filter": "electronics",
            "min_amount": 50000.0,
            "priority": 0,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })
        data = response.json()

        assert data["discount_amount"] > 0
        assert data["discount_amount"] == 60000.0 * 0.20

    def test_category_and_product_promotions_combined(self, client: TestClient):
        """Test combining category-based and product-specific promotions"""
        product = client.post("/products/", json={
            "sku": "BOOK-001",
            "title": "Programming Book",
            "base_price": 1000.0,
            "category": "books",
            "stock": 50,
            "tax_rate": 0.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Books Category 10% Off",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "applies_to_category": True,
            "category_filter": "books",
            "priority": 1,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        client.post("/promotions/", json={
            "name": "Product Specific 20% Off",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "product_id": product_id,
            "priority": 0,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })
        data = response.json()

        assert data["discount_amount"] == 200.0

    def test_category_promotion_flat_discount(self, client: TestClient):
        """Test category promotion with flat discount"""
        product = client.post("/products/", json={
            "sku": "FASH-SHOES",
            "title": "Running Shoes",
            "base_price": 5000.0,
            "category": "fashion",
            "stock": 30,
            "tax_rate": 12.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Fashion Flat 500 Off",
            "discount_type": "flat",
            "discount_value": 500.0,
            "applies_to_category": True,
            "category_filter": "fashion",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 2
        })
        data = response.json()

        assert data["discount_amount"] == 1000.0

    def test_category_promotion_bogo(self, client: TestClient):
        """Test category promotion with BOGO"""
        product = client.post("/products/", json={
            "sku": "GROC-CHIPS",
            "title": "Potato Chips",
            "base_price": 50.0,
            "category": "groceries",
            "stock": 200,
            "tax_rate": 5.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Groceries BOGO",
            "discount_type": "bogo",
            "buy_quantity": 2,
            "get_quantity": 1,
            "applies_to_category": True,
            "category_filter": "groceries",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 6
        })
        data = response.json()

        assert data["discount_amount"] == 100.0


class TestCategoryWithMinQuantity:
    """Test category promotions with quantity requirements"""

    def test_category_promotion_min_quantity(self, client: TestClient):
        """Test category promotion with minimum quantity"""
        product = client.post("/products/", json={
            "sku": "STAT-PEN",
            "title": "Ball Pen",
            "base_price": 10.0,
            "category": "stationery",
            "stock": 500,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Bulk Stationery Discount",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "applies_to_category": True,
            "category_filter": "stationery",
            "min_quantity": 10,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response1 = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 5
        })
        data1 = response1.json()
        assert data1["discount_amount"] == 0

        response2 = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 10
        })
        data2 = response2.json()
        assert data2["discount_amount"] == 20.0


class TestCategoryPromotionPriority:
    """Test priority handling for category promotions"""

    def test_category_promotion_priority_order(self, client: TestClient):
        """Test that higher priority category promotions apply first"""
        product = client.post("/products/", json={
            "sku": "HOME-LAMP",
            "title": "Table Lamp",
            "base_price": 2000.0,
            "category": "home",
            "stock": 25,
            "tax_rate": 12.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Home 15% Off",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "applies_to_category": True,
            "category_filter": "home",
            "priority": 1,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        client.post("/promotions/", json={
            "name": "Home Premium 25% Off",
            "discount_type": "percentage",
            "discount_value": 25.0,
            "applies_to_category": True,
            "category_filter": "home",
            "min_amount": 1500.0,
            "priority": 0,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })
        data = response.json()

        assert data["discount_amount"] == 500.0


class TestCategoryPromotionEdgeCases:
    """Test edge cases for category promotions"""

    def test_category_promotion_no_category_product(self, client: TestClient):
        """Test category promotion doesn't apply to product without category"""
        product = client.post("/products/", json={
            "sku": "MISC-001",
            "title": "Miscellaneous Item",
            "base_price": 100.0,
            "stock": 10,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "Category Promo",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "applies_to_category": True,
            "category_filter": "electronics",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })
        data = response.json()
        assert data["discount_amount"] == 0

    def test_category_promotion_case_sensitive(self, client: TestClient):
        """Test category matching is case-sensitive"""
        product = client.post("/products/", json={
            "sku": "BOOK-002",
            "title": "Novel",
            "base_price": 300.0,
            "category": "Books",
            "stock": 40,
            "tax_rate": 0.0
        })
        product_id = product.json()["id"]

        client.post("/promotions/", json={
            "name": "books promo",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "applies_to_category": True,
            "category_filter": "books",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })
        data = response.json()
        assert data["discount_amount"] == 0
