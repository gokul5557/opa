import requests
import json

# ==========================================
# 1. CONFIGURATION
# ==========================================
OPA_URL = "http://localhost:8181/v1/data/app_config"

# Service Definitions (URI Prefixes)
SERVICES = {
    "mail": ["/mail"],
    "drive": ["/drive"],
    "calendar": ["/calendar"],
    "meet": ["/meet", "/rooms"],
    "chat": ["/chat"],
    "admin": ["/api/method/saga_directory", "/api/method/saga_auth"], # General Admin APIs
    "billing": ["/api/method/billing"],
    "org": ["/api/method/organization"],
    "all": ["/"] # Wildcard
}

# Plans (Define which services are available)
PLANS = {
    "basic": ["mail", "drive"],
    "pro": ["mail", "drive", "calendar"],
    "premium": ["mail", "drive", "calendar", "meet"],
    "enterprise": ["all"]
}

# Roles (Define permissions and extra services)
# Permissions: "read" (GET), "write" (POST, PUT, DELETE, PATCH)
ROLES = {
    "workspace_admin": {
        "services": ["all"],
        "permissions": ["read", "write"]
    },
    "billing_admin": {
        "services": ["billing"],
        "permissions": ["read", "write"]
    },
    "org_admin": {
        "services": ["org"],
        "permissions": ["read", "write"]
    },
    "user_admin": {
        "services": ["admin"], # Assuming user mgmt is under admin
        "permissions": ["read", "write"]
    },
    "email_admin": {
        "services": ["mail"],
        "permissions": ["read", "write"]
    },
    "drive_admin": {
        "services": ["drive"],
        "permissions": ["read", "write"]
    },
    "calendar_admin": {
        "services": ["calendar"],
        "permissions": ["read", "write"]
    },
    "meet_admin": {
        "services": ["meet"],
        "permissions": ["read", "write"]
    },
    "employee": {
        "services": [], # Services come from PLAN
        "permissions": ["read", "write"]
    },
    "guest": {
        "services": [], # Services come from PLAN
        "permissions": ["read"]
    }
}

# Users (Assign Plan and Roles)
USERS = {
    "gokul@sagasoft.io": {
        "plan": "basic",
        "roles": ["employee"]
    },
    "gokul@sagaid.com": {
        "plan": "enterprise",
        "roles": ["workspace_admin"]
    },
    "billing@sagasoft.xyz": {
        "plan": "basic",
        "roles": ["billing_admin"]
    },
    "guest@sagasoft.xyz": {
        "plan": "pro",
        "roles": ["guest"]
    }
}

# ==========================================
# 2. LOGIC (Pre-calculation)
# ==========================================
def calculate_effective_access():
    user_config = {}
    
    for email, config in USERS.items():
        plan_name = config["plan"]
        role_names = config["roles"]
        
        allowed_services = set()
        allowed_permissions = set()
        
        # 1. Add services from Plan
        if plan_name in PLANS:
            for svc in PLANS[plan_name]:
                allowed_services.add(svc)
                
        # 2. Add services and permissions from Roles
        for role in role_names:
            if role in ROLES:
                role_def = ROLES[role]
                # Add Role Services
                for svc in role_def["services"]:
                    allowed_services.add(svc)
                # Add Role Permissions
                for perm in role_def["permissions"]:
                    allowed_permissions.add(perm)
        
        # 3. Expand "all" service to actual prefixes
        final_prefixes = set()
        if "all" in allowed_services:
            final_prefixes.add("/") # Root allows everything
        else:
            for svc in allowed_services:
                if svc in SERVICES:
                    for prefix in SERVICES[svc]:
                        final_prefixes.add(prefix)
                        
        user_config[email] = {
            "prefixes": list(final_prefixes),
            "permissions": list(allowed_permissions)
        }
        
    return user_config

# ==========================================
# 3. PUSH TO OPA
# ==========================================
def push_to_opa():
    data = calculate_effective_access()
    
    payload = {
        "users": data
    }
    
    print("Generated Configuration:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.put(OPA_URL, json=payload)
        if response.status_code == 204: # OPA returns 204 on success
            print("\n✅ Successfully pushed to OPA!")
        else:
            print(f"\n❌ Failed to push to OPA. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"\n❌ Error connecting to OPA: {e}")

if __name__ == "__main__":
    push_to_opa()
