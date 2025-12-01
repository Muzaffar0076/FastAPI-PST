import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


class TestAuditLogging:

    def test_price_calculation_creates_audit_log(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "AUDIT-001",
            "title": "Audit Test Product",
            "base_price": 1000.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        promo = client.post("/promotions/", json={
            "name": "Audit Test Promo",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        price_response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 2
        })
        assert price_response.status_code == 200

        logs_response = client.get("/audit/logs")
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert len(logs) > 0

        latest_log = logs[0]
        assert latest_log["product_id"] == product_id
        assert latest_log["quantity"] == 2
        assert latest_log["discount_amount"] > 0

    def test_get_audit_log_by_id(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "AUDIT-002",
            "title": "Audit Test Product 2",
            "base_price": 500.0,
            "stock": 100,
            "tax_rate": 12.0
        })
        product_id = product.json()["id"]

        client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })

        logs_response = client.get("/audit/logs", params={"limit": 1})
        logs = logs_response.json()
        log_id = logs[0]["id"]

        log_response = client.get(f"/audit/logs/{log_id}")
        assert log_response.status_code == 200
        log = log_response.json()
        assert log["id"] == log_id
        assert log["product_id"] == product_id

    def test_get_nonexistent_audit_log(self, client: TestClient):
        response = client.get("/audit/logs/99999")
        assert response.status_code == 404

    def test_filter_logs_by_product(self, client: TestClient):
        product1 = client.post("/products/", json={
            "sku": "AUDIT-FILTER-1",
            "title": "Filter Test 1",
            "base_price": 1000.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product1_id = product1.json()["id"]

        product2 = client.post("/products/", json={
            "sku": "AUDIT-FILTER-2",
            "title": "Filter Test 2",
            "base_price": 2000.0,
            "stock": 30,
            "tax_rate": 12.0
        })
        product2_id = product2.json()["id"]

        client.post("/engine/compute", json={"product_id": product1_id, "quantity": 1})
        client.post("/engine/compute", json={"product_id": product1_id, "quantity": 2})
        client.post("/engine/compute", json={"product_id": product2_id, "quantity": 1})

        logs_response = client.get("/audit/logs", params={"product_id": product1_id})
        logs = logs_response.json()

        assert all(log["product_id"] == product1_id for log in logs)
        assert len([log for log in logs if log["product_id"] == product1_id]) >= 2

    def test_audit_log_contains_metadata(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "AUDIT-META",
            "title": "Metadata Test",
            "base_price": 750.0,
            "stock": 25,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 3
        })

        logs_response = client.get("/audit/logs", params={"limit": 1})
        log = logs_response.json()[0]

        assert "request_id" in log
        assert "ip_address" in log
        assert "user_agent" in log
        assert "created_at" in log

    def test_audit_log_promotion_details(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "AUDIT-PROMO",
            "title": "Promotion Detail Test",
            "base_price": 5000.0,
            "stock": 20,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        promo = client.post("/promotions/", json={
            "name": "Test Audit Promo",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })

        logs_response = client.get("/audit/logs", params={"limit": 1})
        log = logs_response.json()[0]

        assert len(log["applied_promotions"]) > 0
        assert log["applied_promotions"][0]["name"] == "Test Audit Promo"


class TestAuditStatistics:

    def test_get_statistics_no_data(self, client: TestClient):
        future_date = datetime.utcnow() + timedelta(days=365)
        response = client.get("/audit/statistics", params={
            "start_date": future_date.isoformat()
        })

        assert response.status_code == 200
        stats = response.json()
        assert stats["total_calculations"] == 0
        assert stats["total_revenue"] == 0

    def test_get_statistics_with_data(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "STATS-001",
            "title": "Statistics Test",
            "base_price": 1000.0,
            "stock": 100,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        for i in range(5):
            client.post("/engine/compute", json={
                "product_id": product_id,
                "quantity": i + 1
            })

        response = client.get("/audit/statistics")
        assert response.status_code == 200
        stats = response.json()

        assert stats["total_calculations"] >= 5
        assert stats["total_revenue"] > 0
        assert stats["unique_products"] >= 1

    def test_statistics_filtered_by_product(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "STATS-FILTER",
            "title": "Stats Filter Test",
            "base_price": 2000.0,
            "stock": 50,
            "tax_rate": 12.0
        })
        product_id = product.json()["id"]

        for _ in range(3):
            client.post("/engine/compute", json={
                "product_id": product_id,
                "quantity": 2
            })

        response = client.get("/audit/statistics", params={"product_id": product_id})
        stats = response.json()

        assert stats["unique_products"] >= 1


class TestAuditCleanup:

    def test_cleanup_old_logs(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "CLEANUP-001",
            "title": "Cleanup Test",
            "base_price": 500.0,
            "stock": 50,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })

        response = client.delete("/audit/cleanup", params={"days": 1})
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data

    def test_cleanup_validation(self, client: TestClient):
        response = client.delete("/audit/cleanup", params={"days": 500})
        assert response.status_code == 422


class TestAuditPagination:

    def test_pagination_limit(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "PAGE-001",
            "title": "Pagination Test",
            "base_price": 1000.0,
            "stock": 100,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        for _ in range(10):
            client.post("/engine/compute", json={
                "product_id": product_id,
                "quantity": 1
            })

        response = client.get("/audit/logs", params={"limit": 5})
        logs = response.json()
        assert len(logs) <= 5

    def test_pagination_offset(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "PAGE-002",
            "title": "Pagination Offset Test",
            "base_price": 800.0,
            "stock": 50,
            "tax_rate": 12.0
        })
        product_id = product.json()["id"]

        for _ in range(5):
            client.post("/engine/compute", json={
                "product_id": product_id,
                "quantity": 1
            })

        first_page = client.get("/audit/logs", params={
            "product_id": product_id,
            "limit": 2,
            "offset": 0
        }).json()

        second_page = client.get("/audit/logs", params={
            "product_id": product_id,
            "limit": 2,
            "offset": 2
        }).json()

        if len(first_page) > 0 and len(second_page) > 0:
            assert first_page[0]["id"] != second_page[0]["id"]


class TestAuditDateFiltering:

    def test_filter_by_date_range(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "DATE-001",
            "title": "Date Filter Test",
            "base_price": 1500.0,
            "stock": 30,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 1
        })

        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)

        response = client.get("/audit/logs", params={
            "product_id": product_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        })

        logs = response.json()
        assert len(logs) >= 1


class TestAuditIntegrity:

    def test_audit_accuracy(self, client: TestClient):
        product = client.post("/products/", json={
            "sku": "INTEGRITY-001",
            "title": "Integrity Test",
            "base_price": 3000.0,
            "stock": 25,
            "tax_rate": 18.0
        })
        product_id = product.json()["id"]

        promo = client.post("/promotions/", json={
            "name": "Integrity Promo",
            "discount_type": "flat",
            "discount_value": 500.0,
            "product_id": product_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "is_active": True
        })

        price_response = client.post("/engine/compute", json={
            "product_id": product_id,
            "quantity": 2
        })
        price_data = price_response.json()

        logs_response = client.get("/audit/logs", params={"limit": 1})
        log = logs_response.json()[0]

        assert log["original_price"] == price_data["original_price"]
        assert log["final_price"] == price_data["final_price"]
        assert log["discount_amount"] == price_data["discount_amount"]
        assert log["tax_amount"] == price_data["tax_amount"]
