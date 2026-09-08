#!/bin/sh
ps aux | grep -E 'ollama|runner' | grep -v grep | head -10
echo "== load =="
cat /proc/loadavg
