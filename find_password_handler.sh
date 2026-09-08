#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import os, sys
sys.path.insert(0, '/app/api')

# Find password-related code
for root, dirs, files in os.walk('/app/api'):
    for f in files:
        if f.endswith('.py') and ('account' in f.lower() or 'login' in f.lower() or 'auth' in f.lower()):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    content = fh.read()
                    if 'password' in content.lower() and ('hash' in content.lower() or 'encrypt' in content.lower() or 'verify' in content.lower()):
                        print(path)
            except:
                pass
" 2>/dev/null | head -20