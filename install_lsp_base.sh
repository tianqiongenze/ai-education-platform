#!/bin/bash
# Install jupyterlab-lsp + python-lsp-server for reliable non-AI code completion
# Also check what's already installed
set -e

echo "=== Current JupyterLab version ==="
jupyter lab --version 2>&1

echo ""
echo "=== Check existing LSP extensions ==="
pip list 2>/dev/null | grep -iE "lsp|jupyterlab-lsp|python-lsp|pylsp|jedi" || echo "None found"

echo ""
echo "=== Installing python-lsp-server (pylsp) ==="
pip install --quiet 'python-lsp-server[all]' 2>&1 | tail -5

echo ""
echo "=== Installing jupyterlab-lsp frontend extension ==="
pip install --quiet jupyterlab-lsp 2>&1 | tail -5

echo ""
echo "=== Installing jupyter-lsp server extension ==="
pip install --quiet jupyter-lsp 2>&1 | tail -5

echo ""
echo "=== Verify pylsp ==="
pylsp --version 2>&1 || pylsp --help 2>&1 | head -3

echo ""
echo "=== Enable server extensions ==="
jupyter server extension enable --py jupyter_lsp 2>&1
jupyter server extension enable --py jupyterlab_lsp 2>&1 || true

echo ""
echo "=== List server extensions ==="
jupyter server extension list 2>&1

echo ""
echo "=== List lab extensions ==="
jupyter labextension list 2>&1

echo ""
echo "=== Check jupyter_ai inline completion presence ==="
python3 -c "
try:
    import jupyter_ai
    print(f'jupyter_ai version: {jupyter_ai.__version__}')
    from jupyter_ai.completions.handlers import BaseInlineCompletionHandler
    print('jupyter_ai 2.x inline completion handlers: FOUND')
except ImportError as e:
    print(f'jupyter_ai inline handlers not available: {e}')
except Exception as e:
    print(f'jupyter_ai check: {e}')
" 2>&1

echo ""
echo "=== DONE ==="
