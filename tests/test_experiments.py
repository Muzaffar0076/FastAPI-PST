import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

class TestExperimentHealthCheck:

    def test_experiment_health_check(self, client: TestClient):
        response = client.get('/experiments/health/check')
        assert response.status_code == 200
        data = response.json()
        assert data['service'] == 'Experiment Engine'
        assert data['status'] == 'operational'
        assert 'features' in data

class TestExperimentCRUD:

    def test_create_experiment(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'EXP-PROD-001', 'title': 'Experiment Product', 'base_price': 1000.0, 'stock': 100, 'tax_rate': 18.0})
        product_id = product_response.json()['id']
        experiment_data = {'name': 'Test Promotion A vs B', 'description': 'Compare 10% vs 15% discount', 'experiment_type': 'promotion_comparison', 'control_config': {'name': '10% Off', 'discount_type': 'percentage', 'discount_value': 10.0}, 'variant_config': {'name': '15% Off', 'discount_type': 'percentage', 'discount_value': 15.0}, 'traffic_split': 50.0, 'product_id': product_id}
        response = client.post('/experiments/', json=experiment_data)
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == experiment_data['name']
        assert data['status'] == 'draft'
        assert data['is_active'] is False
        assert 'id' in data

    def test_create_duplicate_experiment(self, client: TestClient):
        experiment_data = {'name': 'Duplicate Experiment', 'description': 'Test', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}}
        client.post('/experiments/', json=experiment_data)
        response = client.post('/experiments/', json=experiment_data)
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail'].lower()

    def test_get_experiment(self, client: TestClient):
        experiment_data = {'name': 'Get Test Experiment', 'description': 'Test retrieval', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}}
        create_response = client.post('/experiments/', json=experiment_data)
        experiment_id = create_response.json()['id']
        response = client.get(f'/experiments/{experiment_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == experiment_id
        assert data['name'] == experiment_data['name']

    def test_get_nonexistent_experiment(self, client: TestClient):
        response = client.get('/experiments/99999')
        assert response.status_code == 404

    def test_list_experiments(self, client: TestClient):
        for i in range(3):
            client.post('/experiments/', json={'name': f'List Test Experiment {i}', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}})
        response = client.get('/experiments/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_experiment(self, client: TestClient):
        create_response = client.post('/experiments/', json={'name': 'Update Test Experiment', 'description': 'Original description', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}})
        experiment_id = create_response.json()['id']
        update_data = {'description': 'Updated description', 'traffic_split': 70.0}
        response = client.put(f'/experiments/{experiment_id}', json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data['description'] == 'Updated description'
        assert data['traffic_split'] == 70.0

    def test_delete_experiment(self, client: TestClient):
        create_response = client.post('/experiments/', json={'name': 'Delete Test Experiment', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}})
        experiment_id = create_response.json()['id']
        response = client.delete(f'/experiments/{experiment_id}')
        assert response.status_code == 200
        get_response = client.get(f'/experiments/{experiment_id}')
        assert get_response.status_code == 404

class TestExperimentExecution:

    def test_start_experiment(self, client: TestClient):
        create_response = client.post('/experiments/', json={'name': 'Start Test Experiment', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}})
        experiment_id = create_response.json()['id']
        response = client.post(f'/experiments/{experiment_id}/start')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'running'
        assert data['is_active'] is True
        assert data['start_date'] is not None

    def test_stop_experiment(self, client: TestClient):
        create_response = client.post('/experiments/', json={'name': 'Stop Test Experiment', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}})
        experiment_id = create_response.json()['id']
        client.post(f'/experiments/{experiment_id}/start')
        response = client.post(f'/experiments/{experiment_id}/stop')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'completed'
        assert data['is_active'] is False
        assert data['end_date'] is not None

    def test_run_experiment(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'RUN-EXP-001', 'title': 'Run Experiment Product', 'base_price': 2000.0, 'stock': 50, 'tax_rate': 12.0})
        product_id = product_response.json()['id']
        create_response = client.post('/experiments/', json={'name': 'Run Test Experiment', 'control_config': {'name': 'Control 5% Off', 'discount_type': 'percentage', 'discount_value': 5.0}, 'variant_config': {'name': 'Variant 10% Off', 'discount_type': 'percentage', 'discount_value': 10.0}, 'product_id': product_id})
        experiment_id = create_response.json()['id']
        client.post(f'/experiments/{experiment_id}/start')
        response = client.post(f'/experiments/{experiment_id}/run', params={'product_id': product_id, 'quantity': 5})
        assert response.status_code == 200
        data = response.json()
        assert data['experiment_id'] == experiment_id
        assert data['assigned_variant'] in ['control', 'variant']
        assert 'control_result' in data
        assert 'variant_result' in data
        assert 'selected_result' in data
        assert 'shadow_evaluation' in data

    def test_run_inactive_experiment(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'INACTIVE-EXP-001', 'title': 'Inactive Experiment Product', 'base_price': 1500.0, 'stock': 30, 'tax_rate': 18.0})
        product_id = product_response.json()['id']
        create_response = client.post('/experiments/', json={'name': 'Inactive Test Experiment', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}})
        experiment_id = create_response.json()['id']
        response = client.post(f'/experiments/{experiment_id}/run', params={'product_id': product_id, 'quantity': 3})
        assert response.status_code == 400
        assert 'not active' in response.json()['detail'].lower()

