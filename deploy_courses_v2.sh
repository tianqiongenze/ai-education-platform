#!/bin/bash
# Fix ConfigMap: use safe English keys, update startup script to match
set -e

echo "=== Rebuild ConfigMap with safe keys ==="

CM_ARGS=""

# Helper function to add file with safe key
add_file() {
  local file=$1
  local key=$2
  if [ -f "$file" ]; then
    CM_ARGS="$CM_ARGS --from-file=${key}=${file}"
  else
    echo "WARNING: File not found: $file"
  fi
}

# ===== 02-程序设计基础 (w01-w12) =====
add_file "/tmp/w01_0.1_设备参数初始化系_学生版.ipynb" "b1_w01_student"
add_file "/tmp/w01_0.1_设备参数初始化系_教师版.ipynb" "b1_w01_teacher"
add_file "/tmp/w02_0.2a_工业实时告警系统_学生版.ipynb" "b1_w02_student"
add_file "/tmp/w02_0.2a_工业实时告警系统_教师版.ipynb" "b1_w02_teacher"
add_file "/tmp/w03_0.2b_工业实时告警系统_学生版.ipynb" "b2_w03_student"
add_file "/tmp/w03_0.2b_工业实时告警系统_教师版.ipynb" "b2_w03_teacher"
add_file "/tmp/w04_0.3_工业设备类设计_学生版.ipynb" "b2_w04_student"
add_file "/tmp/w04_0.3_工业设备类设计_教师版.ipynb" "b2_w04_teacher"
add_file "/tmp/w05_0.4_工业设备继承体系_学生版.ipynb" "b3_w05_student"
add_file "/tmp/w05_0.4_工业设备继承体系_教师版.ipynb" "b3_w05_teacher"
add_file "/tmp/w06_0.5_健壮的工业数据采_学生版.ipynb" "b3_w06_student"
add_file "/tmp/w06_0.5_健壮的工业数据采_教师版.ipynb" "b3_w06_teacher"
add_file "/tmp/w07_1.1_工业数据格式转换_学生版.ipynb" "b4_w07_student"
add_file "/tmp/w07_1.1_工业数据格式转换_教师版.ipynb" "b4_w07_teacher"
add_file "/tmp/w08_1.2_工业数据文件处理_学生版.ipynb" "b4_w08_student"
add_file "/tmp/w08_1.2_工业数据文件处理_教师版.ipynb" "b4_w08_teacher"
add_file "/tmp/w09_1.3_工业故障分析报告_学生版.ipynb" "b5_w09_student"
add_file "/tmp/w09_1.3_工业故障分析报告_教师版.ipynb" "b5_w09_teacher"
add_file "/tmp/w10_1.4_工业图像处理与报_学生版.ipynb" "b5_w10_student"
add_file "/tmp/w10_1.4_工业图像处理与报_教师版.ipynb" "b5_w10_teacher"
add_file "/tmp/w11_1.5_工业互联网数据采_学生版.ipynb" "b6_w11_student"
add_file "/tmp/w11_1.5_工业互联网数据采_教师版.ipynb" "b6_w11_teacher"
add_file "/tmp/w12_Z_综合项目数据处理_学生版.ipynb" "b6_w12_student"
add_file "/tmp/w12_Z_综合项目数据处理_教师版.ipynb" "b6_w12_teacher"

# 02-程序设计基础 code framework
add_file "/tmp/w01_device_init.py" "fw_w01_device_init"
add_file "/tmp/w02_alarm_if.py" "fw_w02_alarm_if"
add_file "/tmp/w03_alarm_loop.py" "fw_w03_alarm_loop"
add_file "/tmp/w04_device_class.py" "fw_w04_device_class"
add_file "/tmp/w05_inherit.py" "fw_w05_inherit"
add_file "/tmp/w06_robust_collector.py" "fw_w06_robust_collector"
add_file "/tmp/w07_parser.py" "fw_w07_parser"
add_file "/tmp/w08_fileio.py" "fw_w08_fileio"
add_file "/tmp/w09_wordcloud_report.py" "fw_w09_wordcloud_report"
add_file "/tmp/w10_report_pdf.py" "fw_w10_report_pdf"
add_file "/tmp/w11_collector.py" "fw_w11_collector"
add_file "/tmp/w12_project_template.py" "fw_w12_project_template"

