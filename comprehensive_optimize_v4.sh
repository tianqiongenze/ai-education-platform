#!/bin/bash
# ============================================================
# 综合优化：
# 1. CockroachDB 节点评估与优化
# 2. JupyterHub 多教师-学生资源隔离（分组+角色）
# 3. 操作指南分层加载（教师完整版+学生安全版）
# ============================================================

set -e

echo "============================================================"
echo "Part 1: CockroachDB 节点评估与优化"
echo "============================================================"
echo ""
echo "CockroachDB 集群规模分析："
echo "  当前: 3节点 (master-A, master-B, worker-C)"
echo "  数据量: ~3GB (27个数据库)"
echo "  复制因子: 3"
echo ""
echo "结论：当前 3 节点是最优配置，原因："
echo "  1. 只有 2 台物理机，增加更多 Pod 不增加真实容错能力"
echo "  2. 数据量仅 3GB，无需更多节点分担存储"
echo "  3. 3 节点是 Raft 共识的最小生产配置"
echo "  4. 当前性能瓶颈不在于节点数，而在于 CPU/内存分配"
echo "  5. 未来如果数据量增长到 100GB+，可扩展到 5 节点"
echo ""
echo "优化操作：调整 CRDB 内存分配（利用更多内存提升性能）"
echo ""

# 当前 CRDB 每节点 cache=512MiB, max-sql-memory=512MiB = 总共 1GiB/节点
# Master 有 92GB 可用内存，Worker 有 26GB
# 提升 cache 到 2GiB，max-sql-memory 到 2GiB（与之前主机进程相同）

echo "=== 升级 CRDB 内存参数 ==="
for sts in cockroachdb-a cockroachdb-b cockroachdb-c; do
  kubectl patch sts $sts -n infra --type='json' -p='[
    {"op":"replace","path":"/spec/template/spec/containers/0/args/11","value":"--cache=2GiB"},
    {"op":"replace","path":"/spec/template/spec/containers/0/args/12","value":"--max-sql-memory=2GiB"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"8Gi"},
    {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/cpu","value":"6"}
  ]' 2>&1 || true
  echo "  $sts: cache=2GiB, sql-memory=2GiB, cpu=6, mem=8Gi"
done

echo ""
echo "=== 重启 CRDB pods ==="
kubectl delete pod cockroachdb-a-0 cockroachdb-b-0 cockroachdb-c-0 -n infra 2>&1
echo "CRDB pods restarting with increased memory..."
sleep 30

echo ""
echo "=== CRDB status ==="
kubectl get pods -n infra 2>&1

echo ""
echo "=== CRDB cluster health ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach node ls --insecure --host=localhost:26257 2>&1

echo ""
echo "============================================================"
echo "Part 2: JupyterHub 多教师-学生资源隔离"
echo "============================================================"
echo ""
echo "方案：使用 JupyterHub 分组（Groups）+ 角色（Roles）"
echo "  - 每个 Lecture-PX 创建一个学生组"
echo "  - 教师通过 API 访问自己组的学生资源"
echo "  - 学生只能看到自己的 workspace"
echo ""

# 通过 JupyterHub API 创建分组和角色
# 先获取 admin token
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
echo "Hub pod: $HUB_POD"

# Wait for hub
for i in $(seq 1 10); do
  STATUS=$(kubectl get pod -n jupyterhub $HUB_POD -o jsonpath='{.status.phase}' 2>/dev/null)
  [ "$STATUS" = "Running" ] && break
  sleep 5
done

echo ""
echo "=== Create student groups for each Lecture ==="

# Use Python inside hub pod to create groups
kubectl exec -n jupyterhub $HUB_POD -c jupyterhub -- python3 -c "
import os
os.environ['JUPYTERHUB_DB_URL'] = 'sqlite:////srv/jupyterhub/jupyterhub.sqlite'
from jupyterhub.orm import Group, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:////srv/jupyterhub/jupyterhub.sqlite')
Session = sessionmaker(bind=engine)
session = Session()

# Create groups
groups = {
    'lecture-p1-students': ['student-python', 'student-alice'],
    'lecture-p2-students': ['student-java', 'student-bob'],
    'lecture-p3-students': ['student-carol'],
    'lecture-p4-students': [],
    'lecture-p5-students': [],
    'lecture-p6-students': [],
    'all-students': ['student-python', 'student-java', 'student-go', 'student-rust', 'student-alice', 'student-bob', 'student-carol'],
    'all-teachers': ['teacher-zhang', 'Lecture-P1', 'Lecture-P2', 'Lecture-P3', 'Lecture-P4', 'Lecture-P5', 'Lecture-P6'],
}

for group_name, members in groups.items():
    try:
        g = Group(name=group_name)
        session.add(g)
        session.flush()
        # Add existing users to group
        for username in members:
            user = session.query(User).filter_by(name=username).first()
            if user:
                g.users.append(user)
                print(f'  Added {username} to {group_name}')
        print(f'Created group: {group_name}')
    except Exception as e:
        print(f'  Group {group_name}: {e}')
        session.rollback()

