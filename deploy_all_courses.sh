#!/bin/bash
# ============================================================
# 多课程 JupyterHub 完整部署
# 3门课程 × 16个Lecture账户 = 完整教学体系
# ============================================================

set -e

echo "============================================================"
echo "Step 1: 创建所有 Lecture 账户"
echo "============================================================"

# Create accounts via JupyterHub DB
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
echo "Hub pod: $HUB_POD"

kubectl exec -n jupyterhub $HUB_POD -c jupyterhub -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()

# All teacher accounts
teachers = [
    'teacher-zhang',
    # 02-程序设计基础 (6 accounts)
    'Lecture-B1', 'Lecture-B2', 'Lecture-B3', 'Lecture-B4', 'Lecture-B5', 'Lecture-B6',
    # 01-AI应用基础 (4 accounts)
    'Lecture-A1', 'Lecture-A2', 'Lecture-A3', 'Lecture-A4',
    # 03-Python程序设计-项目实战 (6 accounts, existing)
    'Lecture-P1', 'Lecture-P2', 'Lecture-P3', 'Lecture-P4', 'Lecture-P5', 'Lecture-P6',
]

for t in teachers:
    try:
        c.execute('INSERT INTO users (name, admin) VALUES (?, 1)', (t,))
        print(f'Created: {t}')
    except:
        c.execute('UPDATE users SET admin = 1 WHERE name = ?', (t,))
        print(f'Updated: {t}')

conn.commit()

# Create groups
groups = {
    'lecture-b1-students': [], 'lecture-b2-students': [], 'lecture-b3-students': [],
    'lecture-b4-students': [], 'lecture-b5-students': [], 'lecture-b6-students': [],
    'lecture-a1-students': [], 'lecture-a2-students': [], 'lecture-a3-students': [],
    'lecture-a4-students': [],
    'lecture-p1-students': [], 'lecture-p2-students': [], 'lecture-p3-students': [],
    'lecture-p4-students': [], 'lecture-p5-students': [], 'lecture-p6-students': [],
    'course-b-students': [],  # All 02-程序设计基础 students
    'course-a-students': [],  # All 01-AI应用基础 students
    'course-p-students': [],  # All 03-项目实战 students
    'all-students': [],
    'all-teachers': teachers,
}

for gname, members in groups.items():
    try:
        c.execute('INSERT INTO groups (name) VALUES (?)', (gname,))
        print(f'Group: {gname}')
    except:
        print(f'Group exists: {gname}')

conn.commit()

# Add teachers to all-teachers group
c.execute('SELECT id FROM groups WHERE name=\"all-teachers\"')
gid = c.fetchone()
if gid:
    for t in teachers:
        try:
            c.execute('SELECT id FROM users WHERE name=?', (t,))
            uid = c.fetchone()
            if uid:
                c.execute('INSERT INTO users_groups (user_id, group_id) VALUES (?, ?)', (uid[0], gid[0]))
        except:
            pass

conn.commit()
conn.close()
print('All accounts and groups created!')
" 2>&1

echo ""
echo "============================================================"
echo "Step 2: 更新 lecture-notebooks ConfigMap（全部3门课程内容）"
echo "============================================================"

# Build the configmap with ALL files
# 02-程序设计基础 notebooks
CM_ARGS=""
for f in /tmp/w0*.ipynb /tmp/w1*.ipynb; do
  basename=$(basename "$f")
  key=$(echo "$basename" | sed 's/_学生版//;s/_教师版//;s/.ipynb//' | tr 'A-Z' 'a-z')
  if echo "$basename" | grep -q "学生版"; then
    CM_ARGS="$CM_ARGS --from-file=${key}_student=$f"
  else
    CM_ARGS="$CM_ARGS --from-file=${key}_teacher=$f"
  fi
done

# 01-AI应用基础 notebooks
for f in /tmp/m1*.ipynb /tmp/m2*.ipynb /tmp/m3*.ipynb /tmp/m4*.ipynb; do
  basename=$(basename "$f")
  key=$(echo "$basename" | sed 's/_学生版//;s/_教师版//;s/.ipynb//' | tr 'A-Z' 'a-z')
  if echo "$basename" | grep -q "学生版"; then
    CM_ARGS="$CM_ARGS --from-file=${key}_student=$f"
  else
    CM_ARGS="$CM_ARGS --from-file=${key}_teacher=$f"
  fi
