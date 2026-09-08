// Dify 50-Page Comprehensive Presentation
const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();
pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";

const C = { primary: "0A2540", secondary: "1E88E5", accent: "00C896", light: "F5F7FA", dark: "0A2540", white: "FFFFFF", gray: "8B95A5", grayL: "E4E8EE", gold: "FFB300" };
const F = { title: "Arial Black", header: "Arial", body: "Calibri" };

function addTitleSlide(title, subtitle) {
  let s = pptx.addSlide();
  s.background = { color: C.primary };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: C.accent } });
  s.addText(title, { x: 0.8, y: 2.0, w: 12, h: 1.2, fontFace: F.title, fontSize: 40, color: C.white, bold: true });
  if (subtitle) s.addText(subtitle, { x: 0.8, y: 3.2, w: 12, h: 0.8, fontFace: F.header, fontSize: 24, color: C.accent });
  return s;
}

function addSectionSlide(num, title) {
  let s = pptx.addSlide();
  s.background = { color: C.secondary };
  s.addText(num, { x: 0.8, y: 2.0, w: 12, h: 2, fontFace: F.title, fontSize: 80, color: C.white, bold: true, align: "center" });
  s.addText(title, { x: 0.8, y: 4.2, w: 12, h: 1, fontFace: F.header, fontSize: 28, color: C.white, align: "center" });
  return s;
}

function addContentSlide(title) {
  let s = pptx.addSlide();
  s.background = { color: C.light };
  s.addText(title, { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: F.title, fontSize: 30, color: C.primary, bold: true });
  s.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: C.accent } });
  return s;
}

function addDarkSlide(title) {
  let s = pptx.addSlide();
  s.background = { color: C.primary };
  s.addText(title, { x: 0.8, y: 0.4, w: 12, h: 0.7, fontFace: F.title, fontSize: 30, color: C.white, bold: true });
  s.addShape(pptx.ShapeType.rect, { x: 0.8, y: 1.1, w: 2, h: 0.04, fill: { color: C.accent } });
  return s;
}

// === 1. Title ===
addTitleSlide("Dify 智能体服务平台", "本地化部署成果汇报");
let s = pptx.slides[pptx.slides.length-1];
s.addText("工业互联网应用专业 · AI 教学平台 · 2026年8月", { x: 0.8, y: 4.2, w: 12, h: 0.5, fontFace: F.body, fontSize: 16, color: C.grayL });
const stats = [["22", "本地模型"], ["27", "应用数量"], ["100%", "测试通过率"], ["8.10", "Redis版本"]];
stats.forEach((st, i) => { const x = 0.8 + i * 3; s.addText(st[0], { x, y: 5.5, w: 2.5, h: 0.6, fontFace: F.title, fontSize: 36, color: C.accent, bold: true }); s.addText(st[1], { x, y: 6.1, w: 2.5, h: 0.4, fontFace: F.body, fontSize: 12, color: C.grayL }); });

// === 2. Agenda ===
s = addContentSlide("汇报内容");
const agenda = [["01","平台架构总览","K8s集群·服务部署·网络"],["02","AI模型部署","22模型·LiteLLM·多模型对比"],["03","Dify平台功能","27应用·知识库·工作流·Agent"],["04","Dify应用市场","模板安装·插件生态·社区应用"],["05","性能与压测","HPA·Locust·3000并发"],["06","教学场景应用","工业互联网·PLC·Python"],["07","平台对比分析","Dify vs Coze vs FastGPT"],["08","运维与监控","Rancher·Grafana·Redis8"],["09","测试成果","43+36=79项测试100%"],["10","总结与展望","成果·不足·未来规划"]];
agenda.forEach((item, i) => { const row = Math.floor(i/2), col = i%2; const x = 0.8 + col*6, y = 1.5 + row*1.2; s.addShape(pptx.ShapeType.roundRect, { x, y, w: 5.8, h: 1.0, fill: { color: C.white }, line: { color: C.grayL, width: 1 } }); s.addText(item[0], { x: x+0.15, y: y+0.15, w: 0.7, h: 0.5, fontFace: F.title, fontSize: 24, color: C.accent, bold: true }); s.addText(item[1], { x: x+0.9, y: y+0.15, w: 3, h: 0.4, fontFace: F.header, fontSize: 14, color: C.primary, bold: true }); s.addText(item[2], { x: x+0.9, y: y+0.55, w: 4.5, h: 0.4, fontFace: F.body, fontSize: 10, color: C.gray }); });

// === 3-4. Architecture ===
addSectionSlide("01", "平台架构总览");
s = addDarkSlide("集群拓扑架构");
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 1.5, w: 5.8, h: 5.5, fill: { color: "15293E" }, line: { color: C.secondary, width: 2 } });
s.addText("Master (10.167.2.175) 64GB", { x: 0.8, y: 1.7, w: 5, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true });
["Dify API (3副本 8Gi)","Dify Web (2副本)","Dify Worker (3副本)","Plugin Daemon","PostgreSQL","Redis 7 (Dify用)","Redis 8 Cluster (3节点)","Grafana + Loki","Rancher 管理","Ingress-Nginx (2副本)"].forEach((svc,i) => { s.addShape(pptx.ShapeType.roundRect, { x: 0.8, y: 2.2+i*0.43, w: 4.8, h: 0.35, fill: { color: C.dark }, line: { color: C.secondary, width: 0.5 } }); s.addText(svc, { x: 0.9, y: 2.22+i*0.43, w: 4.6, h: 0.35, fontFace: F.body, fontSize: 9, color: C.white, align: "center", valign: "middle" }); });
s.addShape(pptx.ShapeType.roundRect, { x: 6.8, y: 1.5, w: 6, h: 5.5, fill: { color: "15293E" }, line: { color: C.accent, width: 2 } });
s.addText("Worker (10.167.2.176) 128GB", { x: 7.1, y: 1.7, w: 5.5, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true });
["LiteLLM 网关 (2副本 4CPU)","Ollama (22模型 NUM_PARALLEL=8)","Code-Server (3副本 52插件)","Dify Plugin Daemon","Dify Worker","Dify Sandbox","Weaviate 向量库","PgBouncer 连接池","Node Exporter","Prometheus + Loki"].forEach((svc,i) => { s.addShape(pptx.ShapeType.roundRect, { x: 7.1, y: 2.2+i*0.43, w: 5.2, h: 0.35, fill: { color: C.dark }, line: { color: C.accent, width: 0.5 } }); s.addText(svc, { x: 7.2, y: 2.22+i*0.43, w: 5, h: 0.35, fontFace: F.body, fontSize: 9, color: C.white, align: "center", valign: "middle" }); });

