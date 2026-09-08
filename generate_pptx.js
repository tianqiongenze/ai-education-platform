const PptxGenJS = require("pptxgenjs");

const pptx = new PptxGenJS();

// ===== Design System =====
const COLORS = {
  primary: "0A2540",      // Deep navy - dominant
  secondary: "1E88E5",     // Tech blue - supporting
  accent: "00C896",        // Green - accent
  light: "F5F7FA",        // Light bg
  dark: "0A2540",          // Dark bg
  white: "FFFFFF",
  gray: "8B95A5",
  grayLight: "E4E8EE",
  gold: "FFB300",
};

const FONTS = {
  title: "Arial Black",
  header: "Arial",
  body: "Calibri",
};

pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";

// ===== Slide 1: Title =====
let slide = pptx.addSlide();
slide.background = { color: COLORS.primary };

// Decorative accent bar
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: COLORS.accent } });

slide.addText("Dify 智能体服务平台", {
  x: 0.8, y: 1.5, w: 11.5, h: 1.2,
  fontFace: FONTS.title, fontSize: 44, color: COLORS.white, bold: true,
});
slide.addText("本地化部署成果汇报", {
  x: 0.8, y: 2.6, w: 11.5, h: 0.8,
  fontFace: FONTS.header, fontSize: 28, color: COLORS.accent,
});

slide.addText("工业互联网应用专业 · AI 教学平台", {
  x: 0.8, y: 3.8, w: 11.5, h: 0.5,
  fontFace: FONTS.body, fontSize: 16, color: COLORS.grayLight,
});
slide.addText("2026 年 8 月", {
  x: 0.8, y: 4.4, w: 11.5, h: 0.5,
  fontFace: FONTS.body, fontSize: 14, color: COLORS.gray,
});

// Tech stats
const stats = [
  { label: "本地模型", value: "22" },
  { label: "应用数量", value: "27" },
  { label: "测试通过率", value: "100%" },
  { label: "Redis", value: "8.10" },
];
stats.forEach((s, i) => {
  const x = 0.8 + i * 3;
  slide.addText(s.value, { x: x, y: 5.5, w: 2.5, h: 0.6, fontFace: FONTS.title, fontSize: 36, color: COLORS.accent, bold: true });
  slide.addText(s.label, { x: x, y: 6.1, w: 2.5, h: 0.4, fontFace: FONTS.body, fontSize: 12, color: COLORS.grayLight });
});

// ===== Slide 2: Agenda =====
slide = pptx.addSlide();
slide.background = { color: COLORS.light };

slide.addText("汇报内容", { x: 0.8, y: 0.4, w: 12, h: 0.8, fontFace: FONTS.title, fontSize: 36, color: COLORS.primary, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.2, w: 2, h: 0.04, fill: { color: COLORS.accent } });

const agenda = [
  { num: "01", title: "平台架构总览", desc: "K8s 集群拓扑 · 服务部署 · 网络架构" },
  { num: "02", title: "AI 模型部署", desc: "22 个本地模型 · LiteLLM 网关 · 多模型对比" },
  { num: "03", title: "Dify 平台功能", desc: "27 个应用 · 知识库 · 工作流 · Agent" },
  { num: "04", title: "性能与压测", desc: "HPA 自动扩缩容 · Locust 压测 · 3000 并发" },
  { num: "05", title: "教学场景应用", desc: "工业互联网 · PLC 编程 · Python 教学" },
  { num: "06", title: "运维与监控", desc: "Rancher · Grafana · Redis 8 Cluster" },
];
agenda.forEach((item, i) => {
  const row = Math.floor(i / 2);
  const col = i % 2;
  const x = 0.8 + col * 5.9;
  const y = 1.6 + row * 1.8;
  
  slide.addShape(pptx.ShapeType.roundRect, { x: x, y: y, w: 5.5, h: 1.5, fill: { color: COLORS.white }, line: { color: COLORS.grayLight, width: 1 } });
  slide.addText(item.num, { x: x + 0.2, y: y + 0.2, w: 0.8, h: 0.5, fontFace: FONTS.title, fontSize: 28, color: COLORS.accent, bold: true });
  slide.addText(item.title, { x: x + 1.0, y: y + 0.25, w: 4, h: 0.4, fontFace: FONTS.header, fontSize: 16, color: COLORS.primary, bold: true });
  slide.addText(item.desc, { x: x + 1.0, y: y + 0.7, w: 4.2, h: 0.6, fontFace: FONTS.body, fontSize: 11, color: COLORS.gray });
});

