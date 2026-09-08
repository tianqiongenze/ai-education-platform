#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')

# Read the full password.py
with open('/app/api/libs/password.py') as f:
    print(f.read())
" 2>/dev/null