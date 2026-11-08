import sys
import os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from api.server import app
from database.crud import get_user_by_username
from controllers.auth_controller import create_session

client = TestClient(app)

admin_user = get_user_by_username("admin")
if not admin_user:
    print("FAIL: admin user not found")
    sys.exit(1)

token = create_session(admin_user)
headers = {"Authorization": f"Bearer {token}"}
client.cookies.set("ajax_session_token", token)

print("--- Testing /AJAX/admin Page ---")
res = client.get("/AJAX/admin", headers=headers)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
assert "Administrator Command Center" in res.text
print("PASS: /AJAX/admin rendered successfully")

print("--- Testing /api/admin/stats ---")
res = client.get("/api/admin/stats", headers=headers)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
stats = res.json()
print("Stats response:", stats["system"])
assert stats["system"]["neural_vocab_size"] > 0, "Vocab size should be > 0"
assert stats["system"]["database_type"] == "MongoDB Atlas (Cloud)"
print(f"PASS: Stats OK (vocab_size={stats['system']['neural_vocab_size']})")

print("--- Testing /api/admin/users ---")
res = client.get("/api/admin/users", headers=headers)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
users_data = res.json()
print(f"PASS: Found {len(users_data.get('users', []))} users")

print("--- Testing POST /api/admin/users (Create User) ---")
test_username = "test_sub_admin"
# cleanup first if exists
from database.crud import delete_user, get_user_by_username
existing = get_user_by_username(test_username)
if existing:
    delete_user(existing["id"])

res = client.post("/api/admin/users", headers=headers, json={
    "username": test_username,
    "password": "temp_password_123",
    "full_name": "Test Sub Admin",
    "email": "subadmin@example.com",
    "role": "admin"
})
assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
new_u = res.json()["user"]
assert new_u["username"] == test_username
assert new_u["role"] == "admin"
print(f"PASS: Created user {test_username} with role admin")

# Cleanup created test user
delete_user(new_u["id"])
print("PASS: Cleaned up test user")

print("--- Testing POST /api/admin/flush-cache ---")
res = client.post("/api/admin/flush-cache", headers=headers)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
print("PASS: Flush cache succeeded")

print("--- Testing /AJAX/system Page ---")
res = client.get("/AJAX/system", headers=headers)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
assert "Subsystem Diagnostic Probes" in res.text
print("PASS: /AJAX/system rendered with Subsystem Diagnostic Probes")

print("--- Testing /api/status ---")
res = client.get("/api/status", headers=headers)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
status_data = res.json()
assert "cpu" in status_data
assert "ram" in status_data
print("PASS: /api/status returned host hardware metrics")

print("--- Testing /api/diagnostics ---")
res = client.get("/api/diagnostics", headers=headers)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
diag_data = res.json()
assert "subsystems" in diag_data
assert diag_data["subsystems"]["database"]["status"] == "HEALTHY"
print("PASS: /api/diagnostics returned healthy subsystems")

print("\n=== ALL COMPREHENSIVE CHECKS PASSED ===")
