FROM ghcr.io/open-webui/open-webui:main

# Fix numpy to avoid x86-64-v2 requirement
RUN pip install --force-reinstall --no-cache-dir "numpy<2.0" 2>&1 | tail -5

# Verify numpy/chromadb work
RUN python3 -c "import numpy; print('numpy OK:', numpy.__version__); import chromadb; print('chromadb OK')" 2>&1 | head -5
