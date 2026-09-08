#!/bin/bash
# Generate proper Dify password using the actual Dify encrypter
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')
from core.helper import encrypter
import base64

# Check what encrypt_token does
password = 'admin123'
try:
    encrypted = encrypter.encrypt_token(password)
    print(f'encrypt_token result: {encrypted}')
except Exception as e:
    print(f'encrypt_token error: {e}')

# Check the source code of encrypter
import inspect
print()
print(inspect.getsource(encrypter))
" 2>/dev/null