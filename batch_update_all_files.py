#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch update all PPT and DOCX files with JupyterHub new features info.
Adds a summary slide/page to each file with:
- JupyterHub account system (admin, teacher, student accounts)
- LLM/AI chat functionality
- Code grading system
- Test results (13/13 100% pass)
"""
import os
import sys
import glob
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# Configuration
BASE_DIR = r"D:\现代制造\Python编程实战"

# JupyterHub info to add to each file
JUPYTERHUB_INFO = {
    "title": "JupyterHub 平台功能更新",
    "subtitle": "2026-09-04 更新",
    "content": [
        "【访问方式】",
        "  URL: https://10.167.2.175:31825/ide/",
        "  密码: ide2026（所有账户共享）",
        "",
        "【账户体系】",
        "  管理员+教师: teacher-zhang, Lecture-P1~P6",
        "  学生: student-python/java/go/rust/alice/bob/carol",
        "  Lecture-P1: P1.1 Python基础 + P1.2 标准Python工程",
        "  Lecture-P2: P2.1 Pandas数据处理 + P2.2 NumPy故障特征",
        "  Lecture-P3: P3 产线KPI仪表盘",
        "  Lecture-P4: P4.1 多源数据采集系统",
        "  Lecture-P5: P5 产线数据仓库与ORM",
        "  Lecture-P6: P6 故障诊断模型与部署",
        "  teacher-zhang: 全部8个Notebook + 评分系统 + 操作指南",
        "",
        "【AI 功能】",
        "  jupyter-ai 聊天: 登录后直接使用（左侧栏AI面板）",
        "  LLM模型: qwen2.5-coder:7b (Ollama CPU推理)",
        "  响应时间: 6-21秒",
        "  内联补全: LSP+pylsp 弹窗补全 + AI FIM缓存",
        "",
        "【代码评分系统】",
        "  评分维度: PEP8(20%) + 测试通过率(40%) + 查重(20%) + AI率(20%)",
        "  运行: python3 /home/jovyan/work/code_grader.py",
        "  报告: /home/jovyan/work/grading_report.json",
        "  等级: A(≥90) B(80-89) C(70-79) D(60-69) F(<60)",
        "",
        "【测试结果】",
        "  功能测试: 13/13 通过 (100%)",
        "  50并发用户: 100% 成功, 24.5秒",
        "  LLM Chat: PASS (21秒)",
        "  Notebook执行: PASS (1.4秒)",
        "  代码评分: PASS (评级A)",
        "",
        "【管理面板】",
        "  URL: https://10.167.2.175:31825/ide/hub/admin",
        "  功能: 查看用户/服务器状态、启动/停止服务器、作业发布",
    ]
}

def add_jupyterhub_slide_to_ppt(ppt_path):
    """Add a JupyterHub info slide to a PPT file."""
    try:
        prs = Presentation(ppt_path)
        
        # Create a new slide at the end
        slide_layout = prs.slide_layouts[6]  # Blank layout
        slide = prs.slides.add_slide(slide_layout)
        
        # Add title
        left = Inches(0.5)
        top = Inches(0.3)
        width = Inches(9)
        height = Inches(0.6)
        title_box = slide.shapes.add_textbox(left, top, width, height)
        title_tf = title_box.text_frame
        title_tf.text = JUPYTERHUB_INFO["title"]
        title_p = title_tf.paragraphs[0]
        title_p.font.size = Pt(28)
        title_p.font.bold = True
        title_p.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
        
        # Add subtitle
        sub_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(9), Inches(0.4))
        sub_tf = sub_box.text_frame
        sub_tf.text = JUPYTERHUB_INFO["subtitle"]
        sub_p = sub_tf.paragraphs[0]
        sub_p.font.size = Pt(14)
        sub_p.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        
        # Add content
        content_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5.5))
        content_tf = content_box.text_frame
        content_tf.word_wrap = True
        
        for i, line in enumerate(JUPYTERHUB_INFO["content"]):
            if i == 0:
                p = content_tf.paragraphs[0]
            else:
                p = content_tf.add_paragraph()
            p.text = line
            if line.startswith("【"):
                p.font.size = Pt(13)
                p.font.bold = True
                p.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
            else:
                p.font.size = Pt(10)
                p.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        
        prs.save(ppt_path)
        return True
    except Exception as e:
        return f"Error: {str(e)[:100]}"

def update_markdown_files():
    """Update all markdown files with JupyterHub account info."""
    updated = 0
    errors = 0
    
    md_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        if '_docx_work' in root or 'venv' in root or 'node_modules' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))
    
    # The info block to append (only if not already present)
    info_block = """
