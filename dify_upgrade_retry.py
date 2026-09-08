#!/usr/bin/env python3
"""
Retry failed advanced-chat and workflow apps by fetching current hash first.
"""
import requests, base64, json, sys, time

BASE = "http://localhost:5001"
s = requests.Session()
pass_b64 = base64.b64encode(b"Difyai123456").decode()
r = s.post(f"{BASE}/console/api/login", json={"email":"myuwei@126.com","password":pass_b64})
if r.status_code != 200 or r.json().get("result") != "success":
    print("LOGIN FAILED", r.text); sys.exit(1)
access = s.cookies.get("access_token")
csrf = s.cookies.get("csrf_token")
H = {"Authorization": f"Bearer {access}", "X-CSRF-Token": csrf, "Content-Type":"application/json"}

PROVIDER = "langgenius/openai_api_compatible/openai_api_compatible"
M_REASON = "qwen3:14b"
M_CODER  = "qwen2.5-coder:14b"

def make_advanced_chat_graph(system_prompt, model, temp=0.6):
    start_id = str(int(time.time()*1000))
    return {
        "nodes": [
            {"id": start_id, "type": "custom",
             "data": {"variables": [], "type": "start", "title": "开始"},
             "position": {"x": 80, "y": 282}, "targetPosition": "left", "sourcePosition": "right",
             "positionAbsolute": {"x": 80, "y": 282}, "width": 242, "height": 73},
            {"id": "llm", "type": "custom",
             "data": {
                 "model": {"provider": PROVIDER, "name": model, "mode": "chat",
                           "completion_params": {"temperature": temp, "max_tokens": 4096, "top_p": 0.9, "stop": []}},
                 "prompt_template": [{"role": "system", "text": system_prompt}],
                 "context": {"enabled": False, "variable_selector": []},
                 "vision": {"enabled": False},
                 "memory": {"window": {"enabled": True, "size": 10},
                            "query_prompt_template": "{{#sys.query#}}\n\n{{#sys.files#}}",
                            "role_prefix": {"user": "", "assistant": ""}},
                 "selected": False, "type": "llm", "title": "LLM"},
             "position": {"x": 380, "y": 282}, "targetPosition": "left", "sourcePosition": "right",
             "positionAbsolute": {"x": 380, "y": 282}, "width": 242, "height": 88
            },
            {"id": "answer", "type": "custom",
             "data": {"variables": [], "answer": "{{#llm.text#}}", "type": "answer", "title": "直接回复"},
             "position": {"x": 680, "y": 282}, "targetPosition": "left", "sourcePosition": "right",
             "positionAbsolute": {"x": 680, "y": 282}, "width": 242, "height": 103
            }
        ],
        "edges": [
            {"id": f"{start_id}-llm", "source": start_id, "sourceHandle": "source",
             "target": "llm", "targetHandle": "target", "type": "custom",
             "data": {"sourceType": "start", "targetType": "llm"}},
            {"id": "llm-answer", "source": "llm", "sourceHandle": "source",
             "target": "answer", "targetHandle": "target", "type": "custom",
             "data": {"sourceType": "llm", "targetType": "answer"}}
        ],
        "viewport": {"x": 0, "y": 0, "zoom": 1}
    }

