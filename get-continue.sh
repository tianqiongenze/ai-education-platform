#!/bin/bash
URL=$(kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- sh -c "curl -sL --connect-timeout 10 --max-time 30 https://open-vsx.org/api/continue/continue/latest | grep -oP 'https://open-vsx.org/api/continue/continue/[^\"]+\.vsix' | head -1")
echo "VSIX URL: $URL"
if [ -n "$URL" ]; then
  echo "Downloading..."
  kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- sh -c "curl -sL --connect-timeout 30 --max-time 600 '$URL' -o /tmp/continue.vsix && echo 'Downloaded OK'"
  kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- ls -lh /tmp/continue.vsix
  echo "Installing..."
  kubectl exec -n ai-platform code-server-89d9f48d5-bmn76 -- code-server --install-extension /tmp/continue.vsix --force
else
  echo "ERROR: Could not find VSIX URL"
fi
