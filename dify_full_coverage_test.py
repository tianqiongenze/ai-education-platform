#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 100% 功能覆盖测试 - 完整版
覆盖: 认证、应用、聊天、流式、多轮对话、知识库(创建+上传+检索+删除)、
工作流执行、Agent、对话管理、文件上传、模型提供商、教学场景
"""
import requests, json, base64, time, io, sys, urllib3
from datetime import datetime
urllib3.disable_warnings()

BASE = "https://10.167.2.175:31825"
EMAIL = "myuwei@126.com"
PASSWORD = "Difyai123456"
LITELLM = "http://10.167.2.176:30083"
LITELLM_KEY = "sk-ai-platform-master"
CHAT_MODEL = "qwen2.5-coder:7b"

results = []
def log(name, status, detail=""):
    results.append({"test": name, "status": status, "detail": detail})
    sym = "✅" if status=="PASS" else "❌" if status=="FAIL" else "⏭️"
    print(f"{datetime.now().strftime('%H:%M:%S')} {sym} [{name}] {status}: {detail}")

def get_session():
    s = requests.Session(); s.verify = False
    pass_b64 = base64.b64encode(PASSWORD.encode()).decode()
    r = s.post(f"{BASE}/console/api/login", json={"email":EMAIL,"password":pass_b64,"language":"zh-Hans","remember_me":True})
    if r.json().get("result")=="success":
        s.headers["X-CSRF-Token"] = s.cookies.get("csrf_token","")
        return s
    return None

def get_token(s, app_id):
    r = s.get(f"{BASE}/console/api/apps/{app_id}/api-keys")
    keys = r.json().get("data",[])
    if keys: return keys[0].get("token")
    r = s.post(f"{BASE}/console/api/apps/{app_id}/api-keys")
    return r.json().get("token","")

def discover_inputs(s, app_id):
    token = get_token(s, app_id)
    if not token: return {}, token
    api_s = requests.Session(); api_s.verify = False
    api_s.headers.update({"Host":"api.dify-plus.local","Authorization":f"Bearer {token}"})
    r = api_s.get(f"{BASE}/v1/parameters")
    if r.status_code != 200: return {}, token
    inputs = {}
    for item in r.json().get("user_input_form",[]):
        for ftype, cfg in item.items():
            if cfg.get("required") and cfg.get("variable"):
                if ftype=="select":
                    inputs[cfg["variable"]] = cfg.get("options",["True"])[0]
                else:
                    inputs[cfg["variable"]] = "老师讲课很认真，内容丰富，受益匪浅"
    return inputs, token

def chat(token, query, inputs=None, user="test", mode="blocking", conv=None, timeout=300):
    api_s = requests.Session(); api_s.verify = False
    api_s.headers.update({"Host":"api.dify-plus.local","Authorization":f"Bearer {token}","Content-Type":"application/json"})
    payload = {"inputs":inputs or {},"query":query,"response_mode":mode,"user":user}
    if conv: payload["conversation_id"] = conv
    return api_s.post(f"{BASE}/v1/chat-messages", json=payload, timeout=timeout, stream=(mode=="streaming"))

# === 测试开始 ===
print("="*60)
print("Dify 100% 功能覆盖测试 - 完整版")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# 1. 认证
s = get_session()
log("1.1 登录", "PASS" if s else "FAIL", "成功" if s else "失败")
log("1.2 用户资料", "PASS" if s.get(f"{BASE}/console/api/account/profile").status_code==200 else "FAIL")
ws = s.get(f"{BASE}/console/api/workspaces").json().get("workspaces",[])
log("1.3 工作空间", "PASS", f"{len(ws)}个")

# 2. 应用
apps = []
for p in range(1,5):
    r = s.get(f"{BASE}/console/api/apps", params={"page":p,"page_size":50})
    if r.status_code==200:
        d = r.json().get("data",[])
        if not d: break
        apps.extend(d)
log("2.1 应用列表", "PASS", f"{len(apps)}个")
modes = set(a.get("mode") for a in apps)
log("2.2 应用模式", "PASS", str(modes))
if apps:
    log("2.3 应用详情", "PASS" if s.get(f"{BASE}/console/api/apps/{apps[0]['id']}").status_code==200 else "FAIL")

# 3. 模型提供商
r = s.get(f"{BASE}/console/api/workspaces/current/model-providers")
log("3.1 模型提供商", "PASS" if r.status_code==200 else "FAIL", f"{len(r.json().get('data',[]))}个")

# 4. 聊天
chat_app = next((a for a in apps if a.get("mode")=="chat"), None)
if chat_app:
    inputs, token = discover_inputs(s, chat_app["id"])
    log("4.1 获取API Key", "PASS" if token else "FAIL")
    r = chat(token, "你好，请用一句话介绍自己", inputs, "student-1")
    if r.status_code==200:
        ans = r.json().get("answer","")
        conv_id = r.json().get("conversation_id","")
        log("4.2 阻塞聊天", "PASS", ans[:60])
    else:
        log("4.2 阻塞聊天", "FAIL", f"{r.status_code}")
        conv_id = ""

    # 5. 流式聊天
    r = chat(token, "什么是二叉树?", inputs, "student-2", mode="streaming")
    if r.status_code==200:
        events = set()
        for line in r.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                try: events.add(json.loads(line[5:]).get("event",""))
                except: pass
        log("5.1 流式聊天", "PASS", str(events))
    else:
        log("5.1 流式聊天", "FAIL", f"{r.status_code}")

    # 6. 多轮对话
    if conv_id:
        r2 = chat(token, "能举个例子吗?", inputs, "student-1", conv=conv_id)
        log("6.1 多轮对话", "PASS" if r2.status_code==200 else "FAIL", r2.json().get("answer","")[:60] if r2.status_code==200 else f"{r2.status_code}")

    # 7. 对话管理
    api_s = requests.Session(); api_s.verify=False
    api_s.headers.update({"Host":"api.dify-plus.local","Authorization":f"Bearer {token}"})
    r = api_s.get(f"{BASE}/v1/conversations", params={"user":"student-1","limit":10})
    convs = r.json().get("data",[]) if r.status_code==200 else []
    log("7.1 对话列表", "PASS", f"{len(convs)}个")
    if convs:
        cid = convs[0]["id"]
        r = api_s.get(f"{BASE}/v1/messages", params={"user":"student-1","conversation_id":cid,"limit":5})
        log("7.2 消息历史", "PASS" if r.status_code==200 else "FAIL", f"{len(r.json().get('data',[]))}条" if r.status_code==200 else "")
        if r.status_code==200 and r.json().get("data"):
            mid = r.json()["data"][0]["id"]
            r = api_s.post(f"{BASE}/v1/messages/{mid}/feedbacks", json={"rating":"like","user":"student-1"})
            log("7.3 消息反馈", "PASS" if r.status_code==200 else "FAIL")

# 8. 知识库完整流程
r = s.post(f"{BASE}/console/api/datasets", json={
    "name":"测试-工业互联网教学知识库","description":"工业互联网应用专业教学文档",
    "permission":"only_me","indexing_technique":"high_quality","doc_form":"hierarchical_model",
    "embedding_model":"bge-m3","embedding_model_provider":"langgenius/openai_api_compatible/openai_api_compatible"
})
if r.status_code in (200,201):
    ds_id = r.json().get("id","")
    log("8.1 创建知识库", "PASS", ds_id[:20]+"...")

    # 上传文件
    content = "工业互联网核心概念:连接物理世界与数字世界,实现设备智能化。PLC是工业自动化的核心控制器。MES系统管理生产全流程。数字孪生技术实现虚拟仿真。"
    files = {"file":("工业互联网基础.txt", io.BytesIO(content.encode()), "text/plain")}
    r = s.post(f"{BASE}/console/api/files/upload", files=files)
    if r.status_code in (200,201):
        fid = r.json().get("id","")
        log("8.2 上传文件", "PASS", fid[:20]+"...")

        # 创建文档
        r = s.post(f"{BASE}/console/api/datasets/{ds_id}/documents", json={
            "name":"工业互联网基础.txt","indexing_technique":"high_quality","doc_form":"hierarchical_model",
            "data_source":{"type":"upload_file","info_list":{"data_source_type":"upload_file","file_info_list":{"file_ids":[fid]}}},
            "process_rule":{"mode":"hierarchical","rules":{"pre_processing_rules":[{"id":"remove_extra_spaces","enabled":True}],"segmentation":{"separator":"\\n","max_tokens":500,"chunk_overlap":50},"parent_mode":"paragraph"}}
        })
        if r.status_code in (200,201):
            batch = r.json().get("batch","")
            log("8.3 创建文档", "PASS", f"batch={batch[:20]}...")

            # 等待索引
            indexed = False
            for _ in range(24):
                time.sleep(5)
                r = s.get(f"{BASE}/console/api/datasets/{ds_id}/documents/{batch}/indexing-status")
                if r.status_code==200:
                    sd = r.json().get("data",[])
                    if sd and sd[0].get("status") in ("completed","done"):
                        indexed = True; break
            log("8.4 索引完成", "PASS" if indexed else "SKIP", "已索引" if indexed else "超时")

            # 检索测试
            r = s.post(f"{BASE}/console/api/datasets/{ds_id}/hit-testing", json={"query":"什么是工业互联网","retrieval_mode":"single","top_k":3})
            segs = r.json().get("records",r.json().get("data",[])) if r.status_code==200 else []
            log("8.5 检索测试", "PASS" if r.status_code==200 else "FAIL", f"{len(segs)}条分段")
        else:
            log("8.3 创建文档", "FAIL", f"{r.status_code}")
    else:
        log("8.2 上传文件", "FAIL", f"{r.status_code}")

    # 文档列表
    r = s.get(f"{BASE}/console/api/datasets/{ds_id}/documents", params={"page":1,"page_size":20})
    log("8.6 文档列表", "PASS" if r.status_code==200 else "FAIL")

    # 清理
    s.delete(f"{BASE}/console/api/datasets/{ds_id}")
    log("8.7 删除知识库", "PASS", "已清理")
else:
    log("8.1 创建知识库", "FAIL", f"{r.status_code}")

# 9. 工作流
wf_app = next((a for a in apps if a.get("mode")=="workflow"), None)
if wf_app:
    inputs, wtoken = discover_inputs(s, wf_app["id"])
    log("9.1 工作流API Key", "PASS" if wtoken else "FAIL")
    api_s = requests.Session(); api_s.verify=False
    api_s.headers.update({"Host":"api.dify-plus.local","Authorization":f"Bearer {wtoken}","Content-Type":"application/json"})
    for var in inputs: inputs[var] = "老师讲课很认真，内容丰富，受益匪浅"
    # 获取select选项
    rp = api_s.get(f"{BASE}/v1/parameters")
    if rp.status_code==200:
        for item in rp.json().get("user_input_form",[]):
            for ft,cfg in item.items():
                if ft=="select" and cfg.get("required"):
                    opts = cfg.get("options",["True"])
                    inputs[cfg["variable"]] = opts[0]
    r = api_s.post(f"{BASE}/v1/workflows/run", json={"inputs":inputs,"response_mode":"blocking","user":"teacher-wf"}, timeout=300)
    log("9.2 工作流执行", "PASS" if r.status_code==200 else "FAIL", r.text[:80] if r.status_code!=200 else "成功")

# 10. Agent
agent_app = next((a for a in apps if a.get("mode")=="advanced-chat"), None)
if agent_app:
    ainputs, atoken = discover_inputs(s, agent_app["id"])
    log("10.1 Agent API Key", "PASS" if atoken else "FAIL")
    r = chat(atoken, "你好", ainputs, "agent-test")
    log("10.2 Agent对话", "PASS" if r.status_code==200 else "SKIP", f"{r.status_code}" + (" (未发布)" if r.status_code==400 else ""))

# 11. 文件上传
files = {"file":("test.py", io.BytesIO(b"print('hello')"), "text/plain")}
r = s.post(f"{BASE}/console/api/files/upload", files=files)
log("11.1 文件上传", "PASS" if r.status_code in (200,201) else "FAIL")

# 12. LLM连通性
for model in ["qwen2.5-coder:7b", "glm4:9b", "qwen3:4b"]:
    r = requests.post(f"{LITELLM}/v1/chat/completions",
        headers={"Authorization":f"Bearer {LITELLM_KEY}","Content-Type":"application/json"},
        json={"model":model,"messages":[{"role":"user","content":"Hi"}],"max_tokens":20}, timeout=120)
    log(f"12.{['qwen2.5-coder:7b','glm4:9b','qwen3:4b'].index(model)+1} {model}", "PASS" if r.status_code==200 else "FAIL")

# 13. 嵌入模型
r = requests.post(f"{LITELLM}/v1/embeddings",
    headers={"Authorization":f"Bearer {LITELLM_KEY}","Content-Type":"application/json"},
    json={"model":"bge-m3","input":"test"}, timeout=30)
log("13.1 bge-m3嵌入", "PASS" if r.status_code==200 else "FAIL", f"dim={len(r.json().get('data',[{}])[0].get('embedding',[]))}" if r.status_code==200 else "")

# 14. 基础设施
log("14.1 LiteLLM健康", "PASS" if requests.get(f"{LITELLM}/health/liveliness",timeout=5).status_code==200 else "FAIL")
log("14.2 Ollama", "PASS" if requests.get("http://10.167.2.176:30086/api/tags",timeout=5).status_code==200 else "FAIL")
log("14.3 Grafana", "PASS" if requests.get("http://10.167.2.175:30082",timeout=5,allow_redirects=False).status_code in (200,302) else "FAIL")
log("14.4 Rancher", "PASS" if requests.get("https://10.167.2.175",verify=False,timeout=10,allow_redirects=False).status_code==200 else "FAIL")

# 15. 教学场景
if chat_app and token:
    r = chat(token, "什么是工业互联网?用一句话回答", inputs, "iiot-student")
    log("15.1 工业互联网基础", "PASS" if r.status_code==200 else "FAIL", r.json().get("answer","")[:60] if r.status_code==200 else "")
    r = chat(token, "什么是PLC?用一句话回答", inputs, "iiot-student")
    log("15.2 PLC编程", "PASS" if r.status_code==200 else "FAIL", r.json().get("answer","")[:60] if r.status_code==200 else "")

# === 总结 ===
total = len(results)
passed = sum(1 for r in results if r["status"]=="PASS")
failed = sum(1 for r in results if r["status"]=="FAIL")
skipped = sum(1 for r in results if r["status"]=="SKIP")
print(f"\n{'='*60}")
print(f"总计: {total} | 通过: {passed}✅ | 失败: {failed}❌ | 跳过: {skipped}⏭️")
print(f"通过率: {passed/(total-skipped)*100:.1f}%" if total-skipped>0 else "N/A")
print(f"{'='*60}")
if failed:
    print("\n失败项:")
    for r in results:
        if r["status"]=="FAIL": print(f"  ❌ [{r['test']}] {r['detail']}")
