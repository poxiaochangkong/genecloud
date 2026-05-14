"""Debug permission grant test"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
import uuid

flask_app.config['TESTING'] = True
flask_app.config['SECRET_KEY'] = 'test-secret-key'
client = flask_app.test_client()

# Register user1 (will be the genealogy owner)
unique1 = uuid.uuid4().hex[:8]
reg1 = client.post('/api/register', json={
    'username': f'owner_{unique1}',
    'password': 'test123456',
    'email': f'owner_{unique1}@test.com'
})
print(f'Register owner: {reg1.status_code}', reg1.get_json())

# Login as user1
login1 = client.post('/api/login', json={
    'username': f'owner_{unique1}',
    'password': 'test123456'
})
print(f'Login owner: {login1.status_code}', login1.get_json())

# Register user2 (will be the grant target)
unique2 = uuid.uuid4().hex[:8]
reg2 = client.post('/api/register', json={
    'username': f'target_{unique2}',
    'password': 'password123',
    'email': f'target_{unique2}@test.com'
})
print(f'Register target: {reg2.status_code}', reg2.get_json())

# Create genealogy
create = client.post('/api/genealogies', json={
    'name': f'Debug Test {uuid.uuid4().hex[:6]}',
    'surname': 'DebugSurname'
})
print(f'Create genealogy: {create.status_code}', create.get_json())
gid = create.get_json()['genealogy_id']

# Grant permission
grant = client.post(f'/api/genealogies/{gid}/permissions', json={
    'username': f'target_{unique2}',
    'role': 'editor'
})
print(f'Grant permission: {grant.status_code}', grant.get_json())

# Check if owner has correct role
import mysql.connector
from config import DATABASE_CONFIG
conn = mysql.connector.connect(**DATABASE_CONFIG)
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT user_id FROM users WHERE username = %s", (f'owner_{unique1}',))
user1 = cursor.fetchone()
cursor.execute("SELECT role FROM collaborations WHERE user_id = %s AND genealogy_id = %s", (user1['user_id'], gid))
print(f'Owner role in DB: {cursor.fetchone()}')
conn.close()