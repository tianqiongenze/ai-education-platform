#!/bin/bash
echo "=== Problem pods on master ==="
kubectl get pods -A --field-selector spec.nodeName=k8s-master 2>/dev/null | grep -E "CrashLoop|Error|Completed|0/"
echo ""
echo "=== kube-controller-manager logs ==="
kubectl logs -n kube-system kube-controller-manager-k8s-master --tail=20 2>&1 | head -30
echo ""
echo "=== calico-kube-controllers logs ==="
kubectl logs -n kube-system calico-kube-controllers-658d97c59c-6p566 --tail=10 2>&1
echo ""
echo "=== cattle-cluster-agent logs ==="
kubectl logs -n cattle-system cattle-cluster-agent-7764b5fc74-zrjvb --tail=10 2>&1 | head -20
echo ""
echo "=== Master disk usage ==="
df -h / /home
echo ""
echo "=== Old docker data cleanup ==="
rm -rf /var/lib/docker/*
echo "Cleanup done"
df -h /
