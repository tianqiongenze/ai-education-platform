#!/bin/bash
set -e

echo "=== Phase 1b: Worker1 Docker migration ==="
echo "Step 1: Cordon worker"
kubectl cordon k8s-worker1
echo ""

echo "Step 2: Prepare docker directory on /home"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "mkdir -p /home/docker-data"
echo ""

echo "Step 3: Check disk before"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "df -h / /home"
echo ""

echo "Step 4: Drain worker pods (evict all non-DaemonSet)"
kubectl drain k8s-worker1 --ignore-daemonsets --delete-emptydir-data --grace-period=60 --timeout=120s 2>&1 || true
echo ""

echo "Step 5: Stop kubelet on worker"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "systemctl stop kubelet && sleep 3 && systemctl is-active kubelet"
echo ""

echo "Step 6: Stop docker on worker"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "systemctl stop docker.socket && systemctl stop docker && sleep 2 && systemctl is-active docker"
echo ""

echo "Step 7: Move docker data to /home"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "du -sh /var/lib/docker && mv /var/lib/docker/* /home/docker-data/ && rmdir /var/lib/docker && ls /home/docker-data/ | wc -l"
echo ""

echo "Step 8: Update daemon.json"
python3 << 'PYEOF'
import json
cfg = json.load(open("/etc/docker/daemon.json"))
cfg["data-root"] = "/home/docker-data"
json.dump(cfg, open("/etc/docker/daemon.json", "w"), indent=2)
print("Updated daemon.json")
print(json.dumps(cfg, indent=2))
PYEOF
echo ""

echo "Step 9: Start docker on worker"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "systemctl start docker && sleep 5 && docker info --format '{{.DockerRootDir}}'"
echo ""

echo "Step 10: Start kubelet on worker"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "systemctl start kubelet && sleep 10 && systemctl is-active kubelet"
echo ""

echo "Step 11: Wait for node ready"
for i in $(seq 1 60); do
  if kubectl get node k8s-worker1 2>/dev/null | grep -q "Ready"; then
    echo "Worker ready after ${i}s"
    break
  fi
  sleep 2
done
echo ""

echo "Step 12: Uncordon worker"
kubectl uncordon k8s-worker1
echo ""

echo "Step 13: Verify"
kubectl get nodes -o wide
echo ""
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "df -h / /home"
echo ""
echo "Phase 1b complete!"
