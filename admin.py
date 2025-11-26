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
# We will convert these to "Roles" in data.json so the policy can handle them uniformly
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
    },
    "guest": {
        "services": [], # Services come from PLAN usually
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
    },
    "testuser": {
        "plan": "basic",
        "roles": ["guest"]
    }
}

# ==========================================
# 2. GENERATION LOGIC
# ==========================================
def generate_data_json():
    data = {
        "services": SERVICES,
        "roles": {},
        "users": {}
    }

    # 1. Convert ROLES
    for role_name, config in ROLES.items():
        data["roles"][role_name] = config

    # 2. Convert PLANS to ROLES (prefixed with 'plan_')
    # This allows the Rego policy to treat plans just like roles that grant service access
    for plan_name, services in PLANS.items():
        role_name = f"plan_{plan_name}"
        data["roles"][role_name] = {
            "services": services,
            "permissions": [] # Plans usually just grant access, permissions come from other roles (like employee/guest)
        }

    # 3. Convert USERS
    for email, config in USERS.items():
        user_roles = config.get("roles", []).copy()
        
        # Add the plan as a role
        if "plan" in config:
            user_roles.append(f"plan_{config['plan']}")
            
        data["users"][email] = {
            "roles": user_roles
        }

    return data

# ==========================================
# 3. GIT SYNC
# ==========================================
def git_push():
    try:
        print("Committing and pushing changes to Git...")
        subprocess.run(["git", "add", "data.json"], check=True)
        subprocess.run(["git", "commit", "-m", "Update policy data via admin script"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print("✅ Successfully pushed to Git!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Generate Data
    data = generate_data_json()
    
    # Write to data.json
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("Generated data.json")
    
    # Push to Git
    git_push()
