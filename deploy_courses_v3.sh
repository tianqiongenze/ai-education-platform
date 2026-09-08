#!/bin/bash
# Split ConfigMap by course to stay under 1MB limit
set -e

echo "=== Delete old ConfigMap ==="
kubectl delete cm lecture-notebooks -n jupyterhub 2>/dev/null || true

echo ""
echo "=== ConfigMap 1: 02-程序设计基础 (course-b) ==="
kubectl create configmap cm-course-b -n jupyterhub \
  --from-file=b1_w01_student="/tmp/w01_0.1_设备参数初始化系_学生版.ipynb" \
  --from-file=b1_w01_teacher="/tmp/w01_0.1_设备参数初始化系_教师版.ipynb" \
  --from-file=b1_w02_student="/tmp/w02_0.2a_工业实时告警系统_学生版.ipynb" \
  --from-file=b1_w02_teacher="/tmp/w02_0.2a_工业实时告警系统_教师版.ipynb" \
  --from-file=b2_w03_student="/tmp/w03_0.2b_工业实时告警系统_学生版.ipynb" \
  --from-file=b2_w03_teacher="/tmp/w03_0.2b_工业实时告警系统_教师版.ipynb" \
  --from-file=b2_w04_student="/tmp/w04_0.3_工业设备类设计_学生版.ipynb" \
  --from-file=b2_w04_teacher="/tmp/w04_0.3_工业设备类设计_教师版.ipynb" \
  --from-file=b3_w05_student="/tmp/w05_0.4_工业设备继承体系_学生版.ipynb" \
  --from-file=b3_w05_teacher="/tmp/w05_0.4_工业设备继承体系_教师版.ipynb" \
  --from-file=b3_w06_student="/tmp/w06_0.5_健壮的工业数据采_学生版.ipynb" \
  --from-file=b3_w06_teacher="/tmp/w06_0.5_健壮的工业数据采_教师版.ipynb" \
  --from-file=b4_w07_student="/tmp/w07_1.1_工业数据格式转换_学生版.ipynb" \
  --from-file=b4_w07_teacher="/tmp/w07_1.1_工业数据格式转换_教师版.ipynb" \
  --from-file=b4_w08_student="/tmp/w08_1.2_工业数据文件处理_学生版.ipynb" \
  --from-file=b4_w08_teacher="/tmp/w08_1.2_工业数据文件处理_教师版.ipynb" \
  --from-file=b5_w09_student="/tmp/w09_1.3_工业故障分析报告_学生版.ipynb" \
  --from-file=b5_w09_teacher="/tmp/w09_1.3_工业故障分析报告_教师版.ipynb" \
  --from-file=b5_w10_student="/tmp/w10_1.4_工业图像处理与报_学生版.ipynb" \
  --from-file=b5_w10_teacher="/tmp/w10_1.4_工业图像处理与报_教师版.ipynb" \
  --from-file=b6_w11_student="/tmp/w11_1.5_工业互联网数据采_学生版.ipynb" \
  --from-file=b6_w11_teacher="/tmp/w11_1.5_工业互联网数据采_教师版.ipynb" \
  --from-file=b6_w12_student="/tmp/w12_Z_综合项目数据处理_学生版.ipynb" \
  --from-file=b6_w12_teacher="/tmp/w12_Z_综合项目数据处理_教师版.ipynb" \
  --from-file=fw_w01="/tmp/w01_device_init.py" \
  --from-file=fw_w02="/tmp/w02_alarm_if.py" \
  --from-file=fw_w03="/tmp/w03_alarm_loop.py" \
  --from-file=fw_w04="/tmp/w04_device_class.py" \
  --from-file=fw_w05="/tmp/w05_inherit.py" \
  --from-file=fw_w06="/tmp/w06_robust_collector.py" \
  --from-file=fw_w07="/tmp/w07_parser.py" \
  --from-file=fw_w08="/tmp/w08_fileio.py" \
  --from-file=fw_w09="/tmp/w09_wordcloud_report.py" \
  --from-file=fw_w10="/tmp/w10_report_pdf.py" \
  --from-file=fw_w11="/tmp/w11_collector.py" \
  --from-file=fw_w12="/tmp/w12_project_template.py" \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "course-b ConfigMap created"

