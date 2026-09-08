#!/bin/bash
# Complete setup: install server extension + build & install labextension
set -e

echo "=== 1. Install server extension ==="
# Install as a proper Python package
mkdir -p /home/jovyan/work/jupyter-inline-completion/jupyter_inline_completion
cp /tmp/jupyter_inline_completion.py /home/jovyan/work/jupyter-inline-completion/jupyter_inline_completion/__init__.py

# Create setup.py
cat > /home/jovyan/work/jupyter-inline-completion/setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="jupyter-inline-completion",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "jupyter-server",
        "tornado",
    ],
    python_requires=">=3.9",
    jupyter_server_extension_points=[
        {"module": "jupyter_inline_completion"},
    ],
)
EOF

# Create package __init__.py for the server extension module
cat > /home/jovyan/work/jupyter-inline-completion/jupyter_inline_completion/__init__.py << 'PYEOF'
# Re-export from the main module file
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ._handler import *
PYEOF

# Copy handler
cp /tmp/jupyter_inline_completion.py /home/jovyan/work/jupyter-inline-completion/jupyter_inline_completion/_handler.py

# Install
cd /home/jovyan/work/jupyter-inline-completion
pip install -e . --no-deps 2>&1 | tail -5

echo ""
echo "=== 2. Enable server extension ==="
jupyter server extension enable --py jupyter_inline_completion 2>&1 || true
jupyter server extension list 2>&1 | grep inline

echo ""
echo "=== 3. Create labextension project ==="
mkdir -p /home/jovyan/work/jupyter-inline-completion/src
mkdir -p /home/jovyan/work/jupyter-inline-completion/schema

# Copy package.json
cp /tmp/ext_package.json /home/jovyan/work/jupyter-inline-completion/package.json

# Copy tsconfig.json
cp /tmp/ext_tsconfig.json /home/jovyan/work/jupyter-inline-completion/tsconfig.json

# Write schema
cat > /home/jovyan/work/jupyter-inline-completion/schema/plugin.json << 'EOF'
{
  "title": "AI Inline Completion",
  "description": "AI-powered ghost text inline completion settings",
  "jupyter.lab.setting-icon": "jupyter-inline-completion:icon",
  "properties": {
    "enabled": {
      "type": "boolean",
      "title": "Enable inline completion",
      "description": "Enable/disable AI ghost text inline completion",
      "default": true
    },
    "endpoint": {
      "type": "string",
      "title": "Completion endpoint",
      "description": "Server endpoint for FIM completion requests",
      "default": "/inline-completion/v1/completion"
    },
    "debounceMs": {
      "type": "number",
      "title": "Debounce delay (ms)",
      "description": "Delay before sending completion request after typing stops",
      "default": 600
    },
    "maxTokens": {
      "type": "number",
      "title": "Max tokens",
      "description": "Maximum number of tokens to generate per completion",
      "default": 32
    }
  },
  "additionalProperties": false
}
EOF

# Write the TypeScript source
cat > /home/jovyan/work/jupyter-inline-completion/src/index.ts << 'TSEOF'
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import {
  ICompletionProviderManager
} from '@jupyterlab/completer';

const PLUGIN_ID = 'jupyter-inline-completion:plugin';

const provider: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [ICompletionProviderManager],
  optional: [ISettingRegistry],
  activate: async (
    app: JupyterFrontEnd,
    manager: ICompletionProviderManager,
    settings: ISettingRegistry | null
  ) => {
    console.log('JupyterLab inline completion extension is activated!');

    let enabled = true;
    let endpoint = '/inline-completion/v1/completion';
    let debounceMs = 600;
    let maxTokens = 32;

    if (settings) {
      const setting = await settings.load(PLUGIN_ID);
      const updateSettings = () => {
        enabled = setting.get('enabled').composite as boolean;
        endpoint = setting.get('endpoint').composite as string;
        debounceMs = setting.get('debounceMs').composite as number;
        maxTokens = setting.get('maxTokens').composite as number;
      };
      updateSettings();
      setting.changed.connect(updateSettings);
    }

    const inlineProvider = {
      identifier: 'ai-inline-completion',
      name: 'AI Inline Completion',
      async fetch(
        request: any,
        context: any,
        triggerKind: number
      ): Promise<any> {
        if (!enabled) {
          return null;
        }

        const prefix = request.text ?? '';
        const suffix = request.suffix ?? '';
        const language = context?.mimeType ?? 'python';
        const filename = context?.path ?? 'untitled.py';

        // Debounce
        await new Promise(resolve => setTimeout(resolve, debounceMs));

        // Skip very short prefixes for automatic triggers
        if (triggerKind === 0 && prefix.trim().length < 3) {
          return null;
        }

        try {
          const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              prefix: prefix.slice(-1024),
              suffix: suffix.slice(0, 512),
              language: language,
              filename: filename,
              max_tokens: maxTokens
            })
          });

          if (!response.ok) {
            console.warn('Inline completion request failed:', response.status);
            return null;
          }

          const data = await response.json();

          if (data.suggestion && data.suggestion.trim()) {
            return {
              suggestions: [data.suggestion]
            };
          }
        } catch (err) {
          console.warn('Inline completion error:', err);
        }

        return null;
      }
    };

    // Register with the completion manager
    if (manager.registerInlineProvider) {
      manager.registerInlineProvider(inlineProvider);
      console.log('AI inline completion provider registered');
    } else {
      console.warn('registerInlineProvider not available on manager');
    }
  }
};

export default provider;
TSEOF

echo ""
echo "=== 4. Install build dependencies ==="
cd /home/jovyan/work/jupyter-inline-completion
jlpm install 2>&1 | tail -10

echo ""
echo "=== 5. Build labextension ==="
jlpm run build 2>&1 | tail -20

echo ""
echo "=== 6. Install labextension ==="
jupyter labextension install --no-build . 2>&1 | tail -5

echo ""
echo "=== 7. Build JupyterLab ==="
jupyter lab build --minimize=False 2>&1 | tail -10

echo ""
echo "=== 8. Verify installation ==="
jupyter labextension list 2>&1 | grep -i inline || echo "inline extension not found in list"
jupyter server extension list 2>&1 | grep inline || echo "inline server extension not found"

echo ""
echo "=== DONE ==="