done

# 03-项目实战 notebooks (existing)
CM_ARGS="$CM_ARGS --from-file=p11_student=/tmp/p11_P1.1_Python基础_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p11_teacher=/tmp/p11_P1.1_Python基础_教师版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p12_student=/tmp/p12_P1.2_标准Python_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p12_teacher=/tmp/p12_P1.2_标准Python_教师版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p21_student=/tmp/p21_P2.1_Pandas数据_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p21_teacher=/tmp/p21_P2.1_Pandas数据_教师版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p22_student=/tmp/p22_P2.2_NumPy故障特_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p22_teacher=/tmp/p22_P2.2_NumPy故障特_教师版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p33_student=/tmp/p33_P3_产线KPI仪表盘_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p33_teacher=/tmp/p33_P3_产线KPI仪表盘_教师版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p41_student=/tmp/p41_P4.1_多源数据采集系统_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p41_teacher=/tmp/p41_P4.1_多源数据采集系统_教师版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p55_student=/tmp/p55_P5_产线数据仓库与O_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p55_teacher=/tmp/p55_P5_产线数据仓库与O_教师版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p66_student=/tmp/p66_P6_故障诊断模型与部_学生版.ipynb"
CM_ARGS="$CM_ARGS --from-file=p66_teacher=/tmp/p66_P6_故障诊断模型与部_教师版.ipynb"

# Code frameworks (all courses)
for f in /tmp/w0*.py /tmp/w1*.py; do
  basename=$(basename "$f" .py)
  CM_ARGS="$CM_ARGS --from-file=$basename=$f"
done
for f in /tmp/m1*_starter.py /tmp/m2*_starter.py /tmp/m3*_starter.py /tmp/m4*_starter.py; do
  basename=$(basename "$f" .py)
  CM_ARGS="$CM_ARGS --from-file=$basename=$f"
done
for f in /tmp/p11_exercises.py /tmp/p12_template.py /tmp/p21_pipeline.py /tmp/p22_features.py /tmp/p33_dashboard.py /tmp/p41_collector.py /tmp/p55_warehouse.py /tmp/p66_ml_service.py; do
  basename=$(basename "$f" .py)
  CM_ARGS="$CM_ARGS --from-file=$basename=$f"
done

# Guides and grader
CM_ARGS="$CM_ARGS --from-file=guide=/tmp/JUPYTERHUB-OPERATION-GUIDE.md"
CM_ARGS="$CM_ARGS --from-file=student_guide=/tmp/JUPYTERHUB-STUDENT-GUIDE.md"
CM_ARGS="$CM_ARGS --from-file=code_grader=/tmp/code_grader.py"

echo "Creating ConfigMap with ALL content..."
kubectl create configmap lecture-notebooks -n jupyterhub $CM_ARGS --dry-run=client -o yaml | kubectl apply -f - 2>&1
echo "ConfigMap created!"

