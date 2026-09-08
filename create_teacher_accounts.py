#!/usr/bin/env python3
"""Create multi-teacher + class groups in JupyterHub DB."""
import sqlite3

conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()

teachers = [
    'teacher-b1-01', 'teacher-b2-01', 'teacher-b3-01',
    'teacher-b4-01', 'teacher-b5-01', 'teacher-b6-01',
    'teacher-a1-01', 'teacher-a2-01', 'teacher-a3-01', 'teacher-a4-01',
    'teacher-p1-01', 'teacher-p2-01', 'teacher-p3-01',
    'teacher-p4-01', 'teacher-p5-01', 'teacher-p6-01',
]

for t in teachers:
    try:
        c.execute('INSERT INTO users (name, admin) VALUES (?, 1)', (t,))
        print('Created: ' + t)
    except:
        c.execute('UPDATE users SET admin = 1 WHERE name = ?', (t,))
        print('Updated: ' + t)

classes = [
    'class-b1-01-A', 'class-b1-01-B',
    'class-b2-01-A', 'class-b3-01-A', 'class-b4-01-A',
    'class-b5-01-A', 'class-b6-01-A',
    'class-a1-01-A', 'class-a1-01-B',
    'class-a2-01-A', 'class-a3-01-A', 'class-a4-01-A',
    'class-p1-01-A', 'class-p1-01-B',
    'class-p2-01-A', 'class-p3-01-A', 'class-p4-01-A',
    'class-p5-01-A', 'class-p6-01-A',
    'course-b-teachers', 'course-a-teachers', 'course-p-teachers',
]

for g in classes:
    try:
        c.execute('INSERT INTO groups (name) VALUES (?)', (g,))
        print('Group: ' + g)
    except:
        print('Group exists: ' + g)

mapping = {
    'teacher-b1-01': ['course-b-teachers', 'class-b1-01-A', 'class-b1-01-B'],
    'teacher-b2-01': ['course-b-teachers', 'class-b2-01-A'],
    'teacher-b3-01': ['course-b-teachers', 'class-b3-01-A'],
    'teacher-b4-01': ['course-b-teachers', 'class-b4-01-A'],
    'teacher-b5-01': ['course-b-teachers', 'class-b5-01-A'],
    'teacher-b6-01': ['course-b-teachers', 'class-b6-01-A'],
    'teacher-a1-01': ['course-a-teachers', 'class-a1-01-A', 'class-a1-01-B'],
    'teacher-a2-01': ['course-a-teachers', 'class-a2-01-A'],
    'teacher-a3-01': ['course-a-teachers', 'class-a3-01-A'],
    'teacher-a4-01': ['course-a-teachers', 'class-a4-01-A'],
    'teacher-p1-01': ['course-p-teachers', 'class-p1-01-A', 'class-p1-01-B'],
    'teacher-p2-01': ['course-p-teachers', 'class-p2-01-A'],
    'teacher-p3-01': ['course-p-teachers', 'class-p3-01-A'],
    'teacher-p4-01': ['course-p-teachers', 'class-p4-01-A'],
    'teacher-p5-01': ['course-p-teachers', 'class-p5-01-A'],
    'teacher-p6-01': ['course-p-teachers', 'class-p6-01-A'],
}

for teacher, groups in mapping.items():
    c.execute('SELECT id FROM users WHERE name=?', (teacher,))
    uid = c.fetchone()
    if not uid:
        continue
    for gname in groups:
        c.execute('SELECT id FROM groups WHERE name=?', (gname,))
        gid = c.fetchone()
        if gid:
            try:
                c.execute('INSERT INTO users_groups (user_id, group_id) VALUES (?, ?)', (uid[0], gid[0]))
            except:
                pass

conn.commit()

c.execute('SELECT COUNT(*) FROM users WHERE admin=1')
print('Admin users: ' + str(c.fetchone()[0]))
c.execute('SELECT COUNT(*) FROM groups')
print('Total groups: ' + str(c.fetchone()[0]))
c.execute('SELECT name FROM users WHERE admin=1 AND name LIKE "teacher-%" ORDER BY name')
new_teachers = [r[0] for r in c.fetchall()]
print('New teacher accounts: ' + str(len(new_teachers)))
for t in new_teachers:
    print('  ' + t)

conn.close()
print('Done!')