---

## JupyterHub 平台功能更新 (2026-09-04)

> **所有新功能已同步到此文件。以下为 JupyterHub 平台最新功能概要。**

### 访问方式
- **URL**: `https://10.167.2.175:31825/ide/`
- **密码**: `ide2026`（所有账户共享）

### 账户体系
| 账户 | 类型 | 对应课程 |
|------|------|----------|
| `teacher-zhang` | 管理员+总教师 | 全部8个Notebook |
| `Lecture-P1` | 管理员+章节教师 | P1.1 Python基础 + P1.2 标准Python工程 |
| `Lecture-P2` | 管理员+章节教师 | P2.1 Pandas数据处理 + P2.2 NumPy故障特征 |
| `Lecture-P3` | 管理员+章节教师 | P3 产线KPI仪表盘 |
| `Lecture-P4` | 管理员+章节教师 | P4.1 多源数据采集系统 |
| `Lecture-P5` | 管理员+章节教师 | P5 产线数据仓库与ORM |
| `Lecture-P6` | 管理员+章节教师 | P6 故障诊断模型与部署 |
| `student-python` | 学生 | Python 工业遥测分析项目 |
| `student-java` | 学生 | Java MES 生产管理系统 |
| `student-go` | 学生 | Go 工业网关项目 |
| `student-rust` | 学生 | Rust 安全审计项目 |

### AI 功能
- **jupyter-ai 聊天**: 登录后直接使用（左侧栏AI面板，无需配置）
- **LLM模型**: qwen2.5-coder:7b (Ollama CPU推理, 响应6-21秒)
- **内联补全**: LSP+pylsp 弹窗补全 + AI FIM缓存

### 代码评分系统
- **评分维度**: PEP8(20%) + 测试通过率(40%) + 查重(20%) + AI率(20%)
- **运行**: `python3 /home/jovyan/work/code_grader.py`
- **等级**: A(≥90) / B(80-89) / C(70-79) / D(60-69) / F(<60)

### 测试结果
- **功能测试**: 13/13 通过 (100%)
- **50并发用户**: 100% 成功, 24.5秒
- **LLM Chat**: PASS (21秒)
- **Notebook执行**: PASS (1.4秒)

### 管理面板
- **URL**: `https://10.167.2.175:31825/ide/hub/admin`
- **功能**: 查看用户/服务器状态、启动/停止服务器、作业发布与检查
"""
    
    for md_path in md_files:
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Only add if not already present
            if 'JupyterHub 平台功能更新 (2026-09-04)' in content:
                continue
            
            # Append the info block
            with open(md_path, 'a', encoding='utf-8') as f:
                f.write(info_block)
            updated += 1
        except Exception as e:
            errors += 1
    
    return updated, errors

def main():
    print("=" * 70)
    print("Batch Update All Files with JupyterHub New Features")
    print("=" * 70)
    
    # 1. Update PPT files
    print("\n=== Phase 1: Update PPT files ===")
    ppt_files = glob.glob(os.path.join(BASE_DIR, "**", "*.pptx"), recursive=True)
    ppt_files = [f for f in ppt_files if '_docx_work' not in f and 'venv' not in f]
    
    ppt_updated = 0
    ppt_errors = 0
    for ppt_path in ppt_files:
        result = add_jupyterhub_slide_to_ppt(ppt_path)
        if result is True:
            ppt_updated += 1
            print(f"  Updated: {os.path.basename(ppt_path)}")
        else:
            ppt_errors += 1
            print(f"  Error: {os.path.basename(ppt_path)} - {result}")
    
    print(f"\nPPT: {ppt_updated} updated, {ppt_errors} errors, {len(ppt_files)} total")
    
    # 2. Update Markdown files
    print("\n=== Phase 2: Update Markdown files ===")
    md_updated, md_errors = update_markdown_files()
    print(f"Markdown: {md_updated} updated, {md_errors} errors")
    
    # 3. Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"PPT files updated:      {ppt_updated}")
    print(f"PPT errors:              {ppt_errors}")
    print(f"Markdown files updated:  {md_updated}")
    print(f"Markdown errors:        {md_errors}")
    print(f"Total files updated:    {ppt_updated + md_updated}")
    print("=" * 70)

if __name__ == "__main__":
    main()