def make_workflow_graph(system_prompt, model, input_vars, temp=0.6):
    start_id = str(int(time.time()*1000))
    end_id = str(int(time.time()*1000)+1)
    start_variables = []
    for iv in input_vars:
        start_variables.append({
            "variable": iv["variable"], "label": iv["label"], "type": iv.get("type","paragraph"),
            "required": iv.get("required", True), "max_length": iv.get("max_length", 2000),
            "default": "", "hint": "", "options": [], "placeholder": ""
        })
    msg_text = "{{#%s.%s#}}" % (start_id, input_vars[0]["variable"]) if input_vars else "{{#sys.query#}}"
    return {
        "nodes": [
            {"id": start_id, "type": "custom",
             "data": {"variables": start_variables, "type": "start", "title": "开始"},
             "position": {"x": 80, "y": 282}, "targetPosition": "left", "sourcePosition": "right",
             "positionAbsolute": {"x": 80, "y": 282}, "width": 242, "height": 73},
            {"id": "llm", "type": "custom",
             "data": {
                 "model": {"provider": PROVIDER, "name": model, "mode": "chat",
                           "completion_params": {"temperature": temp, "max_tokens": 4096, "top_p": 0.9, "stop": []}},
                 "prompt_template": [{"role": "system", "text": system_prompt},
                                     {"role": "user", "text": msg_text}],
                 "context": {"enabled": False, "variable_selector": []},
                 "vision": {"enabled": False},
                 "memory": {"window": {"enabled": False, "size": 10},
                            "query_prompt_template": "{{#sys.query#}}\n\n{{#sys.files#}}",
                            "role_prefix": {"user": "", "assistant": ""}},
                 "selected": False, "type": "llm", "title": "LLM"},
             "position": {"x": 380, "y": 282}, "targetPosition": "left", "sourcePosition": "right",
             "positionAbsolute": {"x": 380, "y": 282}, "width": 242, "height": 88
            },
            {"id": end_id, "type": "custom",
             "data": {"outputs": [{"value_selector": ["llm","text"], "value_type": "string", "variable": "result"}],
                      "selected": False, "title": "结束", "type": "end"},
             "position": {"x": 680, "y": 282}, "targetPosition": "left", "sourcePosition": "right",
             "positionAbsolute": {"x": 680, "y": 282}, "width": 242, "height": 88
            }
        ],
        "edges": [
            {"id": f"{start_id}-llm", "source": start_id, "sourceHandle": "source",
             "target": "llm", "targetHandle": "target", "type": "custom",
             "data": {"sourceType": "start", "targetType": "llm"}},
            {"id": f"llm-{end_id}", "source": "llm", "sourceHandle": "source",
             "target": end_id, "targetHandle": "target", "type": "custom",
             "data": {"sourceType": "llm", "targetType": "end"}}
        ],
        "viewport": {"x": 0, "y": 0, "zoom": 1}
    }

def default_features():
    return {
        "opening_statement": "", "suggested_questions": [],
        "suggested_questions_after_answer": {"enabled": False},
        "text_to_speech": {"enabled": False, "voice": "", "language": ""},
        "speech_to_text": {"enabled": False}, "retriever_resource": {"enabled": False},
        "sensitive_word_avoidance": {"enabled": False},
        "file_upload": {
            "image": {"enabled": False, "number_limits": 3, "transfer_methods": ["local_file","remote_url"]},
            "enabled": False, "allowed_file_types": ["image"],
            "allowed_file_extensions": [".JPG",".JPEG",".PNG",".GIF",".WEBP",".SVG"],
            "allowed_file_upload_methods": ["local_file","remote_url"], "number_limits": 3,
            "fileUploadConfig": {"file_size_limit":15,"batch_count_limit":5,"file_upload_limit":20,
                "image_file_size_limit":10,"video_file_size_limit":100,"audio_file_size_limit":50,
                "workflow_file_upload_limit":10,"image_file_batch_limit":10,
                "single_chunk_attachment_limit":10,"attachment_image_file_size_limit":2}}
    }

def get_current_hash(aid):
    r = s.get(f"{BASE}/console/api/apps/{aid}/workflows/draft", headers=H)
    if r.status_code == 200:
        return r.json().get("hash")
    return None

def update_workflow(aid, graph, features, current_hash):
    payload = {"graph": graph, "features": features,
               "environment_variables": [], "conversation_variables": [],
               "hash": current_hash}
    r = s.post(f"{BASE}/console/api/apps/{aid}/workflows/draft", headers=H, json=payload)
    return r.status_code, r.text[:400]

PROMPTS_AC = {}

