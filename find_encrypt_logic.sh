#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')

# Find _decrypt_field
import os
for root, dirs, files in os.walk('/app/api'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    content = fh.read()
                    if 'def _decrypt_field' in content:
                        print(f'Found in: {path}')
                        lines = content.split('\n')
                        in_func = False
                        indent = 0
                        for i, line in enumerate(lines):
                            if 'def _decrypt_field' in line:
                                in_func = True
                                indent = len(line) - len(line.lstrip())
                            if in_func:
                                print(line)
                                cur_indent = len(line) - len(line.lstrip())
                                if line.strip() and cur_indent <= indent and i > 0:
                                    break
            except:
                pass
" 2>/dev/null