#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execute all 8 student notebooks (v2) - fix os.chdir and capture full output.
Patches: 1) Replace os.chdir("../") with os.chdir("/home/jovyan/work")
         2) Wrap assert/test cells in try/except
"""
import json
import os
import sys
import time
import nbformat
from nbclient import NotebookClient

NOTEBOOK_DIR = "/home/jovyan/work"

NOTEBOOKS = [
    "p11_P1.1_Python基础_学生版.ipynb",
    "p12_P1.2_标准Python_学生版.ipynb",
    "p21_P2.1_Pandas数据_学生版.ipynb",
    "p22_P2.2_NumPy故障特_学生版.ipynb",
    "p33_P3_产线KPI仪表盘_学生版.ipynb",
    "p41_P4.1_多源数据采集系统_学生版.ipynb",
    "p55_P5_产线数据仓库与O_学生版.ipynb",
    "p66_P6_故障诊断模型与部_学生版.ipynb",
]

def execute_notebook(nb_path):
    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    code_indices = [i for i, c in enumerate(nb.cells) if c.cell_type == 'code']
    
    for ci in code_indices:
        cell = nb.cells[ci]
        src = ''.join(cell.source)
        
        # Fix 1: Replace os.chdir("../") with safe directory
        if 'os.chdir' in src and '../' in src:
            src = src.replace('os.path.abspath("../")', '"/home/jovyan/work"')
            src = src.replace('os.path.abspath(\'../\')', '"/home/jovyan/work"')
            cell.source = src
            cell['source'] = src
        
        # Fix 2: Wrap assert/test cells in try/except
        if 'assert' in src or 'if __name__' in src:
            patched = 'try:\n' + '\n'.join('    ' + line if line else '' for line in src.split('\n'))
            patched += '\nexcept AssertionError as e:\n    print("断言失败(学生模板预期):", e)\n'
            patched += 'except Exception as e:\n    print("错误:", type(e).__name__, str(e)[:200])\n'
            cell.source = patched
            cell['source'] = patched
    
    client = NotebookClient(nb, timeout=60, kernel_name='python3')
    client.execute()
    
    # Collect all outputs
    outputs = []
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'code':
            for out in cell.get('outputs', []):
                if out.get('output_type') == 'stream':
                    text = ''.join(out.get('text', ''))
                    if text.strip():
                        outputs.append({'cell': i, 'type': 'stream', 'text': text.strip()})
                elif out.get('output_type') in ('execute_result', 'display_data'):
                    data = out.get('data', {})
                    if 'text/plain' in data:
                        text = ''.join(data['text/plain'])
                        if text.strip():
                            outputs.append({'cell': i, 'type': 'result', 'text': text.strip()})
                elif out.get('output_type') == 'error':
                    outputs.append({
                        'cell': i, 'type': 'error',
                        'ename': out.get('ename', ''),
                        'evalue': out.get('evalue', ''),
                    })
    
    return outputs

def main():
    print("=" * 70)
    print("执行全部8个学生版Notebook并输出结果 (v2 - 修复os.chdir)")
    print("=" * 70)
    print()
    
    summary = []
    
    for nb_name in NOTEBOOKS:
        nb_path = os.path.join(NOTEBOOK_DIR, nb_name)
        if not os.path.exists(nb_path):
            print("[NOT FOUND] %s" % nb_name)
            continue
        
        print("-" * 70)
        print("NOTEBOOK: %s" % nb_name)
        print("-" * 70)
        
        start = time.time()
        try:
            outputs = execute_notebook(nb_path)
            elapsed = time.time() - start
            status = "成功"
            print("状态: %s | 耗时: %.2fs | 输出: %d条" % (status, elapsed, len(outputs)))
            print()
            
            if outputs:
                print("=== 输出内容 ===")
                for out in outputs:
                    ci = out['cell']
                    if out['type'] == 'stream':
                        for line in out['text'].split('\n'):
                            print("  [Cell %d] %s" % (ci, line))
                    elif out['type'] == 'result':
                        for line in out['text'].split('\n'):
                            print("  [Cell %d] => %s" % (ci, line))
                    elif out['type'] == 'error':
                        print("  [Cell %d] ERROR: %s: %s" % (ci, out['ename'], out['evalue']))
            else:
                print("=== 无输出 ===")
            
            summary.append((nb_name, "成功", elapsed, len(outputs)))
            
        except Exception as e:
            elapsed = time.time() - start
            err = str(e)[:500]
            print("状态: 失败 | 耗时: %.2fs" % elapsed)
            print("错误: %s" % err)
            summary.append((nb_name, "失败", elapsed, 0))
        
        print()
    
    # Summary
    print("=" * 70)
    print("执行汇总")
    print("=" * 70)
    print("%-45s %-6s %-8s %-6s" % ("Notebook", "状态", "耗时(s)", "输出"))
    print("-" * 70)
    for name, status, elapsed, n_out in summary:
        print("%-45s %-6s %-8.2f %-6d" % (name, status, elapsed, n_out))
    
    success = sum(1 for s in summary if s[1] == "成功")
    failed = sum(1 for s in summary if s[1] == "失败")
    print("-" * 70)
    print("成功: %d/8 | 失败: %d/8" % (success, failed))
    print("=" * 70)

if __name__ == "__main__":
    main()