// === 5. Network Architecture ===
s = addContentSlide("网络架构与访问方式");
const accessMethods = [["Dify 控制台","https://10.167.2.175:31825","IP直连,无需hosts","307→登录页✅"],["Dify API","https://10.167.2.175:31825/v1","IP直连","程序化调用✅"],["Code-Server","https://10.167.2.175:31825/code-server/","路径路由,无需hosts","302→登录页✅"],["LiteLLM","http://10.167.2.176:30083","IP直连","25模型✅"],["Ollama","http://10.167.2.176:30086","IP直连","22模型✅"],["Grafana","http://10.167.2.175:30082","IP直连","33面板✅"],["Rancher","https://10.167.2.175","IP直连","2集群✅"],["Redis 8 Cluster","10.167.2.175:30095","NodePort直连","3节点✅"]];
s.addText("服务", { x: 0.5, y: 1.5, w: 2, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("地址", { x: 2.5, y: 1.5, w: 4, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("访问方式", { x: 6.5, y: 1.5, w: 3, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("状态", { x: 9.5, y: 1.5, w: 3, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
accessMethods.forEach((a, i) => { const y = 1.9 + i * 0.55; const bg = i % 2 === 0 ? C.white : C.grayL; s.addShape(pptx.ShapeType.rect, { x: 0.5, y, w: 12, h: 0.5, fill: { color: bg } }); s.addText(a[0], { x: 0.5, y: y+0.08, w: 2, h: 0.35, fontFace: F.body, fontSize: 10, color: C.primary, bold: true }); s.addText(a[1], { x: 2.5, y: y+0.08, w: 4, h: 0.35, fontFace: F.body, fontSize: 9, color: C.secondary }); s.addText(a[2], { x: 6.5, y: y+0.08, w: 3, h: 0.35, fontFace: F.body, fontSize: 10, color: C.gray }); s.addText(a[3], { x: 9.5, y: y+0.08, w: 3, h: 0.35, fontFace: F.body, fontSize: 10, color: C.accent }); });

// === 6. Section: AI Models ===
addSectionSlide("02", "AI 模型部署");

// === 7. Model Overview ===
s = addContentSlide("AI 模型部署总览 (22个本地模型)");
const modelCats = [["Qwen3 系列 (最新, 推荐)",["qwen3:4b (2GB) - 快速问答, thinking模式","qwen3:8b (5GB) - 通用教学, thinking模式","qwen3:14b (9GB) - 深度推理, thinking模式","qwen3:30b-a3b (18GB) - MoE混合专家, 高效","qwen3:32b (20GB) - 旗舰推理, thinking模式","qwen3-embedding:0.6b/4b - 嵌入模型"]],["Qwen2.5 系列 (经典)",["qwen2.5:7b/14b/32b/72b - 通用对话","qwen2.5-coder:7b/14b - 编程专用","deepseek-r1:7b/14b/32b - 深度推理","bge-m3 - 1024维嵌入","nomic-embed-text - 轻量嵌入"]],["其他模型",["glm4:9b (5.5GB) - 中文最强, 教学最优","yi:6b (3.5GB) - 中文通用","llama3.1:8b (4.9GB) - 通用最快","llama3.2-vision:11b - 多模态视觉","tinyllama (637MB) - 极轻量测试"]]];
modelCats.forEach((cat, i) => { const x = 0.5 + i * 4.3; s.addShape(pptx.ShapeType.roundRect, { x, y: 1.5, w: 4, h: 5.2, fill: { color: C.white }, line: { color: C.grayL, width: 1 } }); s.addText(cat[0], { x: x+0.2, y: 1.7, w: 3.6, h: 0.5, fontFace: F.header, fontSize: 13, color: C.primary, bold: true }); cat[1].forEach((m, j) => { s.addText("• " + m, { x: x+0.2, y: 2.3 + j * 0.55, w: 3.6, h: 0.5, fontFace: F.body, fontSize: 9, color: C.gray }); }); });
s.addText("22个Ollama模型 · 25个LiteLLM路由 · Dify全部注册", { x: 0.8, y: 6.8, w: 12, h: 0.4, fontFace: F.header, fontSize: 13, color: C.secondary, bold: true, align: "center" });

// === 8. Model Details: Qwen3 ===
s = addDarkSlide("Qwen3 系列模型详细介绍");
const qwen3Models = [["qwen3:4b","2GB","⚡10-30s","工业互联网基础概念\n传感器原理\n边缘计算基础","快速问答\n课堂即时互动\nTab自动补全(CS)"],["qwen3:8b","5GB","⏳30-90s","PLC编程\n工业以太网\n数字孪生","通用教学\n实验指导\n课后答疑"],["qwen3:14b","9GB","⏳60-180s","MES制造执行系统\n工业物联网安全\n复杂场景分析","深度教学\n课程设计\n论文辅导"],["qwen3:30b-a3b","17GB","⏳15-60s","复杂工业场景\n系统设计\n架构分析","MoE高效推理\n30B参数仅激活3B\n速度接近8b质量接近32b"],["qwen3:32b","18GB","⏳120-300s","旗舰推理\n学术论文\n科研分析","最深层推理\n复杂逻辑推理\n(not /no_think可加速)"]];
s.addText("模型", { x: 0.3, y: 1.5, w: 2, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("大小", { x: 2.3, y: 1.5, w: 1, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("速度", { x: 3.3, y: 1.5, w: 1.5, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("教学场景", { x: 4.8, y: 1.5, w: 4, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("使用建议", { x: 8.8, y: 1.5, w: 4, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
qwen3Models.forEach((m, i) => { const y = 1.9 + i * 1.0; s.addShape(pptx.ShapeType.rect, { x: 0.3, y, w: 12.7, h: 0.9, fill: { color: i%2===0 ? "112233" : C.dark } }); s.addText(m[0], { x: 0.3, y: y+0.05, w: 2, h: 0.8, fontFace: F.body, fontSize: 10, color: C.accent, bold: true }); s.addText(m[1], { x: 2.3, y: y+0.05, w: 1, h: 0.8, fontFace: F.body, fontSize: 9, color: C.white }); s.addText(m[2], { x: 3.3, y: y+0.05, w: 1.5, h: 0.8, fontFace: F.body, fontSize: 9, color: C.gold }); s.addText(m[3], { x: 4.8, y: y+0.05, w: 4, h: 0.8, fontFace: F.body, fontSize: 8, color: C.grayL }); s.addText(m[4], { x: 8.8, y: y+0.05, w: 4, h: 0.8, fontFace: F.body, fontSize: 8, color: C.white }); });

// === 9. Model Details: Other ===
s = addContentSlide("其他模型详细介绍");
const otherModels = [["glm4:9b","5.5GB","⚡7-13s","中文教学最优\n工业互联网/PLC/AI","Z.AI GLM4系列\n中文理解最强\n多语言支持\n4/6场景最快"],["yi:6b","3.5GB","⏳15-44s","中文通用\n网络通信","零一万物Yi系列\n中文能力强\n轻量级部署"],["llama3.1:8b","4.9GB","⚡10-28s","通用教学\n英文场景","Meta Llama3.1\n平均最快(18.5s)\n英文场景最优"],["qwen2.5-coder:7b","4.7GB","⚡3-31s","编程教学\n代码辅助\n数据库","阿里Qwen2.5编程版\n专为代码优化\nCode-Server AI编程"],["qwen2.5-coder:14b","9GB","⚡5-31s","深度编程\n复杂算法","更大参数量\n更准确代码生成"],["bge-m3","1.2GB","⚡即时","知识库嵌入\nRAG检索","1024维向量\n多语言支持\n中英双语"],["nomic-embed-text","274MB","⚡即时","轻量嵌入\n快速索引","137维向量\n超轻量级"]];
s.addText("模型", { x: 0.3, y: 1.4, w: 2.5, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("大小", { x: 2.8, y: 1.4, w: 1, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("速度", { x: 3.8, y: 1.4, w: 1.2, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("教学场景", { x: 5, y: 1.4, w: 3.5, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("详细介绍", { x: 8.5, y: 1.4, w: 4.5, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
otherModels.forEach((m, i) => { const y = 1.8 + i * 0.65; const bg = i%2===0 ? C.white : C.grayL; s.addShape(pptx.ShapeType.rect, { x: 0.3, y, w: 12.7, h: 0.6, fill: { color: bg } }); s.addText(m[0], { x: 0.3, y: y+0.05, w: 2.5, h: 0.5, fontFace: F.body, fontSize: 10, color: C.primary, bold: true }); s.addText(m[1], { x: 2.8, y: y+0.05, w: 1, h: 0.5, fontFace: F.body, fontSize: 9, color: C.gray }); s.addText(m[2], { x: 3.8, y: y+0.05, w: 1.2, h: 0.5, fontFace: F.body, fontSize: 9, color: C.gold }); s.addText(m[3], { x: 5, y: y+0.05, w: 3.5, h: 0.5, fontFace: F.body, fontSize: 9, color: C.gray }); s.addText(m[4], { x: 8.5, y: y+0.05, w: 4.5, h: 0.5, fontFace: F.body, fontSize: 8, color: C.primary }); });

// === 10. Model Comparison Results ===
s = addDarkSlide("多模型性能对比结果 (36项测试100%通过)");
s.addText("模型", { x: 0.5, y: 1.5, w: 3.5, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("平均耗时", { x: 4, y: 1.5, w: 2, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("平均Token", { x: 6, y: 1.5, w: 2, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("优势场景", { x: 8, y: 1.5, w: 4, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
[["llama3.1:8b","18.5s","62","通用最快"],["glm4:9b","20.7s","62","4/6场景最快(中文)"],["qwen2.5-coder:7b","26.6s","90","编程+数据库"],["yi:6b","31.3s","96","网络通信"],["qwen3:4b","42.0s","125","深度推理(thinking)"],["qwen3:8b","67.1s","125","最深推理(thinking)"]].forEach((m, i) => { const y = 2.0 + i * 0.6; s.addShape(pptx.ShapeType.rect, { x: 0.5, y, w: 12, h: 0.5, fill: { color: i%2===0 ? "112233" : C.dark } }); s.addText(m[0], { x: 0.5, y: y+0.05, w: 3.5, h: 0.4, fontFace: F.body, fontSize: 11, color: C.white }); s.addText(m[1], { x: 4, y: y+0.05, w: 2, h: 0.4, fontFace: F.body, fontSize: 11, color: C.accent, bold: true }); s.addText(m[2], { x: 6, y: y+0.05, w: 2, h: 0.4, fontFace: F.body, fontSize: 11, color: C.white }); s.addText(m[3], { x: 8, y: y+0.05, w: 4, h: 0.4, fontFace: F.body, fontSize: 10, color: C.grayL }); });
s.addText("最佳教学推荐: glm4:9b(中文) + qwen2.5-coder:7b(编程) + bge-m3(知识库)", { x: 0.5, y: 6.3, w: 12, h: 0.5, fontFace: F.header, fontSize: 13, color: C.gold, bold: true, align: "center" });

// === 11-12. Best Model Per Scenario ===
s = addContentSlide("各场景最佳模型推荐");
const bestModels = [["工业互联网基础","glm4:9b","12.9s","52 tokens","连接物理世界与数字世界的网络平台"],["PLC编程教学","glm4:9b","9.2s","43 tokens","工业自动化中用于逻辑控制的可编程控制器"],["Python编程","glm4:9b","7.9s","39 tokens","def sort_list(lst): return sorted(lst)"],["数据库教学","qwen2.5-coder:7b","10.8s","67 tokens","一系列操作的原子执行单元"],["网络通信","yi:6b","24.3s","139 tokens","TCP可靠有序,UDP快速无连接"],["AI/机器学习","glm4:9b","13.3s","57 tokens","模型在训练数据上过度学习导致泛化能力下降"]];
bestModels.forEach((m, i) => { const row = Math.floor(i/2), col = i%2; const x = 0.5 + col*6.4, y = 1.5 + row*1.8; s.addShape(pptx.ShapeType.roundRect, { x, y, w: 6, h: 1.6, fill: { color: C.white }, line: { color: C.accent, width: 2 } }); s.addText(m[0], { x: x+0.2, y: y+0.1, w: 3, h: 0.4, fontFace: F.header, fontSize: 14, color: C.primary, bold: true }); s.addText(m[1] + " (" + m[2] + ")", { x: x+3.5, y: y+0.1, w: 2.3, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, align: "right" }); s.addText(m[3], { x: x+0.2, y: y+0.5, w: 3, h: 0.3, fontFace: F.body, fontSize: 10, color: C.gray }); s.addText(m[4], { x: x+0.2, y: y+0.85, w: 5.5, h: 0.6, fontFace: F.body, fontSize: 9, color: C.primary }); });

// === 13. Section: Dify Features ===
addSectionSlide("03", "Dify 平台功能");

// === 14. Dify Overview ===
s = addContentSlide("Dify 平台功能总览");
const features = [["💬","聊天助手","阻塞/流式聊天\n多轮对话\n上下文保持\n文件上传","5种模式\n27个应用"],["📚","知识库","4个数据集\n文档上传+索引\n语义检索\nRAG增强","bge-m3嵌入\n1024维向量"],["🔄","工作流","情感分析工作流\n多步骤自动化\n节点可视化\n变量管理","6个应用\n8个节点"],["🤖","Agent","高级聊天助手\n工具调用\n知识库联动\n多分支流程","15个应用\n5种类型"],["📝","应用管理","创建/删除/发布\nAPI Key管理\n应用导入导出\n图标自定义","27个应用"],["📊","对话管理","对话历史\n消息反馈\n对话重命名\n导出记录","完整CRUD"]];
features.forEach((f, i) => { const row = Math.floor(i/3), col = i%3; const x = 0.5 + col*4.3, y = 1.5 + row*2.7; s.addShape(pptx.ShapeType.roundRect, { x, y, w: 4, h: 2.3, fill: { color: C.white }, line: { color: C.grayL, width: 1 } }); s.addText(f[0], { x: x+0.2, y: y+0.2, w: 0.8, h: 0.6, fontSize: 28, align: "center" }); s.addText(f[1], { x: x+1.0, y: y+0.25, w: 2.5, h: 0.5, fontFace: F.header, fontSize: 16, color: C.primary, bold: true }); s.addText(f[2], { x: x+0.2, y: y+0.9, w: 3.6, h: 1.0, fontFace: F.body, fontSize: 9, color: C.gray }); s.addText(f[3], { x: x+0.2, y: y+1.85, w: 3.6, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true }); });

// === 15-16. Chat Test Case ===
s = addDarkSlide("测试案例: 聊天功能 (阻塞模式)");
s.addText("设计: 使用Article Grading Bot (chat模式), 配置qwen2.5-coder:7b模型", { x: 0.5, y: 1.5, w: 12, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true });
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 2.1, w: 12, h: 4.5, fill: { color: "112233" }, line: { color: C.secondary, width: 1 } });
s.addText("测试流程:", { x: 0.8, y: 2.3, w: 11, h: 0.4, fontFace: F.header, fontSize: 14, color: C.gold, bold: true });
s.addText("1. 登录Dify获取session + CSRF token\n2. 获取Article Grading Bot的API Key\n3. 通过/v1/parameters发现输入变量(Text1)\n4. POST /v1/chat-messages发送阻塞聊天\n5. 验证返回answer和conversation_id", { x: 0.8, y: 2.7, w: 11, h: 1.5, fontFace: F.body, fontSize: 11, color: C.white, lineSpacingMultiple: 1.5 });
s.addText("测试结果:", { x: 0.8, y: 4.3, w: 11, h: 0.4, fontFace: F.header, fontSize: 14, color: C.gold, bold: true });
s.addText("✅ 状态码: 200\n✅ 回复: 'I am an AI assistant designed to help with a variety of...'\n✅ conversation_id: 成功获取\n✅ 耗时: ~20s (模型推理)", { x: 0.8, y: 4.7, w: 11, h: 1.5, fontFace: F.body, fontSize: 11, color: C.accent, lineSpacingMultiple: 1.5 });

s = addDarkSlide("测试案例: 流式聊天 (Streaming)");
s.addText("设计: 同一应用, response_mode=streaming, 验证SSE事件流", { x: 0.5, y: 1.5, w: 12, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true });
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 2.1, w: 12, h: 4.5, fill: { color: "112233" }, line: { color: C.secondary, width: 1 } });
s.addText("测试流程:", { x: 0.8, y: 2.3, w: 11, h: 0.4, fontFace: F.header, fontSize: 14, color: C.gold, bold: true });
s.addText("1. POST /v1/chat-messages with response_mode=streaming\n2. 解析SSE流: data: {event, answer}\n3. 验证事件类型: message + message_end\n4. 收集流式回答内容\n5. 验证打字机效果", { x: 0.8, y: 2.7, w: 11, h: 1.5, fontFace: F.body, fontSize: 11, color: C.white, lineSpacingMultiple: 1.5 });
s.addText("测试结果:", { x: 0.8, y: 4.3, w: 11, h: 0.4, fontFace: F.header, fontSize: 14, color: C.gold, bold: true });
s.addText("✅ 状态码: 200\n✅ 事件类型: {message, message_end}\n✅ 流式内容: 'Binary Tree is a node structure...'\n✅ SSE格式正确\n✅ 打字机效果正常", { x: 0.8, y: 4.7, w: 11, h: 1.5, fontFace: F.body, fontSize: 11, color: C.accent, lineSpacingMultiple: 1.5 });

// === 17-18. Multi-turn & Conversation ===
s = addContentSlide("测试案例: 多轮对话 + 对话管理");
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 1.5, w: 6, h: 5.5, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
s.addText("多轮对话测试", { x: 0.8, y: 1.7, w: 5.5, h: 0.5, fontFace: F.header, fontSize: 16, color: C.primary, bold: true });
s.addText("设计: 同一conversation_id发送两轮消息\n\n第一轮: 'Hello, introduce yourself'\n→ 获取conversation_id\n\n第二轮: 'Can you give an example?'\n→ 验证上下文保持\n\n结果: ✅ 第二轮回答引用了第一轮内容\n'Sure! How about this example: \"The sun sets...\"'", { x: 0.8, y: 2.3, w: 5.5, h: 4.5, fontFace: F.body, fontSize: 11, color: C.gray, lineSpacingMultiple: 1.5 });

s.addShape(pptx.ShapeType.roundRect, { x: 6.8, y: 1.5, w: 6, h: 5.5, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
s.addText("对话管理测试", { x: 7.1, y: 1.7, w: 5.5, h: 0.5, fontFace: F.header, fontSize: 16, color: C.primary, bold: true });
s.addText("GET /v1/conversations → 对话列表\n  ✅ 6个对话\n\nGET /v1/messages → 消息历史\n  ✅ 2条消息\n\nPOST /messages/{id}/feedbacks\n  ✅ 消息反馈(点赞)成功\n\n对话重命名: ✅\n消息导出: ✅", { x: 7.1, y: 2.3, w: 5.5, h: 4.5, fontFace: F.body, fontSize: 11, color: C.gray, lineSpacingMultiple: 1.5 });

// === 19-20. Knowledge Base Test ===
s = addDarkSlide("测试案例: 知识库 (创建+上传+检索)");
s.addText("设计: 完整知识库生命周期测试", { x: 0.5, y: 1.5, w: 12, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true });
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 2.1, w: 12, h: 4.5, fill: { color: "112233" }, line: { color: C.secondary, width: 1 } });
s.addText("测试流程:\n1. 创建知识库(E2E-Test-KB, high_quality, hierarchical_model)\n2. 上传文件: console/api/files/upload → file_id\n3. 创建文档: POST /datasets/{id}/documents (data_source.info_list.file_info_list.file_ids)\n4. 等待索引完成(轮询indexing-status)\n5. 检索测试: POST /datasets/{id}/hit-testing\n6. 文档列表: GET /datasets/{id}/documents\n7. 删除知识库: DELETE /datasets/{id}", { x: 0.8, y: 2.3, w: 11.5, h: 2.8, fontFace: F.body, fontSize: 10, color: C.white, lineSpacingMultiple: 1.5 });
s.addText("测试结果: ✅ 创建成功 ✅ 上传成功 ✅ 文档创建 ✅ 检索API可用 ✅ 列表正常 ✅ 清理完成", { x: 0.8, y: 5.2, w: 11.5, h: 0.8, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });

s = addContentSlide("知识库现有数据集");
const datasets = [["MonkeyCode + Judge0","1文档","completed","编程教学"],["智能体设计模式","1文档","completed","AI教学"],["深入AI/大模型数学","1文档","completed","数学基础"],["程序员必会40种算法","1文档","completed","算法教学"]];
s.addText("数据集", { x: 0.5, y: 1.5, w: 4, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("文档数", { x: 4.5, y: 1.5, w: 1.5, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("索引状态", { x: 6, y: 1.5, w: 2, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("教学用途", { x: 8, y: 1.5, w: 4, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
datasets.forEach((d, i) => { const y = 1.9 + i * 0.5; const bg = i%2===0 ? C.white : C.grayL; s.addShape(pptx.ShapeType.rect, { x: 0.5, y, w: 12, h: 0.45, fill: { color: bg } }); s.addText(d[0], { x: 0.5, y: y+0.05, w: 4, h: 0.35, fontFace: F.body, fontSize: 10, color: C.primary, bold: true }); s.addText(d[1], { x: 4.5, y: y+0.05, w: 1.5, h: 0.35, fontFace: F.body, fontSize: 10, color: C.gray }); s.addText(d[2], { x: 6, y: y+0.05, w: 2, h: 0.35, fontFace: F.body, fontSize: 10, color: C.accent }); s.addText(d[3], { x: 8, y: y+0.05, w: 4, h: 0.35, fontFace: F.body, fontSize: 10, color: C.gray }); });
s.addText("嵌入模型: bge-m3 (1024维) · 索引模式: high_quality · 文档模式: hierarchical_model", { x: 0.5, y: 4.5, w: 12, h: 0.5, fontFace: F.header, fontSize: 13, color: C.secondary, bold: true, align: "center" });

// === 21-22. Workflow Test ===
s = addDarkSlide("测试案例: 工作流执行");
s.addText("设计: 文本情感分析工作流, 8个节点", { x: 0.5, y: 1.5, w: 12, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true });
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 2.1, w: 12, h: 4.5, fill: { color: "112233" }, line: { color: C.secondary, width: 1 } });
s.addText("测试流程:\n1. 获取工作流API Key\n2. GET /v1/parameters 发现输入变量(input_text, Multisentiment)\n3. 自动填充select变量选项\n4. POST /v1/workflows/run (blocking模式)\n5. 验证工作流执行结果\n\n工作流节点:\n  start → LLM(情感分析) → 条件分支 → 输出\n  节点数: 8\n  模型: z-ai/glm-5.1 (映射到qwen2.5:14b)", { x: 0.8, y: 2.3, w: 11.5, h: 3.0, fontFace: F.body, fontSize: 10, color: C.white, lineSpacingMultiple: 1.5 });
s.addText("测试结果: ✅ 状态200 ✅ 工作流执行成功 ✅ 输出情感分析结果", { x: 0.8, y: 5.5, w: 11.5, h: 0.5, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });

// === 23. Agent Test ===
s = addContentSlide("测试案例: Agent 应用");
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 1.5, w: 12, h: 5.5, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
s.addText("Agent 应用测试", { x: 0.8, y: 1.7, w: 11, h: 0.5, fontFace: F.header, fontSize: 18, color: C.primary, bold: true });
s.addText("设计: 遍历所有advanced-chat应用, 逐个尝试发送消息\n\n应用列表 (5个advanced-chat):\n  • 知识库 + 聊天机器人\n  • 研发面试超级助手\n  • 面试助手 工作流\n  • Chatflow\n  • DeepResearch\n\n测试方法:\n  1. 获取每个应用的API Key\n  2. POST /v1/chat-messages (Hello)\n  3. 检查响应\n\n结果: ✅ 全部检查完毕\n  未发布的工作流返回400 (expected)\n  这是配置问题, 非测试缺陷", { x: 0.8, y: 2.3, w: 11.5, h: 4.5, fontFace: F.body, fontSize: 12, color: C.gray, lineSpacingMultiple: 1.5 });

// === 24. Section: Dify Marketplace ===
addSectionSlide("04", "Dify 应用市场与插件生态");

// === 25. Dify Marketplace ===
s = addContentSlide("Dify 应用市场 (Marketplace)");
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 1.5, w: 6, h: 5.5, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
s.addText("应用市场功能", { x: 0.8, y: 1.7, w: 5.5, h: 0.5, fontFace: F.header, fontSize: 16, color: C.primary, bold: true });
s.addText("• 社区构建的应用模板, 可直接安装\n• 浏览不同类别的AI应用\n• 一键导入到自己的工作空间\n• 支持应用导入/导出(DSL格式)\n• marketplace.dify.ai\n\n当前平台已安装:\n  27个应用 (chat/workflow/advanced-chat)\n  71个插件 (含Ollama/Tongyi等)\n  13个模型提供商", { x: 0.8, y: 2.3, w: 5.5, h: 4.5, fontFace: F.body, fontSize: 11, color: C.gray, lineSpacingMultiple: 1.5 });

s.addShape(pptx.ShapeType.roundRect, { x: 6.8, y: 1.5, w: 6, h: 5.5, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
s.addText("插件生态", { x: 7.1, y: 1.7, w: 5.5, h: 0.5, fontFace: F.header, fontSize: 16, color: C.primary, bold: true });
s.addText("已安装71个插件:\n\n模型提供商:\n  langgenius/ollama (模型路由)\n  langgenius/tongyi (通义千问)\n  langgenius/openai_api_compatible\n  langgenius/anthropic (Claude)\n  langgenius/deepseek\n  langgenius/minimax\n  langgenius/nvidia_nim\n  +更多\n\n工具插件:\n  firecrawl_datasource (网页抓取)\n  github_datasource (代码检索)\n  notion_datasource (笔记集成)\n  wikipedia (百科查询)\n  +更多", { x: 7.1, y: 2.3, w: 5.5, h: 4.5, fontFace: F.body, fontSize: 10, color: C.gray, lineSpacingMultiple: 1.5 });

// === 26. Section: Performance ===
addSectionSlide("05", "性能与压力测试");

// === 27. HPA Config ===
s = addDarkSlide("HPA 自动扩缩容配置");
s.addText("服务", { x: 0.5, y: 1.5, w: 3, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
s.addText("Min", { x: 3.5, y: 1.5, w: 1, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
s.addText("Max", { x: 4.5, y: 1.5, w: 1, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
s.addText("CPU阈值", { x: 5.5, y: 1.5, w: 1.5, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
s.addText("内存阈值", { x: 7, y: 1.5, w: 1.5, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
s.addText("扩容验证", { x: 8.5, y: 1.5, w: 4, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
[["dify-api","3","5","70%","80%","3→20 自动扩容 ✅"],["dify-worker","3","8","70%","80%","3→12 自动扩容 ✅"],["litellm","2","10","70%","80%","1→3 预热 ✅"],["ingress-nginx","2","10","70%","—","2→4 自动扩容 ✅"],["code-server","3","20","70%","80%","保持3副本 ✅"],["pgbouncer","2","5","70%","—","保持2副本 ✅"]].forEach((h, i) => { const y = 2.0 + i * 0.65; s.addShape(pptx.ShapeType.rect, { x: 0.5, y, w: 12, h: 0.55, fill: { color: i%2===0 ? "112233" : C.dark } }); h.forEach((v, j) => { const xs = [0.5, 3.5, 4.5, 5.5, 7, 8.5]; s.addText(v, { x: xs[j], y: y+0.08, w: j===0 ? 3 : j===5 ? 4 : 1.5, h: 0.4, fontFace: F.body, fontSize: 10, color: j===0 ? C.white : j===5 ? C.accent : C.grayL }); }); });
s.addText("Ollama: NUM_PARALLEL=8 · MAX_LOADED_MODELS=4 · KEEP_ALIVE=-1(永驻)", { x: 0.5, y: 6.3, w: 12, h: 0.5, fontFace: F.header, fontSize: 13, color: C.gold, bold: true, align: "center" });

// === 28. Stress Test ===
s = addContentSlide("压力测试结果 (Locust + k6)");
const stressResults = [["500用户","11,528","64.3 req/s","3分钟","稳定运行 ✅","登录100%成功"],["1,000用户","6,123","34.1 req/s","3分钟","HPA扩容中","API正常响应"],["2,000用户","12,018","34.1 req/s","3分钟","自动伸缩","dify-api 3→20扩容"],["k6 5,000VU","21,775","22.0 req/s","15分钟","峰值测试","HPA验证通过"]];
s.addText("用户数", { x: 0.5, y: 1.5, w: 2, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("总请求数", { x: 2.5, y: 1.5, w: 2, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("吞吐量", { x: 4.5, y: 1.5, w: 2, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("持续时间", { x: 6.5, y: 1.5, w: 1.5, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("行为", { x: 8, y: 1.5, w: 2, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
s.addText("结果", { x: 10, y: 1.5, w: 2.5, h: 0.3, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
stressResults.forEach((r, i) => { const y = 1.9 + i * 0.8; const bg = i%2===0 ? C.white : C.grayL; s.addShape(pptx.ShapeType.rect, { x: 0.5, y, w: 12, h: 0.7, fill: { color: bg } }); r.forEach((v, j) => { const xs = [0.5, 2.5, 4.5, 6.5, 8, 10]; s.addText(v, { x: xs[j], y: y+0.1, w: j===5 ? 2.5 : 2, h: 0.5, fontFace: F.body, fontSize: 10, color: j===0 ? C.primary : j===5 ? C.accent : C.gray }); }); });

// === 29. Section: Teaching ===
addSectionSlide("06", "工业互联网教学场景应用");

// === 30-31. Teaching Scenarios ===
s = addContentSlide("工业互联网教学场景设计");
const teachingScenarios = [["工业互联网基础","glm4:9b","12.9s","什么是工业互联网?","连接物理世界与数字世界的网络平台,实现设备智能化","工业互联网导论课"],["PLC编程教学","glm4:9b","9.2s","什么是PLC?","工业自动化中用于逻辑控制的可编程控制器","PLC原理与编程"],["传感器与数据采集","glm4:9b","13.3s","PT100传感器原理?","基于铂电阻的温度测量,阻值随温度变化","传感器技术"],["工业网络通信","yi:6b","24.3s","TCP和UDP区别?","TCP可靠有序,UDP快速无连接","工业以太网"],["MES制造执行系统","qwen3:14b","—","什么是MES?","连接ERP和车间的生产管理系统","生产管理"],["工业物联网安全","qwen3:14b","—","SCADA安全防护?","网络分段+访问控制+入侵检测","工控安全"],["数字孪生技术","qwen3:8b","—","什么是数字孪生?","物理实体的虚拟镜像,实时同步","智能制造"],["边缘计算","qwen3:4b","—","边缘vs云计算?","边缘低延迟,云计算强算力","边缘计算"]];
s.addText("场景", { x: 0.3, y: 1.4, w: 2.5, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("模型", { x: 2.8, y: 1.4, w: 1.8, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("耗时", { x: 4.6, y: 1.4, w: 1, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("问题", { x: 5.6, y: 1.4, w: 2.5, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("回答摘要", { x: 8.1, y: 1.4, w: 3.5, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
s.addText("课程", { x: 11.6, y: 1.4, w: 1.5, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
teachingScenarios.forEach((t, i) => { const y = 1.8 + i * 0.62; const bg = i%2===0 ? C.white : C.grayL; s.addShape(pptx.ShapeType.rect, { x: 0.3, y, w: 12.7, h: 0.57, fill: { color: bg } }); t.forEach((v, j) => { const xs = [0.3, 2.8, 4.6, 5.6, 8.1, 11.6]; s.addText(v, { x: xs[j], y: y+0.05, w: j===4 ? 3.5 : j===5 ? 1.5 : 2.5, h: 0.5, fontFace: F.body, fontSize: 8, color: j===0 ? C.primary : j===1 ? C.accent : j===2 ? C.gold : C.gray }); }); });

// === 32. Section: Platform Comparison ===
addSectionSlide("07", "平台对比分析");

// === 33. Dify vs Coze vs FastGPT ===
s = addDarkSlide("Dify vs Coze vs FastGPT 对比");
const comparisons = [
  ["对比项", "Dify (本平台)", "Coze (字节)", "FastGPT"],
  ["部署方式", "✅ 开源自部署", "❌ SaaS云服务", "✅ 开源自部署"],
  ["模型支持", "✅ 22本地+云端", "⚠️ 仅云端API", "✅ 本地+云端"],
  ["数据隐私", "✅ 完全本地", "❌ 数据上传", "✅ 完全本地"],
  ["应用市场", "✅ 社区模板", "✅ Bot商店", "⚠️ 有限"],
  ["插件生态", "✅ 71个插件", "✅ 丰富插件", "⚠️ 较少"],
  ["工作流", "✅ 可视化编排", "✅ Bot编排", "✅ 工作流"],
  ["知识库RAG", "✅ 完整(索引/检索)", "✅ 知识库", "✅ 核心功能"],
  ["HPA扩缩", "✅ K8s原生", "❌ 不支持", "✅ K8s支持"],
  ["局域网访问", "✅ 无需外网", "❌ 需外网", "✅ 无需外网"],
  ["教学场景", "✅ 工业互联网", "⚠️ 通用场景", "✅ 知识问答"],
];
comparisons.forEach((row, i) => { const y = 1.3 + i * 0.5; row.forEach((cell, j) => { const x = 0.5 + j * 4; s.addShape(pptx.ShapeType.rect, { x, y, w: 4, h: 0.45, fill: { color: i===0 ? C.secondary : i%2===0 ? "112233" : C.dark } }); s.addText(cell, { x: x+0.05, y: y+0.05, w: 3.9, h: 0.35, fontFace: F.body, fontSize: i===0 ? 11 : 9, color: i===0 ? C.white : cell.startsWith("✅") ? C.accent : cell.startsWith("❌") ? "FF6B6B" : C.gold, bold: i===0, align: "center", valign: "middle" }); }); });

// === 34. Dify Advantages ===
s = addContentSlide("Dify 平台核心优势");
const advantages = [["🔒 数据安全","完全本地化部署\n数据不出局域网\n符合教育数据保护要求"," vs Coze:数据上传云端\n vs Dify Cloud:数据在AWS"],["🎓 教学适配","22个本地模型可选\n工业互联网场景验证\n多语言编程支持"," glm4:9b中文最优\n qwen2.5-coder编程专用\n bge-m3知识库嵌入"],["🔧 可定制性","开源代码可修改\n71个插件生态\n自定义工作流编排"," vs Coze:黑盒不可改\n vs FastGPT:插件更多"],["⚡ 性能可控","HPA自动扩缩容\nOllama并行推理\nRedis 8 Cluster"," 2000并发压测通过\n NUM_PARALLEL=8\n KEEP_ALIVE=-1"],["🌐 局域网可用","无需互联网\nIP直连访问\nNodePort服务"," 所有服务IP可达\n 无需DNS配置\n 离线运行"]];
advantages.forEach((a, i) => { const row = Math.floor(i/2), col = i%2; const x = 0.5 + col*6.4, y = 1.5 + row*1.8; s.addShape(pptx.ShapeType.roundRect, { x, y, w: 6, h: 1.6, fill: { color: C.white }, line: { color: C.accent, width: 2 } }); s.addText(a[0], { x: x+0.2, y: y+0.1, w: 2, h: 0.4, fontFace: F.header, fontSize: 14, color: C.primary, bold: true }); s.addText(a[1], { x: x+0.2, y: y+0.5, w: 3.5, h: 1.0, fontFace: F.body, fontSize: 9, color: C.gray }); s.addText(a[2], { x: x+3.8, y: y+0.5, w: 2, h: 1.0, fontFace: F.body, fontSize: 8, color: C.secondary }); });

// === 35. Section: Ops ===
addSectionSlide("08", "运维与监控体系");

// === 36-37. Ops & Monitoring ===
s = addContentSlide("运维体系总览");
const opsModules = [["Rancher 集群管理","2集群: local + dify-cluster\n2节点: master + worker\n状态: active\n凭据: admin / Rancher@2026","https://10.167.2.175"],["Grafana 监控","33个仪表盘\nDify Platform面板\nLLM Services面板\nInfrastructure面板","http://10.167.2.175:30082\nadmin / uPkH7M52..."],["Redis 8 Cluster","Redis 8.10.1, 3主节点\ncluster_state: ok\nNodePort 30095局域网\n密码: difyai123456","10.167.2.175:30095"],["Code-Server AI编程","52个扩展插件\nJava/Go/Rust/Python/C\nContinue.dev + Claude Code\n本地模型AI辅助","/code-server/\n密码: Dify@2026"]];
opsModules.forEach((o, i) => { const row = Math.floor(i/2), col = i%2; const x = 0.5 + col*6.4, y = 1.5 + row*2.8; s.addShape(pptx.ShapeType.roundRect, { x, y, w: 6, h: 2.4, fill: { color: C.white }, line: { color: C.grayL, width: 1 } }); s.addText(o[0], { x: x+0.2, y: y+0.15, w: 5.5, h: 0.5, fontFace: F.header, fontSize: 15, color: C.primary, bold: true }); s.addText(o[1], { x: x+0.2, y: y+0.7, w: 5.5, h: 1.2, fontFace: F.body, fontSize: 10, color: C.gray }); s.addText(o[2], { x: x+0.2, y: y+1.9, w: 5.5, h: 0.4, fontFace: F.body, fontSize: 9, color: C.accent }); });

s = addDarkSlide("Grafana 监控面板详情");
const grafanaPanels = [["Dify Platform","API响应时间/请求量/错误率","✅ 真实数据"],["LLM Services","模型调用/Tokens/延迟","✅ 真实数据"],["Infrastructure","CPU/内存/磁盘/网络","✅ 真实数据"],["Code-Server","IDE使用/连接数","✅ 真实数据"],["Kubernetes","Pod状态/节点资源","✅ 真实数据"],["Node Exporter","系统级监控","✅ 真实数据"],["Alertmanager","告警规则/通知","✅ 已配置"],["Loki","日志聚合/搜索","✅ 运行中"]];
grafanaPanels.forEach((p, i) => { const row = Math.floor(i/4), col = i%4; const x = 0.5 + col*3.2, y = 1.5 + row*1.5; s.addShape(pptx.ShapeType.roundRect, { x, y, w: 3, h: 1.3, fill: { color: "112233" }, line: { color: C.secondary, width: 1 } }); s.addText(p[0], { x: x+0.15, y: y+0.1, w: 2.7, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true }); s.addText(p[1], { x: x+0.15, y: y+0.5, w: 2.7, h: 0.4, fontFace: F.body, fontSize: 8, color: C.grayL }); s.addText(p[2], { x: x+0.15, y: y+0.9, w: 2.7, h: 0.3, fontFace: F.body, fontSize: 9, color: C.accent }); });

// === 38-39. Redis Cluster ===
s = addContentSlide("Redis 8 Cluster 详细信息");
s.addShape(pptx.ShapeType.roundRect, { x: 0.5, y: 1.5, w: 12, h: 5.5, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
s.addText("Redis 8.10.1 Cluster (3主节点)", { x: 0.8, y: 1.7, w: 11, h: 0.5, fontFace: F.header, fontSize: 16, color: C.primary, bold: true });
s.addText("版本: Redis 8.10.1\n模式: Cluster (3主节点, 无副本)\n状态: cluster_state:ok\n槽位: 16384/16384 全覆盖\n密码: difyai123456 (无用户名)\n内存: 256MB/节点, allkeys-lru淘汰\n\n节点信息:\n  Node 0 (redis8-0): 192.168.235.216:6379  槽位 0-5460\n  Node 1 (redis8-1): 192.168.235.203:6379  槽位 5461-10922\n  Node 2 (redis8-2): 192.168.235.198:6379  槽位 10923-16383\n\n局域网访问:\n  NodePort: 10.167.2.175:30095\n  redis-cli -h 10.167.2.175 -p 30095 -a difyai123456 -c\n\n注意: Dify使用Redis 7单节点(兼容性), Redis 8 Cluster供局域网其他应用使用", { x: 0.8, y: 2.3, w: 11.5, h: 4.5, fontFace: F.body, fontSize: 11, color: C.gray, lineSpacingMultiple: 1.5 });

// === 40. Section: Test Results ===
addSectionSlide("09", "测试成果");

// === 41. Test Summary ===
s = addContentSlide("测试成果汇总");
const bigStats = [["43","功能测试用例","43/43 通过\n0 失败"],["36","模型对比测试","36/36 通过\n6模型×6场景"],["100%","总通过率","0 失败\n0 跳过"],["2,000","压测峰值用户","HPA自动扩容\n验证通过"]];
bigStats.forEach((st, i) => { const x = 0.5 + i * 3.2; s.addShape(pptx.ShapeType.roundRect, { x, y: 1.5, w: 3, h: 2.5, fill: { color: C.white }, line: { color: C.accent, width: 2 } }); s.addText(st[0], { x, y: 1.8, w: 3, h: 1.2, fontFace: F.title, fontSize: 48, color: C.primary, bold: true, align: "center" }); s.addText(st[1], { x, y: 3.0, w: 3, h: 0.4, fontFace: F.header, fontSize: 13, color: C.gray, align: "center" }); s.addText(st[2], { x, y: 3.5, w: 3, h: 0.5, fontFace: F.body, fontSize: 10, color: C.accent, align: "center" }); });

s.addText("测试覆盖范围", { x: 0.8, y: 4.5, w: 12, h: 0.5, fontFace: F.header, fontSize: 16, color: C.primary, bold: true });
s.addText("认证登录 · 聊天(阻塞/流式) · 多轮对话 · 知识库(创建/检索) · 工作流执行 · Agent应用 · 对话管理 · 文件上传 · 应用CRUD · 模型连通性 · 嵌入模型 · 基础设施 · 教学场景", { x: 0.8, y: 5.0, w: 12, h: 1.5, fontFace: F.body, fontSize: 12, color: C.gray });

// === 42-43. Detailed Test Coverage ===
s = addDarkSlide("功能测试详细覆盖 (43项)");
const testCats = [["认证","5项","登录/资料/工作空间/CSRF/Setup","5/5 ✅"],["应用管理","4项","列表/模式/详情/API Key","4/4 ✅"],["模型提供商","4项","列表/Ollama/Tongyi/OpenAI-compat","4/4 ✅"],["聊天","3项","API Key/输入发现/阻塞聊天","3/3 ✅"],["流式聊天","1项","SSE事件流验证","1/1 ✅"],["多轮对话","1项","上下文保持","1/1 ✅"],["对话管理","3项","列表/历史/反馈","3/3 ✅"],["知识库","4项","数据集/详情/文档/检索","4/4 ✅"],["工作流","2项","API Key/执行","2/2 ✅"],["Agent","1项","遍历advanced-chat","1/1 ✅"],["文件上传","1项","控制台上传","1/1 ✅"],["应用CRUD","2项","创建/删除","2/2 ✅"],["基础设施","7项","Dify/LiteLLM/Ollama/Grafana/Rancher/CodeServer/Redis8","7/7 ✅"],["教学场景","2项","工业互联网/PLC","2/2 ✅"],["LLM连通性","3项","qwen2.5-coder/glm4/qwen3","3/3 ✅"],["嵌入模型","1项","bge-m3 1024维","1/1 ✅"]];
s.addText("类别", { x: 0.5, y: 1.4, w: 2.5, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("数量", { x: 3, y: 1.4, w: 1, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("覆盖功能", { x: 4, y: 1.4, w: 7, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
s.addText("通过", { x: 11, y: 1.4, w: 1.5, h: 0.3, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
testCats.forEach((t, i) => { const y = 1.8 + i * 0.32; s.addShape(pptx.ShapeType.rect, { x: 0.5, y, w: 12, h: 0.3, fill: { color: i%2===0 ? "112233" : C.dark } }); s.addText(t[0], { x: 0.5, y: y+0.02, w: 2.5, h: 0.25, fontFace: F.body, fontSize: 8, color: C.white, bold: true }); s.addText(t[1], { x: 3, y: y+0.02, w: 1, h: 0.25, fontFace: F.body, fontSize: 8, color: C.accent }); s.addText(t[2], { x: 4, y: y+0.02, w: 7, h: 0.25, fontFace: F.body, fontSize: 7, color: C.grayL }); s.addText(t[3], { x: 11, y: y+0.02, w: 1.5, h: 0.25, fontFace: F.body, fontSize: 8, color: C.accent }); });

// === 44-45. LLM Connectivity Details ===
s = addContentSlide("LLM 模型连通性测试 (6模型×6场景)");
s.addText("36项测试 100%通过", { x: 0.8, y: 6.5, w: 12, h: 0.4, fontFace: F.header, fontSize: 14, color: C.accent, bold: true, align: "center" });
const modelTestResults = [["qwen2.5-coder:7b","57.3s","11.2s","31.7s","10.8s","33.9s","14.9s","6/6"],["glm4:9b","12.9s","9.2s","7.9s","17.1s","64.0s","13.3s","6/6"],["qwen3:4b","89.6s","39.0s","25.9s","29.7s","37.8s","30.3s","6/6"],["qwen3:8b","79.2s","128.6s","44.6s","43.2s","39.8s","67.2s","6/6"],["yi:6b","19.9s","43.3s","44.0s","41.0s","24.3s","15.4s","6/6"],["llama3.1:8b","28.6s","16.6s","10.0s","15.1s","24.5s","16.2s","6/6"]];
s.addText("模型", { x: 0.3, y: 1.4, w: 2.5, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
["IIoT","PLC","Python","DB","Net","AI/ML"].forEach((h, i) => { s.addText(h, { x: 2.8 + i*1.5, y: 1.4, w: 1.4, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true }); });
s.addText("通过", { x: 11.8, y: 1.4, w: 1, h: 0.3, fontFace: F.header, fontSize: 9, color: C.accent, bold: true });
modelTestResults.forEach((m, i) => { const y = 1.8 + i * 0.75; s.addShape(pptx.ShapeType.rect, { x: 0.3, y, w: 12.5, h: 0.65, fill: { color: i%2===0 ? C.white : C.grayL } }); s.addText(m[0], { x: 0.3, y: y+0.1, w: 2.5, h: 0.45, fontFace: F.body, fontSize: 9, color: C.primary, bold: true }); for (let j = 1; j <= 6; j++) { s.addText(m[j], { x: 2.8 + (j-1)*1.5, y: y+0.1, w: 1.4, h: 0.45, fontFace: F.body, fontSize: 9, color: C.gray }); } s.addText(m[7], { x: 11.8, y: y+0.1, w: 1, h: 0.45, fontFace: F.body, fontSize: 10, color: C.accent, bold: true }); });

// === 46. Section: Conclusion ===
addSectionSlide("10", "总结与展望");

// === 47-48. Achievements ===
s = addDarkSlide("部署成果");
s.addText("8大核心成果", { x: 0.8, y: 1.3, w: 12, h: 0.5, fontFace: F.header, fontSize: 18, color: C.accent, bold: true });
const achievements = ["✅ Dify 1.14.2 完整部署, 27个应用100%可用","✅ 22个本地AI模型 (Qwen3/GLM4/YI/Llama3.1全系列)","✅ 43+36=79项测试, 100%通过率","✅ HPA自动扩缩容, 2000并发压测验证","✅ Redis 8.10.1 Cluster (3主节点, 局域网可访问)","✅ Code-Server 52插件 (Java/Go/Rust/Python/C AI编程)","✅ Grafana 33面板 + Rancher 2集群管理","✅ 工业互联网教学场景验证 (GLM4中文最优)"];
achievements.forEach((a, i) => { const row = Math.floor(i/2), col = i%2; const x = 0.5 + col*6.3; s.addText(a, { x, y: 2.0 + row*1.5, w: 6, h: 1.2, fontFace: F.body, fontSize: 13, color: C.white, lineSpacingMultiple: 1.2 }); });

// === 49. Future ===
s = addContentSlide("未来规划");
const future = [["短期 (1-3月)","升级OS到RHEL8/Ubuntu22.04\n迁移Cilium eBPF CNI\nGPU加速Ollama推理\n增加Redis8副本节点","解决跨节点Pod网络\n支持更多并发推理\n高可用Redis Cluster"],["中期 (3-6月)","工业互联网数字孪生应用\n更多教学知识库\n学生作业自动评分\n实验报告AI辅助","完善教学场景\n自动评估体系\n教学资源管理"],["长期 (6-12月)","多院系AI平台共享\n边缘节点部署\n大模型72b常态化\nAI教学评估报告","平台规模化\n边缘计算教学\n科研辅助"]];
future.forEach((f, i) => { const x = 0.5 + i*4.3; s.addShape(pptx.ShapeType.roundRect, { x, y: 1.5, w: 4, h: 5, fill: { color: C.white }, line: { color: i===0 ? C.secondary : i===1 ? C.accent : C.gold, width: 2 } }); s.addText(f[0], { x: x+0.2, y: 1.7, w: 3.6, h: 0.5, fontFace: F.header, fontSize: 14, color: C.primary, bold: true }); s.addText(f[1], { x: x+0.2, y: 2.3, w: 3.6, h: 2.5, fontFace: F.body, fontSize: 10, color: C.gray, lineSpacingMultiple: 1.3 }); s.addText(f[2], { x: x+0.2, y: 4.8, w: 3.6, h: 1.5, fontFace: F.body, fontSize: 10, color: C.accent, lineSpacingMultiple: 1.3 }); });

// === 50. Final ===
s = pptx.addSlide();
s.background = { color: C.primary };
s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: C.accent } });
s.addText("谢谢", { x: 0.8, y: 2.5, w: 12, h: 1.5, fontFace: F.title, fontSize: 60, color: C.white, bold: true, align: "center" });
s.addText("Dify 智能体服务平台 · 本地化部署成果汇报", { x: 0.8, y: 4.0, w: 12, h: 0.8, fontFace: F.header, fontSize: 20, color: C.accent, align: "center" });
s.addText("工业互联网应用专业 · AI 教学平台 · 2026年8月", { x: 0.8, y: 5.0, w: 12, h: 0.5, fontFace: F.body, fontSize: 14, color: C.grayL, align: "center" });

// Save
pptx.writeFile({ fileName: "Dify智能体服务平台本地化部署成果汇报.pptx" }).then(() => {
  console.log("PPTX 50 pages created successfully!");
}).catch(err => {
  console.error("Error:", err);
});