// ===== Slide 3: Architecture Overview =====
slide = pptx.addSlide();
slide.background = { color: COLORS.primary };

slide.addText("平台架构总览", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.white, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

// Master node
slide.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 1.5, w: 5.5, h: 5.5, fill: { color: "15293E" }, line: { color: COLORS.secondary, width: 2 } });
slide.addText("Master 节点 (10.167.2.175)", { x: 0.8, y: 1.7, w: 5, h: 0.4, fontFace: FONTS.header, fontSize: 14, color: COLORS.accent, bold: true });

const masterSvcs = ["Dify API (3副本)", "Dify Web (2副本)", "Dify Worker (3副本)", "Dify Plugin Daemon", "PostgreSQL", "Redis 7 (Dify用)", "Redis 8 Cluster (3节点)", "Grafana 监控", "Rancher 管理", "Ingress-Nginx (2副本)"];
masterSvcs.forEach((s, i) => {
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.8, y: 2.2 + i * 0.45, w: 4.5, h: 0.35, fill: { color: COLORS.dark }, line: { color: COLORS.secondary, width: 0.5 } });
  slide.addText(s, { x: 0.9, y: 2.22 + i * 0.45, w: 4.3, h: 0.35, fontFace: FONTS.body, fontSize: 10, color: COLORS.white, align: "center", valign: "middle" });
});

// Worker node
slide.addShape(pptx.ShapeType.roundRect, { x: 6.8, y: 1.5, w: 6, h: 5.5, fill: { color: "15293E" }, line: { color: COLORS.accent, width: 2 } });
slide.addText("Worker 节点 (10.167.2.176)", { x: 7.1, y: 1.7, w: 5.5, h: 0.4, fontFace: FONTS.header, fontSize: 14, color: COLORS.accent, bold: true });

const workerSvcs = ["LiteLLM 网关 (2副本)", "Ollama (22模型)", "Code-Server (3副本, 52插件)", "Dify Plugin Daemon", "Dify Worker", "Dify Sandbox", "Weaviate 向量库", "PgBouncer", "Node Exporter", "Prometheus + Loki"];
workerSvcs.forEach((s, i) => {
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.1, y: 2.2 + i * 0.45, w: 5, h: 0.35, fill: { color: COLORS.dark }, line: { color: COLORS.accent, width: 0.5 } });
  slide.addText(s, { x: 7.2, y: 2.22 + i * 0.45, w: 4.8, h: 0.35, fontFace: FONTS.body, fontSize: 10, color: COLORS.white, align: "center", valign: "middle" });
});

// ===== Slide 4: AI Models =====
slide = pptx.addSlide();
slide.background = { color: COLORS.light };

