#!/bin/bash
# Manual validation + fix the server extension issue
echo "=== Check Python path ==="
which python3
python3 -c "import jupyter_inline_completion; print(dir(jupyter_inline_completion))" 2>&1

echo ""
echo "=== Check jupyter server extension enable output ==="
jupyter server extension enable --py jupyter_inline_completion --debug 2>&1 | tail -20

echo ""
echo "=== Manual config file approach ==="
# Instead of relying on enable, manually write the config
cat > /opt/conda/etc/jupyter/jupyter_server_config.d/jupyter_inline_completion.json << 'EOF'
{
  "ServerApp": {
    "jpserver_extensions": {
      "jupyter_inline_completion": true
    }
  }
}
EOF

echo "Config written:"
cat /opt/conda/etc/jupyter/jupyter_server_config.d/jupyter_inline_completion.json

echo ""
echo "=== Now check if server extension is listed ==="
jupyter server extension list 2>&1 | grep -A1 inline

echo ""
echo "=== Build labextension ==="
cd /home/jovyan/work/jupyter-inline-completion
echo "--- npm install ---"
jlpm install 2>&1 | tail -5
echo "--- build TS ---"
npx tsc -b 2>&1 | tail -10
echo "--- build labext ---"
jupyter labextension build . 2>&1 | tail -10

echo ""
echo "=== Install labextension ==="
jupyter labextension install --no-build . 2>&1 | tail -5

echo ""
echo "=== Build JupyterLab ==="
jupyter lab build --minimize=False 2>&1 | tail -15

echo ""
echo "=== Final verify ==="
jupyter labextension list 2>&1 | grep -i inline || echo "labext not found"
jupyter server extension list 2>&1 | grep inline || echo "server ext not found"

echo "=== DONE ==="