# ===== 01-AI应用基础 (m11-m42) =====
add_file "/tmp/m11_M1.1_泵类设备故障诊断_学生版.ipynb" "a1_m11_student"
add_file "/tmp/m11_M1.1_泵类设备故障诊断_教师版.ipynb" "a1_m11_teacher"
add_file "/tmp/m12_M1.2_特征工程优化的故_学生版.ipynb" "a1_m12_student"
add_file "/tmp/m12_M1.2_特征工程优化的故_教师版.ipynb" "a1_m12_teacher"
add_file "/tmp/m21_M2.1_工业焊接缺陷检测_学生版.ipynb" "a2_m21_student"
add_file "/tmp/m21_M2.1_工业焊接缺陷检测_教师版.ipynb" "a2_m21_teacher"
add_file "/tmp/m22_M2.2_轴承寿命预测系统_学生版.ipynb" "a2_m22_student"
add_file "/tmp/m22_M2.2_轴承寿命预测系统_教师版.ipynb" "a2_m22_teacher"
add_file "/tmp/m31_M3.1_产品表面缺陷尺寸_学生版.ipynb" "a3_m31_student"
add_file "/tmp/m31_M3.1_产品表面缺陷尺寸_教师版.ipynb" "a3_m31_teacher"
add_file "/tmp/m32_M3.2_产线实时缺陷检测_学生版.ipynb" "a3_m32_student"
add_file "/tmp/m32_M3.2_产线实时缺陷检测_教师版.ipynb" "a3_m32_teacher"
add_file "/tmp/m41_M4.1_工业故障报告自动_学生版.ipynb" "a4_m41_student"
add_file "/tmp/m41_M4.1_工业故障报告自动_教师版.ipynb" "a4_m41_teacher"
add_file "/tmp/m42_M4.2_工业智能决策助手_学生版.ipynb" "a4_m42_student"
add_file "/tmp/m42_M4.2_工业智能决策助手_教师版.ipynb" "a4_m42_teacher"

# 01-AI应用基础 code framework
add_file "/tmp/m11_starter.py" "fw_m11_starter"
add_file "/tmp/m12_starter.py" "fw_m12_starter"
add_file "/tmp/m21_starter.py" "fw_m21_starter"
add_file "/tmp/m22_starter.py" "fw_m22_starter"
add_file "/tmp/m31_starter.py" "fw_m31_starter"
add_file "/tmp/m32_starter.py" "fw_m32_starter"
add_file "/tmp/m41_starter.py" "fw_m41_starter"
add_file "/tmp/m42_starter.py" "fw_m42_starter"

# ===== 03-Python程序设计-项目实战 (p11-p66) =====
add_file "/tmp/p11_P1.1_Python基础_学生版.ipynb" "p1_p11_student"
add_file "/tmp/p11_P1.1_Python基础_教师版.ipynb" "p1_p11_teacher"
add_file "/tmp/p12_P1.2_标准Python_学生版.ipynb" "p1_p12_student"
add_file "/tmp/p12_P1.2_标准Python_教师版.ipynb" "p1_p12_teacher"
add_file "/tmp/p21_P2.1_Pandas数据_学生版.ipynb" "p2_p21_student"
add_file "/tmp/p21_P2.1_Pandas数据_教师版.ipynb" "p2_p21_teacher"
add_file "/tmp/p22_P2.2_NumPy故障特_学生版.ipynb" "p2_p22_student"
add_file "/tmp/p22_P2.2_NumPy故障特_教师版.ipynb" "p2_p22_teacher"
add_file "/tmp/p33_P3_产线KPI仪表盘_学生版.ipynb" "p3_p33_student"
add_file "/tmp/p33_P3_产线KPI仪表盘_教师版.ipynb" "p3_p33_teacher"
add_file "/tmp/p41_P4.1_多源数据采集系统_学生版.ipynb" "p4_p41_student"
add_file "/tmp/p41_P4.1_多源数据采集系统_教师版.ipynb" "p4_p41_teacher"
add_file "/tmp/p55_P5_产线数据仓库与O_学生版.ipynb" "p5_p55_student"
add_file "/tmp/p55_P5_产线数据仓库与O_教师版.ipynb" "p5_p55_teacher"
add_file "/tmp/p66_P6_故障诊断模型与部_学生版.ipynb" "p6_p66_student"
add_file "/tmp/p66_P6_故障诊断模型与部_教师版.ipynb" "p6_p66_teacher"

