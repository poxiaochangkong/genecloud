# tests/test_stats.py
"""
Statistics module tests - comprehensive boundary condition tests
"""
import pytest
import uuid


class TestDashboardStats:
    """Test dashboard statistics."""
    
    def test_stats_empty_genealogy(self, logged_in_client):
        """Test stats for empty genealogy."""
        create_resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Empty Stats {uuid.uuid4().hex[:6]}',
            'surname': 'EmptyStats'
        })
        if create_resp.status_code == 201:
            gid = create_resp.get_json()['genealogy_id']
            resp = logged_in_client.get(f'/api/genealogies/{gid}/stats')
            assert resp.status_code == 200
            data = resp.get_json()
            # Stats should return some structure
            assert isinstance(data, dict)
    
    def test_stats_nonexistent_genealogy(self, logged_in_client):
        """Test stats for nonexistent genealogy."""
        resp = logged_in_client.get('/api/genealogies/999999/stats')
        assert resp.status_code == 400
    
    def test_stats_requires_login(self, client):
        """Test stats without login."""
        resp = client.get('/api/genealogies/1/stats')
        assert resp.status_code == 401