slide.addText("AI 模型部署总览", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.primary, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

// Model categories
const cats = [
  { title: "Qwen3 系列 (最新)", models: ["qwen3:4b (2GB) - 快速", "qwen3:8b (5GB) - 教学", "qwen3:14b (9GB) - 深度", "qwen3:30b-a3b (18GB) - MoE", "qwen3:32b (20GB) - 旗舰", "qwen3-embedding:0.6b/4b"] },
  { title: "Qwen2.5 系列 (经典)", models: ["qwen2.5:7b/14b/32b/72b", "qwen2.5-coder:7b/14b", "deepseek-r1:7b/14b/32b", "bge-m3 (嵌入1024维)", "nomic-embed-text"] },
  { title: "其他模型", models: ["glm4:9b (中文最强)", "yi:6b (中文通用)", "llama3.1:8b (通用)", "llama3.2-vision:11b", "tinyllama (轻量)"] },
];
cats.forEach((cat, i) => {
  const x = 0.5 + i * 4.3;
  slide.addShape(pptx.ShapeType.roundRect, { x: x, y: 1.5, w: 4, h: 4.5, fill: { color: COLORS.white }, line: { color: COLORS.grayLight, width: 1 } });
  slide.addText(cat.title, { x: x + 0.2, y: 1.7, w: 3.6, h: 0.5, fontFace: FONTS.header, fontSize: 14, color: COLORS.primary, bold: true });
  cat.models.forEach((m, j) => {
    slide.addText("• " + m, { x: x + 0.2, y: 2.3 + j * 0.4, w: 3.6, h: 0.35, fontFace: FONTS.body, fontSize: 10, color: COLORS.gray });
  });
});

// Stats
slide.addText("22 个本地模型 · 25 个 LiteLLM 路由 · 全部 Dify 注册", { x: 0.8, y: 6.3, w: 12, h: 0.5, fontFace: FONTS.header, fontSize: 14, color: COLORS.secondary, bold: true, align: "center" });

// ===== Slide 5: Model Comparison =====
slide = pptx.addSlide();
slide.background = { color: COLORS.primary };

slide.addText("多模型性能对比", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.white, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

const models = [
  { name: "llama3.1:8b", avg: "18.5s", best: "通用最快", pass: "6/6" },
  { name: "glm4:9b", avg: "20.7s", best: "4/6场景最快", pass: "6/6" },
  { name: "qwen2.5-coder:7b", avg: "26.6s", best: "编程+数据库", pass: "6/6" },
  { name: "yi:6b", avg: "31.3s", best: "网络通信", pass: "6/6" },
  { name: "qwen3:4b", avg: "42.0s", best: "深度推理", pass: "6/6" },
  { name: "qwen3:8b", avg: "67.1s", best: "最深推理", pass: "6/6" },
];

// Table header
slide.addText("模型", { x: 0.5, y: 1.5, w: 3.5, h: 0.4, fontFace: FONTS.header, fontSize: 12, color: COLORS.accent, bold: true });
slide.addText("平均耗时", { x: 4, y: 1.5, w: 2, h: 0.4, fontFace: FONTS.header, fontSize: 12, color: COLORS.accent, bold: true });
slide.addText("优势场景", { x: 6, y: 1.5, w: 4, h: 0.4, fontFace: FONTS.header, fontSize: 12, color: COLORS.accent, bold: true });
slide.addText("通过率", { x: 10, y: 1.5, w: 2, h: 0.4, fontFace: FONTS.header, fontSize: 12, color: COLORS.accent, bold: true });

models.forEach((m, i) => {
  const y = 2.0 + i * 0.7;
  const bg = i % 2 === 0 ? "112233" : "0A2540";
  slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: y, w: 12, h: 0.6, fill: { color: bg } });
  slide.addText(m.name, { x: 0.5, y: y + 0.1, w: 3.5, h: 0.4, fontFace: FONTS.body, fontSize: 12, color: COLORS.white });
  slide.addText(m.avg, { x: 4, y: y + 0.1, w: 2, h: 0.4, fontFace: FONTS.body, fontSize: 12, color: COLORS.accent, bold: true });
  slide.addText(m.best, { x: 6, y: y + 0.1, w: 4, h: 0.4, fontFace: FONTS.body, fontSize: 11, color: COLORS.grayLight });
  slide.addText(m.pass, { x: 10, y: y + 0.1, w: 2, h: 0.4, fontFace: FONTS.body, fontSize: 12, color: COLORS.accent });
});

slide.addText("36 项测试 100% 通过 · glm4:9b 在工业互联网/PLC/AI 场景表现最优", { x: 0.8, y: 6.3, w: 12, h: 0.5, fontFace: FONTS.header, fontSize: 13, color: COLORS.gold, bold: true, align: "center" });

// ===== Slide 6: Dify Features =====
slide = pptx.addSlide();
slide.background = { color: COLORS.light };

