#!/bin/bash
set -e
VSIX_URL="https://open-vsx.org/api/Continue/continue/alpine-x64/1.3.38/file/Continue.continue-1.3.38@alpine-x64.vsix"
echo "=== Downloading Continue.dev VSIX ==="
echo "URL: $VSIX_URL"
kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- sh -c "curl -sL --connect-timeout 30 --max-time 600 '$VSIX_URL' -o /tmp/continue.vsix && echo 'Download complete'"
echo "=== File size ==="
kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- ls -lh /tmp/continue.vsix
echo "=== Installing extension ==="
kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- code-server --install-extension /tmp/continue.vsix --force
echo "=== Verify installation ==="
kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- code-server --list-extensions | grep -i continue
echo "=== DONE ==="
