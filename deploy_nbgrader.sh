#!/bin/bash
# Install and configure nbgrader for JupyterHub
# This replaces manual code_grader.py with native JupyterHub assignment system
set -e

echo "============================================================"
echo "Part 1: Install nbgrader on all JupyterHub pods"
echo "============================================================"

# Update startup script to install nbgrader for ALL users
kubectl get cm jupyterhub-startup -n jupyterhub -o jsonpath='{.data.startup\.sh}' > /tmp/startup_nbgrader.sh

# Add nbgrader installation + exchange directory setup
python3 << 'PYEOF'
content = open('/tmp/startup_nbgrader.sh').read()

# Add nbgrader install after pycodestyle
old_pip = "pip install --quiet pycodestyle"
new_pip = """pip install --quiet pycodestyle 2>/dev/null
    pip install --quiet nbgrader 2>/dev/null
    
    # Setup nbgrader exchange directory (shared between users)
    mkdir -p /srv/nbgrader/exchange 2>/dev/null
    mkdir -p /home/jovyan/work/nbgrader 2>/dev/null
    
    # Create nbgrader config for each user
    case "$USERNAME" in
      teacher-zhang|Lecture-*|lecture-*|teacher-*)
        # Teachers: full nbgrader config (create/assign/grade)
        mkdir -p /home/jovyan/work/nbgrader
        cat > /home/jovyan/work/nbgrader/nbgrader_config.py << 'NBGC'
import os
c = get_config()
# Exchange directory (shared)
c.Exchange.exchange_dir = '/srv/nbgrader/exchange'
c.Exchange.cache_dir = '/srv/nbgrader/cache'
# Course id (default)
c.CourseDirectory.course_id = 'default'
c.CourseDirectory.root = '/home/jovyan/work/nbgrader'
# Auto-create directories
c.CourseDirectory.autocreate = True
NBGC
        echo "  nbgrader configured for teacher: $USERNAME"
        ;;
      *)
        # Students: simple config (submit only)
        mkdir -p /home/jovyan/work/nbgrader
        cat > /home/jovyan/work/nbgrader/nbgrader_config.py << 'NBGC'
import os
c = get_config()
c.Exchange.exchange_dir = '/srv/nbgrader/exchange'
c.Exchange.cache_dir = '/srv/nbgrader/cache'
c.CourseDirectory.course_id = 'default'
c.CourseDirectory.root = '/home/jovyan/work/nbgrader'
c.CourseDirectory.autocreate = True
NBGC
        echo "  nbgrader configured for student: $USERNAME"
        ;;
    esac"""

if old_pip in content:
    content = content.replace(old_pip, new_pip)
    print("nbgrader installation added to startup")
else:
    print("WARNING: pycodestyle line not found, appending")
    content += new_pip

open('/tmp/startup_nbgrader.sh', 'w').write(content)
PYEOF

kubectl create configmap jupyterhub-startup -n jupyterhub \
  --from-file=startup.sh=/tmp/startup_nbgrader.sh \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "Startup script updated with nbgrader"

echo ""
echo "============================================================"
echo "Part 2: Install nbgrader on teacher-zhang pod now"
echo "============================================================"

kubectl exec -n jupyterhub jupyter-teacher-zhang -- pip install --quiet nbgrader 2>&1 | tail -3
echo "nbgrader installed on teacher-zhang"

# Create exchange directory
kubectl exec -n jupyterhub jupyter-teacher-zhang -- mkdir -p /srv/nbgrader/exchange /srv/nbgrader/cache 2>/dev/null || true

# Create nbgrader config for teacher
kubectl exec -n jupyterhub jupyter-teacher-zhang -- bash -c '
mkdir -p /home/jovyan/work/nbgrader
cat > /home/jovyan/work/nbgrader/nbgrader_config.py << "NBGC"
import os
c = get_config()
c.Exchange.exchange_dir = "/srv/nbgrader/exchange"
c.Exchange.cache_dir = "/srv/nbgrader/cache"
c.CourseDirectory.course_id = "default"
c.CourseDirectory.root = "/home/jovyan/work/nbgrader"
c.CourseDirectory.autocreate = True
NBGC
' 2>&1