echo ""
echo "=== ConfigMap 2: 01-AI应用基础 (course-a) ==="
kubectl create configmap cm-course-a -n jupyterhub \
  --from-file=a1_m11_student="/tmp/m11_M1.1_泵类设备故障诊断_学生版.ipynb" \
  --from-file=a1_m11_teacher="/tmp/m11_M1.1_泵类设备故障诊断_教师版.ipynb" \
  --from-file=a1_m12_student="/tmp/m12_M1.2_特征工程优化的故_学生版.ipynb" \
  --from-file=a1_m12_teacher="/tmp/m12_M1.2_特征工程优化的故_教师版.ipynb" \
  --from-file=a2_m21_student="/tmp/m21_M2.1_工业焊接缺陷检测_学生版.ipynb" \
  --from-file=a2_m21_teacher="/tmp/m21_M2.1_工业焊接缺陷检测_教师版.ipynb" \
  --from-file=a2_m22_student="/tmp/m22_M2.2_轴承寿命预测系统_学生版.ipynb" \
  --from-file=a2_m22_teacher="/tmp/m22_M2.2_轴承寿命预测系统_教师版.ipynb" \
  --from-file=a3_m31_student="/tmp/m31_M3.1_产品表面缺陷尺寸_学生版.ipynb" \
  --from-file=a3_m31_teacher="/tmp/m31_M3.1_产品表面缺陷尺寸_教师版.ipynb" \
  --from-file=a3_m32_student="/tmp/m32_M3.2_产线实时缺陷检测_学生版.ipynb" \
  --from-file=a3_m32_teacher="/tmp/m32_M3.2_产线实时缺陷检测_教师版.ipynb" \
  --from-file=a4_m41_student="/tmp/m41_M4.1_工业故障报告自动_学生版.ipynb" \
  --from-file=a4_m41_teacher="/tmp/m41_M4.1_工业故障报告自动_教师版.ipynb" \
  --from-file=a4_m42_student="/tmp/m42_M4.2_工业智能决策助手_学生版.ipynb" \
  --from-file=a4_m42_teacher="/tmp/m42_M4.2_工业智能决策助手_教师版.ipynb" \
  --from-file=fw_m11="/tmp/m11_starter.py" \
  --from-file=fw_m12="/tmp/m12_starter.py" \
  --from-file=fw_m21="/tmp/m21_starter.py" \
  --from-file=fw_m22="/tmp/m22_starter.py" \
  --from-file=fw_m31="/tmp/m31_starter.py" \
  --from-file=fw_m32="/tmp/m32_starter.py" \
  --from-file=fw_m41="/tmp/m41_starter.py" \
  --from-file=fw_m42="/tmp/m42_starter.py" \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "course-a ConfigMap created"

