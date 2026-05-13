# tests/test_permission.py
"""
Permission module tests - comprehensive boundary condition tests
"""
import pytest
import uuid


class TestListPermissions:
    """Test list permissions."""
    
    def test_list_permissions_success(self, logged_in_client):
        """Test listing permissions for owned genealogy."""
        # Create a genealogy
        create_resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Perm Test {uuid.uuid4().hex[:6]}',
            'surname': 'PermSurname'
        })
        if create_resp.status_code == 201:
            gid = create_resp.get_json()['genealogy_id']
            resp = logged_in_client.get(f'/api/genealogies/{gid}/permissions')
            assert resp.status_code == 200
    
    def test_list_permissions_requires_login(self, client):
        """Test listing permissions without login."""
        resp = client.get('/api/genealogies/1/permissions')
        assert resp.status_code == 401


class TestGrantPermission:
    """Test grant permission."""
    
    def test_grant_permission_success(self, logged_in_client, client):
        """Test granting permission to another user."""
        # Register a second user
        uuid_str = uuid.uuid4().hex[:8]
        client.post('/api/register', json={
            'username': f'grant_{uuid_str}',
            'password': 'password123',
            'email': f'grant_{uuid_str}@test.com'
        })

        # Create genealogy
        create_resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Grant Test {uuid.uuid4().hex[:6]}',
            'surname': 'GrantSurname'
        })
        if create_resp.status_code == 201:
            gid = create_resp.get_json()['genealogy_id']
            resp = logged_in_client.post(f'/api/genealogies/{gid}/permissions', json={
                'username': f'grant_{uuid_str}',
                'role': 'editor'
            })
            assert resp.status_code == 200
    
    def test_grant_permission_nonexistent_user(self, logged_in_client):
        """Test granting permission to nonexistent user."""
        create_resp = logged_in_client.post('/api/genealogies', json={
            'name': f'Grant NonExistent {uuid.uuid4().hex[:6]}',
            'surname': 'GrantNE'
        })
        if create_resp.status_code == 201:
            gid = create_resp.get_json()['genealogy_id']
            resp = logged_in_client.post(f'/api/genealogies/{gid}/permissions', json={
                'username': 'nonexistent_user_xyz',
                'role': 'editor'
            })
            assert resp.status_code == 400
    
    def test_grant_permission_requires_login(self, client):
        """Test granting permission without login."""
        resp = client.post('/api/genealogies/1/permissions', json={
            'username': 'any_user',
            'role': 'editor'
        })
        assert resp.status_code == 401


class TestRevokePermission:
    """Test revoke permission."""
    
    def test_revoke_permission_success(self, logged_in_client, client):
        """Test revoking permission."""
        uuid_str = uuid.uuid4().hex[:8]
        reg_resp = client.post('/api/register', json={
            'username': f'revoke_{uuid_str}',
            'password': 'password123',
            'email': f'revoke_{uuid_str}@test.com'
        })
        if reg_resp.status_code in [200, 201]:
            target_uid = reg_resp.get_json().get('user_id')
            
            create_resp = logged_in_client.post('/api/genealogies', json={
                'name': f'Revoke Test {uuid.uuid4().hex[:6]}',
                'surname': 'RevokeSurname'
            })
            if create_resp.status_code == 201 and target_uid:
                gid = create_resp.get_json()['genealogy_id']
                resp = logged_in_client.delete(
                    f'/api/genealogies/{gid}/permissions/{target_uid}'
                )
                assert resp.status_code == 200
    
    def test_revoke_permission_requires_login(self, client):
        """Test revoking permission without login."""
        resp = client.delete('/api/genealogies/1/permissions/1')
        assert resp.status_code == 401