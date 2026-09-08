#!/bin/sh
# Inspect 6599 bundle: which plugin provides inline completions & what settings it exposes
F=/opt/conda/share/jupyter/lab/static/6599.9902a78dc05c8f24.js
echo "== plugin id strings =="
grep -o '"@jupyterlab/[a-z-]*"' $F | sort -u | head
echo "== inlineCompletion context snippets =="
grep -o '.\{60\}inlineCompletion.\{60\}' $F | head -6
echo "== settings schema keys =="
grep -o '"jupyterlab[a-z.]*:[a-z-]*"' $F | sort -u | head
