import pytest
from decimal import Decimal

class TestProductCRUD:

    def test_create_product(self, client, sample_product_data):
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        data = response.json()
        assert data['sku'] == sample_product_data['sku']
        assert data['title'] == sample_product_data['title']
        assert float(data['base_price']) == sample_product_data['base_price']
        assert data['category'] == sample_product_data['category']
        assert data['stock'] == sample_product_data['stock']
        assert 'id' in data

    def test_create_duplicate_sku(self, client, sample_product_data):
        client.post('/products/', json=sample_product_data)
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail'].lower()

    def test_get_product(self, client, sample_product_data):
        create_response = client.post('/products/', json=sample_product_data)
        product_id = create_response.json()['id']
        response = client.get(f'/products/{product_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == product_id
        assert data['sku'] == sample_product_data['sku']

    def test_get_nonexistent_product(self, client):
        response = client.get('/products/99999')
        assert response.status_code == 404

    def test_get_all_products(self, client, sample_product_data):
        client.post('/products/', json=sample_product_data)
        product_2 = sample_product_data.copy()
        product_2['sku'] = 'TEST-002'
        product_2['title'] = 'Test Product 2'
        client.post('/products/', json=product_2)
        response = client.get('/products/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert isinstance(data, list)

    def test_update_product(self, client, sample_product_data):
        create_response = client.post('/products/', json=sample_product_data)
        product_id = create_response.json()['id']
        update_data = {'title': 'Updated Product Title', 'base_price': 1500.0, 'stock': 50}
        response = client.put(f'/products/{product_id}', json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == update_data['title']
        assert float(data['base_price']) == update_data['base_price']
        assert data['stock'] == update_data['stock']

    def test_update_nonexistent_product(self, client):
        update_data = {'title': 'Should Fail'}
        response = client.put('/products/99999', json=update_data)
        assert response.status_code == 404

    def test_delete_product(self, client, sample_product_data):
        create_response = client.post('/products/', json=sample_product_data)
        product_id = create_response.json()['id']
        response = client.delete(f'/products/{product_id}')
        assert response.status_code == 200
        assert 'deleted' in response.json()['message'].lower()
        get_response = client.get(f'/products/{product_id}')
        assert get_response.status_code == 404

    def test_delete_nonexistent_product(self, client):
        response = client.delete('/products/99999')
        assert response.status_code == 404

class TestProductValidation:

    def test_create_product_missing_required_fields(self, client):
        invalid_data = {'sku': 'TEST-001'}
        response = client.post('/products/', json=invalid_data)
        assert response.status_code == 422

    def test_create_product_invalid_price(self, client, sample_product_data):
        sample_product_data['base_price'] = -100.0
        response = client.post('/products/', json=sample_product_data)

    def test_create_product_invalid_tax_rate(self, client, sample_product_data):
        sample_product_data['tax_rate'] = 150.0
        response = client.post('/products/', json=sample_product_data)

    def test_product_currency_field(self, client, sample_product_data):
        sample_product_data['currency'] = 'USD'
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        assert response.json()['currency'] == 'USD'

    def test_product_with_zero_stock(self, client, sample_product_data):
        sample_product_data['stock'] = 0
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        assert response.json()['stock'] == 0

    def test_product_max_discount_cap(self, client, sample_product_data):
        sample_product_data['max_discount_cap'] = 500.0
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        data = response.json()
        assert float(data['max_discount_cap']) == 500.0

    def test_product_without_max_discount_cap(self, client, sample_product_data):
        sample_product_data['max_discount_cap'] = None
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        data = response.json()
        assert data['max_discount_cap'] is None

class TestProductEdgeCases:

    def test_create_product_with_very_high_price(self, client, sample_product_data):
        sample_product_data['base_price'] = 999999.99
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        assert float(response.json()['base_price']) == 999999.99

    def test_create_product_with_decimal_price(self, client, sample_product_data):
        sample_product_data['base_price'] = 1234.56
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        assert float(response.json()['base_price']) == 1234.56

    def test_product_category_classification(self, client, sample_product_data):
        categories = ['electronics', 'clothing', 'food', 'books']
        for idx, category in enumerate(categories):
            product_data = sample_product_data.copy()
            product_data['sku'] = f'TEST-{idx:03d}'
            product_data['category'] = category
            response = client.post('/products/', json=product_data)
            assert response.status_code == 200
            assert response.json()['category'] == category

    def test_update_product_price_multiple_times(self, client, sample_product_data):
        create_response = client.post('/products/', json=sample_product_data)
        product_id = create_response.json()['id']
        prices = [1000.0, 1200.0, 950.0, 1100.0]
        for price in prices:
            update_data = {'base_price': price}
            response = client.put(f'/products/{product_id}', json=update_data)
            assert response.status_code == 200
            assert float(response.json()['base_price']) == price

    def test_tax_inclusive_flag(self, client, sample_product_data):
        sample_product_data['tax_inclusive'] = True
        response = client.post('/products/', json=sample_product_data)
        assert response.status_code == 200
        assert response.json()['tax_inclusive'] is True
        product_2 = sample_product_data.copy()
        product_2['sku'] = 'TEST-002'
        product_2['tax_inclusive'] = False
        response = client.post('/products/', json=product_2)
        assert response.status_code == 200
        assert response.json()['tax_inclusive'] is False