echo ""
echo "=== ConfigMap 3: 03-Python项目实战 (course-p) ==="
kubectl create configmap cm-course-p -n jupyterhub \
  --from-file=p1_p11_student="/tmp/p11_P1.1_Python基础_学生版.ipynb" \
  --from-file=p1_p11_teacher="/tmp/p11_P1.1_Python基础_教师版.ipynb" \
  --from-file=p1_p12_student="/tmp/p12_P1.2_标准Python_学生版.ipynb" \
  --from-file=p1_p12_teacher="/tmp/p12_P1.2_标准Python_教师版.ipynb" \
  --from-file=p2_p21_student="/tmp/p21_P2.1_Pandas数据_学生版.ipynb" \
  --from-file=p2_p21_teacher="/tmp/p21_P2.1_Pandas数据_教师版.ipynb" \
  --from-file=p2_p22_student="/tmp/p22_P2.2_NumPy故障特_学生版.ipynb" \
  --from-file=p2_p22_teacher="/tmp/p22_P2.2_NumPy故障特_教师版.ipynb" \
  --from-file=p3_p33_student="/tmp/p33_P3_产线KPI仪表盘_学生版.ipynb" \
  --from-file=p3_p33_teacher="/tmp/p33_P3_产线KPI仪表盘_教师版.ipynb" \
  --from-file=p4_p41_student="/tmp/p41_P4.1_多源数据采集系统_学生版.ipynb" \
  --from-file=p4_p41_teacher="/tmp/p41_P4.1_多源数据采集系统_教师版.ipynb" \
  --from-file=p5_p55_student="/tmp/p55_P5_产线数据仓库与O_学生版.ipynb" \
  --from-file=p5_p55_teacher="/tmp/p55_P5_产线数据仓库与O_教师版.ipynb" \
  --from-file=p6_p66_student="/tmp/p66_P6_故障诊断模型与部_学生版.ipynb" \
  --from-file=p6_p66_teacher="/tmp/p66_P6_故障诊断模型与部_教师版.ipynb" \
  --from-file=fw_p11="/tmp/p11_exercises.py" \
  --from-file=fw_p12="/tmp/p12_template.py" \
  --from-file=fw_p21="/tmp/p21_pipeline.py" \
  --from-file=fw_p22="/tmp/p22_features.py" \
  --from-file=fw_p33="/tmp/p33_dashboard.py" \
  --from-file=fw_p41="/tmp/p41_collector.py" \
  --from-file=fw_p55="/tmp/p55_warehouse.py" \
  --from-file=fw_p66="/tmp/p66_ml_service.py" \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "course-p ConfigMap created"

echo ""
echo "=== ConfigMap 4: Common (guides + grader) ==="
kubectl create configmap cm-common -n jupyterhub \
  --from-file=guide_teacher="/tmp/JUPYTERHUB-OPERATION-GUIDE.md" \
  --from-file=guide_student="/tmp/JUPYTERHUB-STUDENT-GUIDE.md" \
  --from-file=code_grader="/tmp/code_grader.py" \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "common ConfigMap created"

echo ""
echo "=== Update volume mounts to include ALL ConfigMaps ==="
kubectl get cm jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_volumes.py

python3 -c "
content = open('/tmp/jhub_volumes.py').read()
# Remove existing volume config
import re
content = re.sub(r'c\.KubeSpawner\.volumes\s*=\s*\[.*?\]', '', content, flags=re.DOTALL)
content = re.sub(r'c\.KubeSpawner\.volume_mounts\s*=\s*\[.*?\]', '', content, flags=re.DOTALL)
content += '''
c.KubeSpawner.volumes = [
    {\"name\": \"workspace-{username}\", \"persistentVolumeClaim\": {\"claimName\": \"claim-{username}\"}},
    {\"name\": \"startup-script\", \"configMap\": {\"name\": \"jupyterhub-startup\"}},
    {\"name\": \"nb-course-b\", \"configMap\": {\"name\": \"cm-course-b\"}},
    {\"name\": \"nb-course-a\", \"configMap\": {\"name\": \"cm-course-a\"}},
    {\"name\": \"nb-course-p\", \"configMap\": {\"name\": \"cm-course-p\"}},
    {\"name\": \"nb-common\", \"configMap\": {\"name\": \"cm-common\"}},
]
c.KubeSpawner.volume_mounts = [
    {\"name\": \"workspace-{username}\", \"mountPath\": \"/home/jovyan/work\"},
    {\"name\": \"startup-script\", \"mountPath\": \"/tmp/startup.sh\", \"subPath\": \"startup.sh\"},
    {\"name\": \"nb-course-b\", \"mountPath\": \"/tmp/notebooks/b\"},
    {\"name\": \"nb-course-a\", \"mountPath\": \"/tmp/notebooks/a\"},
    {\"name\": \"nb-course-p\", \"mountPath\": \"/tmp/notebooks/p\"},
    {\"name\": \"nb-common\", \"mountPath\": \"/tmp/notebooks/common\"},
]
'''
open('/tmp/jhub_volumes.py', 'w').write(content)
print('Volumes updated')
"

kubectl create cm jupyterhub-config -n jupyterhub --from-file=jupyterhub_config.py=/tmp/jhub_volumes.py --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "JupyterHub volumes updated for 4 ConfigMaps"

