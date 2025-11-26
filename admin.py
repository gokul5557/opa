import json
import os
import subprocess

# ==========================================
# 1. CONFIGURATION
# ==========================================

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
        "services": ["admin"],
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
        "services": [], # Services come from PLAN usually
        "permissions": ["read", "write"]
    }
}

# Users (Assign Plan and Roles)
import random

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
        "roles": ["employee"]
    },
    "testuser": {
        "plan": "basic",
        "roles": ["employee"]
    }
}

# Generate 100 random users
DOMAINS = ["sagasoft.io", "sagaid.com"]
PLAN_KEYS = list(PLANS.keys())
ROLE_KEYS = list(ROLES.keys())

for i in range(1, 101):
    domain = random.choice(DOMAINS)
    email = f"user{i}@{domain}"
    plan = random.choice(PLAN_KEYS)
    
    # Randomly assign extra roles
    roles = ["employee"] # Everyone is an employee by default
    if random.random() > 0.8: # 20% chance of extra role
        extra_role = random.choice(ROLE_KEYS)
        if extra_role != "employee":
            roles.append(extra_role)
            
    USERS[email] = {
        "plan": plan,
        "roles": roles
    }

# ==========================================
# 2. LOGIC (Pre-calculation)
# ==========================================
def calculate_effective_access():
    user_config = {}
    
    for email, config in USERS.items():
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
                # Add Role Services
                for svc in role_def.get("services", []):
                    allowed_services.add(svc)
                # Add Role Permissions
                for perm in role_def.get("permissions", []):
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
        
    return {"users": user_config}

# ==========================================
# 3. GIT SYNC
# ==========================================
def git_push():
    try:
        print("Committing and pushing changes to Git...")
        subprocess.run(["git", "add", "data.json"], check=True)
        subprocess.run(["git", "commit", "-m", "Update policy data via admin script (pre-calc)"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print("✅ Successfully pushed to Git!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Generate Data
    data = calculate_effective_access()
    
    # Write to data.json
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("Generated data.json")
    
    # Push to Git
    git_push()
