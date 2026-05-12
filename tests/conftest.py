# tests/conftest.py
"""
Test configuration and fixtures
"""
import sys
import os
import pytest
import tempfile

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from config import DATABASE_CONFIG
import mysql.connector


def get_test_db_connection():
    """Get test database connection."""
    return mysql.connector.connect(**DATABASE_CONFIG)


@pytest.fixture
def app():
    """Create application for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    yield flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_conn():
    """Get database connection for testing."""
    conn = get_test_db_connection()
    yield conn
    conn.close()


@pytest.fixture
def test_user(client):
    """Create a test user and return credentials."""
    import uuid
    unique = uuid.uuid4().hex[:8]
    username = f"test_user_{unique}"
    password = "test123456"
    email = f"test_{unique}@example.com"
    
    resp = client.post('/api/register', json={
        'username': username,
        'password': password,
        'email': email
    })
    return {
        'username': username,
        'password': password,
        'email': email,
        'response': resp
    }


@pytest.fixture
def logged_in_client(client, test_user):
    """Return a client that is logged in."""
    client.post('/api/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })
    return client