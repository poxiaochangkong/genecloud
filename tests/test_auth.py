# tests/test_auth.py
"""
Authentication module tests - comprehensive boundary condition tests
"""
import pytest
import uuid


class TestRegister:
    """Test user registration."""
    
    def test_register_success(self, client):
        """Test successful registration."""
        unique = uuid.uuid4().hex[:8]
        resp = client.post('/api/register', json={
            'username': f'new_user_{unique}',
            'password': 'password123',
            'email': f'new_{unique}@test.com'
        })
        assert resp.status_code in [200, 201]
    
    def test_register_duplicate_username(self, client, test_user):
        """Test duplicate username registration."""
        resp = client.post('/api/register', json={
            'username': test_user['username'],
            'password': 'password123',
            'email': 'dup@test.com'
        })
        assert resp.status_code == 400
    
    def test_register_username_too_short(self, client):
        """Test registration with username too short (1 char)."""
        resp = client.post('/api/register', json={
            'username': 'a',
            'password': 'password123',
            'email': 'short@test.com'
        })
        assert resp.status_code == 400
    
    def test_register_username_too_long(self, client):
        """Test registration with username too long (21 chars)."""
        resp = client.post('/api/register', json={
            'username': 'a' * 21,
            'password': 'password123',
            'email': 'long@test.com'
        })
        assert resp.status_code == 400
    
    def test_register_password_too_short(self, client):
        """Test registration with password too short (5 chars)."""
        resp = client.post('/api/register', json={
            'username': 'valid_user',
            'password': '12345',
            'email': 'shortpwd@test.com'
        })
        assert resp.status_code == 400
    
    def test_register_missing_username(self, client):
        """Test registration without username."""
        resp = client.post('/api/register', json={
            'password': 'password123',
            'email': 'nouser@test.com'
        })
        # Empty username should be rejected
        assert resp.status_code == 400
    
    def test_register_missing_password(self, client):
        """Test registration without password."""
        resp = client.post('/api/register', json={
            'username': 'nopwd_user',
            'email': 'nopwd@test.com'
        })
        # Empty password should be rejected
        assert resp.status_code == 400


class TestLogin:
    """Test user login."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        resp = client.post('/api/login', json={
            'username': test_user['username'],
            'password': test_user['password']
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'user_id' in data
        assert 'username' in data
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        resp = client.post('/api/login', json={
            'username': test_user['username'],
            'password': 'wrongpassword'
        })
        assert resp.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent username."""
        unique = uuid.uuid4().hex[:8]
        resp = client.post('/api/login', json={
            'username': f'nonexistent_{unique}',
            'password': 'password123'
        })
        assert resp.status_code == 401
    
    def test_login_missing_username(self, client):
        """Test login without username."""
        resp = client.post('/api/login', json={
            'password': 'password123'
        })
        # Application may return 400 or 401 for missing username
        assert resp.status_code in [400, 401]
    
    def test_login_missing_password(self, client):
        """Test login without password."""
        resp = client.post('/api/login', json={
            'username': 'valid_user'
        })
        # Application may return 400 or 401 for missing password
        assert resp.status_code in [400, 401]


class TestLogout:
    """Test user logout."""
    
    def test_logout_success(self, logged_in_client):
        """Test successful logout."""
        resp = logged_in_client.post('/api/logout')
        assert resp.status_code == 200
    
    def test_logout_without_login(self, client):
        """Test logout without being logged in."""
        resp = client.post('/api/logout')
        assert resp.status_code == 200


class TestCurrentUser:
    """Test get current user info."""
    
    def test_get_me_success(self, logged_in_client, test_user):
        """Test getting current user info when logged in."""
        resp = logged_in_client.get('/api/me')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['username'] == test_user['username']
    
    def test_get_me_without_login(self, client):
        """Test getting current user info when not logged in."""
        resp = client.get('/api/me')
        assert resp.status_code == 401