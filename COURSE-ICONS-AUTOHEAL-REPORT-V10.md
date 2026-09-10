# 课程图标自愈机制部署报告 — V10

日期: 2026-09-10
前置: STUDIO-LINK-ICONS-REPORT-V9.md (commit dc18a82)

## 需求

以后每添加一门课程, 若没有图标则自动生成主题相关的图标, 保证课程图标永远正常显示, 不再出现异常/裂图。

## 方案: 自愈脚本 + CronJob 定时巡检

### 1. `ensure_course_icons.py` (自愈脚本)

在 CMS pod 内运行的幂等巡检脚本, 对 modulestore 中每一门课程:

1. `course_image` 为空 → 生成图标并上传 contentstore, 同时设置
   course_image / banner_image / thumbnail_image / hero_image 四个字段;
2. `course_image` 已设置但 asset 在 contentstore 中不存在 (被删/未上传) →
   重新生成同名 asset 并发布;
3. 图标完好 → 跳过 (0 改动, 幂等安全)。

**图标主题自动匹配**: 按课程 key + display_name 中的关键词从 16 组
(图形, 配色) 主题规则中选取 — python/java/go/rust→code, 数据结构/算法→tree,
web/网络→globe, 数据分析→plot, 机器学习/AI→brain, 数据库→db, 安全→shield,
云/DevOps→cloud, 游戏→game, 机器人→robot 等; 无关键词命中时回落到默认
"eye" 图形。任何新课程都会得到一枚主题相关的 480x480 PNG (纯 Python
zlib/struct 编码, 无第三方图像依赖), 不会再出现异常显示。

### 2. CronJob `ensure-course-icons` (namespace: openedx)

- 调度: `7 * * * *` (每小时第 7 分钟, 与写回类任务错峰);
- 镜像: 与 CMS 相同的 `10.100.135.132:5000/overhangio/openedx:13.3.2`
  (本地 registry, 免拉取延迟); DJANGO_SETTINGS_MODULE=cms.envs.tutor.production,
  工作目录 /openedx/edx-platform;
- 脚本与 runner 由 ConfigMap 挂载:
  `cm-ensure-icons-code` (ensure_course_icons.py) + `cm-ensure-icons-script` (run.sh);
- concurrencyPolicy: Forbid, backoffLimit: 1, 带 resources requests/limits;
- 声明文件: `cronjob_ensure_icons.yaml`。

即新课程在 Studio 创建后, 最迟 1 小时内图标自动补齐; 也可手动触发:
`kubectl create job --from=cronjob/ensure-course-icons <name> -n openedx`。

## 验证

| 验证项 | 结果 |
|---|---|
| 首次巡检 (16门课全部完好) | `Summary: 0 fixed, 17 already-ok` ✅ |
| 故障注入: 删除 P1 的 asset 后巡检 | `FIXED course-v1:AIEDU+P1+2026 -> p1_course_image.png (glyph=code)`, `1 fixed, 16 already-ok` ✅ |
| 重生图标对外服务 | `GET /asset-v1:AIEDU+P1+2026+...p1_course_image.png` → **200**, 响应体为合法 PNG (magic `\x89PNG\r\n\x1a\n`) ✅ |
| CronJob 手动触发 (ensure-icons-t10) | Job 状态 **Complete:True, succeeded=1** ✅ |
| 测试 Job 清理 | ensure-icons-t5~t10 等测试 Job 已删除, 仅保留 CronJob ✅ |

## 运维说明

- 查看巡检历史: `kubectl get jobs -n openedx | grep ensure-course-icons`
- 查看某次巡检日志: 找到对应 job 的 pod 后 `kubectl logs <pod> -n openedx`
- 新增主题规则: 编辑 ConfigMap `cm-ensure-icons-code` 中 THEME_RULES 列表
- 临时禁用: `kubectl patch cronjob ensure-course-icons -n openedx -p '{"spec":{"suspend":true}}'`

## 产物

| 文件 | 说明 |
|---|---|
| `ensure_course_icons.py` | 图标自愈脚本 (主题匹配 + PNG 生成 + contentstore 上传) |
| `cronjob_ensure_icons.yaml` | CronJob + ConfigMap 声明文件 |
