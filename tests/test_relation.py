# tests/test_relation.py
"""
Relation module tests - comprehensive boundary condition tests
"""
import pytest
import uuid


def create_test_genealogy_and_members(client):
    """Helper to create a test genealogy with two members."""
    gid_resp = client.post('/api/genealogies', json={
        'name': f'Relation Test {uuid.uuid4().hex[:6]}',
        'surname': 'RelSurname'
    })
    if gid_resp.status_code != 201:
        return None, None, None
    gid = gid_resp.get_json()['genealogy_id']
    
    # Create parent (male for father relation)
    p_resp = client.post(f'/api/genealogies/{gid}/members', json={
        'name': 'Parent1', 'gender': 'M', 'birth_year': 1960,
        'death_year': None, 'bio': ''
    })
    if p_resp.status_code != 201:
        return gid, None, None
    pid = p_resp.get_json()['member_id']
    
    # Create child
    c_resp = client.post(f'/api/genealogies/{gid}/members', json={
        'name': 'Child1', 'gender': 'F', 'birth_year': 1990,
        'death_year': None, 'bio': ''
    })
    if c_resp.status_code != 201:
        return gid, pid, None
    cid = c_resp.get_json()['member_id']
    
    return gid, pid, cid


class TestGetParents:
    """Test get parents."""
    
    def test_get_parents_success(self, logged_in_client):
        """Test getting parents of a child."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship with 'father' type
            link_resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            assert link_resp.status_code in [200, 201]
            # Get parents
            resp = logged_in_client.get(f'/api/members/{cid}/parents')
            assert resp.status_code == 200
    
    def test_get_parents_no_parents(self, logged_in_client):
        """Test getting parents when none exist."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if cid:
            resp = logged_in_client.get(f'/api/members/{cid}/parents')
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)
    
    def test_get_parents_requires_login(self, client):
        """Test getting parents without login."""
        resp = client.get('/api/members/1/parents')
        assert resp.status_code == 401


class TestGetChildren:
    """Test get children."""
    
    def test_get_children_success(self, logged_in_client):
        """Test getting children of a parent."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship
            link_resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            assert link_resp.status_code in [200, 201]
            # Get children
            resp = logged_in_client.get(f'/api/members/{pid}/children')
            assert resp.status_code == 200
    
    def test_get_children_requires_login(self, client):
        """Test getting children without login."""
        resp = client.get('/api/members/1/children')
        assert resp.status_code == 401


class TestAddLink:
    """Test add parent link."""
    
    def test_add_link_success(self, logged_in_client):
        """Test establishing a parent-child relationship."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid,
                'parent_id': pid,
                'relation_type': 'father'
            })
            assert resp.status_code in [200, 201]
    
    def test_add_link_self_parent(self, logged_in_client):
        """Test adding yourself as your own parent (should fail)."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid:
            resp = logged_in_client.post('/api/relations/link', json={
                'child_id': pid,
                'parent_id': pid,
                'relation_type': 'father'
            })
            # Should fail - self-reference
            assert resp.status_code in [400, 409]
    
    def test_add_link_requires_login(self, client):
        """Test adding link without login."""
        resp = client.post('/api/relations/link', json={
            'child_id': 1, 'parent_id': 2, 'relation_type': 'father'
        })
        assert resp.status_code == 401
    
    def test_add_link_invalid_relation_type(self, logged_in_client):
        """Test adding link with invalid relation_type."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid,
                'parent_id': pid,
                'relation_type': 'biological'  # Invalid - should be 'father' or 'mother'
            })
            assert resp.status_code == 400


class TestQueryAncestors:
    """Test query ancestors."""
    
    def test_query_ancestors_success(self, logged_in_client):
        """Test querying ancestors."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship
            logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            resp = logged_in_client.get(f'/api/members/{cid}/ancestors')
            assert resp.status_code == 200
    
    def test_query_ancestors_requires_login(self, client):
        """Test querying ancestors without login."""
        resp = client.get('/api/members/1/ancestors')
        assert resp.status_code == 401


class TestQueryDescendants:
    """Test query descendants."""
    
    def test_query_descendants_success(self, logged_in_client):
        """Test querying descendants."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship
            logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            resp = logged_in_client.get(f'/api/members/{pid}/descendants')
            assert resp.status_code == 200
    
    def test_query_descendants_requires_login(self, client):
        """Test querying descendants without login."""
        resp = client.get('/api/members/1/descendants')
        assert resp.status_code == 401


class TestQueryKinship:
    """Test query kinship between two members."""
    
    def test_query_kinship_success(self, logged_in_client):
        """Test querying kinship path."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            resp = logged_in_client.get(
                f'/api/relations/kinship?member_a={pid}&member_b={cid}'
            )
            assert resp.status_code == 200
    
    def test_query_kinship_missing_params(self, logged_in_client):
        """Test kinship query with missing parameters."""
        resp = logged_in_client.get('/api/relations/kinship')
        assert resp.status_code == 400
    
    def test_query_kinship_requires_login(self, client):
        """Test kinship query without login."""
        resp = client.get('/api/relations/kinship?member_a=1&member_b=2')
        assert resp.status_code == 401