PROMPTS_AC["工业设备预测性维护智能体"] = """你是一名工业设备预测性维护(PdM)智能体,融合机理模型与数据驱动方法,精通振动分析(ISO 10816/10817/20816)、油液分析、温度监测、电流签名分析(MCSA)等多源状态监测技术,掌握RUL(剩余寿命)预测、故障预测与健康管理(PHM)方法论,能基于设备运行数据与机理知识输出可执行的维护决策。

【核心知识体系】
1. 状态监测技术:振动(加速度/速度/位移,FFT频谱、包络谱、阶次分析)、油液(颗粒计数、元素光谱、铁谱)、热成像、声发射、电流签名,各类技术适用故障(不平衡/不对中/轴承故障/齿轮磨损/电气故障)的对应关系。
2. 故障模式与机理:旋转机械(轴承外圈/内圈/滚动体/保持架故障特征频率BPFO/BPFI/BSF/FTF)、齿轮(啮合频率、边带)、电机(转子断条、定子偏心)、泵(气蚀、喘振)、风机(失速)。
3. 预测建模:基于阈值(ISO 10816振动速度限值)、基于趋势(线性/指数拟合)、基于机器学习(LSTM/Transformer时序预测、Survival Analysis生存分析)、物理-数据混合模型(Kalman滤波+ML残差)。
4. 维护策略:CBM(状态基维护)、PdM(预测性)、RTF(运行至失效)的决策矩阵,维护窗口规划与备件管理,遵循RCM(以可靠性为中心的维护)。
5. 标准与规范:ISO 17359(机器状态监测与诊断通则)、ISO 13374(数据处理与诊断)、ISO 20919(风电机组状态监测)、VDI 3832。

【多步骤推理回答规范】
1. 设备与故障界定:明确设备类型(电机/泵/风机/齿轮箱/压缩机)、关键参数(转速/功率/轴承型号)、故障现象与监测数据来源。
2. 数据评估:说明所需数据(振动频谱、趋势、工艺参数),评估数据质量(采样率、是否有变速变载工况)。
3. 特征与诊断:计算或解读故障特征频率,对比健康基线,定位故障部件与严重度等级(ISO 20816区域A/B/C/D)。
4. RUL预测:基于趋势退化模型或历史失效数据,给出剩余寿命区间与置信度,标注假设与不确定性。
5. 维护决策:给出维护类型(立即停机/计划检修/继续监测)、窗口建议、备件与资源清单、风险(二次损坏、安全)。
6. 验证与闭环:给出修复后验证(振动复测、对中校验)与持续监测指标,形成PdM闭环。

【输出要求】
- 关键结论(故障部位、严重度、建议动作)前置,推理过程分步可追溯。
- 涉及特征频率计算给出公式与代入数值。
- 对安全相关(如转子失衡超标、轴位移越限)给出明确停机阈值依据。"""

PROMPTS_AC["工业安全合规检查员"] = """你是一名工业安全合规检查员智能体,具备法规解读、风险辨识、隐患排查与整改跟踪能力,精通安全生产法、特种设备安全法、IEC 62443工控安全、GB 50058防爆电气设计、GB/T 33000企业安全生产标准化等法规标准体系,能对企业现场(工艺、设备、作业、管理)进行系统性合规评估并输出可执行的整改方案。

【法规标准知识库】
1. 安全生产法律体系:《安全生产法》《特种设备安全法》《消防法》《职业病防治法》,及配套部门规章(如《危险化学品安全管理条例》《工贸企业有限空间作业安全规范》)。
2. 工业控制系统安全:IEC 62443(纵深防御、SL等级)、等保2.0(工控扩展)、关键信息基础设施保护条例、GB/T 32919。
3. 防爆与电气:GB 50058(爆炸危险环境电力装置)、GB 3836(防爆电气设备)、IEC 60079(防爆标准)。
4. 工艺与设备安全:HAZOP(危险与可操作性分析)、LOPA(保护层分析)、SIL定级(IEC 61511功能安全)、PSM工艺安全管理。
5. 安全标准化:GB/T 33000(企业安全生产标准化通用规范)、双重预防机制(风险分级管控+隐患排查治理)。

【多步骤合规检查回答规范】
1. 范围界定:明确检查对象(某装置/车间/系统)、适用法规标准清单、检查维度(设计/运行/管理/应急)。
2. 合规基线:列出该场景下应满足的核心法规条款与标准要求(编号+要点),作为评判依据。
3. 隐患辨识:针对用户描述的现状,运用检查表法、JHA(工作危害分析)、HAZOP等方法识别隐患,按可能/严重度分级(参考LEC或风险矩阵)。
4. 不符合项判定:逐条对照法规标准,判定不符合项,引用具体条款,说明偏离程度。
5. 整改方案:对每项不符合给出整改措施(工程技术/管理/个体防护)、责任建议、时限(立即/短期/中期)、验收标准。
6. 跟踪与闭环:给出整改验证方法、复查周期、台账记录要求,形成PDCA闭环。

【安全准则】
- 严格区分"合规底线"与"风险提升",前者必须满足,后者按ALARP(风险降至合理可行最低)原则建议。
- 对涉及重大危险源、特种作业、有限空间、动火作业等高危场景,给出强制许可与监护要求。
- 不提供任何规避安全监管、降低防护等级的"变通"建议。"""

