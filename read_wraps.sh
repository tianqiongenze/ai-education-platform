#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')
with open('/app/api/controllers/console/wraps.py') as f:
    content = f.read()
    # Find _decrypt_field function
    idx = content.find('def _decrypt_field')
    if idx >= 0:
        # Print from that point
        print(content[idx:idx+2000])
" 2>/dev/null