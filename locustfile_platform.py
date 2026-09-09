"""
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
Locust 压力测试脚本 - 在线编程平台
覆盖: LMS登录、LMS课程页、Studio课程页、JupyterHub登录、PrairieLearn API

用法: locust -f locustfile_platform.py --host=https://10.167.2.175:31825
      或: locust -f locustfile_platform.py --headless -u 50 -r 5 -t 60s --host=https://10.167.2.175:31825
"""
import random
import json
from locust import HttpUser, task, between, tag

LMS_HOST = "https://openedx.10.167.2.175.nip.io:31825"
STUDIO_HOST = "https://studio.openedx.10.167.2.175.nip.io:31825"
HUB_HOST = "https://10.167.2.175:31825"
PRAIRIE_HOST = "http://10.167.2.175:30093"

COURSES = ['A1','A2','A3','A4','B1','B2','B3','B4','B5','B6','P1','P2','P3','P4','P5','P6']

class LMSUser(HttpUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = False
    abstract = True
    """LMS read-only load tests"""
    wait_time = between(1, 3)
    
    @task(3)
    @tag("lms_home")
    def lms_homepage(self):
        """访问LMS首页"""
        with self.client.get(LMS_HOST + "/", name="LMS首页", catch_response=True) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(5)
    @tag("lms_course")
    def lms_course_page(self):
        """访问LMS课程页"""
        course = random.choice(COURSES)
        with self.client.get(
            LMS_HOST + f"/courses/course-v1:AIEDU+{course}+2026/courseware/",
            name=f"LMS课程页-{course}",
            catch_response=True,
            allow_redirects=False
        ) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(2)
    @tag("lms_login")
    def lms_login_page(self):
        """访问LMS登录页"""
        with self.client.get(LMS_HOST + "/login", name="LMS登录页", catch_response=True) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(2)
    @tag("lms_dashboard")
    def lms_dashboard(self):
        """访问LMS仪表盘"""
        with self.client.get(LMS_HOST + "/dashboard", name="LMS仪表盘", catch_response=True, allow_redirects=False) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(1)
    @tag("lms_oauth")
    def lms_oauth_authorize(self):
        """LMS OAuth2授权端点"""
        with self.client.get(
            LMS_HOST + "/oauth2/authorize/?response_type=code&client_id=REDACTED_OAUTH_CLIENT_ID&redirect_uri=https://10.167.2.175:31825/ide/hub/oauth_callback&scope=user_id",
            name="LMS OAuth2授权",
            catch_response=True,
            allow_redirects=False
        ) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")


class StudioUser(HttpUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = False
    """Studio (CMS) load tests"""
    wait_time = between(1, 3)
    
    @task(3)
    @tag("studio_home")
    def studio_homepage(self):
        """访问Studio首页"""
        with self.client.get(STUDIO_HOST + "/", name="Studio首页", catch_response=True) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(5)
    @tag("studio_course_settings")
    def studio_course_settings(self):
        """Studio课程设置页(原404修复验证)"""
        course = random.choice(COURSES)
        with self.client.get(
            STUDIO_HOST + f"/settings/details/course-v1:AIEDU+{course}+2026",
            name=f"Studio课程设置-{course}",
            catch_response=True
        ) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(5)
    @tag("studio_authoring")
    def studio_course_authoring(self):
        """Studio课程创作MFE页面"""
        course = random.choice(COURSES)
        with self.client.get(
            STUDIO_HOST + f"/course-authoring/course-v1:AIEDU+{course}+2026",
            name=f"Studio课程创作-{course}",
            catch_response=True
        ) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")


class JupyterHubUser(HttpUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = False
    """JupyterHub load tests"""
    wait_time = between(1, 3)
    
    @task(3)
    @tag("hub_login")
    def hub_login_page(self):
        """访问Hub登录页"""
        with self.client.get(HUB_HOST + "/ide/hub/login", name="Hub登录页", catch_response=True) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(2)
    @tag("hub_oauth")
    def hub_oauth_login(self):
        """Hub OAuth重定向"""
        with self.client.get(HUB_HOST + "/ide/hub/oauth_login", name="Hub OAuth重定向", catch_response=True, allow_redirects=False) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(2)
    @tag("hub_api")
    def hub_api(self):
        """Hub API状态"""
        with self.client.get(HUB_HOST + "/ide/hub/api", name="Hub API", catch_response=True) as resp:
            if resp.status_code in (200, 401, 403):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(1)
    @tag("hub_health")
    def hub_healthcheck(self):
        """Hub健康检查"""
        with self.client.get(HUB_HOST + "/ide/hub/healthcheck", name="Hub健康检查", catch_response=True) as resp:
            if resp.status_code in (200, 302):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")


class PrairieLearnUser(HttpUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = False
    """PrairieLearn load tests"""
    wait_time = between(1, 3)
    
    @task(3)
    @tag("pl_home")
    def pl_homepage(self):
        """PrairieLearn首页"""
        with self.client.get(PRAIRIE_HOST + "/", name="PrairieLearn首页", catch_response=True) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(2)
    @tag("pl_courses")
    def pl_courses(self):
        """PrairieLearn课程列表"""
        with self.client.get(PRAIRIE_HOST + "/courses", name="PrairieLearn课程", catch_response=True) as resp:
            if resp.status_code in (200, 302, 301):
                resp.success()
            else:
                resp.failure(f"Status: {resp.status_code}")

    @task(1)
    @tag("pl_health")
    def pl_health(self):
        """PrairieLearn健康检查"""
        with self.client.get(PRAIRIE_HOST + "/health", name="PrairieLearn健康检查", catch_response=True) as resp:
            if resp.status_code in (200, 302):
                resp.success()
