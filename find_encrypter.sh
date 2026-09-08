#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import os, sys
# Find the encrypter module
for root, dirs, files in os.walk('/app'):
    for f in files:
        if 'encrypt' in f.lower() and f.endswith('.py'):
            print(os.path.join(root, f))
" 2>/dev/null | head -10