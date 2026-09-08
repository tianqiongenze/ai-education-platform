"""
JupyterHub 1000人并发压力测试
使用 Locust 模拟 1000 个用户同时登录和使用 JupyterHub
"""
from locust import HttpUser, task, between, events
import re

class JupyterHubUser(HttpUser):
    """模拟一个 JupyterHub 学生用户"""
    wait_time = between(1, 5)
    host = "http://10.167.2.175:30089/ide"
    
    def on_start(self):
        """用户注册登录"""
        import uuid
        self.username = f"stress-{uuid.uuid4().hex[:8]}"
        self.password = "ide2026"
        
        # 获取登录页 + XSRF token
        r = self.client.get("/hub/login", name="登录页")
        self.xsrf = ""
        if r.text:
            match = re.search(r'name="_xsrf"\s+value="([^"]+)"', r.text)
            if match:
                self.xsrf = match.group(1)
        
        # 登录
        r = self.client.post("/hub/login", data={
            "username": self.username,
            "password": self.password,
            "_xsrf": self.xsrf
        }, name="用户注册登录", allow_redirects=False)
        
        if r.status_code in (302, 303):
            self.logged_in = True
            # 等待Pod启动（不等，后续API调用会等待）
        else:
            self.logged_in = False
    
    @task(3)
    def view_home(self):
        """访问用户主页"""
        if hasattr(self, 'logged_in') and self.logged_in:
            self.client.get(f"/user/{self.username}/lab", name="用户JupyterLab页面")
    
    @task(2)
    def check_status(self):
        """检查用户状态"""
        if hasattr(self, 'logged_in') and self.logged_in:
            try:
                self.client.get(f"/user/{self.username}/api/status", name="API状态检查")
            except Exception:
                pass
    
    @task(1)
    def list_files(self):
        """列出工作目录文件"""
        if hasattr(self, 'logged_in') and self.logged_in:
            try:
                self.client.get(f"/user/{self.username}/api/contents/work", name="文件列表")
            except Exception:
                pass
    
    @task(1)
    def create_notebook(self):
        """创建笔记本文件"""
        if hasattr(self, 'logged_in') and self.logged_in:
            try:
                self.client.put(
                    f"/user/{self.username}/api/contents/work/stress_test.ipynb",
                    json={
                        "type": "notebook",
                        "format": "json",
                        "content": {
                            "nbformat": 4,
                            "nbformat_minor": 5,
                            "metadata": {},
                            "cells": [{
                                "cell_type": "code",
                                "source": ["print('Hello from stress test')"],
                                "execution_count": None,
                                "outputs": [],
                                "metadata": {}
                            }]
                        }
                    },
                    name="创建笔记本"
                )
            except Exception:
                pass


# 压测配置:
# locust -f jupyterhub_stress_test.py --headless -u 1000 -r 20 -t 300s --host=http://10.167.2.175:30089/ide
# 参数说明:
#   -u 1000      : 1000个并发用户
#   -r 20        : 每秒增加20个用户(50秒达到1000)
#   -t 300s      : 持续5分钟
#   --headless   : 无UI模式
