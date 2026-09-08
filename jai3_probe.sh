#!/bin/sh
# Research phase: which providers does jupyter-ai 3.1.3 ship, and does the
# platform have a local LLM endpoint we can use for inline completions?
echo "== jupyter-ai version & providers =="
pip show jupyter_ai 2>/dev/null | head -3
echo "== ai core modules in 3.x =="
python3 -c "
import jupyter_ai, os
d = os.path.dirname(jupyter_ai.__file__)
print(d)
print(sorted(os.listdir(d)))
" 2>&1 | head -10
echo "== any completion handlers in 3.x? =="
find /opt/conda/lib/python3*/site-packages/jupyter_ai* -name "*complet*" 2>/dev/null | head
echo "== config dir =="
ls ~/.jupyter/ 2>/dev/null
cat ~/.jupyter/jupyter_server_config.py 2>/dev/null | grep -iE "ai|model|provider" | head
echo "== env endpoints =="
env | grep -iE "OPENAI|ANTHROPIC|API_KEY|BASE_URL|OLLAMA|LITELLM" | sed 's/=.*KEY.*/=<redacted>/' | head
