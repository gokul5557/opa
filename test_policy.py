import subprocess
import json
import base64

# ==========================================
# TEST CONFIGURATION
# ==========================================
OPA_URL = "http://localhost:8181/v1/data/apisix/allow"

# Test Cases: (User Email, Method, Path, Expected Allow)
TEST_CASES = [
    # 1. Public Paths (No User)
    (None, "GET", "/auth/login", True),
    (None, "GET", "/logout", True),
    
    # 2. Test User (Basic Plan: Mail, Drive)
    ("testuser", "GET", "/mail/inbox", True),
    ("testuser", "POST", "/mail/send", True),
    ("testuser", "GET", "/drive/files", True),
    ("testuser", "GET", "/calendar/events", False), # Not in Basic Plan
    ("testuser", "GET", "/api/method/billing", False), # Not in Basic Plan
    
    # 3. Gokul Sagasoft (Basic Plan)
    ("gokul@sagasoft.io", "GET", "/mail/inbox", True),
    ("gokul@sagasoft.io", "GET", "/drive/files", True),
    ("gokul@sagasoft.io", "GET", "/calendar/events", False),
    
    # 4. Gokul SagaID (Enterprise Plan: All)
    ("gokul@sagaid.com", "GET", "/mail/inbox", True),
    ("gokul@sagaid.com", "GET", "/drive/files", True),
    ("gokul@sagaid.com", "GET", "/calendar/events", True),
    ("gokul@sagaid.com", "GET", "/api/method/billing", True),
    ("gokul@sagaid.com", "GET", "/api/method/organization", True),
    
    # 5. Billing Admin (Billing Only)
    ("billing@sagasoft.xyz", "GET", "/api/method/billing", True),
    ("billing@sagasoft.xyz", "GET", "/mail/inbox", True), # Has Basic Plan too
    ("billing@sagasoft.xyz", "GET", "/api/method/organization", False),
]

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
