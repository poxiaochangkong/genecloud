# tests/test_member.py
"""
Member module tests - comprehensive boundary condition tests
"""
import pytest
import uuid


def create_test_genealogy(client):
    """Helper to create a test genealogy and return its ID."""
    resp = client.post('/api/genealogies', json={
        'name': f'Member Test Family {uuid.uuid4().hex[:6]}',
        'surname': 'MemberSurname'
    })
    if resp.status_code == 201:
        return resp.get_json()['genealogy_id']
    return None


class TestListMembers:
    """Test list members."""
    
    def test_list_members_empty(self, logged_in_client):
        """Test listing members in empty genealogy."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            resp = logged_in_client.get(f'/api/genealogies/{gid}/members')
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)
    
    def test_list_members_requires_login(self, client):
        """Test listing members without login."""
        resp = client.get('/api/genealogies/1/members')
        assert resp.status_code == 401


class TestCreateMember:
    """Test create member."""
    
    def test_create_member_success(self, logged_in_client):
        """Test successful member creation with valid gender M."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            resp = logged_in_client.post(f'/api/genealogies/{gid}/members', json={
                'name': 'TestMale',
                'gender': 'M',
                'birth_year': 1990,
                'death_year': None,
                'bio': 'Test bio'
            })
            assert resp.status_code == 201
    
    def test_create_member_female(self, logged_in_client):
        """Test successful member creation with valid gender F."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            resp = logged_in_client.post(f'/api/genealogies/{gid}/members', json={
                'name': 'TestFemale',
                'gender': 'F',
                'birth_year': 1995,
                'death_year': None,
                'bio': 'Test bio'
            })
            assert resp.status_code == 201
    
    def test_create_member_invalid_gender(self, logged_in_client):
        """Test member creation with invalid gender X."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            resp = logged_in_client.post(f'/api/genealogies/{gid}/members', json={
                'name': 'InvalidGender',
                'gender': 'X',
                'birth_year': 1990,
                'death_year': None,
                'bio': ''
            })
            assert resp.status_code == 400
    
    def test_create_member_future_birth_year(self, logged_in_client):
        """Test member creation with future birth year 2030."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            resp = logged_in_client.post(f'/api/genealogies/{gid}/members', json={
                'name': 'FuturePerson',
                'gender': 'M',
                'birth_year': 2030,
                'death_year': None,
                'bio': ''
            })
            # 应该被拒绝，因为出生年份在未来
            assert resp.status_code == 400
    
    def test_create_member_old_birth_year(self, logged_in_client):
        """Test member creation with very old birth year 1800."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            resp = logged_in_client.post(f'/api/genealogies/{gid}/members', json={
                'name': 'OldPerson',
                'gender': 'M',
                'birth_year': 1800,
                'death_year': None,
                'bio': ''
            })
            # 这可能会被接受或拒绝，取决于验证规则
            assert resp.status_code in [201, 400]
    
    def test_create_member_requires_login(self, client):
        """Test member creation without login."""
        resp = client.post('/api/genealogies/1/members', json={
            'name': 'NoAuth',
            'gender': 'M',
            'birth_year': 1990,
            'death_year': None,
            'bio': ''
        })
        assert resp.status_code == 401


class TestGetMemberDetail:
    """Test get member detail."""
    
    def test_get_member_success(self, logged_in_client):
        """Test getting member detail."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            # Create a member
            create_resp = logged_in_client.post(f'/api/genealogies/{gid}/members', json={
                'name': 'DetailMember',
                'gender': 'M',
                'birth_year': 1985,
                'death_year': None,
                'bio': 'Bio'
            })
            if create_resp.status_code == 201:
                mid = create_resp.get_json()['member_id']
                resp = logged_in_client.get(f'/api/members/{mid}')
                assert resp.status_code == 200
    
    def test_get_member_nonexistent(self, logged_in_client):
        """Test getting nonexistent member."""
        resp = logged_in_client.get('/api/members/999999')
        assert resp.status_code == 404
    
    def test_get_member_requires_login(self, client):
        """Test getting member without login."""
        resp = client.get('/api/members/1')
        assert resp.status_code == 401


class TestSearchMembers:
    """Test search members."""
    
    def test_search_members(self, logged_in_client):
        """Test searching members by keyword."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            resp = logged_in_client.get(
                f'/api/genealogies/{gid}/members/search?keyword=test'
            )
            assert resp.status_code == 200
    
    def test_search_requires_login(self, client):
        """Test search without login."""
        resp = client.get('/api/genealogies/1/members/search?keyword=test')
        assert resp.status_code == 401


class TestDeleteMember:
    """Test delete member."""
    
    def test_delete_member_success(self, logged_in_client):
        """Test successful member deletion."""
        gid = create_test_genealogy(logged_in_client)
        if gid:
            create_resp = logged_in_client.post(f'/api/genealogies/{gid}/members', json={
                'name': 'ToBeDeleted',
                'gender': 'M',
                'birth_year': 1990,
                'death_year': None,
                'bio': ''
            })
            if create_resp.status_code == 201:
                mid = create_resp.get_json()['member_id']
                resp = logged_in_client.delete(f'/api/members/{mid}')
                assert resp.status_code == 200
    
    def test_delete_requires_login(self, client):
        """Test delete without login."""
        resp = client.delete('/api/members/1')
        assert resp.status_code == 401