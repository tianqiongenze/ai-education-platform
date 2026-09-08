#!/bin/bash
# Inspect project structures across all pods
echo "=== Python: industrial-analytics ==="
kubectl exec -n jupyterhub jupyter-student-python -- find /home/jovyan/work/industrial-analytics -type f -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" -o -name "*.cfg" 2>&1 | head -40
echo "--- Frontend files ---"
kubectl exec -n jupyterhub jupyter-student-python -- find /home/jovyan/work/industrial-analytics -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.jsx" -o -name "*.vue" -o -name "*.ts" \) 2>&1 | head -20
echo "--- Test files ---"
kubectl exec -n jupyterhub jupyter-student-python -- find /home/jovyan/work/industrial-analytics -type f -name "test*" -o -name "*test*" -o -name "*spec*" 2>&1 | head -20

echo ""
echo "=== Java: mes-system ==="
kubectl exec -n jupyterhub jupyter-student-java -- find /home/jovyan/work/mes-system -type f \( -name "*.java" -o -name "*.html" -o -name "*.js" -o -name "*.xml" -o -name "*.properties" -o -name "*.yml" -o -name "*.md" \) 2>&1 | head -40
echo "--- Frontend files ---"
kubectl exec -n jupyterhub jupyter-student-java -- find /home/jovyan/work/mes-system -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.jsx" -o -name "*.vue" \) 2>&1 | head -20
echo "--- Test files ---"
kubectl exec -n jupyterhub jupyter-student-java -- find /home/jovyan/work/mes-system -type f -name "*Test*" -o -name "*test*" 2>&1 | head -20

echo ""
echo "=== Go: industrial-gateway ==="
kubectl exec -n jupyterhub jupyter-student-go -- find /home/jovyan/work/industrial-gateway -type f \( -name "*.go" -o -name "*.html" -o -name "*.js" -o -name "*.yaml" -o -name "*.yml" -o -name "*.mod" -o -name "*.md" \) 2>&1 | head -40
echo "--- Frontend files ---"
kubectl exec -n jupyterhub jupyter-student-go -- find /home/jovyan/work/industrial-gateway -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.jsx" -o -name "*.vue" \) 2>&1 | head -20
echo "--- Test files ---"
kubectl exec -n jupyterhub jupyter-student-go -- find /home/jovyan/work/industrial-gateway -type f -name "*_test.go" 2>&1 | head -20

echo ""
echo "=== Rust: security-audit ==="
kubectl exec -n jupyterhub jupyter-student-rust -- find /home/jovyan/work/security-audit -type f \( -name "*.rs" -o -name "*.html" -o -name "*.js" -o -name "*.toml" -o -name "*.md" \) 2>&1 | head -40
echo "--- Frontend files ---"
kubectl exec -n jupyterhub jupyter-student-rust -- find /home/jovyan/work/security-audit -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.jsx" -o -name "*.vue" \) 2>&1 | head -20
echo "--- Test files ---"
kubectl exec -n jupyterhub jupyter-student-rust -- find /home/jovyan/work/security-audit -type f -name "*.rs" -path "*/tests/*" 2>&1 | head -20
