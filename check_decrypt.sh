#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')

# Find decrypt_password_field
import os
for root, dirs, files in os.walk('/app/api'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    content = fh.read()
                    if 'def decrypt_password_field' in content:
                        print(f'Found in: {path}')
                        # Print the function
                        lines = content.split('\n')
                        in_func = False
                        indent = 0
                        for i, line in enumerate(lines):
                            if 'def decrypt_password_field' in line:
                                in_func = True
                                indent = len(line) - len(line.lstrip())
                                print(line)
                                continue
                            if in_func:
                                cur_indent = len(line) - len(line.lstrip())
                                if line.strip() and cur_indent <= indent:
                                    break
                                print(line)
            except:
                pass
" 2>/dev/null