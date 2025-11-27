import json
import os
import subprocess
import shutil

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

# Users Source File (The "Database")
USERS_SOURCE_FILE = "users_source.json"

def load_or_generate_users():
    # 1. Try to load existing users
    if os.path.exists(USERS_SOURCE_FILE):
        print(f"📂 Loading users from {USERS_SOURCE_FILE}...")
        with open(USERS_SOURCE_FILE, "r") as f:
            return json.load(f)

    # 2. Generate if not exists
    print("⚡ Generating 100 random users...")
    users = {
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
        "testuser@sagasoft.io": {
            "plan": "basic",
            "roles": ["employee"]
        }
    }

    DOMAINS = ["sagasoft.io", "sagaid.com"]
    PLAN_KEYS = list(PLANS.keys())
    ROLE_KEYS = list(ROLES.keys())

    for i in range(1, 101):
        domain = random.choice(DOMAINS)
        email = f"user{i}@{domain}"
        plan = random.choice(PLAN_KEYS)
        
        roles = ["employee"]
        if random.random() > 0.8:
            extra_role = random.choice(ROLE_KEYS)
            if extra_role != "employee":
                roles.append(extra_role)
                
        users[email] = {
            "plan": plan,
            "roles": roles
        }
        
    # Save to file
    with open(USERS_SOURCE_FILE, "w") as f:
        json.dump(users, f, indent=2)
    print(f"💾 Saved generated users to {USERS_SOURCE_FILE}")
    
    return users

USERS = load_or_generate_users()

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
# 3. WRITE SPLIT FILES (GitOps)
# ==========================================

# ==========================================
# 3. GIT SYNC (Single File)
# ==========================================
def generate_and_push():
    # 1. Calculate Data
    data = calculate_effective_access()
    
    # 2. Write to data.json
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ Generated data.json")
    
    # 3. Push to Git
    try:
        print("Committing and pushing changes to Git...")
        
        # Remove split files if they exist
        if os.path.exists("data/users"):
            shutil.rmtree("data/users")
            
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Revert to single data.json"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print("✅ Successfully pushed to Git!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_and_push()
