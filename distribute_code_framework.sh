#!/bin/bash
# Update the lecture-notebooks ConfigMap to include student code framework files
# Also update the startup script to distribute them

set -e

echo "=== 1. Add student code framework to lecture-notebooks ConfigMap ==="

# Rebuild the configmap with both notebooks AND code framework files
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
  --from-file=p11_exercises=/tmp/p11_exercises.py \
  --from-file=p12_template=/tmp/p12_template.py \
  --from-file=p21_pipeline=/tmp/p21_pipeline.py \
  --from-file=p22_features=/tmp/p22_features.py \
  --from-file=p33_dashboard=/tmp/p33_dashboard.py \
  --from-file=p41_collector=/tmp/p41_collector.py \
  --from-file=p55_warehouse=/tmp/p55_warehouse.py \
  --from-file=p66_ml_service=/tmp/p66_ml_service.py \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "ConfigMap updated with student code framework files"

echo ""
echo "=== 2. Update startup script to distribute code framework ==="

cat << 'STARTEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: jupyterhub-startup
  namespace: jupyterhub
data:
  startup.sh: |
    #!/bin/bash
    # Auto-configure jupyter-ai + distribute notebooks + code framework
    # Runs on every pod startup
    
    USERNAME=$(echo $JUPYTERHUB_USER)
    WORK=/home/jovyan/work
    NB_DIR=/tmp/notebooks
    
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
    
    # Fallback configs
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
    
    # 2. Distribute notebooks + code framework based on username
    mkdir -p $WORK
    
    # Create a student_code directory for code frameworks
    mkdir -p $WORK/student_code_framework
    
    case "$USERNAME" in
      Lecture-P1|lecture-p1)
        cp $NB_DIR/p11_student $WORK/p11_P1.1_Python基础_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p12_student $WORK/p12_P1.2_标准Python_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p11_teacher $WORK/p11_P1.1_Python基础_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p12_teacher $WORK/p12_P1.2_标准Python_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p11_exercises $WORK/student_code_framework/p11_exercises.py 2>/dev/null || true
        cp $NB_DIR/p12_template $WORK/student_code_framework/p12_template.py 2>/dev/null || true
        ;;
      Lecture-P2|lecture-p2)
        cp $NB_DIR/p21_student $WORK/p21_P2.1_Pandas数据_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p22_student $WORK/p22_P2.2_NumPy故障特_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p21_teacher $WORK/p21_P2.1_Pandas数据_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p22_teacher $WORK/p22_P2.2_NumPy故障特_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p21_pipeline $WORK/student_code_framework/p21_pipeline.py 2>/dev/null || true
        cp $NB_DIR/p22_features $WORK/student_code_framework/p22_features.py 2>/dev/null || true
        ;;
      Lecture-P3|lecture-p3)
        cp $NB_DIR/p33_student $WORK/p33_P3_产线KPI仪表盘_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p33_teacher $WORK/p33_P3_产线KPI仪表盘_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p33_dashboard $WORK/student_code_framework/p33_dashboard.py 2>/dev/null || true
        ;;
      Lecture-P4|lecture-p4)
        cp $NB_DIR/p41_student $WORK/p41_P4.1_多源数据采集系统_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p41_teacher $WORK/p41_P4.1_多源数据采集系统_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p41_collector $WORK/student_code_framework/p41_collector.py 2>/dev/null || true
        ;;
      Lecture-P5|lecture-p5)
        cp $NB_DIR/p55_student $WORK/p55_P5_产线数据仓库与O_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p55_teacher $WORK/p55_P5_产线数据仓库与O_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p55_warehouse $WORK/student_code_framework/p55_warehouse.py 2>/dev/null || true
        ;;
      Lecture-P6|lecture-p6)
        cp $NB_DIR/p66_student $WORK/p66_P6_故障诊断模型与部_学生版.ipynb 2>/dev/null || true
        cp $NB_DIR/p66_teacher $WORK/p66_P6_故障诊断模型与部_教师版.ipynb 2>/dev/null || true
        cp $NB_DIR/p66_ml_service $WORK/student_code_framework/p66_ml_service.py 2>/dev/null || true
        ;;
      teacher-zhang)
        # Teacher gets ALL notebooks + ALL code frameworks
        for prefix in p11 p12 p21 p22 p33 p41 p55 p66; do
          cp $NB_DIR/${prefix}_student $WORK/ 2>/dev/null || true
          cp $NB_DIR/${prefix}_teacher $WORK/ 2>/dev/null || true
        done
        # Rename notebooks to proper names
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
        # All code frameworks
        cp $NB_DIR/p11_exercises $WORK/student_code_framework/p11_exercises.py 2>/dev/null || true
        cp $NB_DIR/p12_template $WORK/student_code_framework/p12_template.py 2>/dev/null || true
        cp $NB_DIR/p21_pipeline $WORK/student_code_framework/p21_pipeline.py 2>/dev/null || true
        cp $NB_DIR/p22_features $WORK/student_code_framework/p22_features.py 2>/dev/null || true
        cp $NB_DIR/p33_dashboard $WORK/student_code_framework/p33_dashboard.py 2>/dev/null || true
        cp $NB_DIR/p41_collector $WORK/student_code_framework/p41_collector.py 2>/dev/null || true
        cp $NB_DIR/p55_warehouse $WORK/student_code_framework/p55_warehouse.py 2>/dev/null || true
        cp $NB_DIR/p66_ml_service $WORK/student_code_framework/p66_ml_service.py 2>/dev/null || true
        ;;
    esac
    
    # 3. Copy code grader and guide for all users
    cp $NB_DIR/code_grader $WORK/code_grader.py 2>/dev/null || true
    cp $NB_DIR/guide $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null || true
    
    # 4. Install pycodestyle for grading
    pip install --quiet pycodestyle 2>/dev/null || true
    
    echo "Startup complete for user: $USERNAME"
    echo "  Notebooks: $(ls $WORK/*.ipynb 2>/dev/null | wc -l)"
    echo "  Code files: $(ls $WORK/student_code_framework/*.py 2>/dev/null | wc -l)"
STARTEOF

echo "Startup script updated with code framework distribution"

echo ""
echo "=== 3. Restart hub to pick up changes ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
  echo "Hub restarted"
fi

echo ""
echo "=== DONE ==="
echo ""
echo "Lecture account → Code framework mapping:"
echo "  Lecture-P1 → p11_exercises.py + p12_template.py"
echo "  Lecture-P2 → p21_pipeline.py + p22_features.py"
echo "  Lecture-P3 → p33_dashboard.py"
echo "  Lecture-P4 → p41_collector.py"
echo "  Lecture-P5 → p55_warehouse.py"
echo "  Lecture-P6 → p66_ml_service.py"
echo "  teacher-zhang → ALL 8 code framework files"
echo ""
echo "Each Lecture account also gets:"
echo "  - Corresponding student + teacher notebooks"
echo "  - code_grader.py (for AI grading)"
echo "  - JUPYTERHUB-OPERATION-GUIDE.md"
echo "  - jupyter-ai pre-configured"