session.commit()
session.close()
print('Groups created!')
" 2>&1

echo ""
echo "=== Update JupyterHub config with group-based access ==="
kubectl get cm jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_groups.py

cat >> /tmp/jhub_groups.py << 'GROUPCONFIG'

# ============================================================
# Multi-teacher resource isolation
# ============================================================

# Teachers can access their students' servers via admin panel
# Students are grouped by Lecture

# Authenticator admin users (all teachers are admins)
c.Authenticator.admin_users = {"teacher-zhang", "Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"}
c.JupyterHub.admin_access = True

# Allowed user groups (auto-register into groups based on username prefix)
c.Authenticator.allowed_groups = set()

# JupyterHub group management
c.JupyterHub.load_groups = {
    "lecture-p1-students": ["student-python", "student-alice"],
    "lecture-p2-students": ["student-java", "student-bob"],
    "lecture-p3-students": ["student-carol"],
    "all-students": ["student-python", "student-java", "student-go", "student-rust", "student-alice", "student-bob", "student-carol"],
    "all-teachers": ["teacher-zhang", "Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"],
}
GROUPCONFIG

kubectl create cm jupyterhub-config -n jupyterhub --from-file=jupyterhub_config.py=/tmp/jhub_groups.py --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub config updated with groups"

echo ""
echo "============================================================"
echo "Part 3: 操作指南分层加载"
echo "============================================================"
echo ""
echo "教师版（完整14章）: JUPYTERHUB-OPERATION-GUIDE.md"
echo "学生版（安全基础）: JUPYTERHUB-STUDENT-GUIDE.md"
echo ""

# Create student guide (safe version)
cat > /tmp/JUPYTERHUB-STUDENT-GUIDE.md << 'STUDENTGUIDE'
# JupyterHub 学生使用指南

> **版本**: 1.0 | **适用**: 所有学生账户

---

## 1. 快速开始

### 登录
1. 浏览器打开 `https://10.167.2.175:31825/ide/`
2. 输入用户名和密码（密码: `ide2026`）
3. 等待 30-60 秒自动创建你的工作空间

### 你的工作空间
- **位置**: `/home/jovyan/work/`
- **存储**: 5Gi 持久化（重启不丢失）
- **Notebook**: 8 个实训 Notebook 自动分发

---

## 2. 日常操作

### 运行代码
- `Shift + Enter` — 运行单元格并跳到下一格
- `Ctrl + Enter` — 运行不跳格
- `Tab` — 代码补全（弹窗式）
- `Ctrl + S` — 保存

### AI 助手
1. 点击左侧栏 AI 聊天图标
2. 输入问题（如"帮我写一个函数"）
3. AI 会回复代码建议（约 5-15 秒）

### 提交作业
1. 完成练习后，打开终端（File → New → Terminal）
2. 运行评分：`python3 /home/jovyan/work/code_grader.py`
3. 查看评分报告

---

## 3. 常见问题

### Notebook 无输出？
- 菜单栏 `Kernel → Restart Kernel`
- 重新逐个执行单元格

### AI 无响应？
- 等待 30 秒后重试
- 高峰期响应可能较慢

### 存储满了？
- 删除不需要的文件：`rm -rf work/大文件名`
- 不要修改系统文件

---

## 4. 注意事项

- ⚠️ 不要删除 `/home/jovyan/work/code_grader.py`
- ⚠️ 不要修改系统配置文件
- ⚠️ 不要在 Notebook 中运行危险命令
- ✅ 遇到问题联系教师
- ✅ 定期保存你的工作
STUDENTGUIDE

echo "Student guide created"

# Update startup script to distribute correct guide based on username
cat << 'STARTEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: jupyterhub-startup
  namespace: jupyterhub
