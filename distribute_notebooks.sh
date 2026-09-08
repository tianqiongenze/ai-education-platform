#!/bin/bash
# Update the startup ConfigMap to distribute notebooks to each Lecture account
# Also include the code grader and operation guide

set -e

echo "=== Upload all notebooks to master /tmp ==="
# Already there from previous step

echo ""
echo "=== Create a combined ConfigMap with all notebooks ==="

# Create configmap with all 8 student + 8 teacher notebooks
kubectl create configmap lecture-notebooks \
  --namespace jupyterhub \
  --from-file=p11_student=/tmp/p11_P1.1_Python基础_学生版.ipynb \
  --from-file=p11_teacher=/tmp/p11_P1.1_Python基础_教师版.ipynb \
  --from-file=p12_student=/tmp/p12_P1.2_标准Python_学生版.ipynb \
  --from-file=p12_teacher=/tmp/p12_P1.2_标准Python_教师版.ipynb \
  --from-file=p21_student=/tmp/p21_P2.1_Pandas数据_学生版.ipynb \
  --from-file=p21_teacher=/tmp/p21_P2.1_Pandas数据_教师版.ipynb \
  --from-file=p22_student=/tmp/p22_P2.2_NumPy故障特_学生版.ipynb \
  --from-file=p22_teacher=/tmp/p22_P2.2_NumPy故障特_教师版.ipynb \
  --from-file=p33_student=/tmp/p33_P3_产线KPI仪表盘_学生版.ipynb \
  --from-file=p33_teacher=/tmp/p33_P3_产线KPI仪表盘_教师版.ipynb \
  --from-file=p41_student=/tmp/p41_P4.1_多源数据采集系统_学生版.ipynb \
  --from-file=p41_teacher=/tmp/p41_P4.1_多源数据采集系统_教师版.ipynb \
  --from-file=p55_student=/tmp/p55_P5_产线数据仓库与O_学生版.ipynb \
  --from-file=p55_teacher=/tmp/p55_P5_产线数据仓库与O_教师版.ipynb \
  --from-file=p66_student=/tmp/p66_P6_故障诊断模型与部_学生版.ipynb \
  --from-file=p66_teacher=/tmp/p66_P6_故障诊断模型与部_教师版.ipynb \
  --from-file=code_grader=/tmp/code_grader.py \
  --from-file=guide=/tmp/JUPYTERHUB-OPERATION-GUIDE.md \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "Lecture notebooks configmap created"

echo ""
echo "=== Update startup script to distribute notebooks based on username ==="

cat << 'STARTEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: jupyterhub-startup
  namespace: jupyterhub
data:
  startup.sh: |
    #!/bin/bash
    # Auto-configure jupyter-ai + distribute notebooks based on username
    # Runs on every pod startup
    
    USERNAME=$(echo $JUPYTERHUB_USER)
    WORK=/home/jovyan/work
    
    mkdir -p $WORK
    mkdir -p /home/jovyan/.jupyter
    
    # 1. Create jupyter-ai config
    cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAICONFIG'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    os.environ["OPENAI_BASE_URL"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG
    
    # Also create fallback configs
    cat > /home/jovyan/.jupyter/jupyter_ai_config_tiny.py << 'JAICONFIG2'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "tinyllama:latest"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG2
    
    cat > /home/jovyan/.jupyter/jupyter_ai_config_litellm.py << 'JAICONFIG3'
    import os
    os.environ["OPENAI_API_KEY"] = "sk-ai-platform-master"
    os.environ["OPENAI_API_BASE"] = "http://10.108.11.54:4000/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://10.108.11.54:4000/v1"
    c.AiProvider.api_key = "sk-ai-platform-master"
    JAICONFIG3
    
    # Add env vars to bashrc
    grep -q 'OPENAI_API_BASE' /home/jovyan/.bashrc || cat >> /home/jovyan/.bashrc << 'BASHRC'
    
    # Jupyter AI configuration (auto-configured)
    export OPENAI_API_KEY="ollama"
    export OPENAI_API_BASE="http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    export OPENAI_BASE_URL="http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    BASHRC
    
    # 2. Distribute notebooks based on username
    NB_DIR=/tmp/notebooks
    mkdir -p $NB_DIR
    
    case "$USERNAME" in
      Lecture-P1|lecture-p1)
        cp $NB_DIR/p11_student $WORK/p11_P1.1_Python基础_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p12_student $WORK/p12_P1.2_标准Python_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p11_teacher $WORK/p11_P1.1_Python基础_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p12_teacher $WORK/p12_P1.2_标准Python_教师版.ipynb 2>/dev/null || true
        ;;
      Lecture-P2|lecture-p2)
        cp $NB_DIR/p21_student $WORK/p21_P2.1_Pandas数据_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p22_student $WORK/p22_P2.2_NumPy故障特_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p21_teacher $WORK/p21_P2.1_Pandas数据_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p22_teacher $WORK/p22_P2.2_NumPy故障特_教师版.ipynb 2>/dev/null || true
        ;;
      Lecture-P3|lecture-p3)
        cp $NB_DIR/p33_student $WORK/p33_P3_产线KPI仪表盘_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p33_teacher $WORK/p33_P3_产线KPI仪表盘_教师版.ipynb 2>/dev/null || true
        ;;
      Lecture-P4|lecture-p4)
        cp $NB_DIR/p41_student $WORK/p41_P4.1_多源数据采集系统_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p41_teacher $WORK/p41_P4.1_多源数据采集系统_教师版.ipynb 2>/dev/null || true
        ;;
      Lecture-P5|lecture-p5)
        cp $NB_DIR/p55_student $WORK/p55_P5_产线数据仓库与O_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p55_teacher $WORK/p55_P5_产线数据仓库与O_教师版.ipynb 2>/dev/null || true
        ;;
      Lecture-P6|lecture-p6)
        cp $NB_DIR/p66_student $WORK/p66_P6_故障诊断模型与部_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p66_teacher $WORK/p66_P6_故障诊断模型与部_教师版.ipynb 2>/dev/null || true
        ;;
      teacher-zhang)
        # Teacher gets ALL notebooks
        cp $NB_DIR/p11_student $WORK/p11_P1.1_Python基础_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p12_student $WORK/p12_P1.2_标准Python_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p21_student $WORK/p21_P2.1_Pandas数据_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p22_student $WORK/p22_P2.2_NumPy故障特_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p33_student $WORK/p33_P3_产线KPI仪表盘_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p41_student $WORK/p41_P4.1_多源数据采集系统_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p55_student $WORK/p55_P5_产线数据仓库与O_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p66_student $WORK/p66_P6_故障诊断模型与部_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p11_teacher $WORK/p11_P1.1_Python基础_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p12_teacher $WORK/p12_P1.2_标准Python_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p21_teacher $WORK/p21_P2.1_Pandas数据_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p22_teacher $WORK/p22_P2.2_NumPy故障特_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p33_teacher $WORK/p33_P3_产线KPI仪表盘_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p41_teacher $WORK/p41_P4.1_多源数据采集系统_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p55_teacher $WORK/p55_P5_产线数据仓库与O_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p66_teacher $WORK/p66_P6_故障诊断模型与部_教师版.ipynb 2>/dev/null || true
        ;;
    esac
    
    # 3. Copy code grader and guide for all users
    cp $NB_DIR/code_grader $WORK/code_grader.py 2>/dev/null || true
    cp $NB_DIR/guide $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null || true
    
    # 4. Install pycodestyle for grading if not present
    pip install --quiet pycodestyle 2>/dev/null || true
    
    echo "Startup complete for user: $USERNAME"
