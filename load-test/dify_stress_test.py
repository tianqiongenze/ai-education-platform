#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 平台 5000 人并发压测脚本 (Locust)
=========================================
模拟真实教学场景: 学生上课同时使用 AI 助手
- Dify 平台用户: 登录 -> 应用列表 -> 发送聊天 -> 流式聊天 -> 对话历史
- LiteLLM 网关用户: health -> models -> chat completions -> embeddings

Usage:
  locust -f dify_stress_test.py --host=https://10.167.2.175:31825 --headless \
         -u 5000 -r 100 --run-time 10m --html dify_stress_report.html
"""
import json
import base64
import random
import string
from locust import HttpUser, task, between, tag, events

# 配置
EMAIL = "myuwei@126.com"
PASSWORD = "Difyai123456"
LITELLM_HOST = "http://10.167.2.176:30083"
LITELLM_KEY = "sk-ai-platform-master"

# 高职院校真实教学提问池
TEACHING_QUESTIONS = [
    "什么是Python中的变量？",
    "请解释一下二叉树的遍历方式",
    "Java和Python哪个更适合初学者？",
    "什么是数据库的事务？",
    "TCP和UDP的区别是什么？",
    "请用C语言写一个冒泡排序",
    "什么是机器学习中的过拟合？",
    "如何理解面向对象的封装特性？",
    "SQL中的GROUP BY怎么用？",
    "HTTP状态码404是什么意思？",
    "什么是云计算的IaaS、PaaS、SaaS？",
    "JavaScript的let和var有什么区别？",
    "网络子网掩码怎么计算？",
    "什么是软件工程中的敏捷开发？",
    "请解释CSS盒模型",
    "数据结构中栈和队列的区别？",
    "什么是RESTful API？",
    "Linux常用命令有哪些？",
    "什么是区块链技术？",
    "Python的列表和元组有什么区别？",
]


class DifyStudentUser(HttpUser):
    """模拟学生使用 Dify AI 助手 - 5000 并发"""
    weight = 7
    wait_time = between(2, 8)

    def on_start(self):
        """登录获取 session"""
        self.app_id = None
        self.app_token = None
        self.conversation_id = None
        self.student_id = f"student-{random.randint(1, 9999)}"
        self.login()
        self.pick_app()

    def login(self):
        """管理员登录（模拟学生通过已发布应用访问，此处模拟控制台登录）"""
        pass_b64 = base64.b64encode(PASSWORD.encode()).decode()
        with self.client.post(
            "/console/api/login",
            json={"email": EMAIL, "password": pass_b64,
                  "language": "zh-Hans", "remember_me": True},
            name="/console/api/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                try:
                    csrf = resp.cookies.get("csrf_token", "")
                    self.client.headers.update({"X-CSRF-Token": csrf})
                    resp.success()
                except Exception as e:
                    resp.failure(f"parse error: {e}")
            else:
                resp.failure(f"login failed: {resp.status_code}")

    def pick_app(self):
        """随机选择一个聊天应用"""
        with self.client.get(
            "/console/api/apps?page=1&page_size=50",
            name="/console/api/apps",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                apps = resp.json().get("data", [])
                chat_apps = [a for a in apps if a.get("mode") == "chat"]
                if chat_apps:
                    self.app_id = random.choice(chat_apps).get("id")
                    self.get_api_key()
                resp.success()
            else:
                resp.failure(f"apps failed: {resp.status_code}")

    def get_api_key(self):
        """获取应用 API Key"""
        if not self.app_id:
            return
        with self.client.get(
            f"/console/api/apps/{self.app_id}/api-keys",
            name="/console/api/apps/api-keys",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                keys = resp.json().get("data", [])
                if keys:
                    self.app_token = keys[0].get("token")
                else:
                    r = self.client.post(
                        f"/console/api/apps/{self.app_id}/api-keys",
                        name="/console/api/apps/api-keys-create")
                    self.app_token = r.json().get("token", "")
                resp.success()
            else:
                resp.failure(f"api-keys failed: {resp.status_code}")

    @task(5)
    def send_chat_blocking(self):
        """发送聊天消息（阻塞模式）- 教学提问"""
        if not self.app_token:
            self.pick_app()
            return
        query = random.choice(TEACHING_QUESTIONS)
        headers = {
            "Authorization": f"Bearer {self.app_token}",
            "Host": "api.dify-plus.local",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {"Text1": query},
            "query": query,
            "response_mode": "blocking",
            "user": self.student_id,
        }
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id
        with self.client.post(
            "/v1/chat-messages",
            json=payload,
            headers=headers,
            name="/v1/chat-messages [blocking]",
            catch_response=True,
            timeout=120,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.conversation_id = data.get("conversation_id")
                resp.success()
            elif resp.status_code == 400:
                # 模型超时等预期内失败也算部分成功（标记但不计入失败率）
                resp.failure(f"chat 400: {resp.text[:80]}")
            else:
                resp.failure(f"chat failed: {resp.status_code}")

    @task(2)
    def send_chat_streaming(self):
        """流式聊天 - 模拟学生等待打字机效果"""
        if not self.app_token:
            return
        query = random.choice(TEACHING_QUESTIONS)
        headers = {
            "Authorization": f"Bearer {self.app_token}",
            "Host": "api.dify-plus.local",
        }
        payload = {
            "inputs": {"Text1": query},
            "query": query,
            "response_mode": "streaming",
            "user": self.student_id,
        }
        with self.client.post(
            "/v1/chat-messages",
            json=payload,
            headers=headers,
            name="/v1/chat-messages [streaming]",
            catch_response=True,
            timeout=120,
            stream=True,
        ) as resp:
            if resp.status_code == 200:
                chunk_count = 0
                for line in resp.iter_lines():
                    if line and line.startswith(b"data:"):
                        chunk_count += 1
                resp.success()
            else:
                resp.failure(f"stream failed: {resp.status_code}")

    @task(1)
    def view_conversations(self):
        """查看对话历史"""
        if not self.app_token:
            return
        headers = {
            "Authorization": f"Bearer {self.app_token}",
            "Host": "api.dify-plus.local",
        }
        with self.client.get(
            "/v1/conversations",
            params={"user": self.student_id, "limit": 10},
            headers=headers,
            name="/v1/conversations",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"conversations failed: {resp.status_code}")


class LiteLLMGatewayUser(HttpUser):
    """模拟直接调用 LiteLLM 网关的 AI 服务 - 5000 并发"""
    weight = 3
    wait_time = between(1, 5)

    def on_start(self):
        self.model = random.choice(["qwen2.5:7b", "qwen2.5:14b", "qwen2.5-coder:7b"])

    @task(6)
    def chat_completion(self):
        """LLM 聊天补全"""
        headers = {"Authorization": f"Bearer {LITELLM_KEY}"}
        with self.client.post(
            "/v1/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": random.choice(TEACHING_QUESTIONS)}],
                "max_tokens": 50,
            },
            headers=headers,
            name="/v1/chat/completions",
            catch_response=True,
            timeout=90,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"litellm chat: {resp.status_code}")

    @task(2)
    def list_models(self):
        """获取模型列表"""
        headers = {"Authorization": f"Bearer {LITELLM_KEY}"}
        with self.client.get(
            "/v1/models",
            headers=headers,
            name="/v1/models",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"models: {resp.status_code}")

    @task(1)
    def health_check(self):
        """健康检查"""
        with self.client.get(
            "/health/liveliness",
            name="/health/liveliness",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"health: {resp.status_code}")
