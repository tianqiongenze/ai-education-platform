#!/bin/bash
set -e
echo "=== Fetching open-vsx API for continue.continue ==="
# Get the JSON response
JSON=$(kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- sh -c "curl -sL --connect-timeout 10 --max-time 30 https://open-vsx.org/api/continue/continue/latest")
echo "=== Full response (first 2000 chars) ==="
echo "$JSON" | head -c 2000
echo ""
echo "=== Download URLs ==="
echo "$JSON" | grep -o '"download":"[^"]*"' | head -10
echo "=== Files section ==="
echo "$JSON" | grep -oP '"files":\{[^}]*\}' | head -3
echo "=== Version ==="
echo "$JSON" | grep -o '"version":"[^"]*"' | head -1
