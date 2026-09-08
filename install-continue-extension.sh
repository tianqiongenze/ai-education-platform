#!/bin/bash
for pod in $(kubectl get pods -n ai-platform -l app=code-server --no-headers | grep Running | awk '{print $1}'); do
  echo "Installing Continue on $pod..."
  kubectl cp -n ai-platform /root/continue.vsix "$pod:/home/coder/continue.vsix"
  kubectl exec -n ai-platform "$pod" -- code-server --install-extension /home/coder/continue.vsix 2>&1
  echo "$pod done"
done
