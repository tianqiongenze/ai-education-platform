#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys, os
sys.path.insert(0, '/app/api')

for root, dirs, files in os.walk('/app/api'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    content = fh.read()
                    if 'class FieldEncryption' in content:
                        print(f'Found in: {path}')
                        print(content[:3000])
            except:
                pass
" 2>/dev/null