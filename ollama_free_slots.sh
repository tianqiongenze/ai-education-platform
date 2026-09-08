#!/bin/sh
# Stop non-essential models to free CPU slots for qwen2.5-coder FIM completion
echo "=== BEFORE ==="
ollama ps 2>&1
echo ""
echo "=== Stopping yi:6b ==="
ollama stop yi:6b 2>&1
echo "=== Stopping bge-m3 ==="
ollama stop bge-m3 2>&1
echo ""
echo "=== AFTER ==="
ollama ps 2>&1
echo ""
echo "=== LOADAVG ==="
cat /proc/loadavg
