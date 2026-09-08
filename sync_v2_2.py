#!/usr/bin/env python3
"""Update guides with multi-teacher class system, then sync PPTs and MDs."""

GUIDE_APPEND = """
---

## 22. 多教师同课程+班级关联体系 (v2.2 新增)

### 体系架构

```
teacher-zhang (总管理员)
├── 02-程序设计基础
│   ├── teacher-b1-01 → class-b1-01-A, class-b1-01-B
│   ├── teacher-b2-01 → class-b2-01-A
│   ├── teacher-b3-01 → class-b3-01-A
│   ├── teacher-b4-01 → class-b4-01-A
│   ├── teacher-b5-01 → class-b5-01-A
│   └── teacher-b6-01 → class-b6-01-A
├── 01-AI应用基础
│   ├── teacher-a1-01 → class-a1-01-A, class-a1-01-B
│   ├── teacher-a2-01 → class-a2-01-A
│   ├── teacher-a3-01 → class-a3-01-A
│   └── teacher-a4-01 → class-a4-01-A
└── 03-Python项目实战
    ├── teacher-p1-01 → class-p1-01-A, class-p1-01-B
    ├── teacher-p2-01 → class-p2-01-A
    ├── teacher-p3-01 → class-p3-01-A
    ├── teacher-p4-01 → class-p4-01-A
    ├── teacher-p5-01 → class-p5-01-A
    └── teacher-p6-01 → class-p6-01-A
```

### 同一课程多个教师

同一课程可以有多位教师同时授课，每位教师管理自己的班级：

| 课程 | 教师 | 负责班级 | 可管理学生 |
|------|------|----------|-----------|
| B1 (设备初始化) | teacher-b1-01 | class-b1-01-A, class-b1-01-B | A班+B班学生 |
| B1 (设备初始化) | teacher-b1-02 (新增) | class-b1-02-A | 新教师A班学生 |

> 教师使用 `https://10.167.2.175:31825/ide/hub/admin` 管理面板查看自己班级的学生。

### 学生登录格式

学生用户名格式: `{课程}-{班级}-{学号}`

| 格式 | 含义 | 关联教师 |
|------|------|----------|
| `b1-A-01` | 程序设计基础 B1 A班 01号 | teacher-b1-01 |
| `b1-B-05` | 程序设计基础 B1 B班 05号 | teacher-b1-01 |
| `a1-A-03` | AI应用基础 A1 A班 03号 | teacher-a1-01 |
| `p1-B-10` | Python项目实战 P1 B班 10号 | teacher-p1-01 |

### 教师管理学生流程

1. 教师登录 (`teacher-b1-01`, 密码 `ide2026`)
2. 访问管理面板: `https://10.167.2.175:31825/ide/hub/admin`
3. 查看自己班级的学生服务器状态
4. 启动/停止学生服务器
5. 使用 `code_grader.py` 评分学生代码

### 新增教师流程

1. 总管理员 `teacher-zhang` 在终端创建新教师:
   ```bash
   # 新教师登录即可自动创建 (密码 ide2026)
   # 然后在 hub pod 中将其加入对应课程组和班级组
   ```

2. 将新教师加入课程教师组和班级组（示例）:
   ```bash
   kubectl exec -n jupyterhub <hub-pod> -c jupyterhub -- python3 -c "
   import sqlite3
   conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
   c = conn.cursor()
   # 创建教师
   c.execute('INSERT INTO users (name, admin) VALUES (?, 1)', ('teacher-b1-02',))
   # 加入课程教师组
   c.execute('SELECT id FROM groups WHERE name=\"course-b-teachers\"')
   gid = c.fetchone()
   c.execute('SELECT id FROM users WHERE name=\"teacher-b1-02\"')
   uid = c.fetchone()
   c.execute('INSERT INTO users_groups VALUES (?, ?)', (uid[0], gid[0]))
   # 创建新班级组
   c.execute('INSERT INTO groups (name) VALUES (?)', ('class-b1-02-A',))
   # 加入班级组
   c.execute('SELECT id FROM groups WHERE name=\"class-b1-02-A\"')
   cg = c.fetchone()
   c.execute('INSERT INTO users_groups VALUES (?, ?)', (uid[0], cg[0]))
   conn.commit()
   "
   ```
"""

