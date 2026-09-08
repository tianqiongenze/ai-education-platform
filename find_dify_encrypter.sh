#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import os
# Look in the dify core
for root, dirs, files in os.walk('/app/api/core'):
    for f in files:
        if 'encrypt' in f.lower() or 'password' in f.lower():
            print(os.path.join(root, f))
" 2>/dev/null

echo "==="
kubectl exec -n dify deploy/dify-api -- python3 -c "
# Try to import the encrypter
import sys
sys.path.insert(0, '/app/api')
try:
    from core.helper import encrypter
    print('Found: core.helper.encrypter')
    print(dir(encrypter))
except Exception as e:
    print(f'core.helper.encrypter: {e}')

try:
    from extensions.ext_encryption import encrypt
    print('Found: extensions.ext_encryption')
except Exception as e:
    print(f'extensions: {e}')
" 2>/dev/null