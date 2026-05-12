# tests/test_genealogy.py
"""
Genealogy module tests - comprehensive boundary condition tests
"""
import pytest
import uuid


class TestListGenealogies:
    """Test list genealogies."""
    
    def test_list_empty(self, logged_in_client):
        """Test listing genealogies when user has none."""
        resp = logged_in_client.get('/api/genealogies')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
    
    def test_list_requires_login(self, client):
        """Test listing genealogies without login."""
        resp = client.get('/api/genealogies')
        assert resp.status_code == 401


class TestCreateGenealogy:
    """Test create genealogy."""
    
    def test_create_success(self, logged_in_client):
        """Test successful genealogy creation."""
        resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Test Family {uuid.uuid4().hex[:6]}',
            'surname': 'TestSurname'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'genealogy_id' in data
    
    def test_create_requires_login(self, client):
        """Test creating genealogy without login."""
        resp = client.post('/api/genealogies', json={
            'name': 'Unauthorized Family',
            'surname': 'NoAuth'
        })
        assert resp.status_code == 401


class TestGetGenealogyDetail:
    """Test get genealogy detail."""
    
    def test_get_detail_success(self, logged_in_client):
        """Test getting genealogy detail for owned genealogy."""
        create_resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Detail Test {uuid.uuid4().hex[:6]}',
            'surname': 'DetailSurname'
        })
        assert create_resp.status_code == 201
        genealogy_id = create_resp.get_json()['genealogy_id']
        
        resp = logged_in_client.get(f'/api/genealogies/{genealogy_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['genealogy_id'] == genealogy_id
    
    def test_get_detail_nonexistent(self, logged_in_client):
        """Test getting detail for nonexistent genealogy."""
        resp = logged_in_client.get('/api/genealogies/999999')
        assert resp.status_code == 404
    
    def test_get_detail_requires_login(self, client):
        """Test getting detail without login."""
        resp = client.get('/api/genealogies/1')
        assert resp.status_code == 401


class TestDeleteGenealogy:
    """Test delete genealogy."""
    
    def test_delete_owner_success(self, logged_in_client):
        """Test owner can delete genealogy."""
        create_resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Delete Test {uuid.uuid4().hex[:6]}',
            'surname': 'DeleteSurname'
        })
        assert create_resp.status_code == 201
        genealogy_id = create_resp.get_json()['genealogy_id']
        
        resp = logged_in_client.delete(f'/api/genealogies/{genealogy_id}')
        assert resp.status_code == 200
        
        get_resp = logged_in_client.get(f'/api/genealogies/{genealogy_id}')
        assert get_resp.status_code == 404
    
    def test_delete_requires_login(self, client):
        """Test delete without login."""
        resp = client.delete('/api/genealogies/1')
        assert resp.status_code == 401


class TestGenealogyStats:
    """Test genealogy statistics."""
    
    def test_stats_success(self, logged_in_client):
        """Test getting stats for owned genealogy."""
        create_resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Stats Test {uuid.uuid4().hex[:6]}',
            'surname': 'StatsSurname'
        })
        assert create_resp.status_code == 201
        genealogy_id = create_resp.get_json()['genealogy_id']
        
        resp = logged_in_client.get(f'/api/genealogies/{genealogy_id}/stats')
        assert resp.status_code == 200
    
    def test_stats_requires_login(self, client):
        """Test stats without login."""
        resp = client.get('/api/genealogies/1/stats')
        assert resp.status_code == 401