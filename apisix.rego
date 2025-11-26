package apisix

import future.keywords.if
import future.keywords.in

# Default deny
default allow = {
    "allow": false,
    "reason": "Unauthorized user or path"
}

# Helper: Get Path and Method
path := input.request.path
method := input.request.method

# Helper: Get User Email from Token
user_email := email if {
    user_info_header := input.request.headers["X-Userinfo"]
    user_info_json := base64.decode(user_info_header)
    user := json.unmarshal(user_info_json)
    email := user.email
}

# Helper: Get User Config from OPA Data
user_config := data.users[user_email]

# 1. Shared / Public Paths (Always Allowed)
allow = {"allow": true} if {
    is_shared_path
}

is_shared_path if {
    startswith(path, "/auth")
}
is_shared_path if {
    startswith(path, "/logout")
}
is_shared_path if {
    startswith(path, "/callback")
}

# 2. User Access Check
allow = {"allow": true} if {
    # Ensure user exists in config
    user_config
    
    # Check Permission (Read/Write)
    has_permission
    
    # Check Service Access (Prefix Match)
    has_service_access
}

# Permission Logic
has_permission if {
    method == "GET"
    "read" in user_config.permissions
}
has_permission if {
    method in ["POST", "PUT", "DELETE", "PATCH"]
    "write" in user_config.permissions
}
has_permission if {
    method == "OPTIONS" # Always allow OPTIONS
}

# Service Access Logic
has_service_access if {
    some prefix in user_config.prefixes
    startswith(path, prefix)
}

debug = {
    "email": user_email,
    "config": user_config,
    "has_permission": has_permission,
    "has_service_access": has_service_access
}