# 03-项目实战 code framework
add_file "/tmp/p11_exercises.py" "fw_p11_exercises"
add_file "/tmp/p12_template.py" "fw_p12_template"
add_file "/tmp/p21_pipeline.py" "fw_p21_pipeline"
add_file "/tmp/p22_features.py" "fw_p22_features"
add_file "/tmp/p33_dashboard.py" "fw_p33_dashboard"
add_file "/tmp/p41_collector.py" "fw_p41_collector"
add_file "/tmp/p55_warehouse.py" "fw_p55_warehouse"
add_file "/tmp/p66_ml_service.py" "fw_p66_ml_service"

# Guides + grader
add_file "/tmp/JUPYTERHUB-OPERATION-GUIDE.md" "guide_teacher"
add_file "/tmp/JUPYTERHUB-STUDENT-GUIDE.md" "guide_student"
add_file "/tmp/code_grader.py" "code_grader"

echo "Creating ConfigMap with $(echo "$CM_ARGS" | grep -o ' --from-file' | wc -l) files..."
kubectl create configmap lecture-notebooks -n jupyterhub $CM_ARGS --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "ConfigMap created!"

# Count keys
KEY_COUNT=$(kubectl get cm lecture-notebooks -n jupyterhub -o json | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))")
echo "ConfigMap keys: $KEY_COUNT"

