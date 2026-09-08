#!/bin/sh
cd /tmp/jai/extracted/jupyter_ai-2.31.0.data/data/share/jupyter/labextensions/@jupyter-ai/core
echo "== plugin.json =="
cat schemas/@jupyter-ai/core/plugin.json
echo ""
echo "== inline completion related bundle refs =="
grep -o 'inline-completion[a-zA-Z:.-]*' static/*.js 2>/dev/null | sort -u | head
grep -l 'InlineCompletion' static/*.js 2>/dev/null | head -3
