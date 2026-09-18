# -*- coding: utf-8 -*-
"""新 Lecture（A5~A12 / B7~B12 / P7~P8）工单内容定义。

内容依据教研资料目录：
- 05-AI应用基础48课时版（M系列工单风格 + campus_skills/mini_sched_env 思路）
- 02-程序设计基础（W系列工单风格，W13~W24 为进阶延伸）
- 03-Python程序设计-项目实战（P7 任务书《智能运维平台综合项目》+ 收官 P8）

每个 WORKSHEETS 条目：
  key       : CM key 前缀，如 a5_m51 -> a5_m51_student / a5_m51_teacher / fw_m51
  title     : 工单题名（含编号）
  week      : 周次标注
  predict   : 课前预习快问
  acc_b/acc_c: 分层达标要求
  steps     : 实施步骤
  starters  : [(签名, 学生框架代码)] —— 同时用于学生 notebook 与 fw 框架文件
  solution  : 教师参考实现（必须可独立运行，生成器会 subprocess 验证）
"""

WORKSHEETS = []

# ====================================================================
# A 系（AI应用基础48课时版） A5~A12 —— M5 之后进阶模块 M5+~M8
# ====================================================================

WORKSHEETS.append(dict(
    key="a5_m51", title="M5-1《智能决策入门：规则引擎与置信度》", week="第17周",
    predict="如果温度阈值判断和振动评分冲突，规则引擎应该听谁的？为什么需要置信度？",
    acc_b="3条规则+置信度融合输出，决策理由可解释", acc_c="2条规则生效，能输出决策结果",
    steps=[
        "定义设备状态特征（温度/振动/电流）",
        "实现逐条规则评估函数（返回是否触发+置信度）",
        "多规则加权融合，输出最终决策与理由",
        "构造冲突场景验证决策逻辑",
    ],
    starters=[
        ("RULES = [", '''# -*- coding: utf-8 -*-
"""M5-1 智能决策 starter：把"拍脑袋"变成"可解释的规则引擎"

运行: python m51_starter.py
"""
RULES = []          # TODO-A5-1: 每条规则 = dict(name, cond(fn)->bool, weight, reason)
'''),
        ("def eval_rules(feats):", '''def eval_rules(feats):
    """TODO-A5-2: 逐条评估规则, 返回触发的 [(名称, 置信度, 理由)]"""
    fired = []
    # 置信度建议: 超限幅度越大置信度越高, 用 min(1.0, 超限量/阈值) 之类
    return fired
'''),
        ("def decide(feats):", '''def decide(feats):
    """TODO-A5-3: 融合触发规则(加权), 输出 (决策动作, 置信度, 理由列表)"""
    # 动作建议: 正常 / 关注 / 检修 / 停机
    return "正常", 0.0, []
'''),
        ('if __name__ == "__main__":', '''if __name__ == "__main__":
    # TODO-A5-4: 构造正常/高温/高温+高振动(冲突) 三组特征验证
    pass
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
def eval_rules(feats, rules):
    fired = []
    for r in rules:
        if r["cond"](feats):
            over = r["over"](feats)                      # 超限程度0~1
            fired.append((r["name"], round(min(1.0, over), 2), r["reason"]))
    return fired

def decide(feats, rules):
    fired = eval_rules(feats, rules)
    if not fired:
        return "正常", 0.5, ["所有指标在阈值内"]
    score = sum(c * w for (_, c, _), w in
                zip(fired, [r["weight"] for r in rules if r["name"] in [f[0] for f in fired]]))
    score = min(1.0, score)
    if score >= 0.8: action = "停机检修"
    elif score >= 0.5: action = "安排检修"
    elif score >= 0.3: action = "关注"
    else: action = "正常"
    return action, round(score, 2), [f"{n}(置信{c}) {rs}" for n, c, rs in fired]

RULES = [
    dict(name="高温", weight=0.6, reason="温度>75℃",
         cond=lambda f: f["temp"] > 75, over=lambda f: (f["temp"]-75)/25),
    dict(name="高振动", weight=0.6, reason="振动>8mm/s",
         cond=lambda f: f["vib"] > 8, over=lambda f: (f["vib"]-8)/4),
    dict(name="过流", weight=0.4, reason="电流>1.2倍额定",
         cond=lambda f: f["amp"] > 12, over=lambda f: (f["amp"]-12)/6),
]

if True:  # 验证
    cases = {
        "正常":   dict(temp=60, vib=4.0, amp=9),
        "高温":   dict(temp=85, vib=4.0, amp=9),
        "冲突叠加": dict(temp=90, vib=10, amp=15),
    }
    for tag, f in cases.items():
        a, s, rs = decide(f, RULES)
        print(f"{tag}: {a} 置信={s} 依据={rs}")
    assert decide(cases["冲突叠加"], RULES)[0] == "停机检修"
    assert decide(cases["正常"], RULES)[0] == "正常"
    print("M5-1 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="a6_m52", title="M5-2《模型效果对比与选型报告》", week="第18周",
    predict="准确率高的模型一定更好吗？还要看哪些指标？",
    acc_b="3个模型对比+混淆矩阵，选型结论有数据支撑", acc_c="2个模型对比，能算出准确率",
    steps=[
        "合成二分类数据（设备正常/异常）",
        "实现两个基线模型（规则版与统计版）",
        "计算准确率/召回率，输出混淆矩阵",
        "写选型结论（模型卡片）",
    ],
    starters=[
        ("def make_data(n=400, seed=7):", '''# -*- coding: utf-8 -*-
"""M5-2 模型对比 starter：不用深度学习也能做严肃的模型选型

运行: python m52_starter.py
"""
import numpy as np


def make_data(n=400, seed=7):
    """TODO-A6-1: 合成 (特征, 标签) 数据, 异常约占30%"""
    rng = np.random.RandomState(seed)
    # 特征: temp, vib ; 异常设备 temp/vib 偏高
    return X, y
'''),
        ("def model_rule(X):", '''def model_rule(X):
    """TODO-A6-2: 规则模型——温度或振动超阈值判异常"""
    return np.zeros(len(X))          # 返回0/1预测
'''),
        ("def model_score(X):", '''def model_score(X):
    """TODO-A6-3: 评分模型——z分数标准化后加权求和超阈值判异常"""
    return np.zeros(len(X))
'''),
        ("def evaluate(y, pred):", '''def evaluate(y, pred):
    """TODO-A6-4: 返回 (准确率, 召回率, 混淆矩阵[[TN,FP],[FN,TP]])"""
    return 0.0, 0.0, np.zeros((2, 2), dtype=int)
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import numpy as np

def make_data(n=400, seed=7):
    rng = np.random.RandomState(seed)
    n_bad = int(n * 0.3)
    X_ok = np.c_[rng.normal(60, 5, n - n_bad), rng.normal(4, 1, n - n_bad)]
    X_bad = np.c_[rng.normal(85, 6, n_bad), rng.normal(9, 1.5, n_bad)]
    X = np.vstack([X_ok, X_bad])
    y = np.r_[np.zeros(n - n_bad, dtype=int), np.ones(n_bad, dtype=int)]
    rng.shuffle  # noqa
    idx = rng.permutation(n)
    return X[idx], y[idx]

def model_rule(X):
    return ((X[:, 0] > 75) | (X[:, 1] > 7)).astype(int)

def model_score(X):
    z = (X - X.mean(0)) / X.std(0)
    return (z.sum(1) > 1.0).astype(int)

def evaluate(y, pred):
    tp = int(((y == 1) & (pred == 1)).sum()); fn = int(((y == 1) & (pred == 0)).sum())
    tn = int(((y == 0) & (pred == 0)).sum()); fp = int(((y == 0) & (pred == 1)).sum())
    acc = (tp + tn) / len(y)
    rec = tp / max(1, tp + fn)
    return acc, rec, np.array([[tn, fp], [fn, tp]])

if True:  # 验证
    X, y = make_data()
    print(f"数据: {len(X)}条, 异常占比 {y.mean():.0%}")
    best = None
    for name, pred in [("规则模型", model_rule(X)), ("评分模型", model_score(X))]:
        acc, rec, cm = evaluate(y, pred)
        print(f"{name}: acc={acc:.3f} rec={rec:.3f}\\n混淆矩阵[[TN,FP],[FN,TP]]:\\n{cm}")
        if best is None or acc > best[1]: best = (name, acc, rec)
    print(f"选型结论: 优先{best[0]} (acc={best[1]:.3f}, rec={best[2]:.3f})")
    assert best[1] > 0.85
    print("M5-2 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="a7_m61", title="M6-1《模型部署：从函数到推理服务接口》", week="第19周",
    predict="训练好的模型怎么让别的程序用到它？接口应该传什么、返回什么？",
    acc_b="实现 predict 接口函数+JSON输入输出+异常处理", acc_c="实现 predict 函数，正常输入能出结果",
    steps=[
        "加载/复用 M5-2 的异常判定逻辑作为模型",
        "实现 predict(payload) 接口：JSON进、JSON出",
        "输入校验与异常兜底（缺字段/类型错）",
        "模拟三次调用验证（正常/缺字段/非法值）",
    ],
    starters=[
        ("def load_model():", '''# -*- coding: utf-8 -*-
"""M6-1 模型部署 starter：把模型包成可调用的推理接口

运行: python m61_starter.py
"""
import json


def load_model():
    """TODO-A7-1: 返回一个 predict 用的模型对象/闭包(阈值等)"""
    return {"temp_thr": 75, "vib_thr": 7}
'''),
        ("def predict(payload):", '''def predict(payload, model=None):
    """TODO-A7-2: payload={"temp":..,"vib":..} -> {"label":..,"prob":..}
    异常时返回 {"error": "原因"}，不要抛出未捕获异常"""
    return {"label": 0, "prob": 0.0}
'''),
        ("def batch_predict(payloads):", '''def batch_predict(payloads, model=None):
    """TODO-A7-3: 批量接口——循环调用单条接口"""
    return []
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import json

def load_model():
    return {"temp_thr": 75.0, "vib_thr": 7.0}

def predict(payload, model=None):
    model = model or load_model()
    try:
        temp = float(payload["temp"]); vib = float(payload["vib"])
    except KeyError as e:
        return {"error": f"缺少字段 {e}"}
    except (TypeError, ValueError):
        return {"error": "字段类型应为数值"}
    if not (0 < temp < 200 and 0 <= vib < 50):
        return {"error": "数值超出物理范围"}
    risk = min(1.0, max(0.0, (temp - 60) / 40 * 0.6 + (vib - 4) / 6 * 0.6))
    label = 1 if (temp > model["temp_thr"] or vib > model["vib_thr"]) else 0
    return {"label": label, "prob": round(risk, 3)}

def batch_predict(payloads, model=None):
    return [predict(p, model) for p in payloads]

if True:  # 验证（模拟三次调用）
    m = load_model()
    print(json.dumps(predict({"temp": 90, "vib": 9}, m), ensure_ascii=False))
    print(json.dumps(predict({"temp": "abc"}, m), ensure_ascii=False))
    print(json.dumps(predict({"temp": 999, "vib": 2}, m), ensure_ascii=False))
    r = batch_predict([{"temp": 60, "vib": 3}, {"temp": 88, "vib": 8}], m)
    assert r[0]["label"] == 0 and r[1]["label"] == 1
    assert "error" in predict({"temp": "abc"}, m)
    print("M6-1 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="a8_m62", title="M6-2《A/B 对比实验：新旧策略谁更优》", week="第20周",
    predict="新旧两种告警策略各跑一周，怎么判断新策略真的更好？",
    acc_b="两组对比+均值差与简单显著性判断，结论含业务解读", acc_c="能计算两组均值并比较大小",
    steps=[
        "模拟新旧策略各30天的告警数据",
        "计算两组均值与差值",
        "用重排检验(permutation)判断差异是否显著",
        "输出实验结论卡片",
    ],
    starters=[
        ("def simulate(policy, days=30):", '''# -*- coding: utf-8 -*-
"""M6-2 A/B 实验 starter：让数据说话，而不是"感觉新策略好"

运行: python m62_starter.py
"""
import numpy as np


def simulate(policy, days=30, seed=0):
    """TODO-A8-1: policy in {"old","new"} -> 每日误报率数组"""
    return np.zeros(days)
'''),
        ("def perm_test(a, b, n=2000):", '''def perm_test(a, b, n=2000):
    """TODO-A8-2: 重排检验——返回 p 值(两组均值差 ≥ 观测差 的比例)"""
    return 1.0
'''),
        ("def report(a, b):", '''def report(a, b):
    """TODO-A8-3: 输出对比结论(均值差+p值+是否采纳新策略)"""
    pass
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import numpy as np

def simulate(policy, days=30, seed=0):
    rng = np.random.RandomState(seed + (0 if policy == "old" else 100))
    base = 0.20 if policy == "old" else 0.12
    return rng.normal(base, 0.03, days).clip(0, 1)

def perm_test(a, b, n=2000):
    obs = a.mean() - b.mean()
    pooled = np.r_[a, b]
    rng = np.random.RandomState(42)
    cnt = 0
    for _ in range(n):
        rng.shuffle(pooled)
        d = pooled[:len(a)].mean() - pooled[len(a):].mean()
        if d >= obs: cnt += 1
    return cnt / n

def report(a, b):
    diff = a.mean() - b.mean()
    p = perm_test(a, b)
    adopt = bool(p < 0.05 and diff > 0)
    print(f"旧策略误报率均值={a.mean():.3f} 新策略={b.mean():.3f} 差={diff:.3f} p={p:.4f}")
    print("结论:", "采纳新策略(显著降低误报)" if adopt else "暂不采纳(差异不显著或方向相反)")
    return adopt

if True:  # 验证
    a = simulate("old"); b = simulate("new")
    assert report(a, b) is True
    print("M6-2 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="a9_m71", title="M7-1《多智能体协作：调度员与工程师》", week="第21周",
    predict="两个AI智能体各自只会一部分技能，怎么让它们合作完成一个工单？",
    acc_b="两个角色智能体+任务传递协议，端到端完成模拟工单", acc_c="单个智能体按技能表完成任务",
    steps=[
        "定义技能表（每个智能体具备的能力与耗时）",
        "实现调度员智能体：按工单类型分派",
        "实现工程师智能体：执行技能并回执",
        "端到端跑通3张不同类型工单",
    ],
    starters=[
        ("SKILLS = {", '''# -*- coding: utf-8 -*-
"""M7-1 多智能体协作 starter（campus_skills 思路的工业版）

运行: python m71_starter.py
"""
SKILLS = {
    # TODO-A9-1: "巡检": {"agent": "engineer_a", "cost_min": 20}, ...
}
'''),
        ("class Dispatcher:", '''class Dispatcher:
    """TODO-A9-2: 调度员——按工单所需技能选择智能体并派单"""
    def dispatch(self, ticket):
        return {"agent": None, "ticket": ticket}
'''),
        ("class Engineer:", '''class Engineer:
    """TODO-A9-3: 工程师——执行技能返回回执 {done, report, minutes}"""
    def execute(self, plan):
        return {"done": False, "report": "", "minutes": 0}
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
SKILLS = {
    "巡检":   {"agent": "engineer_a", "cost_min": 20},
    "诊断":   {"agent": "engineer_a", "cost_min": 40},
    "维修":   {"agent": "engineer_b", "cost_min": 60},
    "报告":   {"agent": "engineer_b", "cost_min": 15},
}

class Dispatcher:
    def dispatch(self, ticket):
        need = ticket["type"]
        if need not in SKILLS:
            return {"agent": None, "ticket": ticket, "error": "无对应技能"}
        return {"agent": SKILLS[need]["agent"], "ticket": ticket,
                "cost_min": SKILLS[need]["cost_min"]}

class Engineer:
    def __init__(self, name):
        self.name = name
    def execute(self, plan):
        if plan.get("error"):
            return {"done": False, "report": plan["error"], "minutes": 0}
        return {"done": True,
                "report": f"{self.name} 完成{plan['ticket']['type']}工单#{plan['ticket']['id']}",
                "minutes": plan["cost_min"]}

if True:  # 验证：端到端3张工单
    disp, total = Dispatcher(), 0
    for t in [dict(id=1, type="巡检"), dict(id=2, type="维修"), dict(id=3, type="翻译")]:
        plan = disp.dispatch(t)
        eng = Engineer(plan.get("agent") or "none")
        rec = eng.execute(plan)
        total += rec["minutes"]
        print(rec["report"], f"(耗时{rec['minutes']}min)")
        if t["type"] != "翻译":
            assert rec["done"]
    print(f"总耗时 {total}min")
    print("M7-1 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="a10_m72", title="M7-2《提示词工程进阶：结构化输出》", week="第22周",
    predict="让大模型输出JSON而不是一段话，提示词应该怎么写？",
    acc_b="构造结构化Prompt+解析校验函数，非法输出可重试", acc_c="能写出带格式要求的提示词并解析一次输出",
    steps=[
        "理解结构化提示词四要素（角色/任务/格式/示例）",
        "编写模板函数 build_prompt()",
        "实现 parse_output()：JSON解析+字段校验",
        "用离线样例输出验证解析与重试逻辑",
    ],
    starters=[
        ("def build_prompt(text):", '''# -*- coding: utf-8 -*-
"""M7-2 提示词工程 starter：让大模型"听话"地输出JSON

运行: python m72_starter.py（离线版：不联网，用样例输出验证解析）
"""

def build_prompt(text):
    """TODO-A10-1: 返回结构化提示词——角色+任务+JSON格式要求+示例"""
    return ""
'''),
        ("def parse_output(raw):", '''import json

def parse_output(raw, retry=2):
    """TODO-A10-2: 解析模型输出为 dict{label, reason}; 失败返回 None
    raw 可能夹带 ```json 代码块围栏"""
    return None
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import json, re

def build_prompt(text):
    return (
        "你是工厂设备质检员。对下面的巡检记录判断设备状态。\\n"
        '只输出JSON: {"label": "正常|警告|故障", "reason": "一句话依据"}\\n'
        '示例: {"label": "警告", "reason": "温度连续3小时高于阈值"}\\n'
        f"记录: {text}"
    )

def parse_output(raw, retry=2):
    for _ in range(retry + 1):
        m = re.search(r"\\{.*\\}", raw, re.S)
        if m:
            try:
                d = json.loads(m.group())
                if d.get("label") in ("正常", "警告", "故障") and d.get("reason"):
                    return d
            except (json.JSONDecodeError, AttributeError):
                pass
        # 模拟重试: 剥掉围栏再试一次
        raw = raw.replace("```json", "").replace("```", "")
        retry -= 1
        if retry < 0:
            break
    return None

if True:  # 验证
    print(build_prompt("3号泵温度78℃")[:40], "...")
    ok = parse_output('```json\\n{"label": "故障", "reason": "振动超标2倍"}\\n```')
    bad = parse_output("模型抽风输出：我觉得应该是故障吧")
    assert ok == {"label": "故障", "reason": "振动超标2倍"}, ok
    assert bad is None
    print("解析:", ok, "| 非法输出正确返回None")
    print("M7-2 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="a11_m81", title="M8-1《生产巡检流水线：把前面所有模块串起来》", week="第23周",
    predict="清洗→特征→决策→报告四个环节，数据在环节之间怎么流动？",
    acc_b="四环节流水线+异常数据不中断，输出汇总报告", acc_c="流水线跑通，能输出每台设备结论",
    steps=[
        "复用 M1 清洗思路过滤脏数据",
        "对干净数据计算特征并调用 M5-1 决策",
        "汇总生成巡检报告（逐台+总体）",
        "注入脏数据验证流水线健壮性",
    ],
    starters=[
        ("def clean(rows):", '''# -*- coding: utf-8 -*-
"""M8-1 生产巡检流水线 starter：一次跑通 数据→特征→决策→报告

运行: python m81_starter.py
"""

def clean(rows):
    """TODO-A11-1: rows=[{dev,temp,vib}...] 过滤缺测/非法 -> 干净列表"""
    return []
'''),
        ("def decide_one(rec):", '''def decide_one(rec):
    """TODO-A11-2: 单台决策 -> {dev, action, score}"""
    return {}
'''),
        ("def pipeline(rows):", '''def pipeline(rows):
    """TODO-A11-3: 串联清洗+决策, 返回 (结果列表, 报告文本)"""
    return [], ""
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
def clean(rows):
    out = []
    for r in rows:
        try:
            t, v = float(r["temp"]), float(r["vib"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 < t < 200 and 0 <= v < 50:
            out.append(dict(dev=r["dev"], temp=t, vib=v))
    return out

def decide_one(rec):
    score = min(1.0, max(0.0, (rec["temp"] - 60) / 40 * 0.6 + (rec["vib"] - 4) / 6 * 0.6))
    action = "停机" if score >= 0.8 else ("检修" if score >= 0.5 else ("关注" if score >= 0.3 else "正常"))
    return dict(dev=rec["dev"], action=action, score=round(score, 2))

def pipeline(rows):
    good = clean(rows)
    results = [decide_one(r) for r in good]
    n_bad = len(rows) - len(good)
    lines = [f"{r['dev']}: {r['action']} (风险{r['score']})" for r in results]
    report = f"共{len(rows)}条, 剔除{n_bad}条脏数据, 有效{len(good)}台\\n" + "\\n".join(lines)
    return results, report

if True:  # 验证
    rows = [
        dict(dev="PUMP-01", temp=62, vib=3.5),
        dict(dev="PUMP-02", temp=88, vib=9.0),
        dict(dev="PUMP-03", temp=None, vib=4),      # 缺测
        dict(dev="PUMP-04", temp="abc", vib=2),     # 类型错
        dict(dev="PUMP-05", temp=75, vib=6.5),
    ]
    res, rep = pipeline(rows)
    print(rep)
    assert len(res) == 3
    assert {r["action"] for r in res} == {"正常", "停机", "关注"}
    print("M8-1 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="a12_z2", title="Z2《AI应用进阶答辩：模型卡片与复现实操》", week="第24周",
    predict="向评委证明你的AI方案可用，最少要展示哪几样东西？",
    acc_b="模型卡片+可复现脚本+答辩三分钟讲稿提纲", acc_c="完成模型卡片模板各字段",
    steps=[
        "整理模型卡片（数据/指标/边界/负责人）",
        "准备一键复现脚本入口（跑通即验证）",
        "撰写3分钟答辩讲稿提纲",
        "自检清单核对（8项）",
    ],
    starters=[
        ("MODEL_CARD = {", '''# -*- coding: utf-8 -*-
"""Z2 答辩材料 starter：模型卡片 + 复现入口

运行: python z2_starter.py（完成TODO后应能一键自检通过）
"""
MODEL_CARD = {
    # TODO-A12-1: task/data/metrics/limits/owner 五个字段
}
'''),
        ("def self_check():", '''def self_check():
    """TODO-A12-2: 自检清单——卡片字段齐全 + 指标达标, 返回bool并打印缺项"""
    return False
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
MODEL_CARD = {
    "task": "泵类设备异常检测",
    "data": "400条合成巡检记录(异常30%)",
    "metrics": {"accuracy": 0.95, "recall": 0.92},
    "limits": "仅适用离心泵常温工况; 未覆盖传感器漂移",
    "owner": "第X组",
}

def self_check():
    missing = [k for k in ("task", "data", "metrics", "limits", "owner") if not MODEL_CARD.get(k)]
    m = MODEL_CARD.get("metrics", {})
    ok_metric = m.get("accuracy", 0) >= 0.85 and m.get("recall", 0) >= 0.85
    print("卡片缺项:", missing or "无")
    print("指标达标:", ok_metric)
    return not missing and ok_metric

if True:  # 验证
    assert self_check() is True
    print("Z2 自检通过 ✓ —— 答辩可讲: 任务→数据→指标→边界→分工")
''',
))

# ====================================================================
# B 系（Python编程基础） B7~B12 —— W13~W24 进阶延伸
# ====================================================================

WORKSHEETS.append(dict(
    key="b7_w13", title="1.6《设备台账入库：SQLite 基础》", week="第13周",
    predict="数据存内存里程序一关就没了，怎么让它持久保存还能按条件查询？",
    acc_b="建表+插入5条+条件查询+更新状态，SQL无注入拼接", acc_c="建表+插入+查询全表",
    steps=[
        "用 sqlite3 建设备台账表 devices",
        "插入5条设备记录（参数化SQL）",
        "查询：全部 / 按状态筛选",
        "更新一台设备状态并验证",
    ],
    starters=[
        ("def init_db(path):", '''# -*- coding: utf-8 -*-
"""W13 设备台账入库 starter：程序关了数据还在

运行: python w13_starter.py
"""
import sqlite3


def init_db(path=":memory:"):
    """TODO-B7-1: 建表 devices(id TEXT PRIMARY KEY, name TEXT, status TEXT, temp REAL)"""
    conn = sqlite3.connect(path)
    return conn
'''),
        ("def insert_devices(conn, rows):", '''def insert_devices(conn, rows):
    """TODO-B7-2: 参数化插入 [{id,name,status,temp}]"""
    pass
'''),
        ("def query(conn, status=None):", '''def query(conn, status=None):
    """TODO-B7-3: status=None查全部, 否则按状态筛; 返回list[tuple]"""
    return []
'''),
        ("def update_status(conn, dev_id, status):", '''def update_status(conn, dev_id, status):
    """TODO-B7-4: 更新设备状态, 返回影响行数"""
    return 0
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import sqlite3

def init_db(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE devices (id TEXT PRIMARY KEY, name TEXT, status TEXT, temp REAL)")
    return conn

def insert_devices(conn, rows):
    conn.executemany("INSERT INTO devices VALUES (?,?,?,?)",
                     [(r["id"], r["name"], r["status"], r["temp"]) for r in rows])
    conn.commit()

def query(conn, status=None):
    if status is None:
        return conn.execute("SELECT * FROM devices").fetchall()
    return conn.execute("SELECT * FROM devices WHERE status=?", (status,)).fetchall()

def update_status(conn, dev_id, status):
    cur = conn.execute("UPDATE devices SET status=? WHERE id=?", (status, dev_id))
    conn.commit()
    return cur.rowcount

if True:  # 验证
    conn = init_db()
    insert_devices(conn, [
        dict(id="DEV-01", name="空压机", status="运行", temp=62.5),
        dict(id="DEV-02", name="冷却泵", status="停止", temp=23.0),
        dict(id="DEV-03", name="注塑机", status="运行", temp=71.2),
        dict(id="DEV-04", name="风机", status="运行", temp=45.8),
        dict(id="DEV-05", name="传送带", status="停止", temp=20.1),
    ])
    assert len(query(conn)) == 5
    run = query(conn, "运行")
    assert len(run) == 3 and run[0][0] == "DEV-01"
    assert update_status(conn, "DEV-02", "运行") == 1
    assert len(query(conn, "运行")) == 4
    print("W13 参考实现验证通过 ✓")''',
))

WORKSHEETS.append(dict(
    key="b8_w14", title="1.7《多线程采集模拟：queue 与 Thread》", week="第14周",
    predict="一个线程读传感器、一个线程写日志，它们怎么安全地传数据？",
    acc_b="2生产者1消费者+queue.Queue，收发条数一致", acc_c="1生产者1消费者跑通不丢数据",
    steps=[
        "理解生产者-消费者模型与线程安全队列",
        "实现传感器线程：产生读数放入队列",
        "实现日志线程：从队列取出写列表",
        "join 等待并核对收发条数",
    ],
    starters=[
        ("def producer(q, n, name):", '''# -*- coding: utf-8 -*-
"""W14 多线程采集 starter：queue.Queue 是线程安全的"传送带"

运行: python w14_starter.py
"""
import queue, threading


def producer(q, n, name):
    """TODO-B8-1: 放入 n 条 {"dev":name,"val":随机} , 最后放 None 哨兵"""
    pass
'''),
        ("def consumer(q, out, n_producers=2):", '''def consumer(q, out, n_producers=2):
    """TODO-B8-2: 循环取数据追加到 out; 每个生产者结束会放一个None, 收满 n_producers 个才结束"""
    pass
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import queue, threading, random

def producer(q, n, name):
    for _ in range(n):
        q.put(dict(dev=name, val=round(random.uniform(20, 90), 1)))
    q.put(None)

def consumer(q, out, n_producers=2):
    done = 0
    while done < n_producers:
        item = q.get()
        if item is None:
            done += 1
            continue
        out.append(item)

if True:  # 验证
    q = queue.Queue()
    log = []
    threads = [threading.Thread(target=producer, args=(q, 50, f"DEV-{i:02d}")) for i in range(2)]
    threads.append(threading.Thread(target=consumer, args=(q, log, 2)))
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(log) == 100, len(log)
    devs = {r["dev"] for r in log}
    assert devs == {"DEV-00", "DEV-01"}
    print(f"W14 参考实现验证通过 ✓ 收到{len(log)}条 来自{devs}")''',
))

WORKSHEETS.append(dict(
    key="b9_w15", title="1.8《单元测试入门：unittest 守护代码》", week="第15周",
    predict="改完代码怎么保证没把原来的功能改坏？测试写在哪里最省心？",
    acc_b="被测模块+≥6个断言测试，含1个异常用例", acc_c="≥3个断言测试全部通过",
    steps=[
        "编写被测函数 c_to_f / classify_temp",
        "用 unittest 写正常用例与边界用例",
        "增加异常路径用例（assertRaises）",
        "运行测试并输出绿条",
    ],
    starters=[
        ("def c_to_f(c):", '''# -*- coding: utf-8 -*-
"""W15 单元测试 starter：测试不是负担，是"改代码的保险"

运行: python w15_starter.py
"""

def c_to_f(c):
    """TODO-B9-1: 摄氏转华氏 F=C*9/5+32; 低于-273.15 抛 ValueError"""
    return 0.0
'''),
        ("def classify_temp(c):", '''def classify_temp(c):
    """TODO-B9-2: <40 低温 / 40~80 正常 / >80 高温"""
    return ""
'''),
        ("class TestW15(unittest.TestCase):", '''import unittest

class TestW15(unittest.TestCase):
    def test_c_to_f(self):
        # TODO-B9-3: 100->212, 0->32, 以及非法输入 assertRaises
        pass

    def test_classify(self):
        # TODO-B9-4: 三个区段 + 边界值 40/80
        pass
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import unittest

def c_to_f(c):
    if c < -273.15:
        raise ValueError("低于绝对零度")
    return c * 9 / 5 + 32

def classify_temp(c):
    if c < 40: return "低温"
    if c <= 80: return "正常"
    return "高温"

class TestW15(unittest.TestCase):
    def test_c_tof_normal(self):
        self.assertAlmostEqual(c_to_f(100), 212.0)
        self.assertAlmostEqual(c_to_f(0), 32.0)
    def test_c_to_f_boundary(self):
        self.assertAlmostEqual(c_to_f(-273.15), -459.67)
    def test_c_to_f_invalid(self):
        with self.assertRaises(ValueError):
            c_to_f(-300)
    def test_classify_segments(self):
        self.assertEqual(classify_temp(10), "低温")
        self.assertEqual(classify_temp(60), "正常")
        self.assertEqual(classify_temp(95), "高温")
    def test_classify_edges(self):
        self.assertEqual(classify_temp(40), "正常")
        self.assertEqual(classify_temp(80), "正常")
    def test_classify_invalid_type(self):
        with self.assertRaises(TypeError):
            classify_temp("hot")

if True:  # 验证
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestW15)
    res = unittest.TextTestRunner(verbosity=0).run(suite)
    assert res.wasSuccessful() and res.testsRun == 6
    print(f"W15 参考实现验证通过 ✓ {res.testsRun}个用例全绿")''',
))

WORKSHEETS.append(dict(
    key="b10_w16", title="1.9《日志与正则：从报错文本提取关键信息》", week="第16周",
    predict="一段上千行的设备日志，怎么只把 ERROR 行和时间戳捞出来？",
    acc_b="正则提取时间戳+ERROR行，汇总成结构化列表", acc_c="能按关键字过滤出错误行",
    steps=[
        "生成模拟日志（INFO/WARN/ERROR 混合）",
        "用正则提取 [时间戳] [级别] 消息",
        "统计各级别条数、ERROR 去重原因",
        "输出巡检摘要",
    ],
    starters=[
        ("def gen_log(n=50):", '''# -*- coding: utf-8 -*-
"""W10 日志与正则 starter：re 是日志处理的瑞士军刀

运行: python w16_starter.py
"""
import re, random, datetime


def gen_log(n=50):
    """TODO-B10-1: 生成 n 行 '[2026-03-01 08:00:00] LEVEL 消息'"""
    return []
'''),
        ("def parse_line(line):", '''LINE_RE = None   # TODO-B10-2: 编译正则 r"\\[(.+?)\\] (\\w+) (.+)"

def parse_line(line):
    """TODO-B10-3: 解析一行 -> (ts, level, msg) 或 None"""
    return None
'''),
        ("def summarize(lines):", '''def summarize(lines):
    """TODO-B10-4: 返回 {各级别条数}, ERROR原因去重列表"""
    return {}, []
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import re, random, datetime

LEVELS = ["INFO", "INFO", "INFO", "WARN", "ERROR"]
MSGS = {"INFO": "采样正常", "WARN": "温度接近阈值", "ERROR": "PLC连接超时"}

def gen_log(n=50):
    out, base = [], datetime.datetime(2026, 3, 1, 8, 0, 0)
    for i in range(n):
        lv = random.choice(LEVELS)
        ts = (base + datetime.timedelta(seconds=i * 10)).strftime("%Y-%m-%d %H:%M:%S")
        out.append(f"[{ts}] {lv} {MSGS[lv]}")
    return out

LINE_RE = re.compile(r"\\[(.+?)\\] (\\w+) (.+)")

def parse_line(line):
    m = LINE_RE.match(line)
    return (m.group(1), m.group(2), m.group(3)) if m else None

def summarize(lines):
    counts, errors = {}, set()
    for ln in lines:
        p = parse_line(ln)
        if not p: continue
        _, lv, msg = p
        counts[lv] = counts.get(lv, 0) + 1
        if lv == "ERROR": errors.add(msg)
    return counts, sorted(errors)

if True:  # 验证
    logs = gen_log(50)
    counts, errs = summarize(logs)
    assert sum(counts.values()) == 50
    assert "ERROR" in counts and errs == ["PLC连接超时"]
    assert parse_line("坏行") is None
    print(f"W16 参考实现验证通过 ✓ 级别分布={counts} 错误原因={errs}")''',
))

WORKSHEETS.append(dict(
    key="b11_w17", title="1.10《生成器与装饰器：让代码更省更优雅》", week="第17周",
    predict="一百万条读数只统计前几条，也要全部加载到内存吗？",
    acc_b="生成器惰性读取+计时装饰器，两者均有测试", acc_c="生成器能逐条产出数据",
    steps=[
        "用生成器逐条产出传感器读数（惰性）",
        "验证生成器不一次性占用内存",
        "实现 @timer 装饰器统计函数耗时",
        "组合：用装饰过的函数消费生成器",
    ],
    starters=[
        ("def read_sensors(total):", '''# -*- coding: utf-8 -*-
"""W17 生成器与装饰器 starter：yield 一条处理一条，内存只占一条

运行: python w17_starter.py
"""

def read_sensors(total):
    """TODO-B11-1: yield 逐条产出 {"seq":i,"val":随机}"""
    yield
'''),
        ("def timer(fn):", '''def timer(fn):
    """TODO-B11-2: 装饰器——打印函数耗时, 保留返回值"""
    def inner(*a, **kw):
        return fn(*a, **kw)
    return inner
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import time, random, functools

def read_sensors(total):
    for i in range(total):
        yield dict(seq=i, val=round(random.uniform(20, 90), 1))

def timer(fn):
    @functools.wraps(fn)
    def inner(*a, **kw):
        t0 = time.perf_counter()
        r = fn(*a, **kw)
        print(f"{fn.__name__} 耗时 {time.perf_counter()-t0:.4f}s")
        return r
    return inner

@timer
def consume(gen, limit=5):
    taken = []
    for item in gen:
        taken.append(item)
        if len(taken) >= limit:
            break
    return taken

if True:  # 验证
    g = read_sensors(1_000_000)      # 不会卡住——惰性
    got = consume(g, 5)
    assert len(got) == 5 and got[0]["seq"] == 0
    import types
    assert isinstance(read_sensors(3), types.GeneratorType)
    print(f"W17 参考实现验证通过 ✓ 惰性取5条: {got[0]}...{got[-1]}")''',
))

WORKSHEETS.append(dict(
    key="b12_w18", title="1.11《阶段收官：台账-采集-测试-日志 迷你系统》", week="第18周",
    predict="把 W13~W17 四个能力拼成一个迷你系统，先从哪个模块写起？",
    acc_b="四模块联动跑通+5个unittest全绿+摘要报告", acc_c="入库+查询两个模块跑通",
    steps=[
        "模块A：采集数据入库（复用 W13/W14 思路）",
        "模块B：正则解析日志并统计（复用 W16）",
        "模块C：unittest 守护核心函数（复用 W15）",
        "输出运行摘要并跑测试",
    ],
    starters=[
        ("def collect_and_store(conn, devs):", '''# -*- coding: utf-8 -*-
"""W18 阶段收官 starter：W13~W17 能力拼装

运行: python w18_starter.py
"""
import sqlite3


def collect_and_store(conn, devs):
    """TODO-B12-1: devs=[(id,name,temp)] 参数化入库"""
    pass
'''),
        ("def hot_devices(conn, thr):", '''def hot_devices(conn, thr):
    """TODO-B12-2: 查询温度>thr 的设备, 返回list[tuple]"""
    return []
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import sqlite3

def collect_and_store(conn, devs):
    conn.execute("CREATE TABLE IF NOT EXISTS t (id TEXT PRIMARY KEY, name TEXT, temp REAL)")
    conn.executemany("INSERT OR REPLACE INTO t VALUES (?,?,?)", devs)
    conn.commit()

def hot_devices(conn, thr):
    return conn.execute("SELECT id, name, temp FROM t WHERE temp > ? ORDER BY temp DESC", (thr,)).fetchall()

if True:  # 验证
    conn = sqlite3.connect(":memory:")
    collect_and_store(conn, [("D1", "空压机", 72.5), ("D2", "冷却泵", 41.0), ("D3", "注塑机", 88.3)])
    hot = hot_devices(conn, 60)
    assert [h[0] for h in hot] == ["D3", "D1"]
    # 模块C: 内联unittest
    import unittest
    class T(unittest.TestCase):
        def test_hot(self):
            c = sqlite3.connect(":memory:")
            collect_and_store(c, [("X", "测试", 99.0)])
            self.assertEqual(len(hot_devices(c, 0)), 1)
        def test_empty(self):
            c = sqlite3.connect(":memory:")
            c.execute("CREATE TABLE IF NOT EXISTS t (id TEXT, name TEXT, temp REAL)")
            self.assertEqual(hot_devices(c, 60), [])
    r = unittest.TextTestRunner(verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T))
    assert r.wasSuccessful()
    print(f"W18 参考实现验证通过 ✓ 高温设备: {hot}")''',
))

# ====================================================================
# P 系（项目实战） P7~P8
# ====================================================================

WORKSHEETS.append(dict(
    key="p7_p77", title="工单P7《智能运维平台综合项目：五库一体·核心链路》", week="第9周(扩展·选做4课时)",
    predict="关系库/时序库/图库/向量库/缓存各管一摊，它们的数据怎么保持一致？",
    acc_b="3个存储引擎跑通+统一门面+健康检查，verify自检通过", acc_c="台账库+预测接口跑通",
    steps=[
        "实现关系存储（SQLite 台账+WAL模式）",
        "实现时序存储（降级方案：SQLite时序表，思路对齐DuckDB）",
        "实现规则版预测引擎（对标机器学习接口）与运维智能体问答",
        "统一服务门面 + /health 自检（verify 思路）",
    ],
    starters=[
        ("class RelationalStore:", '''# -*- coding: utf-8 -*-
"""P7 智能运维平台 starter（对标 p77_smart_ops 包：stores/agent/service 精简单文件版）

运行: python p77_starter.py
"""
import sqlite3, time, hashlib


class RelationalStore:
    """TODO-P7-1: 设备台账 (SQLite, journal_mode=WAL)"""
    def __init__(self, path="ops.db"):
        pass
    def upsert(self, dev_id, name, status):
        pass
    def get(self, dev_id):
        return None
'''),
        ("class TimeseriesStore:", '''class TimeseriesStore:
    """TODO-P7-2: 读数追加与最近N条 (思路对标DuckDB时序表, SQLite降级实现)"""
    def append(self, dev_id, temp, vib, ts=None):
        pass
    def latest(self, dev_id, n=5):
        return []
'''),
        ("class RulePredictor:", '''class RulePredictor:
    """TODO-P7-3: predict(dev_id)->{"label":0/1,"risk":0~1} 阈值规则版(对标模型接口)"""
    def predict(self, dev_id, temp, vib):
        return {"label": 0, "risk": 0.0}
'''),
        ("class OpsAgent:", '''class OpsAgent:
    """TODO-P7-4: ask(dev_id)->运维建议 (规则版"工程师", 对标 agent/engineer.py)"""
    def ask(self, dev_id, temp, vib):
        return ""
'''),
        ("class SmartOpsService:", '''class SmartOpsService:
    """TODO-P7-5: 统一门面 health()/report(dev_id) —— 对标 service/app.py 的 /health /api/report"""
    pass
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
import sqlite3, time

class RelationalStore:
    def __init__(self, path=":memory:"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        try:
            self.conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass                     # 内存库不支持WAL则忽略
        self.conn.execute("CREATE TABLE IF NOT EXISTS devices (id TEXT PRIMARY KEY, name TEXT, status TEXT)")
        self.conn.commit()
    def upsert(self, dev_id, name, status):
        self.conn.execute("INSERT INTO devices VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET name=?, status=?",
                          (dev_id, name, status, name, status))
        self.conn.commit()
    def get(self, dev_id):
        r = self.conn.execute("SELECT id,name,status FROM devices WHERE id=?", (dev_id,)).fetchone()
        return dict(zip(("id", "name", "status"), r)) if r else None

class TimeseriesStore:
    def __init__(self):
        self.rows = {}               # dev_id -> [(ts, temp, vib)]
    def append(self, dev_id, temp, vib, ts=None):
        self.rows.setdefault(dev_id, []).append((ts or time.time(), temp, vib))
    def latest(self, dev_id, n=5):
        return sorted(self.rows.get(dev_id, []))[-n:]

class RulePredictor:
    def predict(self, dev_id, temp, vib):
        risk = min(1.0, max(0.0, (temp - 60) / 40 * 0.6 + (vib - 4) / 6 * 0.6))
        return {"label": 1 if risk >= 0.5 else 0, "risk": round(risk, 2)}

class OpsAgent:
    def ask(self, dev_id, temp, vib):
        p = RulePredictor().predict(dev_id, temp, vib)
        if p["label"] == 1:
            return f"{dev_id} 风险{p['risk']}: 建议安排检修并核查润滑与轴温"
        return f"{dev_id} 风险{p['risk']}: 状态正常, 按计划巡检即可"

class SmartOpsService:
    def __init__(self):
        self.rel, self.ts, self.agent = RelationalStore(), TimeseriesStore(), OpsAgent()
    def health(self):
        return {"relational": "ok", "timeseries": "ok", "predictor": "ok"}
    def report(self, dev_id, temp, vib):
        self.ts.append(dev_id, temp, vib)
        return {"device": dev_id, "predict": RulePredictor().predict(dev_id, temp, vib),
                "advice": self.agent.ask(dev_id, temp, vib),
                "recent": self.ts.latest(dev_id, 3)}

if True:  # 验证（对标 verify.sh 口径：ALL PASS）
    svc = SmartOpsService()
    assert all(v == "ok" for v in svc.health().values())
    svc.rel.upsert("PUMP-03", "3号冷却泵", "运行")
    assert svc.rel.get("PUMP-03")["name"] == "3号冷却泵"
    for t, v in [(62, 3.2), (70, 4.5), (85, 9.0)]:
        rep = svc.report("PUMP-03", t, v)
    assert rep["predict"]["label"] == 1
    assert len(rep["recent"]) == 3
    print(rep["advice"])
    print("P7 参考实现验证通过 ✓ ALL PASS（单文件版，完整五库版见 p77_smart_ops 包）")''',
))

WORKSHEETS.append(dict(
    key="p8_p88", title="工单P8《项目验收与交付：从代码到生产线》", week="第9周(扩展·收官2课时)",
    predict="项目验收时，评委第一个问题往往是'出了问题怎么办'，你的交付物里有没有答案？",
    acc_b="交付清单8项齐全+版本迁移脚本+回滚方案说明", acc_c="交付清单核心5项+验收自检通过",
    steps=[
        "整理交付清单（代码/模型/文档/部署脚本/回滚方案）",
        "实现配置版本迁移函数 migrate(v1→v2)",
        "实现验收自检 acceptance()：逐项核对",
        "模拟回滚：迁移失败时恢复v1配置",
    ],
    starters=[
        ("DELIVERY = {", '''# -*- coding: utf-8 -*-
"""P8 项目验收与交付 starter：会写代码只是开始，能交付才算结束

运行: python p88_starter.py
"""
DELIVERY = {
    # TODO-P8-1: code/model/doc/deploy/rollback 五类交付物路径
}
'''),
        ("def migrate(cfg):", '''def migrate(cfg):
    """TODO-P8-2: v1配置(单阈值) -> v2(分区分阈值); 返回新dict不改旧dict"""
    return {}
'''),
        ("def acceptance():", '''def acceptance():
    """TODO-P8-3: 验收自检——清单齐全+迁移可逆, 每项打印 ✓/✗"""
    return False
'''),
    ],
    solution='''# -*- coding: utf-8 -*-
DELIVERY = {
    "code":    "smart_ops/ (stores+agent+service)",
    "model":   "model_v2.joblib (F1=0.85)",
    "doc":     "README + 部署手册 + 应急预案",
    "deploy":  "docker-compose.yml + smart-ops.service",
    "rollback": "migrate(-1) 恢复v1配置",
}

V1 = {"threshold": 70, "version": 1}
V2 = {"threshold": {"pump": 75, "press": 65}, "version": 2}

def migrate(cfg):
    if cfg.get("version") == 2:
        return cfg
    return {"threshold": {"pump": cfg["threshold"], "press": cfg["threshold"] - 5},
            "version": 2}

def rollback(v2cfg):
    thr = min(v2cfg["threshold"].values()) + 5
    return {"threshold": thr, "version": 1}

def acceptance():
    checks = {
        "交付清单5类齐全": all(DELIVERY.get(k) for k in ("code", "model", "doc", "deploy", "rollback")),
        "迁移v1→v2正确": migrate(V1)["threshold"]["pump"] == 70,
        "迁移幂等": migrate(migrate(V1)) == migrate(V1),
        "回滚恢复v1": rollback(migrate(V1)) == V1,
        "旧配置未被修改": V1 == {"threshold": 70, "version": 1},
    }
    for name, ok in checks.items():
        print(f"{'✓' if ok else '✗'} {name}")
    return all(checks.values())

if True:  # 验证
    assert acceptance() is True
    print("P8 参考实现验证通过 ✓ 交付自检 ALL PASS")''',
))
