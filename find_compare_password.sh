#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import sys
sys.path.insert(0, '/app/api')

# Find compare_password
import os
for root, dirs, files in os.walk('/app/api'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    content = fh.read()
                    if 'def compare_password' in content:
                        print(f'Found in: {path}')
                        # Print the function
                        lines = content.split('\n')
                        in_func = False
                        for i, line in enumerate(lines):
                            if 'def compare_password' in line:
                                in_func = True
                            if in_func:
                                print(line)
                                if in_func and i > 0 and line.strip() == '' and lines[i-1].strip() != '':
                                    # Check if next line is not indented
                                    if i+1 < len(lines) and not lines[i+1].startswith(' ') and not lines[i+1].startswith('\t') and lines[i+1].strip() != '':
                                        break
            except:
                pass
" 2>/dev/null