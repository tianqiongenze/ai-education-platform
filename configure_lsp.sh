#!/bin/bash
# Configure LSP: enable disabled language-server extensions + register pylsp + set up completion settings
set -e

echo "=== Enable disabled LSP-related extensions ==="
# These were disabled - re-enable them
jupyter labextension enable @jupyterlab/fileeditor-extension:language-server 2>&1 || true
jupyter labextension enable @jupyterlab/notebook-extension:language-server 2>&1 || true
jupyter labextension enable @jupyterlab/lsp-extension:settings 2>&1 || true
# Also enable the completer base service which was disabled
jupyter labextension enable @jupyterlab/completer-extension:base-service 2>&1 || true

echo ""
echo "=== Write LSP config for pylsp ==="
mkdir -p /opt/conda/etc/jupyter
cat > /opt/conda/etc/jupyter/jupyter_server_config.d/jupyter_lsp.json << 'EOF'
{
  "ServerApp": {
    "jpserver_extensions": {
      "jupyter_lsp": true
    }
  },
  "LanguageServerManager": {
    "language_servers": {
      "pylsp": {
        "version": 2,
        "argv": ["pylsp"],
        "languages": ["python"],
        "mime_types": ["text/x-python", "text/python"],
        "display_name": "Python LSP Server"
      }
    }
  }
}
EOF

echo "Config written. Contents:"
cat /opt/conda/etc/jupyter/jupyter_server_config.d/jupyter_lsp.json

echo ""
echo "=== Write user-level LSP settings for inline completion ==="
mkdir -p /home/jovyan/.jupyter
cat > /home/jovyan/.jupyter/lab/user-settings/@jupyter-lsp/jupyterlab-lsp/plugin.jupyterlab-settings << 'EOF'
{
  "language_servers": {
    "pylsp": {
      "configuration": {
        "plugins": {
          "jedi_completion": {
            "enabled": true,
            "include_params": true,
            "include_class_objects": true
          },
          "jedi_signature_help": {
            "enabled": true
          },
          "pyflakes": {
            "enabled": true
          },
          "pycodestyle": {
            "enabled": true,
            "maxLineLength": 120
          },
          "autopep8": {
            "enabled": false
          },
          "rope_completion": {
            "enabled": true
          },
          "rope_autoimport": {
            "enabled": true
          }
        }
      }
    }
  },
  "continuousAutocompletion": true,
  "completionTriggerChars": ["."],
  "kernelCompletionsFirst": false
}
EOF

echo "User settings written."

echo ""
echo "=== Check labextension status after enabling ==="
jupyter labextension list 2>&1 | grep -E "lsp|language-server|completer" || true

echo ""
echo "=== Verify pylsp is on PATH ==="
which pylsp && pylsp --version

echo ""
echo "=== Test pylsp responds to initialize request ==="
python3 -c "
import subprocess, json
proc = subprocess.Popen(['pylsp'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
init_msg = {
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'initialize',
    'params': {
        'processId': None,
        'rootUri': 'file:///home/jovyan',
        'capabilities': {}
    }
}
msg = json.dumps(init_msg)
content = f'Content-Length: {len(msg)}\r\n\r\n{msg}'
proc.stdin.write(content.encode())
proc.stdin.flush()
import time
time.sleep(2)
proc.stdin.close()
out = proc.stdout.read(4096)
print('pylsp response:', out[:300].decode('utf-8', errors='replace'))
proc.terminate()
" 2>&1

echo ""
echo "=== DONE ==="
