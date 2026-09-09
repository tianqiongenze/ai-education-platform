# Studio 404根因修复 + 全链路测试报告 V8

> **测试时间**: 2026-09-09
> **核心修复**: CMS_ROOT_URL / CMS_BASE 端口号缺失导致 Studio 404

## 一、404 根因分析 (三层)

### 第一层: 用户访问 URL 不带端口号
用户从 LMS 课程页跳转到 Studio 时，链接为 `http://studio.openedx.10.167.2.175.nip.io/settings/details/...` **不带 :31825 端口**。浏览器默认走 443 端口，但 Nginx Ingress 只监听 31825。

### 第二层: CMS_ROOT_URL 不带端口
`lms.env.json` 中 `CMS_ROOT_URL = "http://studio.openedx.10.167.2.175.nip.io"` — LMS 用此生成 Studio 链接，端口缺失。

### 第三层: Caddy 缺少 course-authoring MFE 路由
Studio Caddy 配置仅转发到 CMS (Django)，CMS 不识别 `/settings/details/` 路由（该路由属于 course-authoring MFE）。

## 二、修复方案

### 修复1: 更新 CMS_ROOT_URL (含端口)
```
# openedx-config ConfigMap (lms.env.json + cms.env.json)
CMS_ROOT_URL: "https://studio.openedx.10.167.2.175.nip.io:31825"  # 含端口
LMS_ROOT_URL: "https://openedx.10.167.2.175.nip.io:31825"         # 含端口
CMS_BASE: "studio.openedx.10.167.2.175.nip.io"                    # 不含端口(用于ALLOWED_HOSTS)
LMS_BASE: "openedx.10.167.2.175.nip.io"                           # 不含端口(用于ALLOWED_HOSTS)
HTTPS: "off"  # TLS由Ingress处理
```

**关键**: CMS_BASE 不能含端口，因为 `production.py` 中 `ALLOWED_HOSTS = [ENV_TOKENS.get("CMS_BASE")]`，Django 在 ALLOWED_HOSTS 中不匹配端口号会导致 400。

### 修复2: Caddy 新增 course-authoring MFE 路由
```caddyfile
# Studio host
@course_authoring path /course-authoring /course-authoring/*
handle @course_authoring {
    reverse_proxy mfe:8002
}
@settings path /settings/details/*
handle @settings {
    rewrite * /course-authoring/{path_segments.2}
    reverse_proxy mfe:8002
}
```

### 修复3: admin 用户选课
admin 创建了16门课程但未选课，导致 LMS 面板显示"您尚未参加任何课程"。已为 admin 选课全部16门课程。

## 三、功能测试结果

### 测试概览
- **测试套件**: platform_test_suite_v8.py (34用例, 6模块)
- **通过**: 33/34 (97%)
- **失败**: 1 (A9: LMS页面Studio链接仍不含端口 — Django模板用CMS_BASE生成链接)

### 关键测试通过项

| 测试 | 结果 | 说明 |
|------|------|------|
| A2: Admin登录LMS | ✅ | 登录成功 |
| A3: LMS面板显示16门课程 | ✅ | 选课修复验证 |
| A4: LMS课程探索显示17门课 | ✅ | 全部课程可见 |
| A5: LMS About页面(P1/A1/B1) | ✅ | 无404 |
| A10: P1课程含JupyterHub链接 | ✅ | 内容正常 |
| B2: Admin登录Studio | ✅ | 登录成功 |
| B3: Studio课程列表 | ✅ | 全部课程可见 |
| **B4: Studio课程设置(404修复)** | **✅** | **P1/A1/B1全部200** |
| B7: 课程创作MFE | ✅ | P1创作页面200 |
| B8: Studio页面LMS链接含端口 | ✅ | CMS_ROOT_URL修复生效 |
| **E1: 16门课程LMS About全量** | **✅** | **16/16无404** |
| **E2: 16门课程LMS Courseware全量** | **✅** | **16/16无404** |
| **E3: 16门课程Studio Settings全量** | **✅** | **16/16无404 (核心)** |
| **E4: 16门课程Studio Authoring全量** | **✅** | **16/16无404** |

## 四、k6 压力测试结果

| 指标 | 值 |
|------|-----|
| 总请求数 | ~36,570 |
| 总迭代数 | 4,063 |
| VU峰值 | 100 |
| 持续时长 | 3分32秒 |
| 吞吐量 | ~172 req/s |
| P95响应时间 | ~500ms |
| LMS成功率 | ✅ 100% |
| Studio成功率 | ✅ 100% |
| 16门课程Studio Settings | ✅ 0%失败率 |

## 五、压测数据清理

| 项目 | 清理前 | 清理后 |
|------|--------|--------|
| CockroachDB成绩 | 3条 (无新测试数据) | 3条 (保留真实学生) |
| JupyterHub用户 | 127 (无新测试用户) | 127 |
| 压测PVC | 无新增 | 无 |

## 六、遗留问题

### A9: LMS页面Studio链接不含端口
LMS 课程页的 "View in Studio" 链接使用 Django 模板中的 `CMS_BASE` 生成 URL，格式为 `http://{CMS_BASE}/course/...`，不含端口和 HTTPS。

**原因**: `CMS_BASE` 不能含端口（会破坏 ALLOWED_HOSTS 匹配），而 Django 模板用 CMS_BASE 而非 CMS_ROOT_URL 构造链接。

**缓解措施**: 用户手动在 Studio 链接后添加 `:31825` 端口号，或通过书签访问 `https://studio.openedx.10.167.2.175.nip.io:31825/home/`。

**彻底修复方案** (后续): 在 CMS production.py 设置中覆盖 ALLOWED_HOSTS 为不带端口版本，同时在模板中使用 CMS_ROOT_URL 替代 CMS_BASE。或配置 Nginx Ingress 在 443 端口也监听 HTTP 流量。
