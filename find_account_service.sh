#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')

# Find the account service
import os
for root, dirs, files in os.walk('/app/api/services'):
    for f in files:
        if 'account' in f.lower():
            print(os.path.join(root, f))
" 2>/dev/null

echo "==="

kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')
from services.account_service import AccountService
import inspect

# Find password-related methods
for name, method in inspect.getmembers(AccountService, predicate=inspect.isfunction):
    if 'password' in name.lower() or 'login' in name.lower() or 'authenticate' in name.lower():
        print(f'Method: {name}')
        try:
            print(inspect.getsource(method)[:500])
        except:
            pass
        print('---')
" 2>/dev/null