STARTEOF

echo "Startup script configmap updated"

echo ""
echo "=== Update JupyterHub config to mount both configmaps ==="
# Get current config
kubectl get configmap jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_config2.py

# We need to add the lecture-notebooks volume to the spawner
# Check if volumes already include notebook configmap
grep -c 'lecture-notebooks' /tmp/jhub_config2.py || true

# Append volume for notebooks
cat >> /tmp/jhub_config2.py << 'CONFIGAPPEND'

# Mount lecture notebooks configmap (for auto-distribution on startup)
c.KubeSpawner.volumes = [
    {
        "name": "workspace-{username}",
        "persistentVolumeClaim": {"claimName": "claim-{username}"},
    },
    {
        "name": "startup-script",
        "configMap": {"name": "jupyterhub-startup"},
    },
    {
        "name": "lecture-notebooks",
        "configMap": {"name": "lecture-notebooks"},
    }
]
c.KubeSpawner.volume_mounts = [
    {
        "name": "workspace-{username}",
        "mountPath": "/home/jovyan/work",
    },
    {
        "name": "startup-script",
        "mountPath": "/tmp/startup.sh",
        "subPath": "startup.sh",
    },
    {
        "name": "lecture-notebooks",
        "mountPath": "/tmp/notebooks",
    }
]
CONFIGAPPEND

# Apply
kubectl create configmap jupyterhub-config -n jupyterhub \
  --from-file=jupyterhub_config.py=/tmp/jhub_config2.py \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub config updated with notebook distribution"

# Restart hub
echo "Restarting hub..."
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
  echo "Hub restarted"
fi

echo ""
echo "=== DONE ==="
echo ""
echo "When any Lecture-PX user logs in:"
echo "  1. Pod is created with PVC (5Gi persistent storage)"
echo "  2. Startup script runs automatically:"
echo "     - jupyter-ai configured (pointing to ollama-master)"
echo "     - Code grader installed"
echo "     - Corresponding notebooks distributed to /home/jovyan/work/"
echo "  3. User can immediately use jupyter-ai and run code_grader.py"
echo ""
echo "Account → Notebook mapping:"
echo "  Lecture-P1 → P1.1 Python基础 + P1.2 标准Python工程"
echo "  Lecture-P2 → P2.1 Pandas数据处理 + P2.2 NumPy故障特征"
echo "  Lecture-P3 → P3 产线KPI仪表盘"
echo "  Lecture-P4 → P4.1 多源数据采集系统"
echo "  Lecture-P5 → P5 产线数据仓库与ORM"
echo "  Lecture-P6 → P6 故障诊断模型与部署"
echo "  teacher-zhang → ALL 8 notebooks + code grader + guide"
