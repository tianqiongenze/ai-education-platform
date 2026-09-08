#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep upgrade of Dify industrial IoT workflows / agents.
Builds complex workflow graphs (multi-node, conditional branches, KB retrieval,
code execution, variable passing) and deploys them via the draft API.
"""
import requests, base64, json, sys, time

BASE = "http://localhost:5001/console/api"

# Model config (confirmed working from existing apps)
MODEL = {
    "provider": "langgenius/openai_api_compatible/openai_api_compatible",
    "name": "qwen3:14b",
    "mode": "chat",
    "completion_params": {"temperature": 0.6, "max_tokens": 4096, "top_p": 0.9, "stop": []},
}

# Knowledge base IDs (from datasets API)
KB_INDUSTRIAL_NET = "ab21c835-135b-49bb-8c18-95c592ef023f"      # 工业网络协议知识库
KB_INDUSTRIAL_SAFETY = "ecad2ab1-3949-4c16-9d7e-dc51cd80927d"   # 工业安全标准知识库
KB_INDUSTRIAL_TEACH = "3fb0f3bf-6117-4b3d-a6e2-d9c4720e3a62"    # 工业互联网教学知识库
KB_TALENT = "bd385dfb-b842-4ec8-8ed0-ef206d79e3b8"              # 工业互联网应用专业人才培养
KB_SW_ENG = "5c637681-edf6-42cd-b518-7f8e5f374107"             # 软件工程最佳实践知识库
KB_JAVA = "98cc2af3-2766-4e9d-8937-de3ac07796d7"               # Java编程教程知识库
KB_PYTHON = "4eb0e985-fc74-49f6-83bc-0ac88418aa08"             # Python编程教程知识库


def get_session():
    s = requests.Session()
    r = s.post(BASE + "/login", json={
        "email": "myuwei@126.com",
        "password": base64.b64encode(b"Difyai123456").decode(),
        "language": "zh-Hans", "remember_me": True,
    })
    if r.status_code != 200:
        raise Exception("Login failed: " + r.text)
    s.headers["X-CSRF-Token"] = s.cookies.get("csrf_token", "")
    return s


def api_get(s, path):
    r = s.get(BASE + path)
    return r.status_code, r.text


def api_post(s, path, body):
    r = s.post(BASE + path, data=json.dumps(body).encode("utf-8"),
               headers={"Content-Type": "application/json"})
    return r.status_code, r.text


# ---------------- Node builders ----------------
def _node(node_id, ntype, title, data, x, y):
    data = dict(data)
    data.setdefault("type", ntype)
    data.setdefault("title", title)
    data.setdefault("selected", False)
    return {
        "id": node_id, "type": "custom", "data": data,
        "position": {"x": x, "y": y}, "targetPosition": "left",
        "sourcePosition": "right", "positionAbsolute": {"x": x, "y": y},
        "width": 242, "height": 88, "selected": False,
    }


def start_node(node_id, variables, x=80, y=300):
    return _node(node_id, "start", "开始", {"variables": variables}, x, y)


def llm_node(node_id, title, system_prompt, user_template, x=400, y=300,
             context_selector=None, vision=False):
    pt = [{"role": "system", "text": system_prompt},
          {"role": "user", "text": user_template}]
    data = {
        "model": MODEL,
        "prompt_template": pt,
        "prompt_config": {"jinja2_variables": []},
        "context": {"enabled": bool(context_selector),
                    "variable_selector": context_selector or []},
        "vision": {"enabled": vision, "configs": {"detail": "high",
                   "variable_selector": ["sys", "files"]}},
        "memory": {"window": {"enabled": False, "size": 10},
                   "query_prompt_template": "{{#sys.query#}}\n\n{{#sys.files#}}",
                   "role_prefix": {"user": "", "assistant": ""}},
    }
    return _node(node_id, "llm", title, data, x, y)


def code_node(node_id, title, code, variables, outputs, x=400, y=600):
    data = {
        "code_language": "python3", "code": code,
        "variables": variables, "outputs": outputs,
    }
    return _node(node_id, "code", title, data, x, y)


def if_else_node(node_id, title, cases, x=720, y=300):
    """cases: list of dicts with case_id, logical_operator, conditions.
    Each condition: {variable_selector:[...], comparison_operator:..., value:...}
    The first matching case is the 'true' (source) handle; else is the else branch.
    """
    data = {"cases": cases}
    return _node(node_id, "if-else", title, data, x, y)


def kb_node(node_id, title, dataset_ids, query_selector, x=400, y=600):
    data = {
        "query_variable_selector": query_selector,
        "dataset_ids": dataset_ids,
        "retrieval_mode": "multiple",
        "multiple_retrieval_config": {
            "top_k": 3, "score_threshold": 0.5,
            "reranking_mode": "reranking_model", "reranking_enable": False,
            "reranking_model": None, "weight": None,
        },
        "single_retrieval_config": None,
        "metadata_filtering_mode": "disabled",
        "metadata_model_config": None,
        "metadata_filtering_conditions": None,
        "vision": {"enabled": False, "configs": {"detail": "high",
                   "variable_selector": ["sys", "files"]}},
    }
    return _node(node_id, "knowledge-retrieval", title, data, x, y)


def end_node(node_id, outputs, x=1040, y=300):
    data = {"outputs": outputs}
    return _node(node_id, "end", "结束", data, x, y)


def answer_node(node_id, answer, x=1040, y=300):
    return _node(node_id, "answer", "直接回复", {"answer": answer}, x, y)


def edge(src, tgt, stype, ttype):
    return {
        "id": src + "-" + tgt, "source": src, "sourceHandle": "source",
        "target": tgt, "targetHandle": "target", "type": "custom",
        "data": {"sourceType": stype, "targetType": ttype},
    }


def make_graph(nodes, edges):
    return {"nodes": nodes, "edges": edges,
            "viewport": {"x": 0, "y": 0, "zoom": 0.6}}


def deploy(s, app_id, graph):
    sc, body = api_get(s, f"/apps/{app_id}/workflows/draft")
    if sc != 200:
        return False, f"GET draft failed {sc}: {body[:300]}"
    d = json.loads(body)
    h = d.get("hash")
    features = d.get("features") or {}
    env_vars = d.get("environment_variables") or []
    conv_vars = d.get("conversation_variables") or []
    payload = {
        "graph": graph, "features": features, "hash": h,
        "environment_variables": env_vars, "conversation_variables": conv_vars,
    }
    sc, body = api_post(s, f"/apps/{app_id}/workflows/draft", payload)
    try:
        rj = json.loads(body)
    except Exception:
        rj = {"raw": body[:500]}
    new_hash = rj.get("hash")
    ok = sc == 200 and rj.get("result") == "success"
    return ok, f"status={sc} hash={new_hash} {body[:300]}"


def verify(s, app_id, expected_nodes):
    sc, body = api_get(s, f"/apps/{app_id}/workflows/draft")
    if sc != 200:
        return False, f"GET failed {sc}"
    d = json.loads(body)
    g = d.get("graph", {})
    nodes = g.get("nodes", [])
    ntypes = {n["data"]["type"] for n in nodes}
    ids = {n["id"] for n in nodes}
    missing = [en for en in expected_nodes if en not in ids]
    return (not missing), f"nodes={len(nodes)} edges={len(g.get('edges',[]))} types={sorted(ntypes)} missing_ids={missing}"


# ============ GRAPH DEFINITIONS ============

def graph1_fault_diagnosis():
    """App 1: 工业设备故障诊断工作流 (workflow)
    Start -> LLM(analyze) -> KB(retrieval) -> Code(parse) -> IF/ELSE(severity)
       critical -> LLM(detailed) -> End
       else     -> End
    """
    n = []
    n.append(start_node("start", [
        {"variable": "fault_description", "label": "故障描述", "type": "paragraph",
         "required": True, "max_length": 2000, "default": "", "hint": "", "options": [], "placeholder": ""},
        {"variable": "device_type", "label": "设备类型", "type": "text-input",
         "required": True, "max_length": 100, "default": "", "hint": "", "options": [], "placeholder": ""},
        {"variable": "sensor_data", "label": "传感器数据", "type": "paragraph",
         "required": False, "max_length": 3000, "default": "", "hint": "", "options": [], "placeholder": ""},
    ], 80, 300))
    n.append(llm_node("llm_analyze", "故障初步分析",
        "你是一名工业设备故障诊断专家。精通旋转机械(电机/泵/风机/齿轮箱)、液压气动、电气驱动、过程设备的故障机理与诊断方法,熟悉ISO 10816/20816振动评估、FMEA、故障树(FTA)分析。\n\n请对输入的故障信息进行结构化分析,在回答最后一行输出严重等级标注,格式为: SEVERITY: critical 或 SEVERITY: warning 或 SEVERITY: normal\n\n分析要点:\n1. 症状解析:提取故障现象(异响/振动/温升/压力异常/电流异常/停机)、发生工况、设备型号与关键参数\n2. 故障假设:列出3-5个可能原因,按概率排序\n3. 验证路径:为每个假设给出验证方法与判断依据\n4. 根因定位:综合证据给出最可能根因,标注置信度\n5. 处置建议:措施、备件、维修工艺、安全注意事项",
        "设备类型: {{#start.device_type#}}\n故障描述: {{#start.fault_description#}}\n传感器数据: {{#start.sensor_data#}}",
        400, 300))
    n.append(kb_node("kb", "故障诊断知识检索",
        [KB_INDUSTRIAL_NET, KB_INDUSTRIAL_TEACH],
        ["start", "fault_description"], 720, 300))
    n.append(code_node("code_parse", "解析诊断结果",
        "def main(diagnosis: str, kb_context: str) -> dict:\n    text = (diagnosis or '') + '\\n---知识库---\\n' + (kb_context or '')\n    severity = 'normal'\n    for line in (diagnosis or '').splitlines():\n        ls = line.strip().lower()\n        if 'severity' in ls:\n            if 'critical' in ls:\n                severity = 'critical'\n            elif 'warning' in ls:\n                severity = 'warning'\n            else:\n                severity = 'normal'\n    is_critical = 1 if severity == 'critical' else 0\n    return {\n        'severity': severity,\n        'is_critical': is_critical,\n        'full_report': text,\n    }",
        [{"variable": "diagnosis", "value_selector": ["llm_analyze", "text"]},
         {"variable": "kb_context", "value_selector": ["kb", "result"]}],
        {"severity": {"type": "string"}, "is_critical": {"type": "number"},
         "full_report": {"type": "string"}},
        1040, 300))
    n.append(if_else_node("if_severity", "严重程度判断",
        [{"case_id": "true", "logical_operator": "and",
          "conditions": [{"variable_selector": ["code_parse", "severity"],
                           "comparison_operator": "is", "value": "critical"}]}],
        1360, 300))
    n.append(llm_node("llm_critical", "严重故障深度分析",
        "你是工业设备故障诊断资深专家。针对被判定为 critical(严重)的故障,请进行深度分析并给出详尽的应急处置方案。\n\n必须包含:\n1. 紧急处置:是否立即停机、降负荷运行、隔离措施\n2. 详细根因分析:结合故障机理、振动频谱特征(BPFO/BPFI/包络谱)、温度趋势\n3. 二次故障风险评估:可能引发的连锁故障\n4. 维修方案:拆装步骤、对中/动平衡规范、备件清单\n5. 安全注意事项:LOTO锁定挂牌、防护措施\n6. 预防措施:监测指标、阈值与定期维护建议,关联ISO 17359",
        "前置分析结果:\n{{#code_parse.full_report#}}\n\n请给出严重故障的深度分析与处置方案。",
        1680, 160))
    n.append(end_node("end", [
        {"variable": "diagnosis_report", "value_selector": ["llm_critical", "text"], "value_type": "string"},
        {"variable": "severity", "value_selector": ["code_parse", "severity"], "value_type": "string"},
        {"variable": "full_report", "value_selector": ["code_parse", "full_report"], "value_type": "string"},
    ], 2000, 300))
    e = [
        edge("start", "llm_analyze", "start", "llm"),
        edge("llm_analyze", "kb", "llm", "knowledge-retrieval"),
        edge("kb", "code_parse", "knowledge-retrieval", "code"),
        edge("code_parse", "if_severity", "code", "if-else"),
        edge("if_severity", "llm_critical", "if-else", "llm"),
        edge("if_severity", "end", "if-else", "end"),
        edge("llm_critical", "end", "llm", "end"),
    ]
    return make_graph(n, e)


def graph2_quality_assessment():
    """App 2: 生产质量评估工作流 (workflow)
    Start -> LLM(analyze quality) -> IF/ELSE(score<threshold)
       low -> LLM(detailed analysis) -> End
       ok  -> End
    """
    n = []
    n.append(start_node("start", [
        {"variable": "quality_data", "label": "质量数据", "type": "paragraph",
         "required": True, "max_length": 3000, "default": "", "hint": "", "options": [], "placeholder": ""},
        {"variable": "product_type", "label": "产品类型", "type": "text-input",
         "required": True, "max_length": 100, "default": "", "hint": "", "options": [], "placeholder": ""},
        {"variable": "standard_level", "label": "标准等级", "type": "select",
         "required": True, "default": "", "hint": "", "options": ["国标GB", "行标", "企标", "ISO国际标准"], "placeholder": ""},
    ], 80, 300))
    n.append(llm_node("llm_quality", "质量分析",
        "你是生产质量管理专家,精通六西格玛、SPC统计过程控制、FMEA、8D问题解决法,熟悉各类工业产品的质量标准(GB/ISO)与检验方法。\n\n请对生产质量数据进行分析,严格按以下结构输出,并在最后一行输出质量评分,格式: QUALITY_SCORE: 85 (0-100整数)。\n\n分析维度:\n1. 数据概览:检测项目、样本量、合格率、关键缺陷分布\n2. 缺陷分析:主要缺陷类型、帕累托分析(关键少数)、缺陷模式\n3. 过程能力:Cp/Cpk评估(若数据支持)、过程稳定性判断\n4. 根因分析:人机料法环测(5M1E)维度分析\n5. 改进建议:纠正措施、预防措施、控制计划更新",
        "产品类型: {{#start.product_type#}}\n标准等级: {{#start.standard_level#}}\n质量数据: {{#start.quality_data#}}",
        400, 300))
    n.append(code_node("code_score", "解析质量评分",
        "def main(report: str) -> dict:\n    score = 100\n    for line in (report or '').splitlines():\n        ls = line.strip()\n        low = ls.lower()\n        if 'quality_score' in low:\n            for tok in ls.replace(':', ' ').split():\n                try:\n                    score = int(tok)\n                except Exception:\n                    pass\n    is_low = 1 if score < 80 else 0\n    return {'score': score, 'is_low': is_low, 'report': report or ''}",
        [{"variable": "report", "value_selector": ["llm_quality", "text"]}],
        {"score": {"type": "number"}, "is_low": {"type": "number"}, "report": {"type": "string"}},
        720, 300))
    n.append(if_else_node("if_score", "质量评分判断",
        [{"case_id": "true", "logical_operator": "and",
          "conditions": [{"variable_selector": ["code_score", "score"],
                           "comparison_operator": "<", "value": "80"}]}],
        1040, 300))
    n.append(llm_node("llm_detail", "低分质量深度分析",
        "你是生产质量管理资深专家。针对质量评分低于80分的产品,请进行深度质量分析并输出8D报告。\n\n必须包含:\n1. D1团队:组建跨职能问题解决团队\n2. D2问题描述:用5W2H精确描述问题\n3. D3临时遏制措施:隔离、分选、返工方案\n4. D4根因分析:鱼骨图+5Why深挖根本原因\n5. D5/D6永久纠正措施:措施选择与实施计划\n6. D7预防措施:更新FMEA、控制计划、作业指导书\n7. D8团队认可:经验教训与知识沉淀",
        "质量分析报告:\n{{#code_score.report#}}\n质量评分: {{#code_score.score#}}\n\n请输出8D深度分析报告。",
        1360, 160))
    n.append(end_node("end", [
        {"variable": "quality_report", "value_selector": ["llm_detail", "text"], "value_type": "string"},
        {"variable": "score", "value_selector": ["code_score", "score"], "value_type": "number"},
        {"variable": "initial_report", "value_selector": ["code_score", "report"], "value_type": "string"},
    ], 1680, 300))
    e = [
        edge("start", "llm_quality", "start", "llm"),
        edge("llm_quality", "code_score", "llm", "code"),
        edge("code_score", "if_score", "code", "if-else"),
        edge("if_score", "llm_detail", "if-else", "llm"),
        edge("if_score", "end", "if-else", "end"),
        edge("llm_detail", "end", "llm", "end"),
    ]
    return make_graph(n, e)


def graph3_code_quality():
    """App 3: 代码质量分析工作流 (workflow)
    Start -> Code(metrics) -> LLM(security analysis) -> IF/ELSE(has_critical)
       yes -> LLM(fix suggestions) -> End
       no  -> End
    """
    n = []
    n.append(start_node("start", [
        {"variable": "source_code", "label": "源代码", "type": "paragraph",
         "required": True, "max_length": 8000, "default": "", "hint": "", "options": [], "placeholder": ""},
        {"variable": "language", "label": "编程语言", "type": "select",
         "required": True, "default": "", "hint": "", "options": ["Python", "Java", "JavaScript", "C/C++", "Go"], "placeholder": ""},
    ], 80, 300))
    n.append(code_node("code_metrics", "代码复杂度计算",
        "def main(source: str) -> dict:\n    code = source or ''\n    lines = code.splitlines()\n    total_lines = len(lines)\n    blank = sum(1 for l in lines if not l.strip())\n    comment = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*')))\n    code_lines = total_lines - blank - comment\n    cyclomatic = 1\n    for kw in ('if ', 'elif ', 'else:', 'for ', 'while ', 'except ', 'and ', 'or ', 'case '):\n        cyclomatic += code.count(kw)\n    max_nesting = 0\n    cur = 0\n    for l in lines:\n        stripped = l.lstrip()\n        indent = len(l) - len(stripped)\n        cur = indent // 4\n        if cur > max_nesting:\n            max_nesting = cur\n    has_critical = 1 if (cyclomatic > 10 or max_nesting > 5) else 0\n    return {\n        'total_lines': total_lines,\n        'code_lines': code_lines,\n        'comment_lines': comment,\n        'blank_lines': blank,\n        'cyclomatic_complexity': cyclomatic,\n        'max_nesting': max_nesting,\n        'has_critical': has_critical,\n    }",
        [{"variable": "source", "value_selector": ["start", "source_code"]}],
        {"total_lines": {"type": "number"}, "code_lines": {"type": "number"},
         "comment_lines": {"type": "number"}, "blank_lines": {"type": "number"},
         "cyclomatic_complexity": {"type": "number"}, "max_nesting": {"type": "number"},
         "has_critical": {"type": "number"}},
        400, 300))
    n.append(llm_node("llm_security", "安全与质量分析",
        "你是代码安全与质量审计专家,精通OWASP Top 10、CWE漏洞分类、SAST静态分析,熟悉多种语言的代码规范与安全最佳实践。\n\n请对代码进行安全与质量分析,在最后一行输出: HAS_CRITICAL: yes 或 HAS_CRITICAL: no\n\n分析维度:\n1. 安全漏洞:注入(SQLi/XSS/命令注入)、认证授权、敏感信息泄露、不安全依赖\n2. 代码异味:长函数、深层嵌套、重复代码、魔法数字\n3. 可维护性:命名规范、注释完整性、模块化程度\n4. 性能问题:潜在N+1查询、资源泄漏、不必要的计算\n5. 错误处理:异常捕获完整性、资源释放",
        "编程语言: {{#start.language#}}\n\n代码复杂度指标:\n- 总行数: {{#code_metrics.total_lines#}}\n- 代码行: {{#code_metrics.code_lines#}}\n- 圈复杂度: {{#code_metrics.cyclomatic_complexity#}}\n- 最大嵌套: {{#code_metrics.max_nesting#}}\n\n源代码:\n{{#start.source_code#}}",
        720, 300))
    n.append(if_else_node("if_critical", "严重问题判断",
        [{"case_id": "true", "logical_operator": "or",
          "conditions": [
              {"variable_selector": ["llm_security", "text"],
               "comparison_operator": "contains", "value": "HAS_CRITICAL: yes"},
              {"variable_selector": ["code_metrics", "has_critical"],
               "comparison_operator": "=", "value": "1"},
          ]}],
        1040, 300))
    n.append(llm_node("llm_fix", "修复建议",
        "你是代码重构与安全修复专家。针对检测出严重问题的代码,请给出具体的修复建议。\n\n必须包含:\n1. 问题清单:按严重程度排序(严重/高/中/低),每个问题标注CWE编号(如适用)\n2. 修复方案:为每个严重/高级问题给出具体代码修复示例(修复前/修复后对比)\n3. 重构建议:针对圈复杂度过高、嵌套过深给出重构方案(提取函数、策略模式、早返回)\n4. 测试建议:单元测试覆盖点、边界用例\n5. 防御性编程:输入校验、错误处理改进",
        "安全分析报告:\n{{#llm_security.text#}}\n\n复杂度指标 - 圈复杂度: {{#code_metrics.cyclomatic_complexity#}}, 最大嵌套: {{#code_metrics.max_nesting#}}\n\n请给出修复建议。",
        1360, 160))
    n.append(end_node("end", [
        {"variable": "fix_suggestions", "value_selector": ["llm_fix", "text"], "value_type": "string"},
        {"variable": "security_report", "value_selector": ["llm_security", "text"], "value_type": "string"},
        {"variable": "metrics", "value_selector": ["code_metrics", "cyclomatic_complexity"], "value_type": "number"},
        {"variable": "total_lines", "value_selector": ["code_metrics", "total_lines"], "value_type": "number"},
    ], 1680, 300))
    e = [
        edge("start", "code_metrics", "start", "code"),
        edge("code_metrics", "llm_security", "code", "llm"),
        edge("llm_security", "if_critical", "llm", "if-else"),
        edge("if_critical", "llm_fix", "if-else", "llm"),
        edge("if_critical", "end", "if-else", "end"),
        edge("llm_fix", "end", "llm", "end"),
    ]
    return make_graph(n, e)


# ---- Advanced-chat graphs (use answer node, sys.query as user input) ----

def graph4_industrial_internet_agent():
    """App 4: 工业互联网智能体 (advanced-chat)
    Start -> LLM(analyze query) -> IF/ELSE(is_technical?)
       yes -> KB retrieval -> LLM(detailed answer) -> Answer
       no  -> LLM(general answer) -> Answer
    """
    n = []
    n.append(start_node("start", [], 80, 300))
    n.append(llm_node("llm_classify", "意图分析",
        "你是工业互联网领域助手。判断用户问题是否为需要专业知识库支撑的技术性问题(如协议、PLC、边缘计算、OT安全、组态等),还是一般性问答。\n\n只输出一行: IS_TECHNICAL: yes 或 IS_TECHNICAL: no",
        "用户问题: {{#sys.query#}}",
        400, 300))
    n.append(if_else_node("if_tech", "技术问题判断",
        [{"case_id": "true", "logical_operator": "and",
          "conditions": [{"variable_selector": ["llm_classify", "text"],
                           "comparison_operator": "contains", "value": "IS_TECHNICAL: yes"}]}],
        720, 300))
    n.append(kb_node("kb", "工业知识检索",
        [KB_INDUSTRIAL_NET, KB_INDUSTRIAL_TEACH, KB_INDUSTRIAL_SAFETY],
        ["sys", "query"], 1040, 160))
    n.append(llm_node("llm_tech", "专业技术解答",
        "你是工业互联网技术专家。请基于检索到的知识库内容,对用户的技术问题给出专业、准确、结构化的解答。\n\n要求:\n1. 直接引用知识库中的关键信息并标注依据\n2. 涉及协议/标准时给出标准编号(如Modbus、OPC UA、IEC 62443)\n3. 给出实际工程应用要点与注意事项\n4. 如信息不足,明确说明需要补充的内容",
        "用户问题: {{#sys.query#}}\n\n知识库检索结果:\n{{#kb.result#}}",
        1360, 160, context_selector=["kb", "result"]))
    n.append(llm_node("llm_general", "通用解答",
        "你是工业互联网领域的友好助手。请用通俗易懂的语言回答用户的常规问题,保持简洁、清晰、有帮助。",
        "用户问题: {{#sys.query#}}",
        1040, 460))
    n.append(answer_node("answer", "{{#llm_tech.text#}}{{#llm_general.text#}}", 1680, 300))
    e = [
        edge("start", "llm_classify", "start", "llm"),
        edge("llm_classify", "if_tech", "llm", "if-else"),
        edge("if_tech", "kb", "if-else", "knowledge-retrieval"),
        edge("kb", "llm_tech", "knowledge-retrieval", "llm"),
        edge("if_tech", "llm_general", "if-else", "llm"),
        edge("llm_tech", "answer", "llm", "answer"),
        edge("llm_general", "answer", "llm", "answer"),
    ]
    return make_graph(n, e)


def graph5_predictive_maintenance():
    """App 5: 工业设备预测性维护智能体 (advanced-chat)
    Start -> LLM(analyze device data) -> IF/ELSE(risk_level)
       high -> LLM(maintenance plan) -> Code(MTBF) -> Answer
       low  -> LLM(status report) -> Answer
    """
    n = []
    n.append(start_node("start", [], 80, 300))
    n.append(llm_node("llm_analyze", "设备风险分析",
        "你是工业设备预测性维护专家,精通振动分析、油液监测、红外热成像、超声检测等状态监测技术,熟悉ISO 17359状态监测标准。\n\n请分析用户描述的设备运行数据/状态,评估故障风险等级,在最后一行输出: RISK_LEVEL: high 或 RISK_LEVEL: medium 或 RISK_LEVEL: low\n\n分析要点:\n1. 状态参数解读:振动/温度/电流/压力等参数趋势与阈值对比\n2. 故障模式预测:基于P-F间隔(潜在故障到功能故障)的剩余寿命估计\n3. 风险等级:综合概率与后果评估\n4. 关键监测指标建议",
        "用户输入: {{#sys.query#}}",
        400, 300))
    n.append(if_else_node("if_risk", "风险等级判断",
        [{"case_id": "true", "logical_operator": "and",
          "conditions": [{"variable_selector": ["llm_analyze", "text"],
                           "comparison_operator": "contains", "value": "RISK_LEVEL: high"}]}],
        720, 300))
    n.append(llm_node("llm_plan", "维护计划制定",
        "你是预测性维护资深专家。针对高风险设备,请制定详尽的维护计划。\n\n必须包含:\n1. 紧急评估:立即检查项、是否需要降负荷/停机\n2. 维护策略:纠正性/预防性/预测性维护选择与理由\n3. 维修方案:拆检步骤、备件清单、工时估算\n4. MTBF/MTTR目标:可靠性指标改善目标\n5. 监测强化:增加测点、缩短监测周期、报警阈值调整\n6. 成本效益:维护投入vs故障损失(ROI)分析",
        "风险分析结果:\n{{#llm_analyze.text#}}\n\n请制定维护计划。",
        1040, 160))
    n.append(code_node("code_mtbf", "计算可靠性指标",
        "def main(analysis: str, plan: str) -> dict:\n    import re\n    text = (analysis or '') + '\\n' + (plan or '')\n    # extract any MTBF number mentioned, else estimate from text length\n    nums = re.findall(r'MTBF[^0-9]{0,10}(\\d+)', text, re.I)\n    mtbf = int(nums[0]) if nums else 720\n    # MTTR estimate hours\n    mttr_nums = re.findall(r'MTTR[^0-9]{0,10}(\\d+)', text, re.I)\n    mttr = int(mttr_nums[0]) if mttr_nums else 8\n    availability = round(mtbf / (mtbf + mttr) * 100, 2)\n    return {\n        'mtbf_hours': mtbf,\n        'mttr_hours': mttr,\n        'availability_pct': availability,\n        'reliability_summary': 'MTBF={}h, MTTR={}h, 可用度={}%'.format(mtbf, mttr, availability),\n    }",
        [{"variable": "analysis", "value_selector": ["llm_analyze", "text"]},
         {"variable": "plan", "value_selector": ["llm_plan", "text"]}],
        {"mtbf_hours": {"type": "number"}, "mttr_hours": {"type": "number"},
         "availability_pct": {"type": "number"}, "reliability_summary": {"type": "string"}},
        1360, 160))
    n.append(llm_node("llm_low", "状态报告",
        "你是设备状态报告专家。针对低风险设备,请生成简洁的运行状态报告,说明设备运行正常,并给出日常维护建议与下次监测建议。",
        "风险分析结果:\n{{#llm_analyze.text#}}\n\n请生成状态报告。",
        1040, 460))
    n.append(answer_node("answer",
        "高风险维护方案:\n{{#llm_plan.text#}}\n\n可靠性指标计算:\n{{#code_mtbf.reliability_summary#}}\n\n低风险状态报告:\n{{#llm_low.text#}}", 1680, 300))
    e = [
        edge("start", "llm_analyze", "start", "llm"),
        edge("llm_analyze", "if_risk", "llm", "if-else"),
        edge("if_risk", "llm_plan", "if-else", "llm"),
        edge("llm_plan", "code_mtbf", "llm", "code"),
        edge("if_risk", "llm_low", "if-else", "llm"),
        edge("code_mtbf", "answer", "code", "answer"),
        edge("llm_low", "answer", "llm", "answer"),
    ]
    return make_graph(n, e)


def graph6_safety_compliance():
    """App 6: 工业安全合规检查员 (advanced-chat)
    Start -> LLM(analyze compliance) -> IF/ELSE(compliance_status)
       non-compliant -> LLM(remediation) -> Answer
       compliant     -> LLM(certification) -> Answer
    """
    n = []
    n.append(start_node("start", [], 80, 300))
    n.append(llm_node("llm_check", "合规性检查",
        "你是工业安全合规检查专家,熟悉GB/T 33009、IEC 61508/61511功能安全、ISO 45001职业健康安全、GB 50058爆炸危险环境、机械安全ISO 13849等标准。\n\n请对用户描述的工业场景/设备/作业进行合规性检查,在最后一行输出: COMPLIANCE: non-compliant 或 COMPLIANCE: compliant\n\n检查维度:\n1. 法规符合性:适用法规与强制性标准识别\n2. 风险评估:HAZOP/LOPA/ SIL定级\n3. 安全防护:联锁、急停、防护罩、光幕\n4. 管理体系:作业许可、培训、应急预案\n5. 缺陷清单:不符合项与对应标准条款",
        "用户输入: {{#sys.query#}}",
        400, 300, context_selector=None))
    n.append(if_else_node("if_compliance", "合规状态判断",
        [{"case_id": "true", "logical_operator": "and",
          "conditions": [{"variable_selector": ["llm_check", "text"],
                           "comparison_operator": "contains", "value": "COMPLIANCE: non-compliant"}]}],
        720, 300))
    n.append(kb_node("kb", "安全标准检索",
        [KB_INDUSTRIAL_SAFETY, KB_INDUSTRIAL_TEACH],
        ["sys", "query"], 1040, 160))
    n.append(llm_node("llm_remediation", "整改方案",
        "你是工业安全整改专家。针对不合规项,请制定详细的整改方案。\n\n必须包含:\n1. 不符合项清单:逐条列出,标注违反的标准条款\n2. 整改措施:工程控制>管理控制>PPE的层级控制策略\n3. 优先级排序:按风险等级排序整改顺序\n4. 责任与时限:整改责任人、完成时限、验收标准\n5. 验证方法:整改后复核与持续监督机制\n6. 基于检索的安全标准给出依据",
        "合规检查结果:\n{{#llm_check.text#}}\n\n安全标准检索:\n{{#kb.result#}}\n\n请制定整改方案。",
        1360, 160, context_selector=["kb", "result"]))
    n.append(llm_node("llm_certify", "合格认证报告",
        "你是工业安全认证专家。针对判定为合规的场景,请出具合规认证报告。\n\n必须包含:\n1. 检查结论:合规声明与适用范围\n2. 符合性矩阵:逐项标准条款符合性证据\n3. 风险 residual:残余风险评估\n4. 维持建议:保持合规的监测与复检周期\n5. 认证建议:可申请的体系认证(ISO 45001等)",
        "合规检查结果:\n{{#llm_check.text#}}\n\n请出具合规认证报告。",
        1040, 460))
    n.append(answer_node("answer",
        "整改方案:\n{{#llm_remediation.text#}}\n\n合规认证报告:\n{{#llm_certify.text#}}", 1680, 300))
    e = [
        edge("start", "llm_check", "start", "llm"),
        edge("llm_check", "if_compliance", "llm", "if-else"),
        edge("if_compliance", "kb", "if-else", "knowledge-retrieval"),
        edge("kb", "llm_remediation", "knowledge-retrieval", "llm"),
        edge("if_compliance", "llm_certify", "if-else", "llm"),
        edge("llm_remediation", "answer", "llm", "answer"),
        edge("llm_certify", "answer", "llm", "answer"),
    ]
    return make_graph(n, e)


def graph7_production_optimization():
    """App 7: 工业生产线优化顾问 (advanced-chat)
    Start -> LLM(analyze production data) -> Code(calculate OEE) -> LLM(optimization) -> Answer
    """
    n = []
    n.append(start_node("start", [], 80, 300))
    n.append(llm_node("llm_analyze", "生产数据分析",
        "你是精益生产与工业工程专家,精通OEE(设备综合效率)、TPM、价值流图(VSM)、瓶颈理论(TOC)、六西格玛。\n\n请分析用户提供的生产数据,提取可用性(Availability)、表现性(Performance)、质量(Quality)相关数据。\n\n在分析末尾,如能从输入中提取数字,请用如下格式输出(无法提取则留0):\nAVAIL: 85 (百分比)\nPERF: 90 (百分比)\nQUAL: 95 (百分比)\n\n分析要点:\n1. 数据解读:计划停机、非计划停机、节拍、良率\n2. 损失识别:六大损失(故障/换型/小停机/速度/缺陷/启动)\n3. 瓶颈定位:约束资源识别\n4. 改善方向:初步优化建议",
        "用户输入: {{#sys.query#}}",
        400, 300))
    n.append(code_node("code_oee", "OEE计算",
        "def main(analysis: str) -> dict:\n    import re\n    text = analysis or ''\n    def grab(key):\n        m = re.search(key + r'[^0-9]{0,5}(\\d+(?:\\.\\d+)?)', text, re.I)\n        return float(m.group(1)) if m else 0.0\n    avail = grab('AVAIL')\n    perf = grab('PERF')\n    qual = grab('QUAL')\n    if avail == 0 and perf == 0 and qual == 0:\n        avail, perf, qual = 85.0, 90.0, 95.0\n    oee = round(avail * perf * qual / 10000, 2)\n    level = '世界级(>85%)' if oee > 85 else ('良好(60-85%)' if oee > 60 else '待改善(<60%)')\n    return {\n        'availability': avail,\n        'performance': perf,\n        'quality': qual,\n        'oee': oee,\n        'level': level,\n        'oee_summary': 'OEE = {}% x {}% x {}% / 10000 = {}% ({})'.format(avail, perf, qual, oee, level),\n    }",
        [{"variable": "analysis", "value_selector": ["llm_analyze", "text"]}],
        {"availability": {"type": "number"}, "performance": {"type": "number"},
         "quality": {"type": "number"}, "oee": {"type": "number"},
         "level": {"type": "string"}, "oee_summary": {"type": "string"}},
        720, 300))
    n.append(llm_node("llm_optimize", "优化方案",
        "你是生产线优化资深顾问。基于OEE分析结果,请给出具体的优化方案与ROI估算。\n\n必须包含:\n1. OEE诊断:基于计算结果(A={availability}%, P={performance}%, Q={quality}%, OEE={oee}%)定位主要损失\n2. 优化措施:针对最低维度(可用性/表现性/质量)的专项改善(SMED快速换型、TPM自主保全、节拍优化)\n3. 实施路线图:速赢(0-30天)、中期(30-90天)、长期(90天+)\n4. KPI目标:改善后OEE目标值与分项指标\n5. ROI估算:投入产出比与回收期\n6. 风险与对策:实施风险识别",
        "生产数据分析:\n{{#llm_analyze.text#}}\n\nOEE计算结果:\n{{#code_oee.oee_summary#}}\n\n请给出优化方案。",
        1040, 300))
    n.append(answer_node("answer",
        "{{#llm_optimize.text#}}", 1360, 300))
    e = [
        edge("start", "llm_analyze", "start", "llm"),
        edge("llm_analyze", "code_oee", "llm", "code"),
        edge("code_oee", "llm_optimize", "code", "llm"),
        edge("llm_optimize", "answer", "llm", "answer"),
    ]
    return make_graph(n, e)


def graph8_programming_review():
    """App 8: 编程作业评审智能体 (advanced-chat)
    Start -> LLM(analyze code) -> IF/ELSE(has_errors)
       yes -> LLM(detailed review) -> Code(count issues) -> Answer
       no  -> LLM(quality score) -> Answer
    """
    n = []
    n.append(start_node("start", [], 80, 300))
    n.append(llm_node("llm_review", "代码初步评审",
        "你是编程教学评审专家。请评审用户提交的代码作业,从正确性、规范性、可读性、算法效率角度分析。\n\n在最后一行输出: HAS_ERRORS: yes 或 HAS_ERRORS: no\n\n评审要点:\n1. 功能正确性:逻辑错误、边界条件、异常处理\n2. 代码规范:命名、缩进、注释\n3. 算法效率:时间/空间复杂度评估\n4. 可读性:结构清晰度、函数划分\n5. 总体评价:优点与不足",
        "用户提交内容: {{#sys.query#}}",
        400, 300))
    n.append(if_else_node("if_errors", "错误判断",
        [{"case_id": "true", "logical_operator": "and",
          "conditions": [{"variable_selector": ["llm_review", "text"],
                           "comparison_operator": "contains", "value": "HAS_ERRORS: yes"}]}],
        720, 300))
    n.append(llm_node("llm_detail", "详细评审",
        "你是编程教学资深评审。针对存在错误的代码作业,请给出详细评审与逐条指导。\n\n必须包含:\n1. 错误清单:按严重程度(致命/严重/一般/建议)分级,逐条说明错误位置、原因、影响\n2. 修正示例:对每个致命/严重错误给出修正前后的代码对比\n3. 学习建议:针对暴露的知识薄弱点给出学习路径\n4. 鼓励性反馈:肯定作业中的亮点\n5. 改进目标:下次提交应达成的具体目标",
        "初步评审:\n{{#llm_review.text#}}\n\n请给出详细评审。",
        1040, 160))
    n.append(code_node("code_count", "问题统计",
        "def main(review: str) -> dict:\n    text = review or ''\n    fatal = text.count('致命')\n    serious = text.count('严重')\n    general = text.count('一般')\n    suggest = text.count('建议')\n    total = fatal + serious + general + suggest\n    return {\n        'fatal': fatal,\n        'serious': serious,\n        'general': general,\n        'suggestion': suggest,\n        'total_issues': total,\n        'summary': '共发现{}个问题:致命{} 严重{} 一般{} 建议{}'.format(total, fatal, serious, general, suggest),\n    }",
        [{"variable": "review", "value_selector": ["llm_detail", "text"]}],
        {"fatal": {"type": "number"}, "serious": {"type": "number"},
         "general": {"type": "number"}, "suggestion": {"type": "number"},
         "total_issues": {"type": "number"}, "summary": {"type": "string"}},
        1360, 160))
    n.append(llm_node("llm_score", "质量评分",
        "你是编程教学评审专家。针对无明显错误的代码作业,请给出质量评分与肯定性评价。\n\n必须包含:\n1. 评分:满分100,按正确性40/规范性20/可读性20/效率20分项打分\n2. 亮点:作业中值得肯定的设计与实现\n3. 进阶建议:在现有基础上可进一步提升的方向\n4. 总体评语:鼓励性总结",
        "初步评审:\n{{#llm_review.text#}}\n\n请给出质量评分。",
        1040, 460))
    n.append(answer_node("answer",
        "详细评审:\n{{#llm_detail.text#}}\n\n问题统计: {{#code_count.summary#}}\n\n质量评分:\n{{#llm_score.text#}}", 1680, 300))
    e = [
        edge("start", "llm_review", "start", "llm"),
        edge("llm_review", "if_errors", "llm", "if-else"),
        edge("if_errors", "llm_detail", "if-else", "llm"),
        edge("llm_detail", "code_count", "llm", "code"),
        edge("if_errors", "llm_score", "if-else", "llm"),
        edge("code_count", "answer", "code", "answer"),
        edge("llm_score", "answer", "llm", "answer"),
    ]
    return make_graph(n, e)


def graph9_architecture_review():
    """App 9: 软件架构评审智能体 (advanced-chat)
    Start -> LLM(analyze architecture) -> IF/ELSE(architecture_type)
       microservice -> LLM(microservice review) -> Answer
       monolith     -> LLM(monolith review) -> Answer
    """
    n = []
    n.append(start_node("start", [], 80, 300))
    n.append(llm_node("llm_analyze", "架构分析",
        "你是软件架构评审专家,精通微服务、单体、事件驱动、CQRS、DDD等领域架构风格,熟悉高可用、高并发、可扩展性设计。\n\n请分析用户描述的软件架构,判断架构类型,在最后一行输出: ARCH_TYPE: microservice 或 ARCH_TYPE: monolith\n\n分析要点:\n1. 架构风格识别:部署模式、服务边界、通信方式\n2. 技术栈分析:语言、框架、中间件、数据存储\n3. 质量属性评估:可用性、可扩展性、可维护性、安全性\n4. 架构问题初步识别:耦合度、数据一致性、运维复杂度",
        "用户输入: {{#sys.query#}}",
        400, 300))
    n.append(if_else_node("if_arch", "架构类型判断",
        [{"case_id": "true", "logical_operator": "and",
          "conditions": [{"variable_selector": ["llm_analyze", "text"],
                           "comparison_operator": "contains", "value": "ARCH_TYPE: microservice"}]}],
        720, 300))
    n.append(kb_node("kb", "架构知识检索",
        [KB_SW_ENG, KB_TALENT],
        ["sys", "query"], 1040, 160))
    n.append(llm_node("llm_micro", "微服务架构评审",
        "你是微服务架构资深评审专家。请针对微服务架构进行深度评审。\n\n必须包含:\n1. 服务拆分评估:限界上下文(Bounded Context)合理性、服务粒度、康威定律契合度\n2. 通信与契约:同步(gRPC/REST)vs异步(消息)选择、API契约管理、幂等性\n3. 数据一致性:分布式事务(Saga/TCC)、最终一致性、CQRS、事件溯源适用性\n4. 可观测性:链路追踪、指标、日志、服务网格(Service Mesh)成熟度\n5. 弹性设计:熔断、降级、限流、重试、舱壁模式\n6. 部署运维:容器化、K8s、CI/CD、蓝绿/金丝雀发布\n7. 改进建议:结合检索的软件工程最佳实践给出优先级排序的建议",
        "架构分析:\n{{#llm_analyze.text#}}\n\n软件工程知识库:\n{{#kb.result#}}\n\n请给出微服务架构评审。",
        1360, 160, context_selector=["kb", "result"]))
    n.append(llm_node("llm_mono", "单体架构评审",
        "你是软件架构资深评审专家。请针对单体架构进行深度评审。\n\n必须包含:\n1. 模块化评估:分层清晰度、模块耦合度、循环依赖检测\n2. 可维护性:代码组织、依赖方向、领域边界识别\n3. 扩展性瓶颈:水平扩展限制、数据库瓶颈、单点故障\n4. 演进路径:向模块化单体(Modular Monolith)再到微服务的渐进式演进策略\n5. 改进建议:在不拆分微服务前提下提升架构质量的具体措施\n6. 何时拆分:单体到微服务的拆分信号与决策框架",
        "架构分析:\n{{#llm_analyze.text#}}\n\n请给出单体架构评审。",
        1040, 460))
    n.append(answer_node("answer",
        "微服务架构评审:\n{{#llm_micro.text#}}\n\n单体架构评审:\n{{#llm_mono.text#}}", 1680, 300))
    e = [
        edge("start", "llm_analyze", "start", "llm"),
        edge("llm_analyze", "if_arch", "llm", "if-else"),
        edge("if_arch", "kb", "if-else", "knowledge-retrieval"),
        edge("kb", "llm_micro", "knowledge-retrieval", "llm"),
        edge("if_arch", "llm_mono", "if-else", "llm"),
        edge("llm_micro", "answer", "llm", "answer"),
        edge("llm_mono", "answer", "llm", "answer"),
    ]
    return make_graph(n, e)


# ============ APP REGISTRY ============
APPS = [
    ("cbd7fa71-d8d1-45b5-bdf7-2c56d575669e", "工业设备故障诊断工作流", graph1_fault_diagnosis,
     ["start", "llm_analyze", "kb", "code_parse", "if_severity", "llm_critical", "end"]),
    ("1471e523-fe83-41fe-a2a8-9d56e8800de1", "生产质量评估工作流", graph2_quality_assessment,
     ["start", "llm_quality", "code_score", "if_score", "llm_detail", "end"]),
    ("2307bf62-6cd4-4599-a046-887c57e95387", "代码质量分析工作流", graph3_code_quality,
     ["start", "code_metrics", "llm_security", "if_critical", "llm_fix", "end"]),
    ("4e63c4d7-baf7-41b1-b295-c4565f72877e", "工业互联网智能体", graph4_industrial_internet_agent,
     ["start", "llm_classify", "if_tech", "kb", "llm_tech", "llm_general", "answer"]),
    ("15b2a9b9-2823-4d55-8c10-30ff760e7382", "工业设备预测性维护智能体", graph5_predictive_maintenance,
     ["start", "llm_analyze", "if_risk", "llm_plan", "code_mtbf", "llm_low", "answer"]),
    ("2dd72f64-61b6-46e8-8841-8300df3d921a", "工业安全合规检查员", graph6_safety_compliance,
     ["start", "llm_check", "if_compliance", "kb", "llm_remediation", "llm_certify", "answer"]),
    ("6fe85559-7f51-4849-a3d3-3c596853864a", "工业生产线优化顾问", graph7_production_optimization,
     ["start", "llm_analyze", "code_oee", "llm_optimize", "answer"]),
    ("9e8d3c60-d35c-4cc4-aec6-278e5214ef0b", "编程作业评审智能体", graph8_programming_review,
     ["start", "llm_review", "if_errors", "llm_detail", "code_count", "llm_score", "answer"]),
    ("e3291494-d3d8-4933-a852-eb605bc8bf83", "软件架构评审智能体", graph9_architecture_review,
     ["start", "llm_analyze", "if_arch", "kb", "llm_micro", "llm_mono", "answer"]),
]


def main():
    s = get_session()
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for app_id, name, graph_fn, expected in APPS:
        if only and only != "all" and only not in app_id:
            continue
        print("\n" + "=" * 70)
        print(f">>> {name}  ({app_id})")
        try:
            graph = graph_fn()
            ok, msg = deploy(s, app_id, graph)
            print(f"DEPLOY: {'OK' if ok else 'FAIL'}  {msg}")
            if ok:
                vok, vmsg = verify(s, app_id, expected)
                print(f"VERIFY: {'OK' if vok else 'FAIL'}  {vmsg}")
        except Exception as ex:
            import traceback
            print(f"ERROR: {ex}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
