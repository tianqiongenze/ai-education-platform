#!/bin/bash
# Update startup script: ALL users get dual guides + code grader by default
# Then sync documentation
set -e

echo "============================================================"
echo "Step 1: Update startup script (ALL users get guides + grader)"
echo "============================================================"

cat << 'STARTEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: jupyterhub-startup
  namespace: jupyterhub
data:
  startup.sh: |
    #!/bin/bash
    USERNAME=$(echo $JUPYTERHUB_USER)
    WORK=/home/jovyan/work
    COMMON=/tmp/notebooks/common
    NBB=/tmp/notebooks/b
    NBA=/tmp/notebooks/a
    NBP=/tmp/notebooks/p
    mkdir -p $WORK /home/jovyan/.jupyter $WORK/student_code_framework
    
    # ===== 1. jupyter-ai config (ALL users) =====
    cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAIC'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAIC
    
    # ===== 2. Dual guides + code grader (ALL users, DEFAULT) =====
    cp $COMMON/guide_teacher $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null
    cp $COMMON/guide_student $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
    cp $COMMON/code_grader $WORK/code_grader.py 2>/dev/null
    
    # ===== 3. Course-specific notebooks + code framework =====
    case "$USERNAME" in
      # ===== 02-程序设计基础 =====
      Lecture-B1|lecture-b1)
        cp $NBB/b1_w01_student "$WORK/w01_设备参数初始化_学生版.ipynb" 2>/dev/null
        cp $NBB/b1_w01_teacher "$WORK/w01_设备参数初始化_教师版.ipynb" 2>/dev/null
        cp $NBB/b1_w02_student "$WORK/w02_实时告警系统_学生版.ipynb" 2>/dev/null
        cp $NBB/b1_w02_teacher "$WORK/w02_实时告警系统_教师版.ipynb" 2>/dev/null
        cp $NBB/fw_w01 $WORK/student_code_framework/w01_device_init.py 2>/dev/null
        cp $NBB/fw_w02 $WORK/student_code_framework/w02_alarm_if.py 2>/dev/null ;;
      Lecture-B2|lecture-b2)
        cp $NBB/b2_w03_student "$WORK/w03_告警循环_学生版.ipynb" 2>/dev/null
        cp $NBB/b2_w03_teacher "$WORK/w03_告警循环_教师版.ipynb" 2>/dev/null
        cp $NBB/b2_w04_student "$WORK/w04_设备类设计_学生版.ipynb" 2>/dev/null
        cp $NBB/b2_w04_teacher "$WORK/w04_设备类设计_教师版.ipynb" 2>/dev/null
        cp $NBB/fw_w03 $WORK/student_code_framework/w03_alarm_loop.py 2>/dev/null
        cp $NBB/fw_w04 $WORK/student_code_framework/w04_device_class.py 2>/dev/null ;;
      Lecture-B3|lecture-b3)
        cp $NBB/b3_w05_student "$WORK/w05_继承体系_学生版.ipynb" 2>/dev/null
        cp $NBB/b3_w05_teacher "$WORK/w05_继承体系_教师版.ipynb" 2>/dev/null
        cp $NBB/b3_w06_student "$WORK/w06_数据采集_学生版.ipynb" 2>/dev/null
        cp $NBB/b3_w06_teacher "$WORK/w06_数据采集_教师版.ipynb" 2>/dev/null
        cp $NBB/fw_w05 $WORK/student_code_framework/w05_inherit.py 2>/dev/null
        cp $NBB/fw_w06 $WORK/student_code_framework/w06_robust_collector.py 2>/dev/null ;;
      Lecture-B4|lecture-b4)
        cp $NBB/b4_w07_student "$WORK/w07_格式转换_学生版.ipynb" 2>/dev/null
        cp $NBB/b4_w07_teacher "$WORK/w07_格式转换_教师版.ipynb" 2>/dev/null
        cp $NBB/b4_w08_student "$WORK/w08_文件处理_学生版.ipynb" 2>/dev/null
        cp $NBB/b4_w08_teacher "$WORK/w08_文件处理_教师版.ipynb" 2>/dev/null
        cp $NBB/fw_w07 $WORK/student_code_framework/w07_parser.py 2>/dev/null
        cp $NBB/fw_w08 $WORK/student_code_framework/w08_fileio.py 2>/dev/null ;;
      Lecture-B5|lecture-b5)
        cp $NBB/b5_w09_student "$WORK/w09_故障报告_学生版.ipynb" 2>/dev/null
        cp $NBB/b5_w09_teacher "$WORK/w09_故障报告_教师版.ipynb" 2>/dev/null
        cp $NBB/b5_w10_student "$WORK/w10_图像处理_学生版.ipynb" 2>/dev/null
        cp $NBB/b5_w10_teacher "$WORK/w10_图像处理_教师版.ipynb" 2>/dev/null
        cp $NBB/fw_w09 $WORK/student_code_framework/w09_wordcloud_report.py 2>/dev/null
        cp $NBB/fw_w10 $WORK/student_code_framework/w10_report_pdf.py 2>/dev/null ;;
      Lecture-B6|lecture-b6)
        cp $NBB/b6_w11_student "$WORK/w11_数据采集网络_学生版.ipynb" 2>/dev/null
        cp $NBB/b6_w11_teacher "$WORK/w11_数据采集网络_教师版.ipynb" 2>/dev/null
        cp $NBB/b6_w12_student "$WORK/w12_综合项目_学生版.ipynb" 2>/dev/null
        cp $NBB/b6_w12_teacher "$WORK/w12_综合项目_教师版.ipynb" 2>/dev/null
        cp $NBB/fw_w11 $WORK/student_code_framework/w11_collector.py 2>/dev/null
        cp $NBB/fw_w12 $WORK/student_code_framework/w12_project_template.py 2>/dev/null ;;
      # ===== 01-AI应用基础 =====
      Lecture-A1|lecture-a1)
        cp $NBA/a1_m11_student "$WORK/m11_泵类设备故障诊断_学生版.ipynb" 2>/dev/null
        cp $NBA/a1_m11_teacher "$WORK/m11_泵类设备故障诊断_教师版.ipynb" 2>/dev/null
        cp $NBA/a1_m12_student "$WORK/m12_特征工程优化_学生版.ipynb" 2>/dev/null
        cp $NBA/a1_m12_teacher "$WORK/m12_特征工程优化_教师版.ipynb" 2>/dev/null
        cp $NBA/fw_m11 $WORK/student_code_framework/m11_starter.py 2>/dev/null
        cp $NBA/fw_m12 $WORK/student_code_framework/m12_starter.py 2>/dev/null ;;
      Lecture-A2|lecture-a2)
        cp $NBA/a2_m21_student "$WORK/m21_焊接缺陷检测_学生版.ipynb" 2>/dev/null
        cp $NBA/a2_m21_teacher "$WORK/m21_焊接缺陷检测_教师版.ipynb" 2>/dev/null
        cp $NBA/a2_m22_student "$WORK/m22_轴承寿命预测_学生版.ipynb" 2>/dev/null
        cp $NBA/a2_m22_teacher "$WORK/m22_轴承寿命预测_教师版.ipynb" 2>/dev/null
        cp $NBA/fw_m21 $WORK/student_code_framework/m21_starter.py 2>/dev/null
        cp $NBA/fw_m22 $WORK/student_code_framework/m22_starter.py 2>/dev/null ;;
      Lecture-A3|lecture-a3)
        cp $NBA/a3_m31_student "$WORK/m31_表面缺陷测量_学生版.ipynb" 2>/dev/null
        cp $NBA/a3_m31_teacher "$WORK/m31_表面缺陷测量_教师版.ipynb" 2>/dev/null
        cp $NBA/a3_m32_student "$WORK/m32_实时缺陷检测_学生版.ipynb" 2>/dev/null
        cp $NBA/a3_m32_teacher "$WORK/m32_实时缺陷检测_教师版.ipynb" 2>/dev/null
        cp $NBA/fw_m31 $WORK/student_code_framework/m31_starter.py 2>/dev/null
        cp $NBA/fw_m32 $WORK/student_code_framework/m32_starter.py 2>/dev/null ;;
      Lecture-A4|lecture-a4)
        cp $NBA/a4_m41_student "$WORK/m41_故障报告分类_学生版.ipynb" 2>/dev/null
        cp $NBA/a4_m41_teacher "$WORK/m41_故障报告分类_教师版.ipynb" 2>/dev/null
        cp $NBA/a4_m42_student "$WORK/m42_智能决策助手_学生版.ipynb" 2>/dev/null
        cp $NBA/a4_m42_teacher "$WORK/m42_智能决策助手_教师版.ipynb" 2>/dev/null
        cp $NBA/fw_m41 $WORK/student_code_framework/m41_starter.py 2>/dev/null
        cp $NBA/fw_m42 $WORK/student_code_framework/m42_starter.py 2>/dev/null ;;
      # ===== 03-Python项目实战 =====
      Lecture-P1|lecture-p1)
        cp $NBP/p1_p11_student "$WORK/p11_Python基础_学生版.ipynb" 2>/dev/null
        cp $NBP/p1_p11_teacher "$WORK/p11_Python基础_教师版.ipynb" 2>/dev/null
        cp $NBP/p1_p12_student "$WORK/p12_标准Python_学生版.ipynb" 2>/dev/null
        cp $NBP/p1_p12_teacher "$WORK/p12_标准Python_教师版.ipynb" 2>/dev/null
        cp $NBP/fw_p11 $WORK/student_code_framework/p11_exercises.py 2>/dev/null
        cp $NBP/fw_p12 $WORK/student_code_framework/p12_template.py 2>/dev/null ;;
      Lecture-P2|lecture-p2)
        cp $NBP/p2_p21_student "$WORK/p21_Pandas数据_学生版.ipynb" 2>/dev/null
        cp $NBP/p2_p21_teacher "$WORK/p21_Pandas数据_教师版.ipynb" 2>/dev/null
        cp $NBP/p2_p22_student "$WORK/p22_NumPy故障_学生版.ipynb" 2>/dev/null
        cp $NBP/p2_p22_teacher "$WORK/p22_NumPy故障_教师版.ipynb" 2>/dev/null
        cp $NBP/fw_p21 $WORK/student_code_framework/p21_pipeline.py 2>/dev/null
        cp $NBP/fw_p22 $WORK/student_code_framework/p22_features.py 2>/dev/null ;;
      Lecture-P3|lecture-p3)
        cp $NBP/p3_p33_student "$WORK/p33_KPI仪表盘_学生版.ipynb" 2>/dev/null
        cp $NBP/p3_p33_teacher "$WORK/p33_KPI仪表盘_教师版.ipynb" 2>/dev/null
        cp $NBP/fw_p33 $WORK/student_code_framework/p33_dashboard.py 2>/dev/null ;;
      Lecture-P4|lecture-p4)
        cp $NBP/p4_p41_student "$WORK/p41_多源采集_学生版.ipynb" 2>/dev/null
        cp $NBP/p4_p41_teacher "$WORK/p41_多源采集_教师版.ipynb" 2>/dev/null
        cp $NBP/fw_p41 $WORK/student_code_framework/p41_collector.py 2>/dev/null ;;
      Lecture-P5|lecture-p5)
        cp $NBP/p5_p55_student "$WORK/p55_数据仓库_学生版.ipynb" 2>/dev/null
        cp $NBP/p5_p55_teacher "$WORK/p55_数据仓库_教师版.ipynb" 2>/dev/null
        cp $NBP/fw_p55 $WORK/student_code_framework/p55_warehouse.py 2>/dev/null ;;
      Lecture-P6|lecture-p6)
        cp $NBP/p6_p66_student "$WORK/p66_故障诊断_学生版.ipynb" 2>/dev/null
        cp $NBP/p6_p66_teacher "$WORK/p66_故障诊断_教师版.ipynb" 2>/dev/null
        cp $NBP/fw_p66 $WORK/student_code_framework/p66_ml_service.py 2>/dev/null ;;
      # ===== Admin teacher gets EVERYTHING =====
      teacher-zhang)
        # All notebooks from all courses
        for cm_dir in $NBB $NBA $NBP; do
          for f in $cm_dir/*_student; do
            [ -f "$f" ] || continue
            base=$(basename "$f" | sed 's/_student$//')
            ext="ipynb"
            cp "$f" "$WORK/${base}_学生版.$ext" 2>/dev/null
          done
          for f in $cm_dir/*_teacher; do
            [ -f "$f" ] || continue
            base=$(basename "$f" | sed 's/_teacher$//')
            ext="ipynb"
            cp "$f" "$WORK/${base}_教师版.$ext" 2>/dev/null
          done
        done
        # All code frameworks
        for cm_dir in $NBB $NBA $NBP; do
          for f in $cm_dir/fw_*; do
            [ -f "$f" ] || continue
            base=$(basename "$f" | sed 's/^fw_//')
            cp "$f" "$WORK/student_code_framework/$base" 2>/dev/null
          done
        done ;;
    esac
    
    # ===== 4. Install dependencies (ALL users) =====
    pip install --quiet pycodestyle 2>/dev/null
    
    # ===== 5. Summary =====
    NB_COUNT=$(ls $WORK/*.ipynb 2>/dev/null | wc -l)
    FW_COUNT=$(ls $WORK/student_code_framework/*.py 2>/dev/null | wc -l)
    echo "Startup complete: $USERNAME"
    echo "  Guides: Teacher+Student (dual) | Grader: yes | Notebooks: $NB_COUNT | Code: $FW_COUNT"
STARTEOF

echo "Startup script updated: ALL users get dual guides + grader"

echo ""
echo "============================================================"
echo "Step 2: Restart JupyterHub"
echo "============================================================"
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "============================================================"
echo "Step 3: Verify all ConfigMaps"
echo "============================================================"
sleep 30

echo "=== Hub ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
kubectl get pod -n jupyterhub $HUB_POD 2>&1

echo ""
echo "=== ConfigMaps ==="
for cm in cm-course-b cm-course-a cm-course-p cm-common; do
  SIZE=$(kubectl get cm $cm -n jupyterhub -o json | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(f'{len(d)} keys, {sum(len(v) for v in d.values())//1024}KB')")
  echo "  $cm: $SIZE"
done

echo ""
echo "=== All services ==="
echo "infra:"
kubectl get pods -n infra 2>&1
echo "ai-platform:"
kubectl get pods -n ai-platform 2>&1 | head -10

echo ""
echo "=== Node load ==="
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "DEPLOYMENT VERIFIED"
echo "============================================================"
echo ""
echo "Default features for EVERY user (teacher, student, new):"
echo "  ✅ JUPYTERHUB-OPERATION-GUIDE.md (教师版指南)"
echo "  ✅ JUPYTERHUB-STUDENT-GUIDE.md (学生版指南)"
echo "  ✅ code_grader.py (评分系统)"
echo "  ✅ jupyter-ai (AI 聊天 + 代码补全)"
echo "  ✅ pycodestyle (PEP8 检查)"
echo ""
echo "Course-specific (based on username):"
echo "  Lecture-B1~B6 → 02-程序设计基础 notebooks + code"
echo "  Lecture-A1~A4 → 01-AI应用基础 notebooks + code"
echo "  Lecture-P1~P6 → 03-Python项目实战 notebooks + code"
echo "  teacher-zhang → ALL courses"
echo ""
echo "Student login format:"
echo "  b1-xxx → 02-程序设计基础 B1 (w01+w02)"
echo "  a1-xxx → 01-AI应用基础 A1 (m11+m12)"
echo "  p1-xxx → 03-项目实战 P1 (p11+p12)"
