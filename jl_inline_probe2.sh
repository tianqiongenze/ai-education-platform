#!/bin/sh
# Search ALL static bundles for inline completion plugin references
cd /opt/conda/share/jupyter/lab/static
echo "== files containing 'inlineCompletion' =="
grep -l 'inlineCompletion' *.js 2>/dev/null | head -5
echo "== files containing 'InlineCompletions' =="
grep -l 'InlineCompletions' *.js 2>/dev/null | head -5
echo "== settings package.json inline =="
grep -o '"jupyter.inlineCompletion[^,]*' /opt/conda/share/jupyter/lab/static/package.json 2>/dev/null | head -5
grep -o 'inlineCompletion[^,}]*' /opt/conda/share/jupyter/lab/static/package.json 2>/dev/null | head -5