echo ""
echo "============================================================"
echo "Step 3: 更新 JupyterHub 启动脚本（全课程分发）"
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
    NB=/tmp/notebooks
    mkdir -p $WORK /home/jovyan/.jupyter $WORK/student_code_framework
    
    # jupyter-ai config
    cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAIC'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAIC
    
    # Distribute guides
    cp $NB/guide $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null
    cp $NB/student_guide $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
    
    # Code grader
    cp $NB/code_grader $WORK/code_grader.py 2>/dev/null
    
    # Course-specific content distribution
    case "$USERNAME" in
      # ===== 02-程序设计基础 =====
      Lecture-B1|lecture-b1)
        cp $NB/w01_0.1_设备参数初始化系_student "$WORK/w01_0.1_设备参数初始化系统_学生版.ipynb" 2>/dev/null
        cp $NB/w01_0.1_设备参数初始化系_teacher "$WORK/w01_0.1_设备参数初始化系统_教师版.ipynb" 2>/dev/null
        cp $NB/w02_0.2a_工业实时告警系统_student "$WORK/w02_0.2a_工业实时告警系统_学生版.ipynb" 2>/dev/null
        cp $NB/w02_0.2a_工业实时告警系统_teacher "$WORK/w02_0.2a_工业实时告警系统_教师版.ipynb" 2>/dev/null
        cp $NB/w01_device_init "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/w02_alarm_if "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-B2|lecture-b2)
        cp $NB/w03_0.2b_工业实时告警系统_student "$WORK/w03_0.2b_工业实时告警系统_学生版.ipynb" 2>/dev/null
        cp $NB/w03_0.2b_工业实时告警系统_teacher "$WORK/w03_0.2b_工业实时告警系统_教师版.ipynb" 2>/dev/null
        cp $NB/w04_0.3_工业设备类设计_student "$WORK/w04_0.3_工业设备类设计_学生版.ipynb" 2>/dev/null
        cp $NB/w04_0.3_工业设备类设计_teacher "$WORK/w04_0.3_工业设备类设计_教师版.ipynb" 2>/dev/null
        cp $NB/w03_alarm_loop "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/w04_device_class "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-B3|lecture-b3)
        cp $NB/w05_0.4_工业设备继承体系_student "$WORK/w05_0.4_工业设备继承体系_学生版.ipynb" 2>/dev/null
        cp $NB/w05_0.4_工业设备继承体系_teacher "$WORK/w05_0.4_工业设备继承体系_教师版.ipynb" 2>/dev/null
        cp $NB/w06_0.5_健壮的工业数据采_student "$WORK/w06_0.5_健壮的工业数据采_学生版.ipynb" 2>/dev/null
        cp $NB/w06_0.5_健壮的工业数据采_teacher "$WORK/w06_0.5_健壮的工业数据采_教师版.ipynb" 2>/dev/null
        cp $NB/w05_inherit "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/w06_robust_collector "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-B4|lecture-b4)
        cp $NB/w07_1.1_工业数据格式转换_student "$WORK/w07_1.1_工业数据格式转换_学生版.ipynb" 2>/dev/null
        cp $NB/w07_1.1_工业数据格式转换_teacher "$WORK/w07_1.1_工业数据格式转换_教师版.ipynb" 2>/dev/null
        cp $NB/w08_1.2_工业数据文件处理_student "$WORK/w08_1.2_工业数据文件处理_学生版.ipynb" 2>/dev/null
        cp $NB/w08_1.2_工业数据文件处理_teacher "$WORK/w08_1.2_工业数据文件处理_教师版.ipynb" 2>/dev/null
        cp $NB/w07_parser "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/w08_fileio "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-B5|lecture-b5)
        cp $NB/w09_1.3_工业故障分析报告_student "$WORK/w09_1.3_工业故障分析报告_学生版.ipynb" 2>/dev/null
        cp $NB/w09_1.3_工业故障分析报告_teacher "$WORK/w09_1.3_工业故障分析报告_教师版.ipynb" 2>/dev/null
        cp $NB/w10_1.4_工业图像处理与报_student "$WORK/w10_1.4_工业图像处理与报_学生版.ipynb" 2>/dev/null
        cp $NB/w10_1.4_工业图像处理与报_teacher "$WORK/w10_1.4_工业图像处理与报_教师版.ipynb" 2>/dev/null
        cp $NB/w09_wordcloud_report "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/w10_report_pdf "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-B6|lecture-b6)
        cp $NB/w11_1.5_工业互联网数据采_student "$WORK/w11_1.5_工业互联网数据采_学生版.ipynb" 2>/dev/null
        cp $NB/w11_1.5_工业互联网数据采_teacher "$WORK/w11_1.5_工业互联网数据采_教师版.ipynb" 2>/dev/null
        cp $NB/w12_Z_综合项目数据处理_student "$WORK/w12_Z_综合项目数据处理_学生版.ipynb" 2>/dev/null
        cp $NB/w12_Z_综合项目数据处理_teacher "$WORK/w12_Z_综合项目数据处理_教师版.ipynb" 2>/dev/null
        cp $NB/w11_collector "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/w12_project_template "$WORK/student_code_framework/" 2>/dev/null
        ;;
      # ===== 01-AI应用基础 =====
      Lecture-A1|lecture-a1)
        cp $NB/m11_m1.1_泵类设备故障诊断_student "$WORK/m11_M1.1_泵类设备故障诊断_学生版.ipynb" 2>/dev/null
        cp $NB/m11_m1.1_泵类设备故障诊断_teacher "$WORK/m11_M1.1_泵类设备故障诊断_教师版.ipynb" 2>/dev/null
        cp $NB/m12_m1.2_特征工程优化的故_student "$WORK/m12_M1.2_特征工程优化的故_学生版.ipynb" 2>/dev/null
        cp $NB/m12_m1.2_特征工程优化的故_teacher "$WORK/m12_M1.2_特征工程优化的故_教师版.ipynb" 2>/dev/null
        cp $NB/m11_starter "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/m12_starter "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-A2|lecture-a2)
        cp $NB/m21_m2.1_工业焊接缺陷检测_student "$WORK/m21_M2.1_工业焊接缺陷检测_学生版.ipynb" 2>/dev/null
        cp $NB/m21_m2.1_工业焊接缺陷检测_teacher "$WORK/m21_M2.1_工业焊接缺陷检测_教师版.ipynb" 2>/dev/null
        cp $NB/m22_m2.2_轴承寿命预测系统_student "$WORK/m22_M2.2_轴承寿命预测系统_学生版.ipynb" 2>/dev/null
        cp $NB/m22_m2.2_轴承寿命预测系统_teacher "$WORK/m22_M2.2_轴承寿命预测系统_教师版.ipynb" 2>/dev/null
        cp $NB/m21_starter "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/m22_starter "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-A3|lecture-a3)
        cp $NB/m31_m3.1_产品表面缺陷尺寸_student "$WORK/m31_M3.1_产品表面缺陷尺寸_学生版.ipynb" 2>/dev/null
        cp $NB/m31_m3.1_产品表面缺陷尺寸_teacher "$WORK/m31_M3.1_产品表面缺陷尺寸_教师版.ipynb" 2>/dev/null
        cp $NB/m32_m3.2_产线实时缺陷检测_student "$WORK/m32_M3.2_产线实时缺陷检测_学生版.ipynb" 2>/dev/null
        cp $NB/m32_m3.2_产线实时缺陷检测_teacher "$WORK/m32_M3.2_产线实时缺陷检测_教师版.ipynb" 2>/dev/null
        cp $NB/m31_starter "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/m32_starter "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-A4|lecture-a4)
        cp $NB/m41_m4.1_工业故障报告自动_student "$WORK/m41_M4.1_工业故障报告自动_学生版.ipynb" 2>/dev/null
        cp $NB/m41_m4.1_工业故障报告自动_teacher "$WORK/m41_M4.1_工业故障报告自动_教师版.ipynb" 2>/dev/null
        cp $NB/m42_m4.2_工业智能决策助手_student "$WORK/m42_M4.2_工业智能决策助手_学生版.ipynb" 2>/dev/null
        cp $NB/m42_m4.2_工业智能决策助手_teacher "$WORK/m42_M4.2_工业智能决策助手_教师版.ipynb" 2>/dev/null
        cp $NB/m41_starter "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/m42_starter "$WORK/student_code_framework/" 2>/dev/null
        ;;
      # ===== 03-Python程序设计-项目实战 =====
      Lecture-P1|lecture-p1)
        cp $NB/p11_student "$WORK/p11_P1.1_Python基础_学生版.ipynb" 2>/dev/null
        cp $NB/p11_teacher "$WORK/p11_P1.1_Python基础_教师版.ipynb" 2>/dev/null
        cp $NB/p12_student "$WORK/p12_P1.2_标准Python_学生版.ipynb" 2>/dev/null
        cp $NB/p12_teacher "$WORK/p12_P1.2_标准Python_教师版.ipynb" 2>/dev/null
        cp $NB/p11_exercises "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/p12_template "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-P2|lecture-p2)
        cp $NB/p21_student "$WORK/p21_P2.1_Pandas数据_学生版.ipynb" 2>/dev/null
        cp $NB/p21_teacher "$WORK/p21_P2.1_Pandas数据_教师版.ipynb" 2>/dev/null
        cp $NB/p22_student "$WORK/p22_P2.2_NumPy故障特_学生版.ipynb" 2>/dev/null
        cp $NB/p22_teacher "$WORK/p22_P2.2_NumPy故障特_教师版.ipynb" 2>/dev/null
        cp $NB/p21_pipeline "$WORK/student_code_framework/" 2>/dev/null
        cp $NB/p22_features "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-P3|lecture-p3)
        cp $NB/p33_student "$WORK/p33_P3_产线KPI仪表盘_学生版.ipynb" 2>/dev/null
        cp $NB/p33_teacher "$WORK/p33_P3_产线KPI仪表盘_教师版.ipynb" 2>/dev/null
        cp $NB/p33_dashboard "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-P4|lecture-p4)
        cp $NB/p41_student "$WORK/p41_P4.1_多源数据采集系统_学生版.ipynb" 2>/dev/null
        cp $NB/p41_teacher "$WORK/p41_P4.1_多源数据采集系统_教师版.ipynb" 2>/dev/null
        cp $NB/p41_collector "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-P5|lecture-p5)
        cp $NB/p55_student "$WORK/p55_P5_产线数据仓库与O_学生版.ipynb" 2>/dev/null
        cp $NB/p55_teacher "$WORK/p55_P5_产线数据仓库与O_教师版.ipynb" 2>/dev/null
        cp $NB/p55_warehouse "$WORK/student_code_framework/" 2>/dev/null
        ;;
      Lecture-P6|lecture-p6)
        cp $NB/p66_student "$WORK/p66_P6_故障诊断模型与部_学生版.ipynb" 2>/dev/null
        cp $NB/p66_teacher "$WORK/p66_P6_故障诊断模型与部_教师版.ipynb" 2>/dev/null
        cp $NB/p66_ml_service "$WORK/student_code_framework/" 2>/dev/null
        ;;
      # ===== Admin teacher gets everything =====
      teacher-zhang)
        for f in $NB/*_student; do
          bn=$(basename "$f" | sed 's/_student//')
          cp "$f" "$WORK/${bn}_学生版.ipynb" 2>/dev/null
        done
        for f in $NB/*_teacher; do
          bn=$(basename "$f" | sed 's/_teacher//')
          cp "$f" "$WORK/${bn}_教师版.ipynb" 2>/dev/null
        done
        for f in $NB/w0*.py $NB/w1*.py $NB/m1*.py $NB/m2*.py $NB/m3*.py $NB/m4*.py; do
          bn=$(basename "$f")
          if echo "$bn" | grep -q "starter\|device\|alarm\|inherit\|collector\|parser\|fileio\|wordcloud\|report_pdf\|project\|exercises\|template\|pipeline\|features\|dashboard\|warehouse\|ml_service"; then
            cp "$f" "$WORK/student_code_framework/" 2>/dev/null
          fi
        done
        ;;
    esac
    
    pip install --quiet pycodestyle 2>/dev/null
    echo "Startup complete: $USERNAME ($(ls $WORK/*.ipynb 2>/dev/null | wc -l) notebooks)"
STARTEOF

echo "Startup script updated"

echo ""
echo "============================================================"
echo "Step 4: 更新 JupyterHub 分组和配置"
echo "============================================================"

kubectl get cm jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_final.py

# Update admin_users to include ALL lecture accounts
python3 -c "
content = open('/tmp/jhub_final.py').read()
# Replace admin_users
import re
new_admin = 'c.Authenticator.admin_users = {\"teacher-zhang\", \"Lecture-B1\", \"Lecture-B2\", \"Lecture-B3\", \"Lecture-B4\", \"Lecture-B5\", \"Lecture-B6\", \"Lecture-A1\", \"Lecture-A2\", \"Lecture-A3\", \"Lecture-A4\", \"Lecture-P1\", \"Lecture-P2\", \"Lecture-P3\", \"Lecture-P4\", \"Lecture-P5\", \"Lecture-P6\"}'
content = re.sub(r'c\.Authenticator\.admin_users\s*=\s*\{[^}]+\}', new_admin, content, count=1)
open('/tmp/jhub_final.py', 'w').write(content)
print('Admin users updated')
"

# Add all groups
cat >> /tmp/jhub_final.py << 'GROUPS'

# Multi-course groups
c.JupyterHub.load_groups = {
    'lecture-b1-students': [], 'lecture-b2-students': [], 'lecture-b3-students': [],
    'lecture-b4-students': [], 'lecture-b5-students': [], 'lecture-b6-students': [],
    'lecture-a1-students': [], 'lecture-a2-students': [], 'lecture-a3-students': [],
    'lecture-a4-students': [],
    'lecture-p1-students': ['student-python', 'student-alice'],
    'lecture-p2-students': ['student-java', 'student-bob'],
    'lecture-p3-students': ['student-carol'],
    'lecture-p4-students': [], 'lecture-p5-students': [], 'lecture-p6-students': [],
    'course-b-students': [], 'course-a-students': [], 'course-p-students': [],
    'all-students': [],
    'all-teachers': ['teacher-zhang', 'Lecture-B1', 'Lecture-B2', 'Lecture-B3',
                     'Lecture-B4', 'Lecture-B5', 'Lecture-B6',
                     'Lecture-A1', 'Lecture-A2', 'Lecture-A3', 'Lecture-A4',
                     'Lecture-P1', 'Lecture-P2', 'Lecture-P3',
                     'Lecture-P4', 'Lecture-P5', 'Lecture-P6'],
}
GROUPS

kubectl create cm jupyterhub-config -n jupyterhub --from-file=jupyterhub_config.py=/tmp/jhub_final.py --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub config updated with 17 admin accounts + 20 groups"

echo ""
echo "============================================================"
echo "Step 5: 重启 JupyterHub"
echo "============================================================"
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "============================================================"
echo "Step 6: 最终验证"
echo "============================================================"
sleep 30

echo "=== Hub status ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
kubectl get pod -n jupyterhub $HUB_POD 2>&1

echo ""
echo "=== Verify accounts ==="
kubectl exec -n jupyterhub $HUB_POD -c jupyterhub -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('SELECT name FROM users WHERE admin=1 AND name LIKE \"Lecture%\" ORDER BY name')
admins = [r[0] for r in c.fetchall()]
print(f'Admin Lecture accounts: {len(admins)}')
for a in admins:
    print(f'  {a}')
c.execute('SELECT COUNT(*) FROM groups')
print(f'Total groups: {c.fetchone()[0]}')
conn.close()
" 2>&1

echo ""
echo "=== ConfigMap keys ==="
kubectl get cm lecture-notebooks -n jupyterhub -o jsonpath='{.data}' 2>&1 | python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
keys = sorted(data.keys())
print(f'Total ConfigMap keys: {len(keys)}')
student_nbs = [k for k in keys if '_student' in k]
teacher_nbs = [k for k in keys if '_teacher' in k]
code_files = [k for k in keys if k.endswith('.py') or any(x in k for x in ['starter', 'exercises', 'template', 'pipeline', 'features', 'dashboard', 'collector', 'warehouse', 'ml_service', 'device', 'alarm', 'inherit', 'parser', 'fileio', 'wordcloud', 'report', 'project'])]
guides = [k for k in keys if 'guide' in k.lower()]
grader = [k for k in keys if 'grader' in k.lower()]
print(f'Student notebooks: {len(student_nbs)}')
print(f'Teacher notebooks: {len(teacher_nbs)}')
print(f'Code framework files: {len(code_files)}')
print(f'Guides: {len(guides)}')
print(f'Code grader: {len(grader)}')
" 2>&1

echo ""
echo "=== Node load ==="
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "多课程账户体系："
echo ""
echo "  课程                        | Lecture账户         | 学生前缀  | Notebook数"
echo "  ────────────────────────────┼────────────────────┼──────────┼───────────"
echo "  02-程序设计基础 (12周)      | Lecture-B1~B6      | b1~b6-xxx | 12×2=24"
echo "  01-AI应用基础 (8模块)       | Lecture-A1~A4      | a1~a4-xxx | 8×2=16"
echo "  03-Python项目实战 (8模块)   | Lecture-P1~P6      | p1~p6-xxx | 8×2=16"
echo "  ────────────────────────────┴────────────────────┴──────────┴───────────"
echo "  合计: 16个Lecture账户, 56个Notebook, 管理员: teacher-zhang"
echo ""
echo "学生登录格式: {课程前缀}-{学生名}"
echo "  b1-alice → Lecture-B1 的学生"
echo "  a1-bob   → Lecture-A1 的学生"
echo "  p1-carol → Lecture-P1 的学生"