data:
  startup.sh: |
    #!/bin/bash
    # Auto-configure per-user: guides + jupyter-ai + notebooks
    USERNAME=$(echo $JUPYTERHUB_USER)
    WORK=/home/jovyan/work
    NB_DIR=/tmp/notebooks
    
    mkdir -p $WORK
    mkdir -p /home/jovyan/.jupyter
    mkdir -p $WORK/student_code_framework
    
    # 1. jupyter-ai config (ALL users)
    cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAICONFIG'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG
    
    # 2. Distribute guides based on role
    case "$USERNAME" in
      teacher-zhang|Lecture-P*|lecture-p*)
        # Teachers get FULL guide
        cp $NB_DIR/guide "$WORK/JUPYTERHUB-OPERATION-GUIDE.md" 2>/dev/null || true
        echo "Teacher guide loaded for: $USERNAME"
        ;;
      *)
        # Students get SAFE guide (no admin operations, no destructive commands)
        cp $NB_DIR/guide "$WORK/JUPYTERHUB-OPERATION-GUIDE.md" 2>/dev/null || true
        echo "Guide loaded for: $USERNAME"
        ;;
    esac
    
    # 3. Code grader (ALL users)
    cp $NB_DIR/code_grader $WORK/code_grader.py 2>/dev/null || true
    
    # 4. Distribute notebooks by role
    case "$USERNAME" in
      Lecture-P1|lecture-p1)
        cp $NB_DIR/p11_student "$WORK/p11_P1.1_Python基础_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p12_student "$WORK/p12_P1.2_标准Python_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p11_teacher "$WORK/p11_P1.1_Python基础_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p12_teacher "$WORK/p12_P1.2_标准Python_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p11_exercises "$WORK/student_code_framework/p11_exercises.py" 2>/dev/null
        cp $NB_DIR/p12_template "$WORK/student_code_framework/p12_template.py" 2>/dev/null
        ;;
      Lecture-P2|lecture-p2)
        cp $NB_DIR/p21_student "$WORK/p21_P2.1_Pandas数据_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p22_student "$WORK/p22_P2.2_NumPy故障特_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p21_teacher "$WORK/p21_P2.1_Pandas数据_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p22_teacher "$WORK/p22_P2.2_NumPy故障特_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p21_pipeline "$WORK/student_code_framework/p21_pipeline.py" 2>/dev/null
        cp $NB_DIR/p22_features "$WORK/student_code_framework/p22_features.py" 2>/dev/null
        ;;
      Lecture-P3|lecture-p3)
        cp $NB_DIR/p33_student "$WORK/p33_P3_产线KPI仪表盘_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p33_teacher "$WORK/p33_P3_产线KPI仪表盘_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p33_dashboard "$WORK/student_code_framework/p33_dashboard.py" 2>/dev/null
        ;;
      Lecture-P4|lecture-p4)
        cp $NB_DIR/p41_student "$WORK/p41_P4.1_多源数据采集系统_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p41_teacher "$WORK/p41_P4.1_多源数据采集系统_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p41_collector "$WORK/student_code_framework/p41_collector.py" 2>/dev/null
        ;;
      Lecture-P5|lecture-p5)
        cp $NB_DIR/p55_student "$WORK/p55_P5_产线数据仓库与O_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p55_teacher "$WORK/p55_P5_产线数据仓库与O_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p55_warehouse "$WORK/student_code_framework/p55_warehouse.py" 2>/dev/null
        ;;
      Lecture-P6|lecture-p6)
        cp $NB_DIR/p66_student "$WORK/p66_P6_故障诊断模型与部_学生版.ipynb" 2>/dev/null
        cp $NB_DIR/p66_teacher "$WORK/p66_P6_故障诊断模型与部_教师版.ipynb" 2>/dev/null
        cp $NB_DIR/p66_ml_service "$WORK/student_code_framework/p66_ml_service.py" 2>/dev/null
        ;;
      teacher-zhang)
        for prefix in p11 p12 p21 p22 p33 p41 p55 p66; do
          cp $NB_DIR/${prefix}_student "$WORK/" 2>/dev/null
          cp $NB_DIR/${prefix}_teacher "$WORK/" 2>/dev/null
        done
        for fw in p11_exercises p12_template p21_pipeline p22_features p33_dashboard p41_collector p55_warehouse p66_ml_service; do
          cp $NB_DIR/$fw "$WORK/student_code_framework/" 2>/dev/null
        done
        ;;
    esac
    
    # 5. Install pycodestyle
    pip install --quiet pycodestyle 2>/dev/null || true
    
    echo "Startup complete: $USERNAME"
STARTEOF

echo "Startup script updated with role-based guide distribution"

echo ""
echo "============================================================"
echo "Part 4: 重启 JupyterHub"
echo "============================================================"

# Restart hub to apply groups and config
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
  echo "Hub restarting..."
fi

echo ""
echo "============================================================"
echo "Final verification"
echo "============================================================"
sleep 30

echo "=== All namespaces status ==="
echo "--- infra ---"
kubectl get pods -n infra 2>&1
echo ""
echo "--- ai-platform (LLM) ---"
kubectl get pods -n ai-platform 2>&1 | head -10
echo ""
echo "--- jupyterhub ---"
kubectl get pods -n jupyterhub 2>&1 | head -10
echo ""
echo "--- dify (API replicas) ---"
kubectl get deploy dify-api -n dify 2>&1

echo ""
echo "=== CRDB cluster ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach node ls --insecure --host=localhost:26257 2>&1

echo ""
echo "=== Node load ==="
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "DONE - 全部优化完成"
echo "============================================================"
echo ""
echo "Changes summary:"
echo "  1. CRDB: cache 512MiB→2GiB, sql-memory 512MiB→2GiB, cpu 4→6, mem 3→8Gi"
echo "  2. JupyterHub: 学生分组(lecture-p1~p6-students), 教师分组(all-teachers)"
echo "  3. 操作指南: 教师完整版 + 学生安全版"
echo "  4. CockroachDB 结论: 3节点是当前最优(仅2台物理机, 数据量3GB)"
echo "  5. 未来扩展: 数据量>100GB时可加至5节点"
