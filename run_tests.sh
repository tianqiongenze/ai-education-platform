#!/bin/bash
# Spawn teacher-zhang pod and run tests
set -e

echo "=== Get hub pod ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
echo "Hub: $HUB_POD"

echo ""
echo "=== Wait for hub ==="
for i in $(seq 1 10); do
  STATUS=$(kubectl get pod -n jupyterhub $HUB_POD -o jsonpath='{.status.phase}')
  echo "  $i: $STATUS"
  [ "$STATUS" = "Running" ] && break
  sleep 5
done

echo ""
echo "=== Login to spawn teacher-zhang ==="
kubectl exec -n jupyterhub $HUB_POD -c jupyterhub -- python3 << 'PYEOF'
import urllib.request, urllib.parse, http.cookiejar
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
resp = opener.open("http://127.0.0.1:8000/ide/hub/login", timeout=10)
csrf = None
for c in cj:
    if "_xsrf" in c.name:
        csrf = c.value
        break
data = urllib.parse.urlencode({"username": "teacher-zhang", "password": "ide2026", "_xsrf": csrf or ""}).encode()
resp2 = opener.open("http://127.0.0.1:8000/ide/hub/login", data=data, timeout=10)
print("Login:", resp2.status, resp2.url)
PYEOF

echo ""
echo "=== Wait for teacher-zhang pod ==="
for i in $(seq 1 20); do
  STATUS=$(kubectl get pod -n jupyterhub jupyter-teacher-zhang -o jsonpath='{.status.phase}' 2>/dev/null)
  echo "  $i: $STATUS"
  [ "$STATUS" = "Running" ] && break
  sleep 10
done

echo ""
echo "=== Push test suite ==="
kubectl cp /tmp/comprehensive_test_suite.py jupyterhub/jupyter-teacher-zhang:/home/jovyan/work/comprehensive_test_suite.py

echo ""
echo "=== Run tests ==="
kubectl exec -n jupyterhub jupyter-teacher-zhang -- python3 /home/jovyan/work/comprehensive_test_suite.py 2>&1 | grep -v '0.00s -\|0.09s -\|Debugger warning\|frozen modules\|Debugging will\|PYDEVD\|to python to disable\|make the debugger'
