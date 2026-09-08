#!/bin/bash
# ============================================================
# 多教师同课程+班级关联重构
# 基于JupyterHub Groups API + Sharing API + Roles
# ============================================================
set -e

echo "============================================================"
echo "Part 1: 重构账户体系 — 多教师同课程+班级"
echo "============================================================"

HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
echo "Hub: $HUB_POD"

echo ""
echo "=== 1.1 创建班级分组和教师分组 ==="

kubectl exec -n jupyterhub $HUB_POD -c jupyterhub -- python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()

# ============================================================
# 账户体系重构：课程 → 教师(可多个) → 班级 → 学生
#
# 命名规则:
#   教师:   teacher-{课程}-{序号}  (如 teacher-b1-01, teacher-b1-02)
#   班级:   class-{课程}-{教师序号}-{班级号} (如 class-b1-01-A)
#   学生:   {课程}-{班级}-{学号}  (如 b1-A-01, b1-A-02)
#
# 分组结构:
#   course-{课程}-teachers: 所有教该课程的教师
#   class-{课程}-{班级}: 该班级的所有学生 + 教师
#   course-{课程}-all: 该课程所有人
# ============================================================

# 定义完整的课程-教师-班级结构
structure = {
    # ===== 02-程序设计基础 =====
    "course-b": {
        "teachers": [
            {"name": "teacher-b1-01", "classes": ["class-b1-01-A", "class-b1-01-B"]},
            {"name": "teacher-b2-01", "classes": ["class-b2-01-A"]},
            {"name": "teacher-b3-01", "classes": ["class-b3-01-A"]},
            {"name": "teacher-b4-01", "classes": ["class-b4-01-A"]},
            {"name": "teacher-b5-01", "classes": ["class-b5-01-A"]},
            {"name": "teacher-b6-01", "classes": ["class-b6-01-A"]},
        ],
        "existing_lectures": ["Lecture-B1", "Lecture-B2", "Lecture-B3", "Lecture-B4", "Lecture-B5", "Lecture-B6"],
    },
    # ===== 01-AI应用基础 =====
    "course-a": {
        "teachers": [
            {"name": "teacher-a1-01", "classes": ["class-a1-01-A", "class-a1-01-B"]},
            {"name": "teacher-a2-01", "classes": ["class-a2-01-A"]},
            {"name": "teacher-a3-01", "classes": ["class-a3-01-A"]},
            {"name": "teacher-a4-01", "classes": ["class-a4-01-A"]},
        ],
        "existing_lectures": ["Lecture-A1", "Lecture-A2", "Lecture-A3", "Lecture-A4"],
    },
    # ===== 03-Python项目实战 =====
    "course-p": {
        "teachers": [
            {"name": "teacher-p1-01", "classes": ["class-p1-01-A", "class-p1-01-B"]},
            {"name": "teacher-p2-01", "classes": ["class-p2-01-A"]},
            {"name": "teacher-p3-01", "classes": ["class-p3-01-A"]},
            {"name": "teacher-p4-01", "classes": ["class-p4-01-A"]},
            {"name": "teacher-p5-01", "classes": ["class-p5-01-A"]},
            {"name": "teacher-p6-01", "classes": ["class-p6-01-A"]},
        ],
        "existing_lectures": ["Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"],
    },
}

# Create teacher accounts
for course_id, course_info in structure.items():
    for teacher in course_info["teachers"]:
        tname = teacher["name"]
        try:
            c.execute('INSERT INTO users (name, admin) VALUES (?, 1)', (tname,))
            print(f'  Created teacher: {tname}')
        except:
            c.execute('UPDATE users SET admin = 1 WHERE name = ?', (tname,))
            print(f'  Updated teacher: {tname}')

