#!/usr/bin/env python3
"""Sync v2.4: nbgrader workflow + multi-teacher classes + Code-Server alternative note."""
import os, glob
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

BASE = r"D:\现代制造\Python编程实战"
DIFY = r"D:\dify-install"

GUIDE_APPEND = """

---

## 24. nbgrader 原生作业系统 (v2.4 新增)

### 概述

JupyterHub 已安装 **nbgrader 0.9.5**，提供原生的作业分发、收集、自动评分和反馈功能，替代了之前的手动 code_grader.py。

### 教师操作流程

```bash
cd ~/work/nbgrader

# 1. 创建作业（在 source/ 目录下创建 Notebook）
#    在 JupyterLab 中使用 nbgrader 工具栏标记单元格类型:
#    - 答案区（Solution）: 学生需要填写的代码
#    - 测试区（Test）: assert 断言（自动评分用）
#    - 只读区（Read-only）: 题目描述

# 2. 生成学生版（自动去除解决方案）
python3 -m nbgrader generate_assignment ps1

# 3. 发布作业到 exchange
python3 -m nbgrader release_assignment ps1

# 4. 查看已发布的作业
python3 -m nbgrader list

# 5. 学生提交后，自动评分
python3 -m nbgrader autograde ps1

# 6. 生成反馈
python3 -m nbgrader generate_feedback ps1
python3 -m nbgrader release_feedback ps1

# 7. 导出成绩 CSV
python3 -m nbgrader export
```

### 学生操作流程

```bash
cd ~/work/nbgrader

# 1. 查看可用作业
python3 -m nbgrader list

# 2. 获取作业
python3 -m nbgrader fetch ps1

# 3. 完成作业后提交
python3 -m nbgrader submit ps1
```

### nbgrader 元数据要求

每个 nbgrader 单元格需要完整的 v3 元数据:
- `grade`: True/False（是否评分）
- `solution`: True/False（是否答案区）
- `task`: False
- `locked`: True/False（是否锁定）
- `points`: 浮点数（分值）
- `grade_id`: 唯一标识符
- `schema_version`: 3
- `cell_type`: "code"

### Exchange 目录

| 路径 | 说明 |
|------|------|
| `~/work/nbgrader/exchange/` | 共享交换目录 |
| `exchange/default/outbound/` | 教师发布的作业 |
| `exchange/default/inbound/` | 学生提交的作业 |

---

## 25. 多教师多课程账户体系 (v2.4 完整版)

### 完整对照表

```
teacher-zhang (总管理员, 密码: ide2026)
├── 02-程序设计基础
│   ├── Lecture-B1~B6 (原始管理员)
│   ├── teacher-b1-01 → class-b1-01-A, class-b1-01-B
│   ├── teacher-b2-01 → class-b2-01-A
│   ├── teacher-b3-01 → class-b3-01-A
│   ├── teacher-b4-01 → class-b4-01-A
│   ├── teacher-b5-01 → class-b5-01-A
│   └── teacher-b6-01 → class-b6-01-A
├── 01-AI应用基础
│   ├── Lecture-A1~A4
│   ├── teacher-a1-01 → class-a1-01-A, class-a1-01-B
│   ├── teacher-a2-01 → class-a2-01-A
│   ├── teacher-a3-01 → class-a3-01-A
│   └── teacher-a4-01 → class-a4-01-A
└── 03-Python项目实战
    ├── Lecture-P1~P6
    ├── teacher-p1-01 → class-p1-01-A, class-p1-01-B
    ├── teacher-p2-01 → class-p2-01-A
    ├── teacher-p3-01 → class-p3-01-A
    ├── teacher-p4-01 → class-p4-01-A
    ├── teacher-p5-01 → class-p5-01-A
    └── teacher-p6-01 → class-p6-01-A
```

### 学生登录格式

| 格式 | 含义 | 关联教师 |
|------|------|----------|
| `b1-A-01` | 程序设计基础 B1 A班 01号 | teacher-b1-01 |
| `a1-B-03` | AI应用基础 A1 B班 03号 | teacher-a1-01 |
| `p1-A-05` | Python项目实战 P1 A班 05号 | teacher-p1-01 |

### 账户总计

- 33 个教师/管理员账户
- 43 个分组
- 56 个 Notebook
- 28 个代码框架
- 3 门课程
"""

PPT_CONTENT = [
    "JupyterHub v2.4 nbgrader+多教师班级",
    "",
    "[nbgrader 原生作业系统]",
    "  已安装: nbgrader 0.9.5",
    "  教师流程: generate -> release -> autograde -> feedback",
    "  学生流程: list -> fetch -> submit",
    "  自动评分+成绩导出CSV",
    "",
    "[多教师多课程体系]",
    "  33个教师/管理员 | 43个分组",
    "  3门课程: B(程序设计) + A(AI应用) + P(项目实战)",
    "  学生格式: {课程}-{班级}-{学号}",
    "",
    "[默认功能]",
    "  教师=双指南 | 学生=学生版指南",
    "  nbgrader + code_grader.py + code_review.py",
    "  AI聊天+补全+嵌入 | 多语言审查",
    "  CockroachDB读写分离 | Redis双级缓存",
    "",
    "[Code-Server 替代方案]",
    "  JupyterHub + nbgrader = 完整教学平台",
    "  AI编程: jupyter-ai + LSP补全",
    "  如需VS Code体验: 安装 jupyterlab-code-formatter",
]

def update_ppts():
    ppts = [f for f in glob.glob(os.path.join(BASE, "**", "*.pptx"), recursive=True)
            if "_docx_work" not in f and "venv" not in f]
    updated = 0
    for path in ppts:
        try:
            prs = Presentation(path)
            has = False
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame and "nbgrader" in shape.text_frame.text and "多教师" in shape.text_frame.text:
                        has = True; break
                if has: break
            if has: continue
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
        except: pass
    return updated, len(ppts)

def update_mds():
    mds = []
    for root, dirs, files in os.walk(BASE):
        if "_docx_work" in root or "venv" in root or "node_modules" in root: continue
        for f in files:
            if f.endswith(".md"): mds.append(os.path.join(root, f))
    updated = 0
    for path in mds:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "nbgrader 原生作业系统" in content: continue
            with open(path, "a", encoding="utf-8") as f:
                f.write(GUIDE_APPEND)
            updated += 1
        except: pass
    return updated, len(mds)

def update_guides():
    updated = 0
    for fname in ["JUPYTERHUB-OPERATION-GUIDE.md", "JUPYTERHUB-STUDENT-GUIDE.md"]:
        path = os.path.join(DIFY, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "nbgrader 原生作业系统" not in content:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(GUIDE_APPEND)
                updated += 1
    return updated

if __name__ == "__main__":
    print("=" * 70)
    print("Sync v2.4: nbgrader + multi-teacher + Code-Server note")
    print("=" * 70)
    pu, pt = update_ppts()
    print(f"PPT: {pu} updated / {pt} total")
    mu, mt = update_mds()
    print(f"MD: {mu} updated / {mt} total")
    gu = update_guides()
    print(f"Guides: {gu} updated")
    total = pu + mu + gu
    print(f"\nTotal: {total} files updated")
    print("=" * 70)
