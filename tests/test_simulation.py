import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

class TestSimulationHealthCheck:

    def test_simulation_health_check(self, client: TestClient):
        response = client.get('/simulate/health')
        assert response.status_code == 200
        data = response.json()
        assert data['service'] == 'Simulation Engine'
        assert data['status'] == 'operational'
        assert 'capabilities' in data
        assert len(data['capabilities']) > 0

class TestSinglePromotionSimulation:

    def test_simulate_percentage_promotion(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-PERCENT-001', 'title': 'Test Product for Simulation', 'base_price': 1000.0, 'stock': 100, 'tax_rate': 18.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        simulation_request = {'product_id': product_id, 'quantity': 5, 'test_promotion': {'name': 'Test 20% Off', 'discount_type': 'percentage', 'discount_value': 20.0, 'min_quantity': 1, 'priority': 1, 'stacking_enabled': False}, 'target_currency': 'INR', 'include_tax': False}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 200
        data = response.json()
        assert data['simulation'] is True
        assert data['product_id'] == product_id
        assert data['quantity'] == 5
        assert 'current_price' in data
        assert 'simulated_price' in data
        assert 'comparison' in data
        assert 'price_difference' in data['comparison']
        assert 'discount_difference' in data['comparison']
        assert 'savings_percentage' in data['comparison']
        assert 'is_better' in data['comparison']
        assert data['current_price']['final_price'] >= 0
        assert data['simulated_price']['final_price'] >= 0

    def test_simulate_flat_discount_promotion(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-FLAT-001', 'title': 'Test Product for Flat Discount', 'base_price': 2000.0, 'stock': 50, 'tax_rate': 10.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        simulation_request = {'product_id': product_id, 'quantity': 3, 'test_promotion': {'name': 'Test Flat ₹300 Off', 'discount_type': 'flat', 'discount_value': 300.0, 'priority': 1}}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 200
        data = response.json()
        assert data['simulation'] is True
        assert 'simulated_price' in data
        assert 'comparison' in data

    def test_simulate_bogo_promotion(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-BOGO-001', 'title': 'Test Product for BOGO', 'base_price': 500.0, 'stock': 100, 'tax_rate': 12.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        simulation_request = {'product_id': product_id, 'quantity': 6, 'test_promotion': {'name': 'Test Buy 2 Get 1 Free', 'discount_type': 'bogo', 'buy_quantity': 2, 'get_quantity': 1, 'priority': 1}}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 200
        data = response.json()
        assert data['simulation'] is True
        assert data['quantity'] == 6
        assert 'simulated_price' in data
        assert 'comparison' in data

    def test_simulate_promotion_with_min_quantity(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-MINQTY-001', 'title': 'Test Product Min Qty', 'base_price': 800.0, 'stock': 100, 'tax_rate': 18.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        simulation_request = {'product_id': product_id, 'quantity': 3, 'test_promotion': {'name': 'Test 15% Off (Min 5)', 'discount_type': 'percentage', 'discount_value': 15.0, 'min_quantity': 5, 'priority': 1}}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 200
        data = response.json()
        assert data['simulation'] is True

    def test_simulate_promotion_nonexistent_product(self, client: TestClient):
        simulation_request = {'product_id': 99999, 'quantity': 5, 'test_promotion': {'name': 'Test Promotion', 'discount_type': 'percentage', 'discount_value': 10.0}}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    def test_simulate_with_currency_conversion(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-CURR-001', 'title': 'Test Product Currency', 'base_price': 1000.0, 'currency': 'INR', 'stock': 50, 'tax_rate': 18.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        simulation_request = {'product_id': product_id, 'quantity': 2, 'test_promotion': {'name': 'Test 10% Off', 'discount_type': 'percentage', 'discount_value': 10.0}, 'target_currency': 'USD'}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 200
        data = response.json()
        assert data['simulation'] is True
        assert 'current_price' in data
        assert 'simulated_price' in data

class TestMultiplePromotionComparison:

    def test_compare_multiple_promotions(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-MULTI-001', 'title': 'Test Product Multiple', 'base_price': 2000.0, 'stock': 100, 'tax_rate': 18.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        comparison_request = {'product_id': product_id, 'quantity': 10, 'test_promotions': [{'name': 'Option A: 20% Off', 'discount_type': 'percentage', 'discount_value': 20.0}, {'name': 'Option B: Flat ₹500 Off', 'discount_type': 'flat', 'discount_value': 500.0}, {'name': 'Option C: Buy 3 Get 1 Free', 'discount_type': 'bogo', 'buy_quantity': 3, 'get_quantity': 1}]}
        response = client.post('/simulate/promotion/compare', json=comparison_request)
        assert response.status_code == 200
        data = response.json()
        assert data['simulation'] is True
        assert data['product_id'] == product_id
        assert data['quantity'] == 10
        assert 'baseline_price' in data
        assert 'baseline_discount' in data
        assert data['tested_promotions'] == 3
        assert 'results' in data
        assert len(data['results']) == 3
        assert 'best_option' in data
        assert 'recommendation' in data
        for result in data['results']:
            assert 'option_number' in result
            assert 'promotion' in result
            assert 'final_price' in result
            assert 'discount_amount' in result
            assert 'savings' in result
            assert 'savings_percentage' in result
        assert len(data['results']) == 3
        for result in data['results']:
            assert result['final_price'] >= 0

    def test_compare_two_promotions(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-TWO-001', 'title': 'Test Product Two Options', 'base_price': 1500.0, 'stock': 50, 'tax_rate': 12.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        comparison_request = {'product_id': product_id, 'quantity': 5, 'test_promotions': [{'name': 'Option 1: 15% Off', 'discount_type': 'percentage', 'discount_value': 15.0}, {'name': 'Option 2: ₹200 Off', 'discount_type': 'flat', 'discount_value': 200.0}]}
        response = client.post('/simulate/promotion/compare', json=comparison_request)
        assert response.status_code == 200
        data = response.json()
        assert data['tested_promotions'] == 2
        assert len(data['results']) == 2
        for result in data['results']:
            assert 'final_price' in result

    def test_compare_promotions_nonexistent_product(self, client: TestClient):
        comparison_request = {'product_id': 99999, 'quantity': 5, 'test_promotions': [{'name': 'Test', 'discount_type': 'percentage', 'discount_value': 10.0}]}
        response = client.post('/simulate/promotion/compare', json=comparison_request)
        assert response.status_code == 404

class TestScenarioComparison:

    def test_compare_quantity_scenarios(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-SCEN-001', 'title': 'Test Product Scenarios', 'base_price': 1000.0, 'stock': 100, 'tax_rate': 18.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        promotion_response = client.post('/promotions/', json={'name': 'Bulk Discount 10%', 'discount_type': 'percentage', 'discount_value': 10.0, 'min_quantity': 10, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id})
        assert promotion_response.status_code == 200
        scenario_request = {'product_id': product_id, 'scenarios': [{'description': 'Buy 5 units', 'quantity': 5, 'currency': 'INR'}, {'description': 'Buy 10 units (bulk discount applies)', 'quantity': 10, 'currency': 'INR'}, {'description': 'Buy 20 units (bulk discount)', 'quantity': 20, 'currency': 'INR'}]}
        response = client.post('/simulate/scenarios', json=scenario_request)
        assert response.status_code == 200
        data = response.json()
        assert data['product_id'] == product_id
        assert data['scenarios_tested'] == 3
        assert 'results' in data
        assert len(data['results']) == 3
        assert 'best_value_scenario' in data
        assert 'recommendation' in data
        for result in data['results']:
            assert 'scenario_number' in result
            assert 'description' in result
            assert 'quantity' in result
            assert 'currency' in result
            assert 'final_price' in result
            assert 'price_per_unit' in result
            assert 'discount_amount' in result
            assert 'applied_promotions' in result
        best_value = data['best_value_scenario']
        assert best_value is not None
        assert 'price_per_unit' in best_value

    def test_compare_currency_scenarios(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-CURR-SCEN-001', 'title': 'Test Product Currency Scenarios', 'base_price': 2000.0, 'currency': 'INR', 'stock': 50, 'tax_rate': 18.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        scenario_request = {'product_id': product_id, 'scenarios': [{'description': 'Buy in INR', 'quantity': 5, 'currency': 'INR'}, {'description': 'Buy in USD', 'quantity': 5, 'currency': 'USD'}, {'description': 'Buy in EUR', 'quantity': 5, 'currency': 'EUR'}]}
        response = client.post('/simulate/scenarios', json=scenario_request)
        assert response.status_code == 200
        data = response.json()
        assert data['scenarios_tested'] == 3
        assert len(data['results']) == 3
        currencies = [result['currency'] for result in data['results']]
        assert 'INR' in currencies
        assert 'USD' in currencies
        assert 'EUR' in currencies

    def test_compare_single_scenario(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-SINGLE-SCEN-001', 'title': 'Test Single Scenario', 'base_price': 1500.0, 'stock': 50, 'tax_rate': 10.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        scenario_request = {'product_id': product_id, 'scenarios': [{'description': 'Standard purchase', 'quantity': 3, 'currency': 'INR'}]}
        response = client.post('/simulate/scenarios', json=scenario_request)
        assert response.status_code == 200
        data = response.json()
        assert data['scenarios_tested'] == 1
        assert len(data['results']) == 1

    def test_compare_scenarios_nonexistent_product(self, client: TestClient):
        scenario_request = {'product_id': 99999, 'scenarios': [{'description': 'Test', 'quantity': 5, 'currency': 'INR'}]}
        response = client.post('/simulate/scenarios', json=scenario_request)
        assert response.status_code == 404

class TestSimulationIntegration:

    def test_simulation_with_existing_promotions(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-EXIST-001', 'title': 'Test Product With Existing Promo', 'base_price': 3000.0, 'stock': 100, 'tax_rate': 18.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        existing_promo_response = client.post('/promotions/', json={'name': 'Existing 10% Off', 'discount_type': 'percentage', 'discount_value': 10.0, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id})
        assert existing_promo_response.status_code == 200
        simulation_request = {'product_id': product_id, 'quantity': 5, 'test_promotion': {'name': 'Test 25% Off', 'discount_type': 'percentage', 'discount_value': 25.0, 'priority': 1}}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 200
        data = response.json()
        assert data['simulation'] is True
        assert 'current_price' in data
        assert 'simulated_price' in data

    def test_simulation_does_not_save_to_database(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SIM-NOSAVE-001', 'title': 'Test No Save', 'base_price': 1000.0, 'stock': 50, 'tax_rate': 12.0})
        assert product_response.status_code == 200
        product_id = product_response.json()['id']
        promotions_before = client.get('/promotions/')
        count_before = len(promotions_before.json())
        simulation_request = {'product_id': product_id, 'quantity': 3, 'test_promotion': {'name': 'Test Simulated Promotion', 'discount_type': 'percentage', 'discount_value': 15.0}}
        response = client.post('/simulate/promotion', json=simulation_request)
        assert response.status_code == 200
        promotions_after = client.get('/promotions/')
        count_after = len(promotions_after.json())
        assert count_before == count_after