import os, glob

BASE = r"D:\现代制造\Python编程实战"
DIFY = r"D:\dify-install"

PPT_CONTENT = [
    "JupyterHub v2.2 多教师班级体系",
    "",
    "【多教师同课程】",
    "  同一课程可有多位教师同时授课",
    "  每位教师管理自己的班级",
    "  教师格式: teacher-{课程}-{序号}",
    "  示例: teacher-b1-01, teacher-b1-02",
    "",
    "【班级关联】",
    "  班级格式: class-{课程}-{序号}-{班级}",
    "  示例: class-b1-01-A, class-b1-01-B",
    "",
    "【学生登录】",
    "  格式: {课程}-{班级}-{学号}",
    "  示例: b1-A-01, a1-B-03, p1-A-05",
    "  自动关联到对应教师的班级",
    "",
    "【账户总计】",
    "  33个教师/管理员 | 43个分组",
    "  3门课程 | 56个Notebook | 28个代码框架",
    "",
    "【功能】",
    "  教师版+学生版分层指南",
    "  多语言代码审查(Python/Java/Go/Rust/C)",
    "  AI聊天+代码补全+嵌入分析",
    "  CockroachDB读写分离",
]

def update_ppts():
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    updated, skipped, errors = 0, 0, 0
    ppts = [f for f in glob.glob(os.path.join(BASE, "**", "*.pptx"), recursive=True)
            if "_docx_work" not in f and "venv" not in f]

    for path in ppts:
        try:
            prs = Presentation(path)
            has = False
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame and "多教师班级体系" in shape.text_frame.text:
                        has = True; break
                if has: break
            if has:
                skipped += 1; continue

            slide = prs.slides.add_slide(prs.slide_layouts[6])
            tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.5))
            tb.text_frame.text = PPT_CONTENT[0]
            p = tb.text_frame.paragraphs[0]
            p.font.size = Pt(26); p.font.bold = True; p.font.color.rgb = RGBColor(0x1F,0x49,0x7D)

            cb = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(6))
            ctf = cb.text_frame; ctf.word_wrap = True
            for i, line in enumerate(PPT_CONTENT[1:]):
                p = ctf.paragraphs[0] if i == 0 else ctf.add_paragraph()
                p.text = line
                if line.startswith("["):
                    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = RGBColor(0x1F,0x49,0x7D)
                else:
                    p.font.size = Pt(10); p.font.color.rgb = RGBColor(0x33,0x33,0x33)
            prs.save(path)
            updated += 1
        except:
            errors += 1
    return updated, skipped, errors, len(ppts)

def update_mds():
    updated, skipped = 0, 0
    mds = []
    for root, dirs, files in os.walk(BASE):
        if "_docx_work" in root or "venv" in root or "node_modules" in root: continue
        for f in files:
            if f.endswith(".md"):
                mds.append(os.path.join(root, f))

    for path in mds:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "多教师同课程" in content:
                skipped += 1; continue
            with open(path, "a", encoding="utf-8") as f:
                f.write(GUIDE_APPEND)
            updated += 1
        except:
            pass
    return updated, skipped, len(mds)

def update_guides():
    updated = 0
    for fname in ["JUPYTERHUB-OPERATION-GUIDE.md", "JUPYTERHUB-STUDENT-GUIDE.md"]:
        path = os.path.join(DIFY, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "多教师同课程" not in content:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(GUIDE_APPEND)
                updated += 1
    return updated

if __name__ == "__main__":
    print("=" * 70)
    print("Sync v2.2: Multi-teacher classes")
    print("=" * 70)

    print("\n--- PPT ---")
    p, s, e, t = update_ppts()
    print(f"PPT: {p} updated, {s} skipped, {e} errors, {t} total")

    print("\n--- MD ---")
    mu, ms, mt = update_mds()
    print(f"MD: {mu} updated, {ms} skipped, {mt} total")

    print("\n--- Guides ---")
    du = update_guides()
    print(f"Guides: {du} updated")

    total = p + mu + du
    print(f"\n{'='*70}")
    print(f"SUMMARY: {total} files updated ({p} PPT + {mu} MD + {du} guides)")
    print(f"{'='*70}")
