import pytest
from datetime import datetime, timedelta

class TestPromotionCRUD:

    def test_create_promotion(self, client, sample_product_data, sample_promotion_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        sample_promotion_data['product_id'] = product_id
        response = client.post('/promotions/', json=sample_promotion_data)
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == sample_promotion_data['name']
        assert data['discount_type'] == sample_promotion_data['discount_type']
        assert data['discount_value'] == sample_promotion_data['discount_value']
        assert data['product_id'] == product_id
        assert 'id' in data

    def test_create_promotion_for_nonexistent_product(self, client, sample_promotion_data):
        sample_promotion_data['product_id'] = 99999
        response = client.post('/promotions/', json=sample_promotion_data)
        assert response.status_code in [400, 404, 422]

    def test_get_promotion(self, client, sample_product_data, sample_promotion_data):
        product_response = client.post('/products/', json=sample_product_data)
        sample_promotion_data['product_id'] = product_response.json()['id']
        create_response = client.post('/promotions/', json=sample_promotion_data)
        promotion_id = create_response.json()['id']
        response = client.get(f'/promotions/{promotion_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == promotion_id
        assert data['name'] == sample_promotion_data['name']

    def test_get_nonexistent_promotion(self, client):
        response = client.get('/promotions/99999')
        assert response.status_code == 404

    def test_get_all_promotions(self, client, sample_product_data, sample_promotion_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        sample_promotion_data['product_id'] = product_id
        client.post('/promotions/', json=sample_promotion_data)
        promo_2 = sample_promotion_data.copy()
        promo_2['name'] = 'Second Promotion'
        promo_2['discount_value'] = 15.0
        client.post('/promotions/', json=promo_2)
        response = client.get('/promotions/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert isinstance(data, list)

    def test_update_promotion(self, client, sample_product_data, sample_promotion_data):
        product_response = client.post('/products/', json=sample_product_data)
        sample_promotion_data['product_id'] = product_response.json()['id']
        create_response = client.post('/promotions/', json=sample_promotion_data)
        promotion_id = create_response.json()['id']
        update_data = {'name': 'Updated Promotion', 'discount_value': 20.0, 'is_active': False}
        response = client.put(f'/promotions/{promotion_id}', json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == update_data['name']
        assert data['discount_value'] == update_data['discount_value']
        assert data['is_active'] == update_data['is_active']

    def test_update_nonexistent_promotion(self, client):
        update_data = {'name': 'Should Fail'}
        response = client.put('/promotions/99999', json=update_data)
        assert response.status_code == 404

    def test_delete_promotion(self, client, sample_product_data, sample_promotion_data):
        product_response = client.post('/products/', json=sample_product_data)
        sample_promotion_data['product_id'] = product_response.json()['id']
        create_response = client.post('/promotions/', json=sample_promotion_data)
        promotion_id = create_response.json()['id']
        response = client.delete(f'/promotions/{promotion_id}')
        assert response.status_code == 200
        assert 'deleted' in response.json()['message'].lower()
        get_response = client.get(f'/promotions/{promotion_id}')
        assert get_response.status_code == 404

    def test_delete_nonexistent_promotion(self, client):
        response = client.delete('/promotions/99999')
        assert response.status_code == 404

class TestPromotionTypes:

    def test_percentage_discount_promotion(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': '10% Off', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        assert response.json()['discount_type'] == 'percentage'
        assert response.json()['discount_value'] == 10.0

    def test_flat_discount_promotion(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': '₹100 Off', 'discount_type': 'flat', 'discount_value': 100.0, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        assert response.json()['discount_type'] == 'flat'
        assert response.json()['discount_value'] == 100.0

    def test_bogo_promotion(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Buy 2 Get 1 Free', 'discount_type': 'bogo', 'discount_value': 0.0, 'buy_quantity': 2, 'get_quantity': 1, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        data = response.json()
        assert data['discount_type'] == 'bogo'
        assert data['buy_quantity'] == 2
        assert data['get_quantity'] == 1

class TestPromotionTimeWindow:

    def test_active_promotion_within_timeframe(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Active Promotion', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': 1, 'stacking_enabled': False, 'start_date': (datetime.utcnow() - timedelta(days=1)).isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        assert response.json()['is_active'] is True

    def test_upcoming_promotion(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Upcoming Promotion', 'discount_type': 'percentage', 'discount_value': 15.0, 'priority': 1, 'stacking_enabled': False, 'start_date': (datetime.utcnow() + timedelta(days=1)).isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200

    def test_expired_promotion(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Expired Promotion', 'discount_type': 'percentage', 'discount_value': 20.0, 'priority': 1, 'stacking_enabled': False, 'start_date': (datetime.utcnow() - timedelta(days=14)).isoformat(), 'end_date': (datetime.utcnow() - timedelta(days=1)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200

class TestPromotionPriority:

    def test_create_promotion_with_priority(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        priorities = [0, 1, 2, 5, 10]
        for idx, priority in enumerate(priorities):
            promo_data = {'name': f'Priority {priority} Promotion', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': priority, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
            response = client.post('/promotions/', json=promo_data)
            assert response.status_code == 200
            assert response.json()['priority'] == priority

class TestPromotionStacking:

    def test_stackable_promotion(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Stackable Promotion', 'discount_type': 'percentage', 'discount_value': 10.0, 'priority': 1, 'stacking_enabled': True, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        assert response.json()['stacking_enabled'] is True

    def test_non_stackable_promotion(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Non-Stackable Promotion', 'discount_type': 'percentage', 'discount_value': 15.0, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        assert response.json()['stacking_enabled'] is False

class TestPromotionMinimumQuantity:

    def test_promotion_with_min_quantity(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'Bulk Discount', 'discount_type': 'percentage', 'discount_value': 15.0, 'min_quantity': 5, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        assert response.json()['min_quantity'] == 5

    def test_promotion_without_min_quantity(self, client, sample_product_data):
        product_response = client.post('/products/', json=sample_product_data)
        product_id = product_response.json()['id']
        promo_data = {'name': 'No Min Quantity', 'discount_type': 'percentage', 'discount_value': 10.0, 'min_quantity': None, 'priority': 1, 'stacking_enabled': False, 'start_date': datetime.utcnow().isoformat(), 'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'is_active': True, 'product_id': product_id}
        response = client.post('/promotions/', json=promo_data)
        assert response.status_code == 200
        assert response.json()['min_quantity'] is None