slide.addText("Dify 平台功能", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.primary, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

const features = [
  { icon: "💬", title: "聊天助手", desc: "阻塞/流式聊天\n多轮对话\n上下文保持", count: "5种模式" },
  { icon: "📚", title: "知识库", desc: "4个数据集\n文档上传+索引\n语义检索", count: "RAG" },
  { icon: "🔄", title: "工作流", desc: "情感分析工作流\n多步骤自动化\n节点可视化", count: "6个应用" },
  { icon: "🤖", title: "Agent", desc: "高级聊天助手\n工具调用\n15个应用", count: "15个" },
  { icon: "📝", title: "应用管理", desc: "27个应用\n创建/删除/发布\nAPI Key管理", count: "27个" },
  { icon: "📊", title: "对话管理", desc: "对话历史\n消息反馈\n导出记录", count: "完整" },
];
features.forEach((f, i) => {
  const row = Math.floor(i / 3);
  const col = i % 3;
  const x = 0.5 + col * 4.3;
  const y = 1.5 + row * 2.7;
  
  slide.addShape(pptx.ShapeType.roundRect, { x: x, y: y, w: 4, h: 2.3, fill: { color: COLORS.white }, line: { color: COLORS.grayLight, width: 1 } });
  slide.addText(f.icon, { x: x + 0.2, y: y + 0.2, w: 0.8, h: 0.6, fontSize: 28, align: "center" });
  slide.addText(f.title, { x: x + 1.0, y: y + 0.25, w: 2.5, h: 0.5, fontFace: FONTS.header, fontSize: 16, color: COLORS.primary, bold: true });
  slide.addText(f.desc, { x: x + 0.2, y: y + 0.9, w: 3.6, h: 1.0, fontFace: FONTS.body, fontSize: 10, color: COLORS.gray });
  slide.addText(f.count, { x: x + 0.2, y: y + 1.85, w: 3.6, h: 0.3, fontFace: FONTS.header, fontSize: 11, color: COLORS.accent, bold: true });
});

// ===== Slide 7: Performance & HPA =====
slide = pptx.addSlide();
slide.background = { color: COLORS.primary };

slide.addText("性能与自动扩缩容", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.white, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

// HPA table
slide.addText("HPA 自动扩缩容配置", { x: 0.8, y: 1.5, w: 6, h: 0.5, fontFace: FONTS.header, fontSize: 16, color: COLORS.accent, bold: true });

const hpas = [
  { svc: "dify-api", min: "3", max: "5", cpu: "70%" },
  { svc: "dify-worker", min: "3", max: "8", cpu: "70%" },
  { svc: "litellm", min: "2", max: "10", cpu: "70%" },
  { svc: "ingress-nginx", min: "2", max: "10", cpu: "70%" },
  { svc: "code-server", min: "3", max: "20", cpu: "70%" },
  { svc: "pgbouncer", min: "2", max: "5", cpu: "70%" },
];
slide.addText("服务", { x: 0.8, y: 2.1, w: 2, h: 0.3, fontFace: FONTS.header, fontSize: 10, color: COLORS.grayLight, bold: true });
slide.addText("Min", { x: 3, y: 2.1, w: 1, h: 0.3, fontFace: FONTS.header, fontSize: 10, color: COLORS.grayLight, bold: true });
slide.addText("Max", { x: 4, y: 2.1, w: 1, h: 0.3, fontFace: FONTS.header, fontSize: 10, color: COLORS.grayLight, bold: true });
slide.addText("CPU阈值", { x: 5, y: 2.1, w: 1.5, h: 0.3, fontFace: FONTS.header, fontSize: 10, color: COLORS.grayLight, bold: true });
hpas.forEach((h, i) => {
  const y = 2.5 + i * 0.4;
  slide.addText(h.svc, { x: 0.8, y: y, w: 2, h: 0.3, fontFace: FONTS.body, fontSize: 10, color: COLORS.white });
  slide.addText(h.min, { x: 3, y: y, w: 1, h: 0.3, fontFace: FONTS.body, fontSize: 10, color: COLORS.accent });
  slide.addText(h.max, { x: 4, y: y, w: 1, h: 0.3, fontFace: FONTS.body, fontSize: 10, color: COLORS.accent });
  slide.addText(h.cpu, { x: 5, y: y, w: 1.5, h: 0.3, fontFace: FONTS.body, fontSize: 10, color: COLORS.white });
});

// Stress test results
slide.addText("压力测试结果", { x: 7.5, y: 1.5, w: 5, h: 0.5, fontFace: FONTS.header, fontSize: 16, color: COLORS.accent, bold: true });

const stress = [
  { users: "500", reqs: "11,528", rps: "64.3", result: "稳定运行" },
  { users: "1,000", reqs: "6,123", rps: "34.1", result: "HPA扩容" },
  { users: "2,000", reqs: "12,018", rps: "34.1", result: "自动伸缩" },
];
stress.forEach((s, i) => {
  const y = 2.1 + i * 1.2;
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.5, y: y, w: 5, h: 1, fill: { color: "112233" } });
  slide.addText(s.users + " 用户", { x: 7.7, y: y + 0.1, w: 2, h: 0.4, fontFace: FONTS.header, fontSize: 14, color: COLORS.accent, bold: true });
  slide.addText(s.rqs + " 请求", { x: 7.7, y: y + 0.5, w: 2, h: 0.4, fontFace: FONTS.body, fontSize: 10, color: COLORS.white });
  slide.addText(s.rps + " req/s", { x: 9.5, y: y + 0.1, w: 1.5, h: 0.4, fontFace: FONTS.body, fontSize: 11, color: COLORS.white });
  slide.addText(s.result, { x: 9.5, y: y + 0.5, w: 2.8, h: 0.4, fontFace: FONTS.body, fontSize: 10, color: COLORS.accent });
});