echo "nbgrader config created for teacher-zhang"

echo ""
echo "============================================================"
echo "Part 3: Verify nbgrader works"
echo "============================================================"

# Check nbgrader is installed
kubectl exec -n jupyterhub jupyter-teacher-zhang -- python3 -c "import nbgrader; print('nbgrader version:', nbgrader.__version__)" 2>&1

# Check labextension
kubectl exec -n jupyterhub jupyter-teacher-zhang -- jupyter labextension list 2>&1 | grep -i nbgrader || echo "nbgrader labextension checking..."

# Create a sample assignment to verify
kubectl exec -n jupyterhub jupyter-teacher-zhang -- bash -c '
cd /home/jovyan/work/nbgrader
mkdir -p source/ps1
cat > source/ps1/problem1.ipynb << "NB"
{
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": ["# Problem 1: Add two numbers\n"]},
  {"cell_type": "code", "execution_count": null, "metadata": {"nbgrader": {"grade": true, "solution": true}}, "source": ["def add(a, b):\n", "    ### BEGIN SOLUTION\n", "    return a + b\n", "    ### END SOLUTION\n"], "outputs": []},
  {"cell_type": "code", "execution_count": null, "metadata": {"nbgrader": {"grade": true, "task": false, "solution": false}}, "source": ["assert add(1, 2) == 3\n", "assert add(-1, 1) == 0\n"], "outputs": []}
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 5
}
NB
echo "Sample assignment created"
' 2>&1

# Test nbgrader generate_assignment
kubectl exec -n jupyterhub jupyter-teacher-zhang -- bash -c '
cd /home/jovyan/work/nbgrader
nbgrader generate_assignment ps1 2>&1 || echo "generate_assignment may need nbgrader_config"
ls -la release/ps1/ 2>&1 || echo "release dir not created"
' 2>&1

echo ""
echo "=== Test: Release assignment ==="
kubectl exec -n jupyterhub jupyter-teacher-zhang -- bash -c '
cd /home/jovyan/work/nbgrader
nbgrader release_assignment ps1 2>&1 || echo "release needs exchange setup"
ls -la /srv/nbgrader/exchange/ 2>&1 || echo "exchange not accessible"
' 2>&1

echo ""
echo "============================================================"
echo "Part 4: Restart hub to apply nbgrader to all new pods"
echo "============================================================"
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "============================================================"
echo "Part 5: Final status"
echo "============================================================"
sleep 20

echo "=== Pods ==="
kubectl get pods -n jupyterhub 2>&1 | head -5

echo ""
echo "=== nbgrader on teacher-zhang ==="
kubectl exec -n jupyterhub jupyter-teacher-zhang -- python3 -c "import nbgrader; print('OK:', nbgrader.__version__)" 2>&1

echo ""
echo "=== nbgrader directory structure ==="
kubectl exec -n jupyterhub jupyter-teacher-zhang -- ls -la /home/jovyan/work/nbgrader/ 2>&1

echo ""
echo "=== Exchange directory ==="
kubectl exec -n jupyterhub jupyter-teacher-zhang -- ls -la /srv/nbgrader/ 2>&1

echo ""
echo "=== Node load ==="
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "nbgrader 部署完成"
echo "============================================================"
echo ""
echo "教师操作流程（简化版）："
echo "  1. 在 JupyterLab 中创建 Notebook（标记答案区和测试区）"
echo "  2. 终端运行: nbgrader generate_assignment <作业ID>"
echo "  3. 发布作业: nbgrader release_assignment <作业ID>"
echo "  4. 学生提交: nbgrader submit <作业ID>"
echo "  5. 自动评分: nbgrader autograde <作业ID>"
echo "  6. 返回反馈: nbgrader generate_feedback <作业ID>"
echo "  7. 导出成绩: nbgrader export"
echo ""
echo "学生操作流程："
echo "  1. 查看作业: nbgrader list"
echo "  2. 获取作业: nbgrader fetch <作业ID>"
echo "  3. 完成后提交: nbgrader submit <作业ID>"
echo ""
echo "所有用户（教师和学生）登录后自动安装 nbgrader"
