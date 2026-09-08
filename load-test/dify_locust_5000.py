#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 5000 人并发压测 (Locust) - 完整版
======================================
在服务器上通过 Docker 运行 Locust

Usage:
  pip install locust  # 或用 docker
  locust -f dify_locust_5000.py --host=https://10.167.2.175:31825 --headless \
         -u 5000 -r 50 --run-time 10m --html dify_locust_report.html \
         --only-summary
"""
import json
import base64
import random
import socket
import ssl
import time
import urllib3
from locust import HttpUser, task, between, events

urllib3.disable_warnings()

EMAIL = "myuwei@126.com"
PASSWORD = "Difyai123456"
LITELLM_HOST = "http://10.167.2.176:30083"
LITELLM_KEY = "sk-ai-platform-master"

# Disable SSL verification for self-signed certs
import ssl as _ssl
_ssl._create_default_https_context = _ssl._create_unverified_context

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
    "Python的列表和元组有什么区别？",
    "什么是大数据的4V特征？",
]


class DifyPlatformUser(HttpUser):
    """模拟学生使用 Dify 平台 - 5000 并发"""
    weight = 8
    wait_time = between(2, 8)
    host = "https://10.167.2.175:31825"
    insecure = True

    def on_start(self):
        self.app_token = None
        self.inputs = {}
        self.student_id = f"student-{random.randint(10000, 99999)}"
        self.csrf = ""
        self.session_cookie = ""
        self.login_and_setup()

    def login_and_setup(self):
        # 登录
        pass_b64 = base64.b64encode(PASSWORD.encode()).decode()
        with self.client.post(
            "/console/api/login",
            json={"email": EMAIL, "password": pass_b64, "language": "zh-Hans", "remember_me": True},
            headers={"Content-Type": "application/json"},
            name="登录",
            catch_response=True,
            verify=False,
        ) as resp:
            if resp.status_code == 200:
                self.csrf = resp.cookies.get("csrf_token", "")
                self.session_cookie = resp.cookies.get("access_token", "")
                resp.success()
            else:
                resp.failure(f"login {resp.status_code}")
                return

        # 获取应用列表和 API Key
        headers = {"Host": "console.dify-plus.local", "X-CSRF-Token": self.csrf,
                    "Cookie": f"access_token={self.session_cookie}; csrf_token={self.csrf}"}
        with self.client.get("/console/api/apps?page=1&page_size=50",
                             headers=headers, name="应用列表", catch_response=True,
                             verify=False) as resp:
            if resp.status_code == 200:
                apps = resp.json().get("data", [])
                chat_apps = [a for a in apps if a.get("mode") == "chat"]
                if chat_apps:
                    self.app_id = random.choice(chat_apps).get("id")
                resp.success()

        if self.app_id:
            with self.client.get(f"/console/api/apps/{self.app_id}/api-keys",
                                 headers=headers, name="API Key", catch_response=True,
                             verify=False) as resp:
                if resp.status_code == 200:
                    keys = resp.json().get("data", [])
                    if keys:
                        self.app_token = keys[0].get("token")
                    resp.success()

            # 获取参数
            if self.app_token:
                with self.client.get("/v1/parameters",
                                     headers={"Host": "api.dify-plus.local",
                                              "Authorization": f"Bearer {self.app_token}"},
                                     name="应用参数", catch_response=True,
                             verify=False) as resp:
                    if resp.status_code == 200:
                        for item in resp.json().get("user_input_form", []):
                            for ftype, cfg in item.items():
                                if cfg.get("required") and cfg.get("variable"):
                                    if ftype == "select":
                                        self.inputs[cfg["variable"]] = cfg.get("options", ["True"])[0]
                                    else:
                                        self.inputs[cfg["variable"]] = "老师讲课很认真，内容丰富，受益匪浅"
                        resp.success()

    @task(6)
    def list_apps(self):
        """获取应用列表 - 轻量级 API 测试"""
        headers = {"Host": "console.dify-plus.local", "X-CSRF-Token": self.csrf,
                    "Cookie": f"access_token={self.session_cookie}; csrf_token={self.csrf}"}
        with self.client.get("/console/api/apps?page=1&page_size=20",
                             headers=headers, name="应用列表[压测]", catch_response=True,
                             verify=False) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"apps {resp.status_code}")

    @task(3)
    def list_datasets(self):
        """获取知识库列表"""
        headers = {"Host": "console.dify-plus.local", "X-CSRF-Token": self.csrf,
                    "Cookie": f"access_token={self.session_cookie}; csrf_token={self.csrf}"}
        with self.client.get("/console/api/datasets?page=1&page_size=20",
                             headers=headers, name="知识库列表", catch_response=True,
                             verify=False) as resp:
            if resp.status_code == 200:
                resp.success()

    @task(2)
    def view_conversations(self):
        """查看对话列表 - 不触发 LLM 推理"""
        if not self.app_token:
            return
        headers = {"Host": "api.dify-plus.local", "Authorization": f"Bearer {self.app_token}"}
        with self.client.get(f"/v1/conversations?user={self.student_id}&limit=5",
                             headers=headers, name="对话列表", catch_response=True,
                             verify=False) as resp:
            if resp.status_code == 200:
                resp.success()

    @task(1)
    def chat_message(self):
        """发送聊天消息 - 触发 LLM 推理（限制频率）"""
        if not self.app_token:
            return
        query = random.choice(TEACHING_QUESTIONS)
        headers = {"Host": "api.dify-plus.local",
                    "Authorization": f"Bearer {self.app_token}",
                    "Content-Type": "application/json"}
        payload = {
            "inputs": self.inputs,
            "query": query,
            "response_mode": "blocking",
            "user": self.student_id,
        }
        with self.client.post("/v1/chat-messages", json=payload,
                              headers=headers, name="聊天消息",
                              catch_response=True, timeout=300) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (400, 500):
                resp.failure(f"chat {resp.status_code}")
            else:
                resp.failure(f"chat {resp.status_code}")


class LiteLLMGatewayUser(HttpUser):
    """模拟直接调用 LiteLLM 网关 - 限制并发"""
    weight = 2
    wait_time = between(3, 10)
    host = "http://10.167.2.176:30083"

    def on_start(self):
        self.model = random.choice(["qwen2.5:7b", "qwen2.5-coder:7b"])

    @task(5)
    def chat_completion(self):
        """LLM 聊天补全"""
        headers = {"Authorization": f"Bearer {LITELLM_KEY}", "Content-Type": "application/json"}
        with self.client.post("/v1/chat/completions",
                              json={"model": self.model,
                                    "messages": [{"role": "user", "content": random.choice(TEACHING_QUESTIONS)}],
                                    "max_tokens": 30},
                              headers=headers, name="LLM聊天", catch_response=True,
                              timeout=120) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"llm {resp.status_code}")

    @task(1)
    def health_check(self):
        """健康检查"""
        with self.client.get("/health/liveliness", name="健康检查", catch_response=True,
                             verify=False) as resp:
            if resp.status_code == 200:
                resp.success()
