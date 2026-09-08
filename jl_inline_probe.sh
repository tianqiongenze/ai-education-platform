#!/bin/sh
# Check JupyterLab 4.6.3 bundle for the built-in inline completions plugin
M=/opt/conda/share/jupyter/lab/static/main.910e4a95b492eb7e.js
echo "inlineCompletion occurrences: $(grep -c inlineCompletion $M 2>/dev/null)"
echo "inline-completions pkg refs:"
grep -o '@jupyterlab/inline-completions' $M 2>/dev/null | sort -u
grep -o 'inline-completions:plugin' $M 2>/dev/null | sort -u
echo "completionProvider setting refs:"
grep -o 'completionProvider' $M 2>/dev/null | sort -u | head
echo "ghost-text / provideInlineCompletions:"
grep -o 'provideInlineCompletions' $M 2>/dev/null | sort -u
