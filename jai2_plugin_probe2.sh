#!/bin/sh
cd /tmp/jai/extracted/jupyter_ai-2.31.0.data/data/share/jupyter/labextensions/@jupyter-ai/core
echo "== plugin ids in bundles =="
grep -o '@jupyter-ai/core:[a-zA-Z-]*' static/*.js | sort -u
echo "== inline-completions context =="
grep -o '.\{80\}inline-completions.\{80\}' static/268.21e1dc707e5e983150f1.js | head -3
