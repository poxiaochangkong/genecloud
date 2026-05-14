"""Reproduce the exact test flow"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
import uuid

flask_app.config['TESTING'] = True
flask_app.config['SECRET_KEY'] = 'test-secret-key'
client = flask_app.test_client()

# Step 1: Register main user and log in
unique1 = uuid.uuid4().hex[:8]
client.post('/api/register', json={
    'username': f'main_{unique1}',
    'password': 'test123456',
    'email': f'main_{unique1}@test.com'
})
login1 = client.post('/api/login', json={
    'username': f'main_{unique1}',
    'password': 'test123456'
})
print(f'Login main user: {login1.status_code}')

# Step 2: Register second user using SAME client (like the test does)
unique2 = uuid.uuid4().hex[:8]
reg2 = client.post('/api/register', json={
    'username': f'target_{unique2}',
    'password': 'password123',
    'email': f'target_{unique2}@test.com'
})
print(f'Register target: {reg2.status_code}')

# Step 3: Create genealogy
create = client.post('/api/genealogies', json={
    'name': f'Test {uuid.uuid4().hex[:6]}',
    'surname': 'TestSurname'
})
print(f'Create genealogy: {create.status_code}', create.get_json())
gid = create.get_json()['genealogy_id']

# Step 4: Grant permission
grant = client.post(f'/api/genealogies/{gid}/permissions', json={
    'username': f'target_{unique2}',
    'role': 'editor'
})
print(f'Grant permission: {grant.status_code}', grant.get_json())