slide.addText("Ollama 并行推理: NUM_PARALLEL=8 · 模型永驻内存: KEEP_ALIVE=-1", { x: 0.8, y: 6.3, w: 12, h: 0.5, fontFace: FONTS.header, fontSize: 13, color: COLORS.gold, bold: true, align: "center" });

// ===== Slide 8: Teaching Scenarios =====
slide = pptx.addSlide();
slide.background = { color: COLORS.light };

slide.addText("工业互联网教学场景", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.primary, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

const scenarios = [
  { title: "工业互联网基础", model: "glm4:9b (12.9s)", q: "什么是工业互联网?", a: "连接物理世界与数字世界的网络平台" },
  { title: "PLC 编程教学", model: "glm4:9b (9.2s)", q: "什么是PLC?", a: "工业自动化中用于逻辑控制的可编程控制器" },
  { title: "Python 编程", model: "qwen2.5-coder:7b (31.7s)", q: "写一个列表排序函数", a: "def sort_list(lst): return sorted(lst)" },
  { title: "数据库事务", model: "qwen2.5-coder:7b (10.8s)", q: "什么是数据库事务?", a: "一系列操作的原子执行单元" },
  { title: "网络通信", model: "yi:6b (24.3s)", q: "TCP和UDP的区别?", a: "TCP可靠有序,UDP快速无连接" },
  { title: "AI/机器学习", model: "glm4:9b (13.3s)", q: "什么是过拟合?", a: "模型在训练数据上过度学习导致泛化能力下降" },
];
scenarios.forEach((s, i) => {
  const row = Math.floor(i / 2);
  const col = i % 2;
  const x = 0.5 + col * 6.4;
  const y = 1.5 + row * 1.8;
  
  slide.addShape(pptx.ShapeType.roundRect, { x: x, y: y, w: 6, h: 1.6, fill: { color: COLORS.white }, line: { color: COLORS.grayLight, width: 1 } });
  slide.addText(s.title, { x: x + 0.2, y: y + 0.1, w: 3, h: 0.4, fontFace: FONTS.header, fontSize: 14, color: COLORS.primary, bold: true });
  slide.addText(s.model, { x: x + 3.5, y: y + 0.1, w: 2.3, h: 0.4, fontFace: FONTS.body, fontSize: 10, color: COLORS.accent, align: "right" });
  slide.addText("Q: " + s.q, { x: x + 0.2, y: y + 0.5, w: 5.5, h: 0.4, fontFace: FONTS.body, fontSize: 11, color: COLORS.gray });
  slide.addText("A: " + s.a, { x: x + 0.2, y: y + 0.9, w: 5.5, h: 0.6, fontFace: FONTS.body, fontSize: 10, color: COLORS.primary });
});

// ===== Slide 9: Operations & Monitoring =====
slide = pptx.addSlide();
slide.background = { color: COLORS.primary };

slide.addText("运维与监控体系", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.white, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

const ops = [
  { title: "Rancher 集群管理", items: ["2个集群: local + dify-cluster", "2节点可视: master + worker", "集群状态: active", "凭据: admin / Rancher@2026"] },
  { title: "Grafana 监控", items: ["33个仪表盘", "Dify Platform 面板", "LLM Services 面板", "Infrastructure 面板"] },
  { title: "Redis 8 Cluster", items: ["Redis 8.10.1, 3主节点", "cluster_state: ok", "NodePort 30095 局域网访问", "密码: difyai123456"] },
  { title: "Code-Server AI编程", items: ["52个扩展插件", "Java/Go/Rust/Python/C 支持", "Continue.dev + Claude Code", "本地模型 AI 辅助编程"] },
];
ops.forEach((o, i) => {
  const row = Math.floor(i / 2);
  const col = i % 2;
  const x = 0.5 + col * 6.4;
  const y = 1.5 + row * 2.8;
  
  slide.addShape(pptx.ShapeType.roundRect, { x: x, y: y, w: 6, h: 2.4, fill: { color: "112233" }, line: { color: COLORS.secondary, width: 1 } });
  slide.addText(o.title, { x: x + 0.2, y: y + 0.15, w: 5.5, h: 0.5, fontFace: FONTS.header, fontSize: 15, color: COLORS.accent, bold: true });
  o.items.forEach((item, j) => {
    slide.addText("• " + item, { x: x + 0.2, y: y + 0.7 + j * 0.4, w: 5.5, h: 0.35, fontFace: FONTS.body, fontSize: 11, color: COLORS.white });
  });
});

// ===== Slide 10: Test Results =====
slide = pptx.addSlide();
slide.background = { color: COLORS.light };

slide.addText("测试成果", { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: FONTS.title, fontSize: 32, color: COLORS.primary, bold: true });
slide.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: COLORS.accent } });

