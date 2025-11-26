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
user_roles := data.users[user_email].roles

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
    # Ensure user is authenticated (has email)
    user_email
    
    # Ensure user has roles
    user_roles
    
    # Check if any role allows this action
    some role in user_roles
    role_allows(role, method, path)
}

# Role Logic
role_allows(role, method, path) if {
    # Check Permissions
    has_permission(role, method)
    
    # Check Service Access
    has_service_access(role, path)
}

# Permission Logic
has_permission(role, method) if {
    method == "GET"
    "read" in data.roles[role].permissions
}
has_permission(role, method) if {
    method in ["POST", "PUT", "DELETE", "PATCH"]
    "write" in data.roles[role].permissions
}
has_permission(role, method) if {
    method == "OPTIONS" # Always allow OPTIONS
}

# Service Access Logic
has_service_access(role, path) if {
    # Get allowed services for the role
    some svc_name in data.roles[role].services
    
    # Get prefixes for the service
    some prefix in data.services[svc_name]
    
    # Check if path starts with prefix
    startswith(path, prefix)
}
