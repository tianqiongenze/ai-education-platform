# Studio「在职员界面查看课程简介页面」404/空白页修复报告 (V11)

## 问题描述

用户以 admin 登录 LMS,从课程简介页
`https://openedx.10.167.2.175.nip.io:31825/courses/course-v1:AIEDU+P1+2026/about`
点击「在职员界面查看课程简介页面」按钮后,跳转到
`https://studio.openedx.10.167.2.175.nip.io:31825/settings/details/course-v1:AIEDU+P1+2026`,
页面显示异常(用户感知为 404/错误页)。

**实际根因**:该 URL 返回 HTTP 200,但 course-authoring MFE 渲染的是**完全空白的页面**
(标题正常显示 "Course Authoring |",body 为空),用户看到白屏误判为 404。

## 三个叠加的根因 (逐一修复)

### 根因 1: `/api/mfe_config/v1` 端点在 tutor 13.3.2 中不存在

course-authoring MFE 启动时通过 frontend-platform 的 config service 请求
`MFE_CONFIG_API_URL + "?mfe=course-authoring"`。tutor 13.3.2 的 edx-platform
没有实现该端点 (Resolver404)。config service 失败后以空配置继续,导致
`getLocale called before configuring i18n` 崩溃 → 整页白屏。

通过反编译 MFE 的 frontend-platform chunk (module 29962) 确认其合并逻辑为
**扁平 key→value JSON 合并** (`Object.assign`),因此只需返回一个扁平 JSON 对象。

**修复**: 在边缘 Caddy 上为 studio/apps/lms 三个站点添加静态 JSON handler:

```
handle /api/mfe_config/v1* {
    respond "{\"BASE_URL\":\"https://studio...:31825\",\"PUBLIC_PATH\":\"/course-authoring/\",...}" 200 { close }
    header Content-Type application/json
}
```

关键配置项: `BASE_URL`(studio), `LMS_BASE_URL`, `LOGIN_URL`, `LOGOUT_URL`,
`REFRESH_ACCESS_TOKEN_ENDPOINT`(LMS /login_refresh), `ACCESS_TOKEN_COOKIE_NAME`
(edx-jwt-cookie-header-payload), `CSRF_TOKEN_API_PATH`, `USER_INFO_COOKIE_NAME`,
`SECURE_COOKIES=true`, `PUBLIC_PATH=/course-authoring/`, `APP_ID=course-authoring`,
`MFE_CONFIG_API_URL=""`(避免 MFE 再向外请求)。

### 根因 2: CORS 拦截认证请求

MFE 需要从 studio 域向 LMS 域发起 XHR (`/login_refresh` 刷新 JWT cookie)。
LMS/CMS 的 `CORS_ORIGIN_WHITELIST` 只包含 `http://apps...`(无 https、无端口),
预检请求被拒,认证链路中断。

**修复**: 在 LMS 和 CMS 的 settings ConfigMap 中追加:

```python
CORS_ORIGIN_WHITELIST.append("https://studio.openedx.10.167.2.175.nip.io:31825")
CORS_ORIGIN_WHITELIST.append("https://apps.openedx.10.167.2.175.nip.io:31825")
CORS_ORIGIN_WHITELIST.append("https://openedx.10.167.2.175.nip.io:31825")
CSRF_TRUSTED_ORIGINS.append("studio.openedx.10.167.2.175.nip.io")
CSRF_TRUSTED_ORIGINS.append("apps.openedx.10.167.2.175.nip.io")
CSRF_TRUSTED_ORIGINS.append("openedx.10.167.2.175.nip.io")
```

(ConfigMap: `openedx-settings-lms-c9mmh48c87`、`openedx-settings-cms-dt5db854k5`,
patch 后已 `rollout restart` lms/cms 并确认预检返回正确的 ACAO 头。)

### 根因 3: `/settings/details/*` 不在 MFE 路由表内

course-authoring MFE 的路由表**只有一条路由** `path:"/course/:courseId"`
(通过反编译 app.9bbe645cea6ba5e6219c.js 确认)。浏览器停留在
`/settings/details/<course_id>` 时,React Router 无匹配 → 静默渲染空 `#root`,
不报任何错。

**修复**: Caddy 将 `/settings/details/*` **302 重定向**(不能 rewrite——rewrite
不改变浏览器 URL,SPA 路由仍匹配不到)到 MFE 路由:

```
@settings path /settings/details/*
handle @settings {
    redir /course-authoring/course/{path_segments.2} 302
}
```

## 部署产物 (集群内现状)

| 对象 | 内容 |
|---|---|
| ConfigMap `caddy-config-new4` | 完整 Caddyfile: 三个站点均含 mfe_config JSON handler; studio 站点含 /settings/details 302; caddy deployment volumes[0] 已指向该 CM |
| ConfigMap `openedx-settings-lms-c9mmh48c87` | production.py 追加 CORS/CSRF 白名单 |
| ConfigMap `openedx-settings-cms-dt5db854k5` | 同上 |

> 注意: 上述 ConfigMap 内含密钥 (OAuth secret / JWT secret),**严禁**导出到本仓库。

## 验证结果

1. **单课程全流程** (playwright 无头浏览器): LMS 登录 → about 页 → 点击按钮 →
   302 → `/course-authoring/course/course-v1:AIEDU+P1+2026` → 完整渲染
   「日程 & 细节」设置页 (body 4134 字符, 0 个控制台错误)。
2. **全部 16 门课程** (A1-A4, B1-B6, P1-P6): 每门课走完整 about→按钮→Studio 流程,
   **16/16 通过**, body 均在 4126-4140 字符, 无 404、无空白。

## 为什么之前多轮测试没有发现 (测试套件缺陷与加固)

V9 套件 A11 用例只断言:

```python
assert "error" not in pg.title().lower()
assert "400" not in pg.title() and "404" not in pg.title()
```

而空白页的标题是正常的 "Course Authoring |"(HTTP 200),标题断言通过——
**从未检查过页面 body 是否真的渲染了内容**。这是典型的"只测状态码/标题,
不测渲染内容"的缺口。

**加固后的 A11**:

```python
pg.goto(target, ...)
pg.wait_for_url("**/course-authoring/**", ...)
time.sleep(10)
body = pg.inner_text("body").strip()
assert len(body) > 300, "studio page nearly empty (blank MFE): %d chars" % len(body)
assert "日程" in body or "Schedule" in body or "大纲" in body or "Outline" in body, ...
assert "getLocale called before" not in pg.content(), "MFE i18n crash"
```

从此任何"HTTP 200 + 白屏"的页面都无法通过测试。