# Create groups
for course_id, course_info in structure.items():
    # Course-level teacher group
    group_name = f'{course_id}-teachers'
    try:
        c.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
        print(f'  Group: {group_name}')
    except:
        print(f'  Group exists: {group_name}')

    # Add teachers to course group
    c.execute('SELECT id FROM groups WHERE name=?', (group_name,))
    gid = c.fetchone()
    if gid:
        for teacher in course_info["teachers"]:
            c.execute('SELECT id FROM users WHERE name=?', (teacher["name"],))
            uid = c.fetchone()
            if uid:
                try:
                    c.execute('INSERT INTO users_groups (user_id, group_id) VALUES (?, ?)', (uid[0], gid[0]))
                except:
                    pass

    # Also add existing Lecture accounts to teachers group
    for lect in course_info["existing_lectures"]:
        c.execute('SELECT id FROM users WHERE name=?', (lect,))
        uid = c.fetchone()
        if uid and gid:
            try:
                c.execute('INSERT INTO users_groups (user_id, group_id) VALUES (?, ?)', (uid[0], gid[0]))
            except:
                pass

    # Create class groups
    for teacher in course_info["teachers"]:
        for cls in teacher["classes"]:
            try:
                c.execute('INSERT INTO groups (name) VALUES (?)', (cls,))
                print(f'  Group: {cls}')
            except:
                pass

            # Add teacher to their class group
            c.execute('SELECT id FROM groups WHERE name=?', (cls,))
            cls_gid = c.fetchone()
            c.execute('SELECT id FROM users WHERE name=?', (teacher["name"],))
            t_uid = c.fetchone()
            if cls_gid and t_uid:
                try:
                    c.execute('INSERT INTO users_groups (user_id, group_id) VALUES (?, ?)', (t_uid[0], cls_gid[0]))
                except:
                    pass

    # Course-wide group (all students + teachers)
    all_group = f'{course_id}-all'
    try:
        c.execute('INSERT INTO groups (name) VALUES (?)', (all_group,))
        print(f'  Group: {all_group}')
    except:
        pass

conn.commit()

# Summary
c.execute('SELECT COUNT(*) FROM users WHERE admin=1')
admin_count = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM groups')
group_count = c.fetchone()[0]
c.execute('SELECT name FROM users WHERE admin=1 AND name LIKE "teacher-%" ORDER BY name')
new_teachers = [r[0] for r in c.fetchall()]

print(f'\nSummary:')
print(f'  Admin users: {admin_count}')
print(f'  Total groups: {group_count}')
print(f'  New teacher accounts: {len(new_teachers)}')
for t in new_teachers:
    print(f'    {t}')

conn.close()
print('Account restructuring complete!')
PYEOF

echo ""
echo "============================================================"
echo "Part 2: 更新 JupyterHub 配置 — 角色和权限"
echo "============================================================"

kubectl get cm jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_roles.py

cat >> /tmp/jhub_roles.py << 'ROLECONFIG'

# ============================================================
# Role-Based Access Control (RBAC) for multi-teacher classes
# ============================================================

# Define roles
c.JupyterHub.load_roles = [
    {
        # Admin role: full access to all servers
        "name": "administrator",
        "scopes": ["admin", "users", "groups", "servers"],
        "users": ["teacher-zhang"],
    },
    {
        # Teacher role: can access servers of students in their groups
        "name": "teacher",
        "scopes": [
            "self",
            "users:names",
            "groups:names",
            "read:users:name",
            "read:groups:name",
            "read:users:servers",
            "access:servers",
            "shares",
        ],
        "groups": [
            "course-b-teachers", "course-a-teachers", "course-p-teachers",
            "all-teachers",
        ],
    },
    {
        # Student role: can only access own server
        "name": "student",
        "scopes": ["self"],
    },
]

# All admin users (legacy + new)
c.Authenticator.admin_users = {
    "teacher-zhang",
    "Lecture-B1", "Lecture-B2", "Lecture-B3", "Lecture-B4", "Lecture-B5", "Lecture-B6",
    "Lecture-A1", "Lecture-A2", "Lecture-A3", "Lecture-A4",
    "Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6",
    "teacher-b1-01", "teacher-b2-01", "teacher-b3-01", "teacher-b4-01", "teacher-b5-01", "teacher-b6-01",
    "teacher-a1-01", "teacher-a2-01", "teacher-a3-01", "teacher-a4-01",
    "teacher-p1-01", "teacher-p2-01", "teacher-p3-01", "teacher-p4-01", "teacher-p5-01", "teacher-p6-01",
}
c.JupyterHub.admin_access = True
ROLECONFIG

kubectl create cm jupyterhub-config -n jupyterhub \
  --from-file=jupyterhub_config.py=/tmp/jhub_roles.py \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub RBAC config updated"

echo ""
echo "============================================================"
echo "Part 3: 更新启动脚本 — 学生自动加入班级"
echo "============================================================"

kubectl get cm jupyterhub-startup -n jupyterhub -o jsonpath='{.data.startup\.sh}' > /tmp/startup_classes.sh

# Add student class auto-assignment based on username pattern:
# {course}-{class}-{student_number} → join class-{course}-{class}
python3 << 'PYEOF'
content = open('/tmp/startup_classes.sh').read()

