#!/bin/sh
cd /tmp/jai/extracted/jupyter_ai-2.31.0.data/data/share/jupyter/labextensions/@jupyter-ai/core
python3 -c "
import json
d = json.load(open('package.json'))
print('name:', d.get('name'), '| version:', d.get('version'))
j = d.get('jupyterlab') or {}
print('jupyterlab compat:', json.dumps(j.get('_build'))[:200] if j.get('_build') else None)
print('extension:', j.get('extension'))
print('schemaDir:', j.get('schemaDir'))
"
echo "== schema keys =="
find . -name "*.json" -path "*schema*" | head -3
ls