class TestExperimentResults:

    def test_get_experiment_results_no_data(self, client: TestClient):
        create_response = client.post('/experiments/', json={'name': 'No Data Experiment', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}})
        experiment_id = create_response.json()['id']
        response = client.get(f'/experiments/{experiment_id}/results')
        assert response.status_code == 200
        data = response.json()
        assert data['total_observations'] == 0
        assert 'No data collected' in data['summary']

    def test_get_experiment_results_with_data(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'RESULTS-EXP-001', 'title': 'Results Experiment Product', 'base_price': 3000.0, 'stock': 100, 'tax_rate': 18.0})
        product_id = product_response.json()['id']
        create_response = client.post('/experiments/', json={'name': 'Results Test Experiment', 'control_config': {'name': 'Control 10% Off', 'discount_type': 'percentage', 'discount_value': 10.0}, 'variant_config': {'name': 'Variant 20% Off', 'discount_type': 'percentage', 'discount_value': 20.0}, 'traffic_split': 50.0, 'product_id': product_id})
        experiment_id = create_response.json()['id']
        client.post(f'/experiments/{experiment_id}/start')
        for _ in range(10):
            client.post(f'/experiments/{experiment_id}/run', params={'product_id': product_id, 'quantity': 2})
        response = client.get(f'/experiments/{experiment_id}/results')
        assert response.status_code == 200
        data = response.json()
        assert data['total_observations'] == 10
        assert 'control' in data
        assert 'variant' in data
        assert 'comparison' in data
        assert data['control']['observations'] + data['variant']['observations'] == 10
        assert 'winner' in data['comparison']
        assert 'improvement_percentage' in data['comparison']
        assert 'recommendation' in data

class TestShadowEvaluation:

    def test_shadow_evaluation_price_comparison(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SHADOW-001', 'title': 'Shadow Eval Product', 'base_price': 5000.0, 'stock': 50, 'tax_rate': 18.0})
        product_id = product_response.json()['id']
        create_response = client.post('/experiments/', json={'name': 'Shadow Eval Test', 'control_config': {'name': 'Control 15% Off', 'discount_type': 'percentage', 'discount_value': 15.0}, 'variant_config': {'name': 'Variant 25% Off', 'discount_type': 'percentage', 'discount_value': 25.0}, 'product_id': product_id})
        experiment_id = create_response.json()['id']
        client.post(f'/experiments/{experiment_id}/start')
        response = client.post(f'/experiments/{experiment_id}/run', params={'product_id': product_id, 'quantity': 1})
        data = response.json()
        shadow = data['shadow_evaluation']
        assert 'control' in shadow
        assert 'variant' in shadow
        assert 'difference' in shadow
        assert shadow['control'] >= 0
        assert shadow['variant'] >= 0
        assert shadow['difference'] == shadow['variant'] - shadow['control']

class TestTrafficSplit:

    def test_traffic_split_distribution(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'SPLIT-001', 'title': 'Split Test Product', 'base_price': 1000.0, 'stock': 200, 'tax_rate': 12.0})
        product_id = product_response.json()['id']
        create_response = client.post('/experiments/', json={'name': 'Traffic Split Test', 'control_config': {'name': 'Control'}, 'variant_config': {'name': 'Variant'}, 'traffic_split': 70.0, 'product_id': product_id})
        experiment_id = create_response.json()['id']
        client.post(f'/experiments/{experiment_id}/start')
        control_count = 0
        variant_count = 0
        runs = 100
        for _ in range(runs):
            response = client.post(f'/experiments/{experiment_id}/run', params={'product_id': product_id, 'quantity': 1})
            if response.json()['assigned_variant'] == 'control':
                control_count += 1
            else:
                variant_count += 1
        control_percentage = control_count / runs * 100
        assert 50 < control_percentage < 90

class TestExperimentIntegration:

    def test_complete_experiment_workflow(self, client: TestClient):
        product_response = client.post('/products/', json={'sku': 'WORKFLOW-001', 'title': 'Workflow Test Product', 'base_price': 2500.0, 'stock': 100, 'tax_rate': 18.0})
        product_id = product_response.json()['id']
        create_response = client.post('/experiments/', json={'name': 'Complete Workflow Test', 'description': 'End-to-end workflow test', 'control_config': {'name': 'Control Flat ₹200', 'discount_type': 'flat', 'discount_value': 200.0}, 'variant_config': {'name': 'Variant Flat ₹400', 'discount_type': 'flat', 'discount_value': 400.0}, 'traffic_split': 50.0, 'product_id': product_id})
        experiment_id = create_response.json()['id']
        start_response = client.post(f'/experiments/{experiment_id}/start')
        assert start_response.json()['status'] == 'running'
        for _ in range(20):
            client.post(f'/experiments/{experiment_id}/run', params={'product_id': product_id, 'quantity': 3})
        results_response = client.get(f'/experiments/{experiment_id}/results')
        results = results_response.json()
        assert results['total_observations'] == 20
        stop_response = client.post(f'/experiments/{experiment_id}/stop')
        assert stop_response.json()['status'] == 'completed'