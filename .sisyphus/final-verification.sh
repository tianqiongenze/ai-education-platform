#!/bin/bash
echo "======================================================"
echo "      FINAL VERIFICATION - CLUSTER HEALTH CHECK"
echo "======================================================"
echo ""

echo "=== 1. NODE STATUS ==="
kubectl get nodes -o wide
echo ""

echo "=== 2. NON-RUNNING/NON-COMPLETED PODS ==="
kubectl get pods -A 2>/dev/null | grep -vE 'Completed|Running' | grep -v 'NAMESPACE'
echo ""

echo "=== 3. SYSTEM PODS (kube-system) ==="
kubectl get pods -n kube-system -o wide
echo ""

echo "=== 4. CATTLE-SYSTEM (Rancher agent) ==="
kubectl get pods -n cattle-system -o wide
echo ""

echo "=== 5. RANCHER DOCKER CONTAINER ==="
docker ps --filter name=rancher --format '{{.Names}} {{.Status}} {{.Ports}}'
curl -sk http://127.0.0.1/ping 2>&1
echo ""

echo "=== 6. APP PODS ==="
kubectl get pods -n dify -o wide 2>&1 | head -10
kubectl get pods -n dify-plus -o wide 2>&1 | head -10
kubectl get pods -n ai-platform -o wide 2>&1 | head -10
kubectl get pods -n monitoring -o wide 2>&1 | head -10
kubectl get pods -n ingress-nginx -o wide 2>&1 | head -5
echo ""

echo "=== 7. DISK USAGE ==="
echo "Master:"
df -h / /home
echo ""
echo "Worker:"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "df -h / /home"
echo ""

echo "=== 8. DOCKER ROOT DIRS ==="
echo "Master: $(docker info --format '{{.DockerRootDir}}')"
echo "Worker: $(ssh -o StrictHostKeyChecking=no root@10.167.2.176 "docker info --format '{{.DockerRootDir}}'")"
echo ""

echo "=== 9. DOCKER DATA SIZES ==="
echo "Master: $(du -sh /home/docker-data/ | cut -f1)"
echo "Worker: $(ssh -o StrictHostKeyChecking=no root@10.167.2.176 "du -sh /home/docker-data/ | cut -f1")"
echo ""

echo "=== 10. LOCAL-PATH DATA ==="
echo "Master:"
ls -la /opt/local-path-provisioner/ 2>&1 | head -5
du -sh /opt/local-path-provisioner/ 2>/dev/null
echo "Worker:"
ssh -o StrictHostKeyChecking=no root@10.167.2.176 "ls -la /opt/local-path-provisioner/ 2>&1 | head -5"
echo ""

echo "======================================================"
echo "                VERIFICATION COMPLETE"
echo "======================================================"
