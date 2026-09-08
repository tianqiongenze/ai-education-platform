#!/bin/sh
# Decision research: does jupyter-ai 2.x work with jupyterlab 4.6.3 client-side?
# jupyter-ai 2.x inline completion requires the jupyter-ai 2.x labextension
# (JupyterAICompletions plugin). Check the 2.31 wheel's labextension bundle
# for the plugin id + its compat range with jupyterlab core.
cd /tmp/jai/extracted
ls jupyter_ai-2.31.0.data/data/share/jupyter/labextensions/ 2>/dev/null
for f in jupyter_ai-2.31.0.data/data/share/jupyter/labextensions/*/package.json; do
  echo "== $f"
  python3 -c "
import json
d = json.load(open('$f'))
print('name:', d.get('name'))
print('version:', d.get('version'))
jlab = d.get('jupyterlab', {})
print('jlab compat:', jlab)
for pid, p in (d.get('jupyterlab', {}).get('schemaDir') and {} or {}).items(): pass
print('plugins:', list((d.get('jupyterlab') or {}).keys()))
"
done
