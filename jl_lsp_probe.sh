#!/bin/sh
# LSP-based inline completion is via jupyter-lsp; check jupyterlab-lsp presence
echo "== jupyterlab-lsp installed? =="
pip list 2>/dev/null | grep -iE "lsp"
echo "== labextensions with lsp =="
ls /opt/conda/share/jupyter/labextensions/ | grep -i lsp
echo "== jupyter server extension list =="
export PATH=/home/jovyan/.local/bin:$PATH
jupyter server extension list 2>&1 | grep -iE "lsp|ai" | head
echo "== jupyter-lsp language servers spec =="
python3 -c "
import json,subprocess
try:
    from jupyter_lsp.specs import python_lsp_server
    print('pylsp spec available')
except Exception as e:
    print('no pylsp spec:', e)
" 2>&1
pip list 2>/dev/null | grep -iE "pylsp|python-lsp"
