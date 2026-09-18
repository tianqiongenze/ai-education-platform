# -*- coding: utf-8 -*-
"""Generate new-Lecture worksheets (A5~A12 / B7~B12 / P7~P8) as CM-ready files.

Output per worksheet: <key>_student.json, <key>_teacher.json (notebooks)
Output per lecture:   fw_<id> framework files
Style mirrors existing cm-course-a/b/p samples (P1.1 / B0.1 / M1-1a).
"""
import json, os, subprocess, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newcm")

HDR = {
    "a": "AI应用基础（48课时版）",
    "b": "Python编程基础",
    "p": "Python程序设计（项目实战）",
}

ENV_CELL = (
    "# --- 环境与数据准备(勿改, 运行即可) ---\n"
    "import os, sys, subprocess\n"
    'os.chdir(os.path.abspath("../"))          # 切到课程包根目录(data/所在处)\n'
    'print("工作目录:", os.getcwd())\n'
)

LAYER = (
    "| 层 | 任务定位 | 达标要求 |\n"
    "|----|---------|---------|\n"
    "| **A 师傅** | 进阶拓展 | 完成全部任务并自加1个边界断言/优化点；示范讲解 |\n"
    "| **B 组长** | 标准达成 | {acc_b} |\n"
    "| **C 操作员** | 基础完成 | {acc_c} |\n"
    "| **D 学徒** | 跟做保底 | 跟做示例跑通TODO-1, 程序出结果 |\n"
    "> 每4周按工单成绩动态升降层（连续2次≥B升一层）\n"
)

PRIMM = (
    "## 一、课前资讯（Predict·预测）\n"
    "> **预习快问**：{predict}\n"
    "\n"
    "> **课前检查**：导学单+预习自测已完成；starter可运行（运行环境准备单元格无报错）\n"
    "\n"
    "## 二、PRIMM五步法（先读后写）\n"
    "本工单按国际编程教学法 **PRIMM** 组织：\n"
    "1. **Predict 预测**——先运行下方示例，猜输出再验证；\n"
    "2. **Run 运行**——跑通环境与数据；\n"
    "3. **Investigate 研究**——读懂starter每段在做什么；\n"
    "4. **Modify 修改**——完成TODO改造；\n"
    "5. **Make 创造**——独立完成工单任务。\n"
)

SUBMIT = {
    "a": "## 四、提交要求与避坑\n- 提交: `学号_姓名_{key}.py` 或本notebook(含输出)\n",
    "b": "## 四、提交要求与避坑\n- 提交: `学号_姓名_{key}.py` 或本notebook(含输出)\n",
    "p": "## 四、提交要求与避坑\n- 提交: `学号_姓名_{key}.py` 或本notebook(含输出)\n",
}


def md_cell(src):
    return {"cell_type": "markdown", "id": "", "metadata": {}, "source": src}


def code_cell(src):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": "",
        "metadata": {},
        "outputs": [],
        "source": src,
    }


def make_student(ws):
    course = ws["key"][0]
    title_cell = md_cell(
        [
            f"# {HDR[course]} · 工单{ws['title']}\n",
            f"**{ws['week']} | 2课时(80分钟) | 理实一体**  | 学生实训版\n",
            "\n",
            LAYER.format(acc_b=ws["acc_b"], acc_c=ws["acc_c"]),
        ]
    )
    cells = [
        title_cell,
        md_cell([PRIMM.format(predict=ws["predict"])]),
        code_cell([ENV_CELL]),
        md_cell(
            [
                "## 三、任务要求（Make）\n**实施步骤**\n"
                + "".join(f"{i+1}. {s}\n" for i, s in enumerate(ws["steps"]))
                + f"\n**验收标准**：及格(D)=`{ws['acc_c']}` ；优秀(B+)=`{ws['acc_b']}`\n"
            ]
        ),
    ]
    for i, (sig, stub) in enumerate(ws["starters"]):
        cells.append(
            md_cell([f"### Starter {i+1}：`{sig}`\n（Investigate: 读代码→Modify: 补全TODO）\n"])
        )
        cells.append(code_cell(stub.splitlines(keepends=True)))
    cells.append(md_cell([SUBMIT[course].format(key=ws["key"].replace("_", "."))]))
    nb = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    # assign deterministic ids
    for i, c in enumerate(nb["cells"]):
        c["id"] = f"{ws['key'].replace('_','')}{i:02d}"
    return nb


def make_teacher(ws):
    course = ws["key"][0]
    fn = ws["key"].split("_")[1]
    cells = [
        md_cell(
            [
                f"# {HDR[course]} · 工单{ws['title']} — 教师参考版\n",
                f"{ws['week']} | 参考实现可直接运行验证 | 答案请勿下发学生",
            ]
        ),
        code_cell([ENV_CELL]),
        md_cell([f"## 参考实现 `{fn}`（含依赖导入）"]),
        code_cell(ws["solution"].splitlines(keepends=True)),
        md_cell(["## 执行与验证"]),
        code_cell([f"{fn}()\n"]),
    ]
    for i, c in enumerate(cells):
        c["id"] = f"t{ws['key'].replace('_','')}{i:02d}"
    return {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def make_fw(ws):
    fw_id = ws["key"].split("_")[1]
    stubs = "\n\n\n".join(s for _, s in ws["starters"])
    body = (
        f"# -*- coding: utf-8 -*-\n"
        f'"""{ws["title"]} starter（学生代码框架）\n'
        f"\n"
        f"运行: python {fw_id}_starter.py  完成各 TODO 后在工单notebook中验证\n"
        f'"""\n'
        f"{stubs}\n"
    )
    if ws.get("fw_main"):
        body += "\n\n" + ws["fw_main"]
    else:
        body += (
            '\n\nif __name__ == "__main__":\n'
            '    print("框架加载成功。请逐个补全 TODO，再回工单notebook运行测试。")\n'
        )
    return body


def main():
    from worksheets import WORKSHEETS  # noqa: E402

    os.makedirs(OUT, exist_ok=True)
    for sub in ("a", "b", "p"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    ok, fail = 0, []
    for ws in WORKSHEETS:
        course = ws["key"][0]
        # verify teacher solution actually runs
        r = subprocess.run(
            [sys.executable, "-c", ws["solution"]],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode != 0:
            fail.append((ws["key"], r.stderr[-500:]))
            continue
        with open(os.path.join(OUT, course, f"{ws['key']}_student.json"), "w", encoding="utf-8") as f:
            json.dump(make_student(ws), f, ensure_ascii=False, indent=1)
        with open(os.path.join(OUT, course, f"{ws['key']}_teacher.json"), "w", encoding="utf-8") as f:
            json.dump(make_teacher(ws), f, ensure_ascii=False, indent=1)
        fw_id = ws["key"].split("_")[1]
        with open(os.path.join(OUT, course, f"fw_{fw_id}"), "w", encoding="utf-8") as f:
            f.write(make_fw(ws))
        ok += 1
    print(f"generated {ok} worksheets -> {OUT}")
    for k, e in fail:
        print("FAIL", k, e)


if __name__ == "__main__":
    main()
