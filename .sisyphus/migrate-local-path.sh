#!/bin/bash
set -e

echo "=== Phase 2: Master local-path-provisioner migration ==="
echo "Current data:"
ls -la /opt/local-path-provisioner/ | head -20
du -sh /opt/local-path-provisioner/

echo ""
echo "Step 1: Create target directory on /home"
mkdir -p /home/k8s-local-path

echo ""
echo "Step 2: Copy data (preserving all attributes)"
cp -a /opt/local-path-provisioner/* /home/k8s-local-path/
sync
echo "Copy complete. Verifying..."
ls /home/k8s-local-path/ | head -10
du -sh /home/k8s-local-path/

echo ""
echo "Step 3: Rename old directory and create symlink"
mv /opt/local-path-provisioner /opt/local-path-provisioner.bak
ln -s /home/k8s-local-path /opt/local-path-provisioner
echo "Symlink created:"
ls -la /opt/local-path-provisioner

echo ""
echo "Step 4: Verify local-path-provisioner pod still runs"
kubectl get pods -n local-path-storage -o wide

echo ""
echo "Step 5: Check if pods using local-path PVs are healthy"
kubectl get pods -n monitoring -l app=loki-stack -o wide 2>&1 | head -5
kubectl get pods -n ai-platform -l app=open-webui -o wide 2>&1 | head -5

echo ""
echo "Phase 2 complete!"
df -h /