echo ""
echo "=== Update startup script with safe key mapping ==="

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
    NB=/tmp/notebooks
    mkdir -p $WORK /home/jovyan/.jupyter $WORK/student_code_framework
    cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAIC'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAIC
    cp $NB/guide_teacher $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null
    cp $NB/guide_student $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
    cp $NB/code_grader $WORK/code_grader.py 2>/dev/null
    case "$USERNAME" in
      Lecture-B1|lecture-b1)
        cp $NB/b1_w01_student "$WORK/w01_设备参数初始化_学生版.ipynb" 2>/dev/null
        cp $NB/b1_w01_teacher "$WORK/w01_设备参数初始化_教师版.ipynb" 2>/dev/null
        cp $NB/b1_w02_student "$WORK/w02_实时告警系统_学生版.ipynb" 2>/dev/null
        cp $NB/b1_w02_teacher "$WORK/w02_实时告警系统_教师版.ipynb" 2>/dev/null
        cp $NB/fw_w01_device_init $WORK/student_code_framework/w01_device_init.py 2>/dev/null
        cp $NB/fw_w02_alarm_if $WORK/student_code_framework/w02_alarm_if.py 2>/dev/null ;;
      Lecture-B2|lecture-b2)
        cp $NB/b2_w03_student "$WORK/w03_告警循环_学生版.ipynb" 2>/dev/null
        cp $NB/b2_w03_teacher "$WORK/w03_告警循环_教师版.ipynb" 2>/dev/null
        cp $NB/b2_w04_student "$WORK/w04_设备类设计_学生版.ipynb" 2>/dev/null
        cp $NB/b2_w04_teacher "$WORK/w04_设备类设计_教师版.ipynb" 2>/dev/null
        cp $NB/fw_w03_alarm_loop $WORK/student_code_framework/w03_alarm_loop.py 2>/dev/null
        cp $NB/fw_w04_device_class $WORK/student_code_framework/w04_device_class.py 2>/dev/null ;;
      Lecture-B3|lecture-b3)
        cp $NB/b3_w05_student "$WORK/w05_继承体系_学生版.ipynb" 2>/dev/null
        cp $NB/b3_w05_teacher "$WORK/w05_继承体系_教师版.ipynb" 2>/dev/null
        cp $NB/b3_w06_student "$WORK/w06_数据采集_学生版.ipynb" 2>/dev/null
        cp $NB/b3_w06_teacher "$WORK/w06_数据采集_教师版.ipynb" 2>/dev/null
        cp $NB/fw_w05_inherit $WORK/student_code_framework/w05_inherit.py 2>/dev/null
        cp $NB/fw_w06_robust_collector $WORK/student_code_framework/w06_robust_collector.py 2>/dev/null ;;
      Lecture-B4|lecture-b4)
        cp $NB/b4_w07_student "$WORK/w07_格式转换_学生版.ipynb" 2>/dev/null
        cp $NB/b4_w07_teacher "$WORK/w07_格式转换_教师版.ipynb" 2>/dev/null
        cp $NB/b4_w08_student "$WORK/w08_文件处理_学生版.ipynb" 2>/dev/null
        cp $NB/b4_w08_teacher "$WORK/w08_文件处理_教师版.ipynb" 2>/dev/null
        cp $NB/fw_w07_parser $WORK/student_code_framework/w07_parser.py 2>/dev/null
        cp $NB/fw_w08_fileio $WORK/student_code_framework/w08_fileio.py 2>/dev/null ;;
      Lecture-B5|lecture-b5)
        cp $NB/b5_w09_student "$WORK/w09_故障报告_学生版.ipynb" 2>/dev/null
        cp $NB/b5_w09_teacher "$WORK/w09_故障报告_教师版.ipynb" 2>/dev/null
        cp $NB/b5_w10_student "$WORK/w10_图像处理_学生版.ipynb" 2>/dev/null
        cp $NB/b5_w10_teacher "$WORK/w10_图像处理_教师版.ipynb" 2>/dev/null
        cp $NB/fw_w09_wordcloud_report $WORK/student_code_framework/w09_wordcloud_report.py 2>/dev/null
        cp $NB/fw_w10_report_pdf $WORK/student_code_framework/w10_report_pdf.py 2>/dev/null ;;
      Lecture-B6|lecture-b6)
        cp $NB/b6_w11_student "$WORK/w11_数据采集网络_学生版.ipynb" 2>/dev/null
        cp $NB/b6_w11_teacher "$WORK/w11_数据采集网络_教师版.ipynb" 2>/dev/null
        cp $NB/b6_w12_student "$WORK/w12_综合项目_学生版.ipynb" 2>/dev/null
        cp $NB/b6_w12_teacher "$WORK/w12_综合项目_教师版.ipynb" 2>/dev/null
        cp $NB/fw_w11_collector $WORK/student_code_framework/w11_collector.py 2>/dev/null
        cp $NB/fw_w12_project_template $WORK/student_code_framework/w12_project_template.py 2>/dev/null ;;
      Lecture-A1|lecture-a1)
        cp $NB/a1_m11_student "$WORK/m11_泵类设备故障诊断_学生版.ipynb" 2>/dev/null
        cp $NB/a1_m11_teacher "$WORK/m11_泵类设备故障诊断_教师版.ipynb" 2>/dev/null
        cp $NB/a1_m12_student "$WORK/m12_特征工程优化_学生版.ipynb" 2>/dev/null
        cp $NB/a1_m12_teacher "$WORK/m12_特征工程优化_教师版.ipynb" 2>/dev/null
        cp $NB/fw_m11_starter $WORK/student_code_framework/m11_starter.py 2>/dev/null
        cp $NB/fw_m12_starter $WORK/student_code_framework/m12_starter.py 2>/dev/null ;;
      Lecture-A2|lecture-a2)
        cp $NB/a2_m21_student "$WORK/m21_焊接缺陷检测_学生版.ipynb" 2>/dev/null
        cp $NB/a2_m21_teacher "$WORK/m21_焊接缺陷检测_教师版.ipynb" 2>/dev/null
        cp $NB/a2_m22_student "$WORK/m22_轴承寿命预测_学生版.ipynb" 2>/dev/null
        cp $NB/a2_m22_teacher "$WORK/m22_轴承寿命预测_教师版.ipynb" 2>/dev/null
        cp $NB/fw_m21_starter $WORK/student_code_framework/m21_starter.py 2>/dev/null
        cp $NB/fw_m22_starter $WORK/student_code_framework/m22_starter.py 2>/dev/null ;;
      Lecture-A3|lecture-a3)
        cp $NB/a3_m31_student "$WORK/m31_表面缺陷测量_学生版.ipynb" 2>/dev/null
        cp $NB/a3_m31_teacher "$WORK/m31_表面缺陷测量_教师版.ipynb" 2>/dev/null
        cp $NB/a3_m32_student "$WORK/m32_实时缺陷检测_学生版.ipynb" 2>/dev/null
        cp $NB/a3_m32_teacher "$WORK/m32_实时缺陷检测_教师版.ipynb" 2>/dev/null
        cp $NB/fw_m31_starter $WORK/student_code_framework/m31_starter.py 2>/dev/null
        cp $NB/fw_m32_starter $WORK/student_code_framework/m32_starter.py 2>/dev/null ;;
      Lecture-A4|lecture-a4)
        cp $NB/a4_m41_student "$WORK/m41_故障报告分类_学生版.ipynb" 2>/dev/null
        cp $NB/a4_m41_teacher "$WORK/m41_故障报告分类_教师版.ipynb" 2>/dev/null
        cp $NB/a4_m42_student "$WORK/m42_智能决策助手_学生版.ipynb" 2>/dev/null
        cp $NB/a4_m42_teacher "$WORK/m42_智能决策助手_教师版.ipynb" 2>/dev/null
        cp $NB/fw_m41_starter $WORK/student_code_framework/m41_starter.py 2>/dev/null
        cp $NB/fw_m42_starter $WORK/student_code_framework/m42_starter.py 2>/dev/null ;;
      Lecture-P1|lecture-p1)
        cp $NB/p1_p11_student "$WORK/p11_Python基础_学生版.ipynb" 2>/dev/null
        cp $NB/p1_p11_teacher "$WORK/p11_Python基础_教师版.ipynb" 2>/dev/null
        cp $NB/p1_p12_student "$WORK/p12_标准Python_学生版.ipynb" 2>/dev/null
        cp $NB/p1_p12_teacher "$WORK/p12_标准Python_教师版.ipynb" 2>/dev/null
        cp $NB/fw_p11_exercises $WORK/student_code_framework/p11_exercises.py 2>/dev/null
        cp $NB/fw_p12_template $WORK/student_code_framework/p12_template.py 2>/dev/null ;;
      Lecture-P2|lecture-p2)
        cp $NB/p2_p21_student "$WORK/p21_Pandas数据_学生版.ipynb" 2>/dev/null
        cp $NB/p2_p21_teacher "$WORK/p21_Pandas数据_教师版.ipynb" 2>/dev/null
        cp $NB/p2_p22_student "$WORK/p22_NumPy故障_学生版.ipynb" 2>/dev/null
        cp $NB/p2_p22_teacher "$WORK/p22_NumPy故障_教师版.ipynb" 2>/dev/null
        cp $NB/fw_p21_pipeline $WORK/student_code_framework/p21_pipeline.py 2>/dev/null
        cp $NB/fw_p22_features $WORK/student_code_framework/p22_features.py 2>/dev/null ;;
      Lecture-P3|lecture-p3)
        cp $NB/p3_p33_student "$WORK/p33_KPI仪表盘_学生版.ipynb" 2>/dev/null
        cp $NB/p3_p33_teacher "$WORK/p33_KPI仪表盘_教师版.ipynb" 2>/dev/null
        cp $NB/fw_p33_dashboard $WORK/student_code_framework/p33_dashboard.py 2>/dev/null ;;
      Lecture-P4|lecture-p4)
        cp $NB/p4_p41_student "$WORK/p41_多源采集_学生版.ipynb" 2>/dev/null
        cp $NB/p4_p41_teacher "$WORK/p41_多源采集_教师版.ipynb" 2>/dev/null
        cp $NB/fw_p41_collector $WORK/student_code_framework/p41_collector.py 2>/dev/null ;;
      Lecture-P5|lecture-p5)
        cp $NB/p5_p55_student "$WORK/p55_数据仓库_学生版.ipynb" 2>/dev/null
        cp $NB/p5_p55_teacher "$WORK/p55_数据仓库_教师版.ipynb" 2>/dev/null
        cp $NB/fw_p55_warehouse $WORK/student_code_framework/p55_warehouse.py 2>/dev/null ;;
      Lecture-P6|lecture-p6)
        cp $NB/p6_p66_student "$WORK/p66_故障诊断_学生版.ipynb" 2>/dev/null
        cp $NB/p6_p66_teacher "$WORK/p66_故障诊断_教师版.ipynb" 2>/dev/null
        cp $NB/fw_p66_ml_service $WORK/student_code_framework/p66_ml_service.py 2>/dev/null ;;
      teacher-zhang)
        for key in $(ls $NB/ 2>/dev/null | grep "_student$"); do
          base=$(echo $key | sed 's/_student//')
          cp "$NB/$key" "$WORK/${base}_学生版.ipynb" 2>/dev/null
        done
        for key in $(ls $NB/ 2>/dev/null | grep "_teacher$"); do
          base=$(echo $key | sed 's/_teacher//')
          cp "$NB/$key" "$WORK/${base}_教师版.ipynb" 2>/dev/null
        done
        for key in $(ls $NB/ 2>/dev/null | grep "^fw_"); do
          bn=$(echo $key | sed 's/^fw_//')
          cp "$NB/$key" "$WORK/student_code_framework/$bn" 2>/dev/null
        done ;;
    esac
    pip install --quiet pycodestyle 2>/dev/null
    echo "Startup complete: $USERNAME ($(ls $WORK/*.ipynb 2>/dev/null | wc -l) notebooks)"
