import pytest
from decimal import Decimal


class TestProductCRUD:
    """Test Product CRUD operations"""

    def test_create_product(self, client, sample_product_data):
        """Test creating a new product"""
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == sample_product_data["sku"]
        assert data["title"] == sample_product_data["title"]
        assert float(data["base_price"]) == sample_product_data["base_price"]
        assert data["category"] == sample_product_data["category"]
        assert data["stock"] == sample_product_data["stock"]
        assert "id" in data

    def test_create_duplicate_sku(self, client, sample_product_data):
        """Test creating product with duplicate SKU should fail"""
        client.post("/products/", json=sample_product_data)
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_get_product(self, client, sample_product_data):
        """Test retrieving a product by ID"""
        create_response = client.post("/products/", json=sample_product_data)
        product_id = create_response.json()["id"]

        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["sku"] == sample_product_data["sku"]

    def test_get_nonexistent_product(self, client):
        """Test retrieving non-existent product"""
        response = client.get("/products/99999")
        assert response.status_code == 404

    def test_get_all_products(self, client, sample_product_data):
        """Test retrieving all products"""
        # Create multiple products
        client.post("/products/", json=sample_product_data)

        product_2 = sample_product_data.copy()
        product_2["sku"] = "TEST-002"
        product_2["title"] = "Test Product 2"
        client.post("/products/", json=product_2)

        response = client.get("/products/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert isinstance(data, list)

    def test_update_product(self, client, sample_product_data):
        """Test updating a product"""
        create_response = client.post("/products/", json=sample_product_data)
        product_id = create_response.json()["id"]

        update_data = {
            "title": "Updated Product Title",
            "base_price": 1500.00,
            "stock": 50
        }

        response = client.put(f"/products/{product_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert float(data["base_price"]) == update_data["base_price"]
        assert data["stock"] == update_data["stock"]

    def test_update_nonexistent_product(self, client):
        """Test updating non-existent product"""
        update_data = {"title": "Should Fail"}
        response = client.put("/products/99999", json=update_data)
        assert response.status_code == 404

    def test_delete_product(self, client, sample_product_data):
        """Test deleting a product"""
        create_response = client.post("/products/", json=sample_product_data)
        product_id = create_response.json()["id"]

        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify product is deleted
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_product(self, client):
        """Test deleting non-existent product"""
        response = client.delete("/products/99999")
        assert response.status_code == 404


class TestProductValidation:
    """Test Product data validation"""

    def test_create_product_missing_required_fields(self, client):
        """Test creating product without required fields"""
        invalid_data = {
            "sku": "TEST-001"
            # Missing title and base_price
        }
        response = client.post("/products/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_product_invalid_price(self, client, sample_product_data):
        """Test creating product with negative price"""
        sample_product_data["base_price"] = -100.00
        response = client.post("/products/", json=sample_product_data)
        # Should either reject or accept based on your validation rules
        # Adjust assertion based on your implementation

    def test_create_product_invalid_tax_rate(self, client, sample_product_data):
        """Test creating product with invalid tax rate"""
        sample_product_data["tax_rate"] = 150.0  # More than 100%
        response = client.post("/products/", json=sample_product_data)
        # Should validate tax_rate is between 0-100

    def test_product_currency_field(self, client, sample_product_data):
        """Test product currency field"""
        sample_product_data["currency"] = "USD"
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        assert response.json()["currency"] == "USD"

    def test_product_with_zero_stock(self, client, sample_product_data):
        """Test creating product with zero stock"""
        sample_product_data["stock"] = 0
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        assert response.json()["stock"] == 0

    def test_product_max_discount_cap(self, client, sample_product_data):
        """Test product with max discount cap"""
        sample_product_data["max_discount_cap"] = 500.00
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        data = response.json()
        assert float(data["max_discount_cap"]) == 500.00

    def test_product_without_max_discount_cap(self, client, sample_product_data):
        """Test product without max discount cap (unlimited discount)"""
        sample_product_data["max_discount_cap"] = None
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        data = response.json()
        assert data["max_discount_cap"] is None


class TestProductEdgeCases:
    """Test edge cases and special scenarios"""

    def test_create_product_with_very_high_price(self, client, sample_product_data):
        """Test product with very high price"""
        sample_product_data["base_price"] = 999999.99
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        assert float(response.json()["base_price"]) == 999999.99

    def test_create_product_with_decimal_price(self, client, sample_product_data):
        """Test product with decimal price precision"""
        sample_product_data["base_price"] = 1234.56
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        # Should maintain 2 decimal places
        assert float(response.json()["base_price"]) == 1234.56

    def test_product_category_classification(self, client, sample_product_data):
        """Test different product categories"""
        categories = ["electronics", "clothing", "food", "books"]

        for idx, category in enumerate(categories):
            product_data = sample_product_data.copy()
            product_data["sku"] = f"TEST-{idx:03d}"
            product_data["category"] = category

            response = client.post("/products/", json=product_data)
            assert response.status_code == 200
            assert response.json()["category"] == category

    def test_update_product_price_multiple_times(self, client, sample_product_data):
        """Test updating product price multiple times"""
        create_response = client.post("/products/", json=sample_product_data)
        product_id = create_response.json()["id"]

        prices = [1000.00, 1200.00, 950.00, 1100.00]

        for price in prices:
            update_data = {"base_price": price}
            response = client.put(f"/products/{product_id}", json=update_data)
            assert response.status_code == 200
            assert float(response.json()["base_price"]) == price

    def test_tax_inclusive_flag(self, client, sample_product_data):
        """Test tax_inclusive flag behavior"""
        # Test with tax_inclusive = True
        sample_product_data["tax_inclusive"] = True
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code == 200
        assert response.json()["tax_inclusive"] is True

        # Test with tax_inclusive = False
        product_2 = sample_product_data.copy()
        product_2["sku"] = "TEST-002"
        product_2["tax_inclusive"] = False
        response = client.post("/products/", json=product_2)
        assert response.status_code == 200
        assert response.json()["tax_inclusive"] is False
