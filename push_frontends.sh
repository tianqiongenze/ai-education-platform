#!/bin/bash
# Push frontends to all 4 project pods and create E2E test directories
set -e

echo "=== 1. Push Python frontend ==="
# Copy frontend to python pod
cat /tmp/frontend_python.html | kubectl exec -i -n jupyterhub jupyter-student-python -- tee /home/jovyan/work/industrial-analytics/frontend/index.html > /dev/null 2>&1
# Ensure directory exists
kubectl exec -n jupyterhub jupyter-student-python -- mkdir -p /home/jovyan/work/industrial-analytics/frontend
cat /tmp/frontend_python.html | kubectl exec -i -n jupyterhub jupyter-student-python -- tee /home/jovyan/work/industrial-analytics/frontend/index.html > /dev/null
echo "Python frontend installed"

echo ""
echo "=== 2. Push Java frontend ==="
kubectl exec -n jupyterhub jupyter-student-java -- mkdir -p /home/jovyan/work/mes-system/frontend
cat /tmp/frontend_java.html | kubectl exec -i -n jupyterhub jupyter-student-java -- tee /home/jovyan/work/mes-system/frontend/index.html > /dev/null
echo "Java frontend installed"

echo ""
echo "=== 3. Push Go frontend ==="
kubectl exec -n jupyterhub jupyter-student-go -- mkdir -p /home/jovyan/work/industrial-gateway/frontend
cat /tmp/frontend_go.html | kubectl exec -i -n jupyterhub jupyter-student-go -- tee /home/jovyan/work/industrial-gateway/frontend/index.html > /dev/null
echo "Go frontend installed"

echo ""
echo "=== 4. Push Rust frontend ==="
kubectl exec -n jupyterhub jupyter-student-rust -- mkdir -p /home/jovyan/work/security-audit/frontend
cat /tmp/frontend_rust.html | kubectl exec -i -n jupyterhub jupyter-student-rust -- tee /home/jovyan/work/security-audit/frontend/index.html > /dev/null
echo "Rust frontend installed"

echo ""
echo "=== 5. Verify all frontends ==="
kubectl exec -n jupyterhub jupyter-student-python -- ls -la /home/jovyan/work/industrial-analytics/frontend/index.html 2>&1
kubectl exec -n jupyterhub jupyter-student-java -- ls -la /home/jovyan/work/mes-system/frontend/index.html 2>&1
kubectl exec -n jupyterhub jupyter-student-go -- ls -la /home/jovyan/work/industrial-gateway/frontend/index.html 2>&1
kubectl exec -n jupyterhub jupyter-student-rust -- ls -la /home/jovyan/work/security-audit/frontend/index.html 2>&1

echo "=== DONE ==="