STARTEOF

echo "Startup script updated with safe key mapping"

echo ""
echo "=== Restart hub ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "=== Final verification ==="
sleep 30
echo "--- Hub ---"
kubectl get pods -n jupyterhub 2>&1 | head -5
echo "--- CRDB ---"
kubectl get pods -n infra 2>&1
echo "--- AI platform ---"
kubectl get pods -n ai-platform 2>&1 | head -10
echo ""
echo "--- ConfigMap summary ---"
kubectl get cm lecture-notebooks -n jupyterhub -o json | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
keys = sorted(data.keys())
print(f'Total keys: {len(keys)}')
nbs = [k for k in keys if '_student' in k or '_teacher' in k]
fws = [k for k in keys if k.startswith('fw_')]
guides = [k for k in keys if 'guide' in k.lower()]
grader = [k for k in keys if 'grader' in k.lower()]
print(f'  Notebooks: {len(nbs)} (student+teacher)')
print(f'  Code frameworks: {len(fws)}')
print(f'  Guides: {len(guides)}')
print(f'  Grader: {len(grader)}')
print()
print('Notebook keys:')
for k in nbs:
    print(f'  {k}')
"
echo ""
echo "--- Node load ---"
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "MULTI-COURSE DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "账户体系总览："
echo ""
echo "  课程                      | Lecture账户      | 学生前缀   | Notebook"
echo "  ─────────────────────────┼─────────────────┼───────────┼──────────"
echo "  02-程序设计基础 (12周)   | Lecture-B1~B6   | b1~b6-xxx | 24个"
echo "  01-AI应用基础 (8模块)    | Lecture-A1~A4   | a1~a4-xxx | 16个"
echo "  03-Python项目实战 (8模块)| Lecture-P1~P6   | p1~p6-xxx | 16个"
echo "  ─────────────────────────┴─────────────────┴───────────┴──────────"
echo "  总计: 17个教师/管理员账户, 56个Notebook, 20个代码框架"
echo ""
echo "多层对照关系："
echo "  teacher-zhang (总管理员)"
echo "    ├── Lecture-B1~B6 → 02-程序设计基础 → b1~b6-学生"
echo "    ├── Lecture-A1~A4 → 01-AI应用基础 → a1~a4-学生"
echo "    └── Lecture-P1~P6 → 03-Python项目实战 → p1~p6-学生"