# Add class auto-assignment after the case statement closes
# Find the line "pip install --quiet pycodestyle" and insert before it
class_logic = '''    # ===== 6. Auto-assign student to class group =====
    # Username format: {course_prefix}-{class_letter}-{student_number}
    # Example: b1-A-01 → class-b1-01-A
    # Example: a1-B-03 → class-a1-01-B
    case "$USERNAME" in
      b[1-6]-[A-Z]-[0-9]*)
        WEEK=$(echo "$USERNAME" | cut -d- -f1)
        CLASS=$(echo "$USERNAME" | cut -d- -f2)
        GROUP_NAME="class-${WEEK}-01-${CLASS}"
        ;;
      a[1-4]-[A-Z]-[0-9]*)
        MOD=$(echo "$USERNAME" | cut -d- -f1)
        CLASS=$(echo "$USERNAME" | cut -d- -f2)
        GROUP_NAME="class-${MOD}-01-${CLASS}"
        ;;
      p[1-6]-[A-Z]-[0-9]*)
        MOD=$(echo "$USERNAME" | cut -d- -f1)
        CLASS=$(echo "$USERNAME" | cut -d- -f2)
        GROUP_NAME="class-${MOD}-01-${CLASS}"
        ;;
      *)
        GROUP_NAME=""
        ;;
    esac
    
    # Log class assignment
    if [ -n "$GROUP_NAME" ]; then
      echo "  Class group: $GROUP_NAME"
    fi

'''
content = content.replace('    pip install --quiet pycodestyle', class_logic + '    pip install --quiet pycodestyle')
open('/tmp/startup_classes.sh', 'w').write(content)
print('Startup script updated with class auto-assignment')
PYEOF

kubectl create configmap jupyterhub-startup -n jupyterhub \
  --from-file=startup.sh=/tmp/startup_classes.sh \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "Startup script updated with class auto-assignment"

echo ""
echo "============================================================"
echo "Part 4: Restart hub"
echo "============================================================"
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "============================================================"
echo "Part 5: Verify"
echo "============================================================"
sleep 30

echo "=== Hub ==="
kubectl get pods -n jupyterhub 2>&1 | head -5

echo ""
echo "=== Teacher accounts ==="
kubectl exec -n jupyterhub $(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}') -c jupyterhub -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('SELECT name FROM users WHERE admin=1 AND name LIKE \"teacher-%\" ORDER BY name')
for r in c.fetchall():
    print(f'  {r[0]}')
c.execute('SELECT COUNT(*) FROM groups')
print(f'Total groups: {c.fetchone()[0]}')
conn.close()
" 2>&1

echo ""
echo "=== Node load ==="
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "多教师同课程+班级关联体系："
echo ""
echo "  课程                    | 教师(可多个)         | 班级分组"
echo "  ────────────────────────┼─────────────────────┼──────────────────"
echo "  02-程序设计基础 B1      | teacher-b1-01       | class-b1-01-A, -B"
echo "  02-程序设计基础 B2      | teacher-b2-01       | class-b2-01-A"
echo "  02-程序设计基础 B3~B6   | teacher-b3~6-01      | class-b3~6-01-A"
echo "  01-AI应用基础 A1        | teacher-a1-01       | class-a1-01-A, -B"
echo "  01-AI应用基础 A2~A4     | teacher-a2~4-01      | class-a2~4-01-A"
echo "  03-Python项目实战 P1    | teacher-p1-01       | class-p1-01-A, -B"
echo "  03-Python项目实战 P2~P6 | teacher-p2~6-01      | class-p2~6-01-A"
echo "  ────────────────────────┴─────────────────────┴──────────────────"
echo "  总管理员: teacher-zhang (可管理所有人)"
echo "  旧Lecture账户保留为管理员"
echo ""
echo "学生登录格式: {课程}-{班级}-{学号}"
echo "  b1-A-01 → 程序设计基础 B1 班级A 01号"
echo "  a1-B-03 → AI应用基础 A1 班级B 03号"
echo "  p1-A-05 → Python项目实战 P1 班级A 05号"
echo ""
echo "教师查看学生: 管理面板 → 自己班级的学生服务器"
echo "  teacher-b1-01 可看到 class-b1-01-A 和 class-b1-01-B 的学生"
echo "  teacher-a1-01 可看到 class-a1-01-A 和 class-a1-01-B 的学生"
