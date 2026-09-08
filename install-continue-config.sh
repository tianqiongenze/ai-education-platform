#!/bin/bash
for pod in $(kubectl get pods -n ai-platform -l app=code-server --no-headers | grep Running | awk '{print $1}'); do
  kubectl exec -n ai-platform "$pod" -- mkdir -p /home/coder/.continue
  kubectl cp -n ai-platform /tmp/continue_config.json "$pod:/home/coder/.continue/config.json"
  echo "$pod: Config installed"
done
