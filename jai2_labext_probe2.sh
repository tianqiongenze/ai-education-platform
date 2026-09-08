#!/bin/sh
cd /tmp/jai/extracted
find . -name "package.json" -path "*labext*" | head -5
echo "=="
find . -maxdepth 6 -type d -name "@jupyter-ai" -o -maxdepth 6 -type d -name "jupyter-ai*" -path "*labext*" | head