echo ""
echo "=== Update startup script paths (NB=/tmp/notebooks/common, B=/tmp/notebooks/b, etc) ==="
# Get current startup and fix paths
kubectl get cm jupyterhub-startup -n jupyterhub -o jsonpath='{.data.startup\.sh}' > /tmp/startup_fix.sh

# Replace $NB references with proper subdirectory paths
sed -i 's|NB=/tmp/notebooks$|NB=/tmp/notebooks/common\n    NBB=/tmp/notebooks/b\n    NBA=/tmp/notebooks/a\n    NBP=/tmp/notebooks/p|' /tmp/startup_fix.sh 2>/dev/null || true

# Fix guide/grader references (now in common)
sed -i 's|\$NB/guide_teacher|\$NB/guide_teacher|g' /tmp/startup_fix.sh
sed -i 's|\$NB/guide_student|\$NB/guide_student|g' /tmp/startup_fix.sh
sed -i 's|\$NB/code_grader|\$NB/code_grader|g' /tmp/startup_fix.sh

kubectl create configmap jupyterhub-startup -n jupyterhub --from-file=startup.sh=/tmp/startup_fix.sh --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "Startup script paths updated"

echo ""
echo "=== Restart hub ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "=== Final verification ==="
sleep 30

echo "--- ConfigMap sizes ---"
for cm in cm-course-b cm-course-a cm-course-p cm-common; do
  SIZE=$(kubectl get cm $cm -n jupyterhub -o json | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(f'{len(d)} keys, {sum(len(v) for v in d.values())//1024}KB')")
  echo "  $cm: $SIZE"
done

echo ""
echo "--- Hub status ---"
kubectl get pods -n jupyterhub 2>&1 | head -5

echo ""
echo "--- All pods ---"
kubectl get pods -n infra 2>&1
kubectl get pods -n ai-platform 2>&1 | head -10

echo ""
echo "--- Node load ---"
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "MULTI-COURSE DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "课程账户体系："
echo ""
echo "  课程                       | Lecture账户      | 学生前缀   | Notebooks | CodeFiles"
echo "  ──────────────────────────┼─────────────────┼───────────┼───────────┼──────────"
echo "  02-程序设计基础 (12周)    | Lecture-B1~B6   | b1~b6-xxx | 24        | 12"
echo "  01-AI应用基础 (8模块)     | Lecture-A1~A4   | a1~a4-xxx | 16        | 8"
echo "  03-Python项目实战 (8模块) | Lecture-P1~P6   | p1~p6-xxx | 16        | 8"
echo "  ──────────────────────────┴─────────────────┴───────────┴───────────┴──────────"
echo "  合计: 17个教师/管理员, 20个分组, 56个Notebook, 28个代码框架"
echo ""
echo "多层对照关系："
echo "  teacher-zhang (总管理员)"
echo "    ├── Lecture-B1~B6 → 02-程序设计基础 → b1~b6-students"
echo "    │   ├── B1: w01设备初始化 + w02实时告警"
echo "    │   ├── B2: w03告警循环 + w04设备类"
echo "    │   ├── B3: w05继承体系 + w06数据采集"
echo "    │   ├── B4: w07格式转换 + w08文件处理"
echo "    │   ├── B5: w09故障报告 + w10图像处理"
echo "    │   └── B6: w11数据采集网络 + w12综合项目"
echo "    ├── Lecture-A1~A4 → 01-AI应用基础 → a1~a4-students"
echo "    │   ├── A1: m11故障诊断 + m12特征工程"
echo "    │   ├── A2: m21焊接检测 + m22寿命预测"
echo "    │   ├── A3: m31缺陷测量 + m32实时检测"
echo "    │   └── A4: m41故障报告 + m42智能决策"
echo "    └── Lecture-P1~P6 → 03-Python项目实战 → p1~p6-students"
echo "        ├── P1: p11 Python基础 + p12 标准工程"
echo "        ├── P2: p21 Pandas数据 + p22 NumPy故障"
echo "        ├── P3: p33 KPI仪表盘"
echo "        ├── P4: p41 多源采集"
echo "        ├── P5: p55 数据仓库"
echo "        └── P6: p66 故障诊断"
