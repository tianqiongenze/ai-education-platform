#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execute all 8 student notebooks in the teacher pod and output all results.
Patches the last code cell to catch AssertionError (expected on student template).
"""
import json
import os
import sys
import time
import nbformat
from nbclient import NotebookClient

NOTEBOOK_DIR = "/home/jovyan/work"

# All 8 student notebooks (explicit names to avoid glob issues)
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
    """Execute a notebook, patching last cell to catch expected errors."""
    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    code_indices = [i for i, c in enumerate(nb.cells) if c.cell_type == 'code']
    
    # Patch all code cells that might raise assertions to wrap in try/except
    for ci in code_indices:
        cell = nb.cells[ci]
        src = ''.join(cell.source)
        # Only patch if it contains assert or test-like code
        if 'assert' in src or '__name__' in src or 'if __name__' in src:
            patched = 'try:\n' + '\n'.join('    ' + line if line else '' for line in src.split('\n'))
            patched += '\nexcept AssertionError as e:\n    print("断言失败(学生模板预期):", e)\n'
            patched += 'except Exception as e:\n    print("错误:", type(e).__name__, e)\n'
            cell.source = patched
            # Also update the source list format
            cell['source'] = patched
    
    client = NotebookClient(nb, timeout=60, kernel_name='python3')
    client.execute()
    
    # Collect all outputs
    outputs = []
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'code':
            cell_src = ''.join(cell.source)[:80]
            cell_outputs = cell.get('outputs', [])
            for out in cell_outputs:
                if out.get('output_type') == 'stream':
                    text = ''.join(out.get('text', ''))
                    if text.strip():
                        outputs.append({
                            'cell_index': i,
                            'type': 'stream',
                            'text': text.strip()
                        })
                elif out.get('output_type') in ('execute_result', 'display_data'):
                    data = out.get('data', {})
                    if 'text/plain' in data:
                        text = ''.join(data['text/plain'])
                        if text.strip():
                            outputs.append({
                                'cell_index': i,
                                'type': 'result',
                                'text': text.strip()
                            })
                elif out.get('output_type') == 'error':
                    outputs.append({
                        'cell_index': i,
                        'type': 'error',
                        'ename': out.get('ename', ''),
                        'evalue': out.get('evalue', ''),
                        'traceback': out.get('traceback', [])[:3]
                    })
    
    return outputs

def main():
    print("=" * 70)
    print("执行全部8个学生版Notebook并输出结果")
    print("=" * 70)
    print()
    
    for nb_name in NOTEBOOKS:
        nb_path = os.path.join(NOTEBOOK_DIR, nb_name)
        if not os.path.exists(nb_path):
            print("[NOT FOUND] %s" % nb_name)
            print()
            continue
        
        print("-" * 70)
        print("NOTEBOOK: %s" % nb_name)
        print("-" * 70)
        
        start = time.time()
        try:
            outputs = execute_notebook(nb_path)
            elapsed = time.time() - start
            print("状态: 成功 | 耗时: %.2fs | 输出条目: %d" % (elapsed, len(outputs)))
            print()
            
            if outputs:
                print("=== 输出内容 ===")
                for out in outputs:
                    cell_idx = out['cell_index']
                    out_type = out['type']
                    if out_type == 'stream':
                        for line in out['text'].split('\n'):
                            print("  [Cell %d] %s" % (cell_idx, line))
                    elif out_type == 'result':
                        for line in out['text'].split('\n'):
                            print("  [Cell %d] => %s" % (cell_idx, line))
                    elif out_type == 'error':
                        print("  [Cell %d] ERROR: %s: %s" % (cell_idx, out['ename'], out['evalue']))
            else:
                print("=== 无输出 ===")
            
        except Exception as e:
            elapsed = time.time() - start
            print("状态: 失败 | 耗时: %.2fs" % elapsed)
            print("错误: %s" % str(e)[:500])
        
        print()
    
    print("=" * 70)
    print("全部Notebook执行完毕")
    print("=" * 70)

if __name__ == "__main__":
    main()
