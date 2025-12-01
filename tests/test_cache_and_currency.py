import pytest
from datetime import datetime, timedelta
import time

class TestCacheService:

    def test_price_cached_on_second_request(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Test Promo', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        client.post('/promotions/', json=promo_data)
        request_data = {'product_id': product_id, 'quantity': 1}
        response1 = client.post('/engine/compute', json=request_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1['cached'] is False
        response2 = client.post('/engine/compute', json=request_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['cached'] is True
        assert data1['final_price'] == data2['final_price']
        assert data1['discount_amount'] == data2['discount_amount']

    def test_cache_invalidation_on_product_update(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1}
        response1 = client.post('/engine/compute', json=request_data)
        original_price = response1.json()['final_price']
        update_data = {'base_price': 1500.0}
        client.put(f'/products/{product_id}', json=update_data)
        response2 = client.post('/engine/compute', json=request_data)
        new_price = response2.json()['final_price']
        assert new_price != original_price

    def test_cache_invalidation_on_promotion_update(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Test Promo', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        promo_response = client.post('/promotions/', json=promo_data)
        promo_id = promo_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1}
        response1 = client.post('/engine/compute', json=request_data)
        original_discount = response1.json()['discount_amount']
        update_data = {'discount_value': 20.0}
        client.put(f'/promotions/{promo_id}', json=update_data)
        response2 = client.post('/engine/compute', json=request_data)
        new_discount = response2.json()['discount_amount']
        assert new_discount != original_discount
        assert new_discount > original_discount

    def test_clear_product_cache_endpoint(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1}
        client.post('/engine/compute', json=request_data)
        clear_response = client.delete(f'/engine/cache/product/{product_id}')
        assert clear_response.status_code == 200
        assert 'cleared' in clear_response.json()['message'].lower()
        response = client.post('/engine/compute', json=request_data)
        assert response.json()['cached'] is False

    def test_clear_all_cache_endpoint(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1}
        client.post('/engine/compute', json=request_data)
        clear_response = client.delete('/engine/cache/all')
        assert clear_response.status_code == 200
        response = client.post('/engine/compute', json=request_data)
        assert response.json()['cached'] is False

    def test_different_quantities_cached_separately(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request1 = {'product_id': product_id, 'quantity': 1}
        response1 = client.post('/engine/compute', json=request1)
        assert response1.json()['cached'] is False
        request2 = {'product_id': product_id, 'quantity': 5}
        response2 = client.post('/engine/compute', json=request2)
        assert response2.json()['cached'] is False
        response1_cached = client.post('/engine/compute', json=request1)
        response2_cached = client.post('/engine/compute', json=request2)
        assert response1_cached.json()['cached'] is True
        assert response2_cached.json()['cached'] is True

class TestCurrencyConversion:

    def test_price_in_original_currency(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['currency'] == 'INR'

    def test_price_conversion_to_usd(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1, 'target_currency': 'USD'}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['currency'] == 'USD'
        assert data['final_price'] < 100

    def test_price_conversion_to_eur(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1, 'target_currency': 'EUR'}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['currency'] == 'EUR'

    def test_price_conversion_to_gbp(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1, 'target_currency': 'GBP'}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['currency'] == 'GBP'

    def test_supported_currencies(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        currencies = ['INR', 'USD', 'EUR', 'GBP', 'AED', 'SAR']
        for currency in currencies:
            request_data = {'product_id': product_id, 'quantity': 1, 'target_currency': currency}
            response = client.post('/engine/compute', json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == currency

    def test_currency_conversion_with_discount(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': '10% Off', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        client.post('/promotions/', json=promo_data)
        request_data = {'product_id': product_id, 'quantity': 1, 'target_currency': 'USD'}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['currency'] == 'USD'
        assert data['discount_amount'] > 0

class TestTaxCalculations:

    def test_tax_exclusive_calculation(self, client, sample_product_data):
        sample_product_data['tax_inclusive'] = False
        sample_product_data['tax_rate'] = 18.0
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        base_price = sample_product_data['base_price']
        request_data = {'product_id': product_id, 'quantity': 1}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        expected_tax = base_price * 0.18
        assert data['tax_inclusive'] is False
        assert abs(data['tax_amount'] - expected_tax) < 0.01
        assert data['final_price'] > base_price

    def test_tax_inclusive_calculation(self, client, sample_product_data):
        sample_product_data['tax_inclusive'] = True
        sample_product_data['tax_rate'] = 18.0
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['tax_inclusive'] is True
        assert data['tax_amount'] > 0

    def test_zero_tax_rate(self, client, sample_product_data):
        sample_product_data['tax_rate'] = 0.0
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['tax_amount'] == 0.0

    def test_tax_with_discount(self, client, sample_product_data):
        sample_product_data['tax_rate'] = 18.0
        sample_product_data['tax_inclusive'] = False
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        base_price = sample_product_data['base_price']
        promo_data = {'name': '20% Off', 'discount_type': 'percentage', 'discount_value': 20.0, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        client.post('/promotions/', json=promo_data)
        request_data = {'product_id': product_id, 'quantity': 1}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        price_after_discount = base_price * 0.8
        expected_tax = price_after_discount * 0.18
        assert abs(data['tax_amount'] - expected_tax) < 0.01

    def test_override_tax_inclusive_flag(self, client, sample_product_data):
        sample_product_data['tax_inclusive'] = False
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1, 'include_tax': True}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data['tax_inclusive'] is True

class TestRoundingStrategies:

    def test_half_up_rounding(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1, 'rounding_strategy': 'half_up'}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200

    def test_down_rounding(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1, 'rounding_strategy': 'down'}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200

    def test_up_rounding(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        request_data = {'product_id': product_id, 'quantity': 1, 'rounding_strategy': 'up'}
        response = client.post('/engine/compute', json=request_data)
        assert response.status_code == 200

    def test_all_rounding_strategies(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        strategies = ['half_up', 'half_down', 'up', 'down', 'nearest']
        for strategy in strategies:
            request_data = {'product_id': product_id, 'quantity': 1, 'rounding_strategy': strategy}
            response = client.post('/engine/compute', json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data['final_price'] > 0

class TestDashboardEndpoint:

    def test_dashboard_summary(self, client, sample_product_data):
        client.post('/products/', json=sample_product_data)
        product_2 = sample_product_data.copy()
        product_2['sku'] = 'TEST-002'
        client.post('/products/', json=product_2)
        response = client.get('/dashboard/summary')
        assert response.status_code == 200
        data = response.json()
        assert 'total_products' in data
        assert data['total_products'] >= 2
        assert 'active_promotions' in data
        assert 'expired_promotions' in data
        assert 'upcoming_promotions' in data

    def test_dashboard_counts_active_promotions(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Active Promo', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': 1, 'stacking_enabled': False, 'start_date': (datetime.utcnow() - timedelta(days=1)).isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        client.post('/promotions/', json=promo_data)
        response = client.get('/dashboard/summary')
        assert response.status_code == 200
        data = response.json()
        assert data['active_promotions'] >= 1