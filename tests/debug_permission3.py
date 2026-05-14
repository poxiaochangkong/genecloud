"""Reproduce test with error detail"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
import uuid
import pytest

flask_app.config['TESTING'] = True
flask_app.config['SECRET_KEY'] = 'test-secret-key'

# Simulate the exact fixture chain: client -> test_user -> logged_in_client
client = flask_app.test_client()

# test_user fixture: register
unique = uuid.uuid4().hex[:8]
username = f"test_user_{unique}"
password = "test123456"
email = f"test_{unique}@example.com"

resp = client.post('/api/register', json={
    'username': username,
    'password': password,
    'email': email
})
print(f'Test user register: {resp.status_code}', resp.get_json())

# logged_in_client fixture: login
login1 = client.post('/api/login', json={
    'username': username,
    'password': password
})
print(f'Logged in: {login1.status_code}', login1.get_json())

# test body: register second user
uuid_str = uuid.uuid4().hex[:8]
reg2 = client.post('/api/register', json={
    'username': f'grant_target_{uuid_str}',
    'password': 'password123',
    'email': f'grant_{uuid_str}@test.com'
})
print(f'Register target: {reg2.status_code}', reg2.get_json())

# test body: create genealogy
create = client.post('/api/genealogies', json={
    'name': f'Grant Test {uuid.uuid4().hex[:6]}',
    'surname': 'GrantSurname'
})
print(f'Create genealogy: {create.status_code}', create.get_json())
gid = create.get_json()['genealogy_id']

# test body: grant permission
grant = client.post(f'/api/genealogies/{gid}/permissions', json={
    'username': f'grant_target_{uuid_str}',
    'role': 'editor'
})
print(f'Grant permission: {grant.status_code}', grant.get_json())