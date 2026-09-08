#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')

# Read the login controller
with open('/app/api/controllers/console/auth/login.py') as f:
    content = f.read()
    print(content[:3000])
" 2>/dev/null