// Big numbers
const bigStats = [
  { num: "43", label: "功能测试用例", sub: "43/43 通过" },
  { num: "36", label: "模型对比测试", sub: "36/36 通过" },
  { num: "100%", label: "总通过率", sub: "0 失败 0 跳过" },
  { num: "2,000", label: "压测峰值用户", sub: "HPA 自动扩容" },
];
bigStats.forEach((s, i) => {
  const x = 0.5 + i * 3.2;
  slide.addShape(pptx.ShapeType.roundRect, { x: x, y: 1.5, w: 3, h: 2.2, fill: { color: COLORS.white }, line: { color: COLORS.accent, width: 2 } });
  slide.addText(s.num, { x: x, y: 1.7, w: 3, h: 1, fontFace: FONTS.title, fontSize: 44, color: COLORS.primary, bold: true, align: "center" });
  slide.addText(s.label, { x: x, y: 2.7, w: 3, h: 0.4, fontFace: FONTS.header, fontSize: 13, color: COLORS.gray, align: "center" });
  slide.addText(s.sub, { x: x, y: 3.1, w: 3, h: 0.4, fontFace: FONTS.body, fontSize: 11, color: COLORS.accent, align: "center" });
});

// Test categories
slide.addText("测试覆盖范围", { x: 0.8, y: 4.2, w: 12, h: 0.5, fontFace: FONTS.header, fontSize: 16, color: COLORS.primary, bold: true });

const cats2 = ["认证登录", "聊天(阻塞/流式)", "多轮对话", "知识库(创建/检索)", "工作流执行", "Agent应用", "对话管理", "文件上传", "应用CRUD", "模型连通性", "嵌入模型", "基础设施", "教学场景"];
slide.addText(cats2.join(" · "), { x: 0.8, y: 4.7, w: 12, h: 1.5, fontFace: FONTS.body, fontSize: 13, color: COLORS.gray, align: "left" });

// ===== Slide 11: Conclusion =====
slide = pptx.addSlide();
slide.background = { color: COLORS.primary };
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: COLORS.accent } });

slide.addText("总结与展望", { x: 0.8, y: 0.8, w: 12, h: 0.8, fontFace: FONTS.title, fontSize: 36, color: COLORS.white, bold: true });

const achievements = [
  "✅ Dify 1.14.2 平台完整部署，27 个应用 100% 可用",
  "✅ 22 个本地 AI 模型，覆盖 Qwen3/GLM4/YI/Llama3.1 全系列",
  "✅ 43 项功能测试 + 36 项模型对比测试，100% 通过",
  "✅ HPA 自动扩缩容，支持 2000 并发用户压测",
  "✅ Redis 8.10.1 Cluster 部署，局域网可访问",
  "✅ Code-Server 52 个插件，支持 Java/Go/Rust/Python/C AI 编程",
  "✅ Grafana 33 个监控面板 + Rancher 2 集群管理",
  "✅ 工业互联网教学场景验证，GLM4 在中文场景表现最优",
];
achievements.forEach((a, i) => {
  slide.addText(a, { x: 0.8, y: 2.0 + i * 0.5, w: 12, h: 0.45, fontFace: FONTS.body, fontSize: 14, color: COLORS.white });
});

slide.addText("工业互联网应用专业 · AI 教学平台本地化部署", { x: 0.8, y: 6.5, w: 12, h: 0.5, fontFace: FONTS.header, fontSize: 16, color: COLORS.accent, bold: true, align: "center" });

// ===== Save =====
pptx.writeFile({ fileName: "Dify智能体服务平台本地化部署成果汇报.pptx" }).then(() => {
  console.log("PPTX created successfully!");
}).catch(err => {
  console.error("Error:", err);
});
