#!/bin/bash
# Configure LSP part 2: create settings dirs, write pylsp settings, test pylsp
set -e

echo "=== Create user settings directory tree ==="
mkdir -p "/home/jovyan/.jupyter/lab/user-settings/@jupyter-lsp/jupyterlab-lsp"
mkdir -p "/home/jovyan/.jupyter/lab/user-settings/@jupyterlab/notebook-extension"
mkdir -p "/home/jovyan/.jupyter/lab/user-settings/@jupyterlab/fileeditor-extension"

echo ""
echo "=== Write LSP completion settings ==="
cat > "/home/jovyan/.jupyter/lab/user-settings/@jupyter-lsp/jupyterlab-lsp/plugin.jupyterlab-settings" << 'EOF'
{
  "language_servers": {
    "pylsp": {
      "configuration": {
        "plugins": {
          "jedi_completion": {
            "enabled": true,
            "include_params": true,
            "include_class_objects": true,
            "include_dictionary": true
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
          },
          "folding": {
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

echo "LSP settings written."

echo ""
echo "=== Write notebook extension settings to enable inline completion ==="
cat > "/home/jovyan/.jupyter/lab/user-settings/@jupyterlab/notebook-extension/completer.jupyterlab-settings" << 'EOF'
{
  "continuousHinting": true,
  "showContinuousAutocompletion": true,
  "autoCompletion": true,
  "autoCompletionDelay": 300
}
EOF

echo "Notebook completer settings written."

echo ""
echo "=== Write fileeditor settings to enable LSP ==="
cat > "/home/jovyan/.jupyter/lab/user-settings/@jupyterlab/fileeditor-extension/plugin.jupyterlab-settings" << 'EOF'
{
  "languageServerCompletion": true
}
EOF

echo "Fileeditor settings written."

echo ""
echo "=== Verify settings files ==="
ls -la /home/jovyan/.jupyter/lab/user-settings/@jupyter-lsp/jupyterlab-lsp/
ls -la /home/jovyan/.jupyter/lab/user-settings/@jupyterlab/notebook-extension/
ls -la /home/jovyan/.jupyter/lab/user-settings/@jupyterlab/fileeditor-extension/

echo ""
echo "=== Verify pylsp on PATH ==="
which pylsp && pylsp --version

echo ""
echo "=== Test pylsp LSP initialize ==="
python3 << 'PYEOF'
import subprocess, json, time, sys

proc = subprocess.Popen(
    ['pylsp'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

init_msg = {
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'initialize',
    'params': {
        'processId': None,
        'rootUri': 'file:///home/jovyan',
        'capabilities': {
            'textDocument': {
                'completion': {
                    'completionItem': {'snippetSupport': True}
                }
            }
        }
    }
}

msg = json.dumps(init_msg)
content = f'Content-Length: {len(msg)}\r\n\r\n{msg}'
proc.stdin.write(content.encode())
proc.stdin.flush()

time.sleep(3)

# Try to read response
import select
ready = select.select([proc.stdout], [], [], 2.0)
if ready[0]:
    data = proc.stdout.read1(4096) if hasattr(proc.stdout, 'read1') else proc.stdout.read(4096)
    print(f'pylsp responded ({len(data)} bytes):')
    print(data[:500].decode('utf-8', errors='replace'))
else:
    print('No response from pylsp (timeout)')

proc.terminate()
proc.wait()
print('pylsp LSP test done')
PYEOF

echo ""
echo "=== DONE ==="