PROMPTS_WF = {}

PROMPTS_WF["生产质量评估工作流"] = """你是一名生产质量评估专家,接收生产过程数据与质量记录,输出符合ISO 9001/SPC方法论的质量评估报告。你精通统计过程控制(SPC)、过程能力分析(Cp/Cpk/Pp/Ppk)、不合格品分析(8D/Pareto/鱼骨图)、MSA测量系统分析,能在良率、过程能力、波动源多维度评估生产线质量状态。

【评估流程——严格按以下步骤推理】
1. 数据梳理:从输入提取质量数据(抽样结果/测量值/批次/工序/不合格项/返修率),识别数据类型(计量型/计数型)、样本量、子组划分。
2. 稳定性判定:判断过程是否处于统计受控状态(控制图:计量型用Xbar-R/单值-移动极差,计数型用p/np/c/u图),识别异常模式(链/趋势/超出控制限)及特殊原因。
3. 过程能力评估:计算Cp/Cpk(短期)与Pp/Ppk(长期),对照客户规格(USL/LSL),按能力指数分级(Cpk<1.0不充分/1.0-1.33边缘/>1.33充分/>1.67优秀),识别偏移与波动问题。
4. 不合格分析:用Pareto识别关键少数不合格项,用鱼骨图(人机料法环测)与5Whys进行根因分析,必要时关联FMEA的RPN。
5. 改进建议:针对波动过大(共性原因)给出系统性改进(工艺优化/设备维护/防错),针对偏移(特殊原因)给出纠正措施,标注优先级与预期Cpk提升。
6. 闭环管理:给出SPC控制计划更新、首件检验、过程审核(ISO 9001 8.5.1)与持续监控建议。

【输出格式——严格遵循】
【质量概况】良率/不合格率/过程能力指数一句话概述。
【数据与判定】数据类型+样本+控制图判定结果(受控/失控+异常点)。
【过程能力】Cp/Cpk/Ppk数值+能力等级+偏移与波动诊断。
【关键不合格分析】Pareto前列项+根因(鱼骨图要素)+RPN。
【改进方案】按优先级排序的措施(系统改进+纠正)+预期收益。
【控制计划】更新后的SPC监控项与频次+审核要点。

对数据不足的场景,给出"建议采集数据"清单(变量、抽样方案、子组大小)。"""

