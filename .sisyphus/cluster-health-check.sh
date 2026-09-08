#!/bin/bash
echo "=== NODES ==="
kubectl get nodes -o wide
echo ""
echo "=== ALL PODS (non-Completed, non-Running) ==="
kubectl get pods -A 2>/dev/null | grep -vE 'Completed|Running' | grep -v 'NAMESPACE'
echo ""
echo "=== CRITICAL SYSTEM PODS ==="
for ns in kube-system cattle-system; do
  echo "--- $ns ---"
  kubectl get pods -n $ns -o wide 2>&1 | grep -v 'Completed'
done
echo ""
echo "=== RANCHER ==="
curl -sk http://127.0.0.1/ping 2>&1
echo ""
echo "=== DISK USAGE ==="
df -h / /home
echo ""
echo "=== TOP FREEABLE: local-path on master ==="
du -sh /opt/local-path-provisioner 2>/dev/null
