#!/bin/bash

# Test User: testuser (Basic Plan)
# Expected: ALLOW (true)

echo "Testing OPA Policy for testuser accessing /mail/inbox..."

curl -v -X POST http://localhost:8181/v1/data/apisix/allow \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
        "request": {
            "method": "GET",
            "path": "/mail/inbox",
            "headers": {
                "X-Userinfo": "eyJlbWFpbCI6ICJ0ZXN0dXNlciJ9"
            }
        }
    }
}'
echo ""
