import subprocess
import json
import base64

# ==========================================
# TEST CONFIGURATION
# ==========================================
OPA_URL = "http://localhost:8181/v1/data/apisix/allow"

# Import definitions from admin.py to know expected state
from admin import USERS, PLANS, ROLES, SERVICES

# ==========================================
# TEST CONFIGURATION
# ==========================================
OPA_URL = "http://localhost:8181/v1/data/apisix/allow"

def get_expected_access(email):
    config = USERS.get(email)
    if not config:
        return set(), set()
        
    plan_name = config.get("plan")
    role_names = config.get("roles", [])
    
    allowed_services = set()
    allowed_permissions = set()
    
    # 1. Add services from Plan
    if plan_name and plan_name in PLANS:
        for svc in PLANS[plan_name]:
            allowed_services.add(svc)
            
    # 2. Add services and permissions from Roles
    for role in role_names:
        if role in ROLES:
            role_def = ROLES[role]
            for svc in role_def.get("services", []):
                allowed_services.add(svc)
            for perm in role_def.get("permissions", []):
                allowed_permissions.add(perm)
                
    # 3. Expand "all"
    final_prefixes = set()
    if "all" in allowed_services:
        final_prefixes.add("/")
    else:
        for svc in allowed_services:
            if svc in SERVICES:
                for prefix in SERVICES[svc]:
                    final_prefixes.add(prefix)
                    
    return final_prefixes, allowed_permissions

# Generate Test Cases dynamically
TEST_CASES = []

# 1. Public Paths
TEST_CASES.append((None, "GET", "/auth/login", True))

# 2. Verify ALL Users
for email in USERS:
    prefixes, permissions = get_expected_access(email)
    
    # Test Mail Access
    should_allow_mail = False
    for p in prefixes:
        if p == "/" or p.startswith("/mail"):
            should_allow_mail = True
            break
    if "read" not in permissions: should_allow_mail = False
    
    TEST_CASES.append((email, "GET", "/mail/inbox", should_allow_mail))
    
    # Test Drive Access
    should_allow_drive = False
    for p in prefixes:
        if p == "/" or p.startswith("/drive"):
            should_allow_drive = True
            break
    if "read" not in permissions: should_allow_drive = False
    
    TEST_CASES.append((email, "GET", "/drive/files", should_allow_drive))
    
    # Test Billing Access (Restricted)
    should_allow_billing = False
    for p in prefixes:
        if p == "/" or p.startswith("/api/method/billing"):
            should_allow_billing = True
            break
    if "read" not in permissions: should_allow_billing = False
    
    TEST_CASES.append((email, "GET", "/api/method/billing", should_allow_billing))


def run_test(email, method, path, expected):
    # Construct Input
    headers = {}
    if email:
        user_info = {"email": email}
        encoded = base64.b64encode(json.dumps(user_info).encode()).decode()
        headers["X-Userinfo"] = encoded
        
    payload = {
        "input": {
            "request": {
                "method": method,
                "path": path,
                "headers": headers
            }
        }
    }
    
    # Run Curl
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", OPA_URL, "-H", "Content-Type: application/json", "-d", json.dumps(payload)],
            capture_output=True, text=True
        )
        response = json.loads(result.stdout)
        allowed = response.get("result", {}).get("allow", False)
        
        status = "✅ PASS" if allowed == expected else "❌ FAIL"
        print(f"{status} | User: {email or 'Public':<20} | {method:<4} {path:<25} | Expected: {expected} | Got: {allowed}")
        return allowed == expected
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Running OPA Policy Tests...")
    print("-" * 80)
    passed = 0
    for email, method, path, expected in TEST_CASES:
        if run_test(email, method, path, expected):
            passed += 1
    
    print("-" * 80)
    print(f"Total: {len(TEST_CASES)} | Passed: {passed} | Failed: {len(TEST_CASES) - passed}")
