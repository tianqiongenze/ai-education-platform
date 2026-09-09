#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LMS选课 → JupyterHub 自动同步服务
读取 Open edX MySQL 的 CourseEnrollment 表，
将新选课的学生/教师同步到 JupyterHub SQLite 数据库，
并根据课程系列将用户加入对应的 JupyterHub 分组。

部署方式: K8s CronJob, 每 5 分钟运行一次
"""
import os, sys, sqlite3, json, traceback
from datetime import datetime, timezone

import MySQLdb  # PyMySQL

# ── 配置 ──
MYSQL_HOST = os.environ.get('MYSQL_HOST', '10.167.2.175')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '32036'))
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASS = os.environ.get('MYSQL_PASS', os.environ.get('MYSQL_PASS', ''))
MYSQL_DB   = os.environ.get('MYSQL_DB', 'openedx')

HUB_DB_PATH = os.environ.get('HUB_DB_PATH', '/srv/jupyterhub/jupyterhub.sqlite')

# Open edX course → JupyterHub group 映射
# A系列 → course-a-students / course-a-teachers
# B系列 → course-b-students / course-b-teachers
# P系列 → course-p-students / course-p-teachers
COURSE_SERIES = {
    'A': {'students': 'course-a-students', 'teachers': 'course-a-teachers'},
    'B': {'students': 'course-b-students', 'teachers': 'course-b-teachers'},
    'P': {'students': 'course-p-students', 'teachers': 'course-p-teachers'},
}

# 16 门课程编号
COURSE_NUMS = ['A1','A2','A3','A4','B1','B2','B3','B4','B5','B6','P1','P2','P3','P4','P5','P6']

def get_lms_enrollments():
    """从 LMS MySQL 读取所有 AIEDU 课程的选课记录"""
    conn = MySQLdb.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                           passwd=MYSQL_PASS, db=MYSQL_DB, charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.email, u.is_staff, ce.course_id
        FROM auth_user u
        JOIN student_courseenrollment ce ON ce.user_id = u.id
        WHERE ce.is_active = 1
          AND ce.course_id LIKE 'course-v1:AIEDU+%%+2026'
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    enrollments = []
    for username, email, is_staff, course_id in rows:
        # parse course number from course_id like "course-v1:AIEDU+A1+2026"
        parts = course_id.split('+')
        if len(parts) >= 3:
            num = parts[1]  # e.g. A1, B3, P5
            series = num[0] if num else '?'
            enrollments.append({
                'username': username,
                'email': email,
                'is_staff': bool(is_staff),
                'course_num': num,
                'series': series,
                'course_id': course_id,
            })
    return enrollments

def hub_username(email):
    """将 LMS email 转为 JupyterHub username
    lecture-a1@edu.local → lecture-a1
    py_a_001@edu.local → py_a_001
    student-python@edu.local → student-python
    """
    return email.split('@')[0]

def sync_to_hub(enrollments):
    """将选课记录同步到 JupyterHub SQLite"""
    conn = sqlite3.connect(HUB_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    stats = {'users_created': 0, 'users_existing': 0, 'groups_uaranteed': 0,
             'group_memberships_added': 0, 'group_memberships_existing': 0, 'errors': []}

    # 1) 确保 all-students / all-teachers 分组存在
    base_groups = ['all-students', 'all-teachers',
                   'course-a-students', 'course-a-teachers',
                   'course-b-students', 'course-b-teachers',
                   'course-p-students', 'course-p-teachers']
    for gn in base_groups:
        cur.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (gn,))
    conn.commit()

    # 获取 group id 映射
    cur.execute("SELECT id, name FROM groups")
    group_map = {row['name']: row['id'] for row in cur.fetchall()}

    # 2) 处理每个选课用户
    seen_users = set()
    for enr in enrollments:
        hub_user = hub_username(enr['email'])
        if hub_user in seen_users:
            continue
        seen_users.add(hub_user)

        # 创建用户（如果不存在）
        cur.execute("SELECT id FROM users WHERE name = ?", (hub_user,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO users (name) VALUES (?)", (hub_user,))
            conn.commit()
            cur.execute("SELECT id FROM users WHERE name = ?", (hub_user,))
            row = cur.fetchone()
            stats['users_created'] += 1
        else:
            stats['users_existing'] += 1
        uid = row['id']

        # 加入对应分组
        series = enr['series']
        is_staff = enr['is_staff'] or hub_user.startswith('lecture-') or hub_user.startswith('teacher-')
        role = 'teachers' if is_staff else 'students'

        groups_to_join = ['all-' + role]
        if series in COURSE_SERIES:
            groups_to_join.append(COURSE_SERIES[series][role])

        for gn in groups_to_join:
            gid = group_map.get(gn)
            if gid is None:
                continue
            cur.execute("SELECT 1 FROM user_group_map WHERE user_id = ? AND group_id = ?", (uid, gid))
            if cur.fetchone() is None:
                cur.execute("INSERT INTO user_group_map (user_id, group_id) VALUES (?, ?)", (uid, gid))
                stats['group_memberships_added'] += 1
            else:
                stats['group_memberships_existing'] += 1
    conn.commit()

    # 3) 为新创建的学生自动创建 PVC claim-{username} 标记（不实际创建 PVC，仅记录日志）
    cur.execute("SELECT name FROM users")
    all_hub_users = [r['name'] for r in cur.fetchall()]
    cur.close()
    conn.close()

    stats['total_hub_users'] = len(all_hub_users)
    return stats

def main():
    print("=== LMS→JupyterHub Sync started at %s ===" % datetime.now(timezone.utc).isoformat())
    try:
        enrollments = get_lms_enrollments()
        print("LMS enrollments found: %d" % len(enrollments))
        # 去重统计
        unique_users = set(e['username'] for e in enrollments)
        print("Unique users: %d" % len(unique_users))
        stats = sync_to_hub(enrollments)
        print("Sync stats: %s" % json.dumps(stats, ensure_ascii=False, indent=2))
        print("=== Sync completed successfully ===")
    except Exception as e:
        print("ERROR: %s" % str(e))
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
