import subprocess
import json
import base64

# ==========================================
# TEST CONFIGURATION
# ==========================================
OPA_URL = "http://localhost:8181/v1/data/apisix/allow"

import json
import os

# ==========================================
# TEST CONFIGURATION
# ==========================================
OPA_URL = "http://localhost:8181/v1/data/apisix/allow"
DATA_DIR = "data/users"

def load_users_from_split_files():
    users = {}
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: {DATA_DIR} not found. Run admin.py first.")
        return {}
    
    # Walk through data/users/{domain}/{username}.json
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".json"):
                # Extract domain and username
                # root looks like "data/users/sagasoft.io"
                domain = os.path.basename(root)
                username = file.replace(".json", "")
                email = f"{username}@{domain}"
                
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    users[email] = json.load(f)
                    
    return users

# Generate Test Cases from Split Files
TEST_CASES = []

# 1. Public Paths
TEST_CASES.append((None, "GET", "/auth/login", True))

# 2. Verify Users from Files
users_data = load_users_from_split_files()

for email, config in users_data.items():
    prefixes = config.get("prefixes", [])
    permissions = config.get("permissions", [])
    
    # Helper to check if a path is allowed by prefixes
    def is_path_allowed(path):
        for p in prefixes:
            if p == "/" or path.startswith(p):
                return True
        return False

    # Test Mail Access
    should_allow_mail = is_path_allowed("/mail/inbox") and "read" in permissions
    TEST_CASES.append((email, "GET", "/mail/inbox", should_allow_mail))
    
    # Test Drive Access
    should_allow_drive = is_path_allowed("/drive/files") and "read" in permissions
    TEST_CASES.append((email, "GET", "/drive/files", should_allow_drive))
    
    # Test Billing Access
    should_allow_billing = is_path_allowed("/api/method/billing") and "read" in permissions
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
