# 在线编程平台 V13 全覆盖测试报告（上线前验收）

- 测试日期：2026-09-11
- 测试方式：Playwright 无头浏览器，真实用户流程（登录 → 页面 → 逐按钮/逐链接点击 → 落点断言）
- 结论：**35/35 全部通过（100%）**，本轮用户报障已修复并回归验证通过。

---

## 1. 本轮报障定位与修复（JupyterHub 实验平台链接无响应）

### 1.1 根因（精准定位）

课程内容 HTML 组件（modulestore html block）中的实验平台链接指向了错误地址：

```
旧链接（错误）: https://apps.openedx.10.167.2.175.nip.io:31825/
```

该地址是 MFE 聚合入口（Caddy `apps.openedx...` 站点），其根路径配置为 `respond / 204`，
浏览器收到 **204 空响应** → 页面无任何内容，表现为"跳转后页面没有正常响应"。

JupyterHub 的正确入口是 `https://jupyterhub.10.167.2.175.nip.io:31825/ide/`
（ingress 仅路由 `/ide/` 前缀到 JupyterHub 服务，会 302 到 OAuth 登录页）。

### 1.2 影响范围与修复

- 全部 **16 门课程**（P1–P6、B1–B6、A1–A4）共 **44 处** HTML 组件含此坏链。
- 修复方式：CMS pod 内 Django shell 脚本批量改写 modulestore，
  统一替换为 `https://jupyterhub.10.167.2.175.nip.io:31825/ide/`。
- 复扫确认 draft 分支 **0 残留**。
- 由于 LMS 课件页读取 published 分支，追加执行了
  **61 个 vertical 子树的 draft→published 发布**（16 门课程全部完成，0 错误），
  LMS 端复扫确认 0 残留、Hub 链接全部正确。

### 1.3 已知项（非缺陷，记录备查）

| 现象 | 原因 | 说明 |
| --- | --- | --- |
| `https://jupyterhub...:31825/`（根路径）返回 503 | jupyterhub-ingress 仅路由 `/ide/` 前缀 | 正确入口为 `/ide/`，已在链接修复中统一使用 |
| `https://apps.openedx...:31825/`（根路径）返回 204 | Caddy 对 MFE 聚合根路径有意返回空响应 | 不能作为任何页面入口链接使用 |

---

## 2. V13 测试用例与结果（35/35 PASS）

### A. LMS 核心（9）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| A1 | LMS 登录页元素完整 | PASS |
| A2 | 管理员登录 LMS | PASS |
| A3 | Dashboard 显示课程 | PASS |
| A3b | 课程发现页列出全部 16 门课程 | PASS |
| A4 | 账号设置页 | PASS |
| A5 | 用户资料页 | PASS |
| A6 | 静态页 6 个（tos/privacy/about/blog/contact_us/donate）全部 200 | PASS |
| A7 | 退出登录（豁免已知 this.unbind 控制台噪音） | PASS |
| A8 | 课程搜索（发现页搜索框） | PASS |

### B. About 页逐链接点击（1）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| B1 | 查看课程→Learning MFE / Studio 链接 / mailto / Twitter / PrairieLearn 学习路径 | PASS |

### C. Learning MFE（1）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| C1 | 16 课程 MFE 课程主页全部渲染 | PASS |

### D. Studio 全功能（4）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| D1 | Studio 主页 | PASS |
| D2 | Studio 课程列表 | PASS |
| D3 | 五个设置/工具页（细节/评分/团队/文件/高级） | PASS |
| D4 | Studio 课程大纲页 | PASS |

### E. 16 课程全扫描（3）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| E1 | 16 课程 About 页无 404 且非空白 | PASS |
| E2 | 16 课程 Courseware(MFE) 无 404 且非空白 | PASS |
| E3 | 16 课程 Studio 设置页无 404 且非空白 | PASS |

### F. JupyterHub（3）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| F1 | 登录页含 OAuth 登录按钮 | PASS |
| F2 | OAuth 登录全链路（Hub → LMS → 回 Hub） | PASS |
| F3 | 管理页可达（未登录跳转，无 500） | PASS |

### G. PrairieLearn 评测 API（3）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| G1 | `/health` 健康检查 | PASS |
| G2 | `/api/courses` 4 门语言课程 | PASS |
| G3 | API Key 认证（无 key 403 / 教师 key 200） | PASS |

### H. Code-Server（1）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| H1 | Code-Server 可访问 | PASS |

### I. 平台一致性（3）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| I1 | MFE 配置接口 200 且内容正确 | PASS |
| I2 | LMS 主页匿名可访问 | PASS |
| I3 | Studio 未登录访问不 500 | PASS |

### J. Studio 垂直页逐链接验证（本轮新增，报障回归）（3）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| J1 | **用户报障路径回归**：Studio vertical1 页点击「JupyterHub 实验平台」链接 → 新标签落点 `jupyterhub.../ide/hub/login?next=/ide/hub/`，OAuth 登录页正常渲染 | PASS |
| J2 | Studio 垂直页所有链接无 apps 根路径死链 | PASS |
| J3 | Studio 垂直页外链逐一核查（全部有效） | PASS |

### K. LMS 课件页链接全扫描（本轮新增）（2）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| K1 | 16 课程课件页链接全扫描：0 个 apps 根路径死链，Hub 链接全部指向 `/ide/`，16 门课程均含 Hub 实验链接 | PASS |
| K2 | 课件页实验平台链接真实点击 → Hub 登录页正常渲染 | PASS |

### L. Hub 入口矩阵（本轮新增）（2）
| 用例 | 内容 | 结果 |
| --- | --- | --- |
| L1 | `/ide/` 302→登录页；`/ide/hub/login` 200 且含 OAuth 按钮 | PASS |
| L2 | Hub 根路径 503 记录项（ingress 仅路由 `/ide/`，属已知部署形态） | PASS |

---

## 3. 迭代历史

| 版本 | 用例数 | 结果 | 主要变化 |
| --- | --- | --- | --- |
| V11 | — | — | About 页 MFE 404 修复（4 个 MFE URL 设置补 ：31825） |
| V12 | 28 | 28/28 (100%) | 全功能基线（OAuth 登录、评测 API、搜索等） |
| **V13** | **35** | **35/35 (100%)** | **+7 用例：垂直页逐链接点击、16 课程课件页链接扫描、Hub 全入口矩阵；修复 44 处实验平台坏链并发布课程** |

## 4. 上线结论

- 本轮报障（实验平台链接无响应）根因已修复：44 处坏链全部改指 JupyterHub 正确入口，
  draft/published 双分支 0 残留，真实点击回归通过。
- 全平台 35 项功能用例 100% 通过，覆盖 LMS / Studio / Learning MFE / JupyterHub /
  PrairieLearn 评测 / Code-Server 及 16 门课程内容链接，**具备上线条件**。