PROMPTS_WF["代码质量分析工作流"] = """你是一名代码质量分析专家,接收源代码,输出涵盖可维护性、可靠性、安全性、性能与规范的全面质量报告。你熟悉ISO/IEC 25010软件质量模型、OWASP Top 10、CWE缺陷分类、SonarQube规则体系,精通Java/Python/C++等主流工业软件语言,能在工业控制与嵌入式语境下评估代码风险。

【分析流程——严格按以下步骤推理】
1. 代码概览:识别语言、框架、模块结构、规模(行数/类/函数),概述代码用途与所在系统(如PLC上位机/边缘网关/MES后端)。
2. 可维护性评估:从圈复杂度(>15需关注)、认知复杂度、函数/类规模(>50行函数、>500行类)、重复代码(>3%块重复)、命名规范、注释密度给出可维护性评分,定位最难维护的模块。
3. 可靠性与缺陷:按CWE分类识别潜在缺陷——空指针(CWE-476)、资源泄漏(CWE-404/775)、并发缺陷(CWE-362/366)、错误处理缺失、边界越界、整数溢出,给出代码位置与修复建议。
4. 安全性扫描:对照OWASP Top 10识别注入(含SQL/命令/LDAP)、XSS、不安全反序列化、硬编码密钥、弱加密、日志泄漏,对工控语境额外检查实时性、看门狗、故障安全(fail-safe)。
5. 性能与资源:识别低效模式(O(n^2)循环、不必要的对象创建、同步阻塞、内存拷贝)、资源占用预测、在受限环境(边缘/嵌入式)的适配风险。
6. 规范与一致性:对照编码规范(如Java阿里巴巴手册、Python PEP 8)列出偏差,评估架构一致性(分层、依赖方向、接口契约)。
7. 优先级排序:将所有问题按严重度(Blocker/Critical/Major/Minor/Info)与影响(安全/功能/性能/可维护)排序,给出修复路线。

【输出格式——严格遵循】
【质量概览】语言+规模+总体评级(A/B/C/D)+一句话结论。
【问题统计】按严重度统计数量(Blocker/Critical/Major/Minor)。
【关键问题清单】按严重度排序前5-10项,每项含:位置、CWE编号、描述、影响、修复建议(含代码片段)、优先级。
【可维护性】复杂度热点+重复+命名/注释评估。
【安全性】OWASP对应项+工控特有风险。
【修复路线图】分立即修复/迭代改进/技术债务重构三阶段,标注工作量估算(人时)。

对仅给出片段的情况,明确标注分析范围局限,不臆测未提供部分。"""

RETRY_AC = [
    ("15b2a9b9-2823-4d55-8c10-30ff760e7382", "工业设备预测性维护智能体", M_REASON),
    ("2dd72f64-61b6-46e8-8841-8300df3d921a", "工业安全合规检查员", M_REASON),
]
RETRY_WF = [
    ("1471e523-fe83-41fe-a2a8-9d56e8800de1", "生产质量评估工作流", M_REASON,
     [{"variable":"quality_data","label":"生产质量数据与记录","type":"paragraph","required":True,"max_length":2000}]),
    ("2307bf62-6cd4-4599-a046-887c57e95387", "代码质量分析工作流", M_CODER,
     [{"variable":"source_code","label":"待分析源代码","type":"paragraph","required":True,"max_length":4000}]),
]

print("=" * 60)
print("RETRY: advanced-chat apps with current hash")
print("=" * 60)
ok = 0; fail = 0
for aid, name, model in RETRY_AC:
    prompt = PROMPTS_AC.get(name, "")
    h = get_current_hash(aid)
    graph = make_advanced_chat_graph(prompt, model)
    features = default_features()
    code, resp = update_workflow(aid, graph, features, h)
    if code == 200:
        print("  [OK] %-26s" % name); ok += 1
    else:
        print("  [FAIL] %-26s code=%d resp=%s" % (name, code, resp)); fail += 1
    time.sleep(0.5)
print("RETRY AC DONE: ok=%d fail=%d" % (ok, fail))

print()
print("=" * 60)
print("RETRY: workflow apps with current hash")
print("=" * 60)
ok = 0; fail = 0
for aid, name, model, ivars in RETRY_WF:
    prompt = PROMPTS_WF.get(name, "")
    h = get_current_hash(aid)
    graph = make_workflow_graph(prompt, model, ivars)
    code, resp = update_workflow(aid, graph, {}, h)
    if code == 200:
        print("  [OK] %-26s" % name); ok += 1
    else:
        print("  [FAIL] %-26s code=%d resp=%s" % (name, code, resp)); fail += 1
    time.sleep(0.5)
print("RETRY WF DONE: ok=%d fail=%d" % (ok, fail))
