# V9 修复与全平台测试报告 — Studio链接端口修复 + 课程图标 + 功能/性能压测

日期: 2026-09-09
前置报告: STUDIO-404-FIX-REPORT-V8.md (commit 2e95fde)

## 一、问题与修复

### 1.1 "View in Studio" 链接缺少 :31825 端口 (彻底修复)

**根因**: LMS 课程页的 Studio 链接由 Django 模板使用 `settings.CMS_BASE` 生成
(`lms/djangoapps/courseware/courses.py:770` → `//{CMS_BASE}/{page}/{course_id}`)。
CMS_BASE 同时被 tutor 的 settings 层用于 ALLOWED_HOSTS 校验，而 Django 3.2 的
`get_host()` 会先用 `split_domain_port()` 剥离端口、只用裸域名校验 ALLOWED_HOSTS
——若在 CMS_BASE 中放 `host:port`，裸域名永远匹配不上，CMS 直接 400 DisallowedHost。
这就是之前"CMS_BASE 不能含端口"结论的来源，导致链接永远缺端口。

**修复方案** (两层):
1. `CMS_BASE = studio.openedx.10.167.2.175.nip.io:31825` (含端口, 供链接生成);
   `ALLOWED_HOSTS` 改为裸域名列表 (供 host 校验)。
2. 打补丁 tutor settings 层 (ConfigMap `openedx-settings-cms-dt5db854k5` /
   `openedx-settings-lms-c9mmh48c87`, 挂载于 pod 的
   `cms/envs/tutor/production.py` / `lms/envs/tutor/production.py`):
   ```python
   ALLOWED_HOSTS = [ENV_TOKENS.get("CMS_BASE"), "cms"] \
       + [_h for _h in ENV_TOKENS.get("ALLOWED_HOSTS", []) if _h]
   ```
   LMS 侧同型: `[LMS_BASE, PREVIEW_LMS_BASE, "lms"] + ENV_TOKENS["ALLOWED_HOSTS"]`。

**验证**: 生成的链接形如
`//studio.openedx.10.167.2.175.nip.io:31825/settings/details/course-v1:AIEDU+P1+2026`，
直接点击可达 (CMS root 200, settings/details 200, LMS 200)，无需手动补端口。

### 1.2 课程图标异常显示 (修复)

- 16 门课程 (P1-P6, B1-B6, A1-A4) 各生成一枚 480x480 主题图标
  (纯 Python zlib/struct 手工编码 PNG, 2-3KB/枚, 配色与图案按课程主题区分)。
- 通过 `upload_icons.py` 在 CMS shell 中写入 contentstore:
  `AssetLocator(ck.for_branch(None), 'asset', fname)` + `StaticContent` +
  `course.course_image = fname` (banner/thumbnail/hero 同步设置), `ms.update_item`。
- About 页现引用 `/asset-v1:AIEDU+{code}+2026+type@asset+block@{code}_course_image.png`，
  16 个 asset URL 全部 200 且为合法 PNG。

## 二、功能测试 (V9 套件, Playwright 无头)

新增用例覆盖本次两处修复; 结果 **14/14 PASS (100%)**, 见 `platform_test_v9_report.json`:

| 模块 | 用例 | 结果 |
|---|---|---|
| A: LMS核心 | A1 登录页可访问 / A2 管理员登录 / A3 Dashboard显示课程 | PASS |
| A: 修复验证 | **A10 About页Studio链接含:31825** / **A11 点击链接直达无错误** | PASS |
| F: 图标 | **F1+F3 16图标asset 200且合法PNG** / **F2 About页引用新图标** | PASS |
| E: 16课程全扫 | E1 About / E2 Courseware / E3 Studio设置 / E4 Studio创作 | PASS |
| B: 回归 | B1-B3 Hub / Code-Server / Autograder | PASS |

## 三、性能与压力测试

### 3.1 k6 (master 节点, 20→50→100 VU 阶梯)

- 覆盖 LMS / Studio / JupyterHub / Autograder 四平台; 修正了两个过期端点
  (Hub→`/ide/healthcheck`; PL→`/api/courses`, autograder 无 UI 路由)。
- 结果: 40,370 请求, **http_req_failed 0.00%**, 四平台成功率均 100%,
  p95 = 1.06s @ 100 VU (≈190 req/s)。

### 3.2 Locust (50 用户 / 3 分钟)

- 修复: 4 个 User 类补 `host` 属性; PL 任务改 `/health` + `/api/courses`;
  Hub 健康检查加 `allow_redirects=False` (规避 hub base_url 302 双前缀
  `/ide/hub/hub/healthcheck` 的已知路由 quirk, 该 302 本身即健康)。
- 结果: **4,433 请求, 0 失败 (0.00%)**, Aggregated p95 = 32ms / p99 = 78ms,
  max 1.6s (单次 Studio 设置页冷缓存)。四平台 (LMS 浏览 / Studio 创作+设置 /
  Hub / PL) 全部 0 失败。

### 3.3 压测数据清理 (完成后清理)

- Open edX: 删除压测注册的 50 个 `py_b_*` 用户及其 100 条选课、
  profiles、schedules 链 (scheduleexperience→schedule→enrollment)、
  forum 角色关联; 复查 auth_userprofile / student_courseenrollment 零孤儿。
  用户数 134 → 84 (仅保留真实用户: admin/teacher/lecture-* /学生)。
- CockroachDB `prairielearn.scores`: 3 行, 均为真实功能测试记录
  (student-python/alice/bob), 无压测写入, 无需清理。
- JupyterHub DB: 127 用户, 无 k6/locust/stress 命名残留。

## 四、产物清单

| 文件 | 说明 |
|---|---|
| `platform_test_suite_v9.py` | V9 功能套件 (14 用例, 含修复验证) |
| `platform_test_v9_report.json` | V9 结果 14/14 PASS |
| `k6_stress_test.js` | k6 四平台压测脚本 (端点已修正) |
| `locustfile_platform.py` | Locust 四平台压测脚本 (allow_redirects 修正) |
| `gen_course_icons.py` | 16 课程图标生成器 (纯 Python PNG 编码) |
| `upload_icons.py` | contentstore 图标上传脚本 |
| 本报告 | STUDIO-LINK-ICONS-REPORT-V9.md |

## 五、结论

- Studio 链接端口问题已从生成机制层面彻底解决 (CMS_BASE 含端口 + ALLOWED_HOSTS
  裸域名双通道), A10/A11 用例固化回归。
- 16 门课程图标全部正常显示。
- 全平台功能 14/14 PASS; k6 100VU 0.00% 失败; Locust 0.00% 失败。
- 压测产生的全部测试数据已清理, 平台恢复至压测前状态。
