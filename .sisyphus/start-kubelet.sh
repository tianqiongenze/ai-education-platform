#!/bin/bash
echo "=== Docker disk usage before cleanup ==="
du -sh /home/docker-data/
du -sh /var/lib/docker/ 2>/dev/null
echo "=== Starting kubelet ==="
systemctl start kubelet
sleep 10
systemctl is-active kubelet
echo "=== Waiting for node ready ==="
for i in $(seq 1 60); do
  if kubectl get node k8s-master 2>/dev/null | grep -q "Ready"; then
    echo "Node ready after ${i}s"
    break
  fi
  sleep 2
done
kubectl get node
kubectl get pods -A --field-selector spec.nodeName=k8s-master 2>/dev/null | head -30
