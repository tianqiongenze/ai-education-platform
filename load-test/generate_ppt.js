const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

// Theme
const DARK_BG = "0F172A";
const CARD_BG = "1E293B";
const ACCENT = "3B82F6";
const ACCENT2 = "8B5CF6";
const GREEN = "22C55E";
const RED = "EF4444";
const YELLOW = "F59E0B";
const WHITE = "F8FAFC";
const GRAY = "94A3B8";
const LIGHT_BLUE = "60A5FA";

pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";

const titleOpts = { fontSize: 36, color: WHITE, bold: true, fontFace: "Arial" };
const subtitleOpts = { fontSize: 18, color: GRAY, fontFace: "Arial" };
const bodyOpts = { fontSize: 14, color: WHITE, fontFace: "Arial" };
const smallOpts = { fontSize: 12, color: GRAY, fontFace: "Arial" };
const metricBig = { fontSize: 48, color: ACCENT, bold: true, fontFace: "Arial" };
const metricLabel = { fontSize: 14, color: GRAY, fontFace: "Arial" };

function addSlide(title) {
  const slide = pptx.addSlide();
  slide.background = { color: DARK_BG };
  // Header bar
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: ACCENT } });
  slide.addText(title, { x: 0.5, y: 0.3, w: 12, h: 0.7, ...titleOpts, fontSize: 28 });
  // Footer
  slide.addText("AI Platform Enterprise Report | June 2026", { x: 0.5, y: 7.0, w: 12, h: 0.4, ...smallOpts });
  return slide;
}

function addCard(slide, x, y, w, h, color) {
  slide.addShape(pptx.ShapeType.rect, { x, y, w, h, fill: { color: color || CARD_BG }, rectRadius: 0.1 });
}

function addMetricCard(slide, x, y, w, h, value, label, color) {
  addCard(slide, x, y, w, h);
  slide.addText(value, { x, y: y + 0.15, w, h: 0.7, align: "center", ...metricBig, color: color || ACCENT });
  slide.addText(label, { x, y: y + 0.85, w, h: 0.5, align: "center", ...metricLabel });
}

// ===== SLIDE 1: TITLE =====
{
  const slide = pptx.addSlide();
  slide.background = { color: DARK_BG };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.12, fill: { color: ACCENT } });
  slide.addText("AI Platform", { x: 1, y: 1.5, w: 11, h: 1.2, fontSize: 54, color: WHITE, bold: true, fontFace: "Arial" });
  slide.addText("Enterprise Deployment & Load Test Report", { x: 1, y: 2.7, w: 11, h: 0.8, fontSize: 28, color: ACCENT, fontFace: "Arial" });
  slide.addShape(pptx.ShapeType.rect, { x: 1, y: 3.7, w: 3, h: 0.06, fill: { color: ACCENT2 } });
  slide.addText("2-Node Kubernetes Cluster | Dify + code-server + litellm + Ollama", { x: 1, y: 4.2, w: 11, h: 0.6, fontSize: 16, color: GRAY, fontFace: "Arial" });
  slide.addText("June 13, 2026", { x: 1, y: 5.0, w: 11, h: 0.5, fontSize: 14, color: GRAY, fontFace: "Arial" });
}

// ===== SLIDE 2: PROJECT OVERVIEW =====
{
  const slide = addSlide("Project Overview");
  const services = [
    ["Dify Platform", "AI application platform\nAPI + Web + Worker + Plugin Daemon"],
    ["code-server", "Browser-based VS Code IDE\n20 pods, 2000 concurrent users"],
    ["litellm", "LLM proxy gateway\n11 pods, 13 Ollama models"],
    ["Open-WebUI", "Chat interface\nConnected to litellm"],
    ["Ollama", "LLM runtime engine\nMaster + Worker, CPU-only"],
    ["Monitoring", "Prometheus + Grafana\n12 ServiceMonitors, 38+ Rules"]
  ];
  services.forEach((s, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 4.2;
    const y = 1.3 + row * 2.8;
    addCard(slide, x, y, 3.8, 2.4);
    slide.addText(s[0], { x: x + 0.2, y: y + 0.2, w: 3.4, h: 0.5, fontSize: 16, color: ACCENT, bold: true, fontFace: "Arial" });
    slide.addText(s[1], { x: x + 0.2, y: y + 0.8, w: 3.4, h: 1.4, ...bodyOpts, fontSize: 13 });
  });
}

// ===== SLIDE 3: ARCHITECTURE =====
{
  const slide = addSlide("Architecture Overview");
  addCard(slide, 0.5, 1.3, 12.3, 5.3);
  slide.addText("2-Node Kubernetes Cluster", { x: 0.8, y: 1.5, w: 11, h: 0.5, fontSize: 18, color: ACCENT, bold: true, fontFace: "Arial" });
  
  // Master node
  addCard(slide, 0.8, 2.2, 5.5, 2.0, "1E293B");
  slide.addText("k8s-master (16 CPU / 64 GB)", { x: 1.0, y: 2.3, w: 5, h: 0.4, fontSize: 14, color: YELLOW, bold: true, fontFace: "Arial" });
  slide.addText("• ollama-master (15 CPU)\n• Control plane components\n• ingress-nginx\n• Rancher", { x: 1.0, y: 2.8, w: 5, h: 1.2, ...bodyOpts, fontSize: 12 });

  // Worker node
  addCard(slide, 7.0, 2.2, 5.5, 2.0, "1E293B");
  slide.addText("k8s-worker1 (32 CPU / 128 GB)", { x: 7.2, y: 2.3, w: 5, h: 0.4, fontSize: 14, color: GREEN, bold: true, fontFace: "Arial" });
  slide.addText("• ollama-worker (13 models)\n• code-server (20 pods)\n• litellm (11 pods)\n• Dify (API/Web/Worker)\n• PostgreSQL, Redis, Weaviate", { x: 7.2, y: 2.8, w: 5, h: 1.2, ...bodyOpts, fontSize: 12 });

  // Ingress
  addCard(slide, 0.8, 4.5, 11.7, 1.8, "1E293B");
  slide.addText("Ingress (nginx NodePort)", { x: 1.0, y: 4.6, w: 11, h: 0.4, fontSize: 14, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("code-server :32231  |  litellm :30083  |  Dify Web :30080  |  Open-WebUI :30084  |  Grafana :30082", { x: 1.0, y: 5.1, w: 11, h: 0.4, ...bodyOpts, fontSize: 12 });
  slide.addText("No GPU available — all LLM inference runs on CPU", { x: 1.0, y: 5.6, w: 11, h: 0.4, fontSize: 13, color: RED, fontFace: "Arial" });
}

// ===== SLIDE 4: ISSUES FIXED =====
{
  const slide = addSlide("Issues Identified & Resolved");
  const issues = [
    ["code-server 404", "Ingress only routed requests with Host header", "Added catch-all ingress rule", GREEN],
    ["Rancher Login", "Password lost / incorrect", "Reset to Rancher@2026", GREEN],
    ["litellm Models", "Config referenced non-existent models", "Updated with all 13 actual ollama models", GREEN],
    ["Ingress Rate Limit", "limit-rps=30 capped all traffic", "Removed rate limits → 88.6%→0% failures", GREEN],
    ["Pod Scheduling", "CPU requests too high for scaling", "Reduced requests (2→500m, 1→200m)", GREEN],
    ["No GPU", "All LLM inference on CPU", "Identified as critical gap for enterprise scale", RED]
  ];
  issues.forEach((iss, i) => {
    const y = 1.3 + i * 0.95;
    addCard(slide, 0.5, y, 12.3, 0.8);
    slide.addText(iss[0], { x: 0.7, y: y + 0.05, w: 2.5, h: 0.35, fontSize: 14, color: WHITE, bold: true, fontFace: "Arial" });
    slide.addText(iss[1], { x: 3.3, y: y + 0.05, w: 4.5, h: 0.35, ...bodyOpts, fontSize: 12 });
    slide.addText(iss[2], { x: 7.9, y: y + 0.05, w: 4.0, h: 0.35, ...bodyOpts, fontSize: 12, color: iss[3] });
    slide.addText(iss[3] === GREEN ? "✓ FIXED" : "✗ NEEDS GPU", { x: 12.0, y: y + 0.05, w: 1.2, h: 0.35, fontSize: 11, color: iss[3], bold: true, fontFace: "Arial" });
  });
}

// ===== SLIDE 5: CODE-SERVER RESULTS =====
{
  const slide = addSlide("Code-Server Load Test — 2,000 Users");
  slide.addText("PASSED", { x: 0.5, y: 1.1, w: 3, h: 0.5, fontSize: 24, color: GREEN, bold: true, fontFace: "Arial" });
  slide.addText("0% service failures — all errors are incorrect test paths (404)", { x: 0.5, y: 1.6, w: 12, h: 0.4, ...bodyOpts });

  addMetricCard(slide, 0.5, 2.3, 2.8, 1.5, "19,595", "Total Requests", ACCENT);
  addMetricCard(slide, 3.6, 2.3, 2.8, 1.5, "0%", "Service Failures", GREEN);
  addMetricCard(slide, 6.7, 2.3, 2.8, 1.5, "145.7", "Peak RPS", ACCENT);
  addMetricCard(slide, 9.8, 2.3, 2.8, 1.5, "20", "Pods Deployed", ACCENT2);

  // Endpoint table
  addCard(slide, 0.5, 4.1, 12.3, 2.6);
  slide.addText("Endpoint Performance", { x: 0.8, y: 4.2, w: 5, h: 0.4, fontSize: 16, color: ACCENT, bold: true, fontFace: "Arial" });
  const rows = [
    ["GET /healthz", "4,551", "0%", "10ms", "PASS"],
    ["GET /login", "2,000", "0%", "9.1s", "PASS"],
    ["POST /login", "2,000", "0%", "8.0s", "PASS"],
    ["GET / (workspace)", "5,556", "0%", "56s", "PASS"]
  ];
  rows.forEach((r, i) => {
    const y = 4.7 + i * 0.45;
    const cols = [0.8, 4.0, 6.5, 8.5, 10.5];
    slide.addText(r[0], { x: cols[0], y, w: 3, h: 0.35, ...bodyOpts, fontSize: 12 });
    slide.addText(r[1], { x: cols[1], y, w: 2, h: 0.35, ...bodyOpts, fontSize: 12 });
    slide.addText(r[2], { x: cols[2], y, w: 1.5, h: 0.35, ...bodyOpts, fontSize: 12, color: GREEN });
    slide.addText(r[3], { x: cols[3], y, w: 1.5, h: 0.35, ...bodyOpts, fontSize: 12 });
    slide.addText(r[4], { x: cols[4], y, w: 1.5, h: 0.35, fontSize: 12, color: GREEN, bold: true, fontFace: "Arial" });
  });
}

// ===== SLIDE 6: LLM RESULTS =====
{
  const slide = addSlide("LLM Services Load Test — 5,000 Users");
  slide.addText("DEGRADED — CPU Bottleneck", { x: 0.5, y: 1.1, w: 6, h: 0.5, fontSize: 24, color: RED, bold: true, fontFace: "Arial" });
  slide.addText("62.6% failure rate — chat/embeddings fail completely on CPU-only inference", { x: 0.5, y: 1.6, w: 12, h: 0.4, ...bodyOpts });

  addMetricCard(slide, 0.5, 2.3, 2.8, 1.5, "81,429", "Total Requests", ACCENT);
  addMetricCard(slide, 3.6, 2.3, 2.8, 1.5, "62.6%", "Failure Rate", RED);
  addMetricCard(slide, 6.7, 2.3, 2.8, 1.5, "371.4", "Peak RPS", ACCENT);
  addMetricCard(slide, 9.8, 2.3, 2.8, 1.5, "11", "Pods Deployed", ACCENT2);

  addCard(slide, 0.5, 4.1, 12.3, 2.6);
  slide.addText("Endpoint Performance", { x: 0.8, y: 4.2, w: 5, h: 0.4, fontSize: 16, color: ACCENT, bold: true, fontFace: "Arial" });
  const rows = [
    ["GET /health/readiness", "29,758", "41.6%", "21.6s", "DEGRADED", YELLOW],
    ["GET /v1/models", "22,317", "41.4%", "21.8s", "DEGRADED", YELLOW],
    ["POST /v1/chat (7b)", "14,784", "100%", "37.9s", "FAIL", RED],
    ["POST /v1/chat (14b)", "7,353", "100%", "75.5s", "FAIL", RED],
    ["POST /v1/embeddings", "4,308", "99.98%", "24.1s", "FAIL", RED]
  ];
  rows.forEach((r, i) => {
    const y = 4.7 + i * 0.4;
    const cols = [0.8, 4.0, 6.5, 8.5, 10.5];
    slide.addText(r[0], { x: cols[0], y, w: 3, h: 0.35, ...bodyOpts, fontSize: 11 });
    slide.addText(r[1], { x: cols[1], y, w: 2, h: 0.35, ...bodyOpts, fontSize: 11 });
    slide.addText(r[2], { x: cols[2], y, w: 1.5, h: 0.35, ...bodyOpts, fontSize: 11, color: r[5] });
    slide.addText(r[3], { x: cols[3], y, w: 1.5, h: 0.35, ...bodyOpts, fontSize: 11 });
    slide.addText(r[4], { x: cols[4], y, w: 1.5, h: 0.35, fontSize: 11, color: r[5], bold: true, fontFace: "Arial" });
  });
}

// ===== SLIDE 7: BOTTLENECK ANALYSIS =====
{
  const slide = addSlide("Bottleneck Analysis");
  const bottlenecks = [
    ["Ingress Rate Limiting", "FIXED", "limit-rps=30 capped code-server to 30 req/s. Removed → 0% failures.", GREEN],
    ["CPU-Only LLM Inference", "UNRESOLVED", "No GPU. Chat takes 30-120s on CPU. 5000 concurrent impossible.", RED],
    ["Master Node CPU Saturation", "MITIGATED", "ollama-master uses 15/16 cores. Reduced pod CPU requests.", YELLOW],
    ["Pod Resource Requests", "FIXED", "Original 2 CPU/pod prevented scaling. Reduced to 500m → 20 pods.", GREEN],
    ["Static Asset Paths", "TEST ISSUE", "Test used wrong paths. 404 errors are test artifacts, not service failures.", YELLOW]
  ];
  bottlenecks.forEach((b, i) => {
    const y = 1.3 + i * 1.15;
    addCard(slide, 0.5, y, 12.3, 1.0);
    slide.addText(b[0], { x: 0.8, y: y + 0.1, w: 4, h: 0.35, fontSize: 15, color: WHITE, bold: true, fontFace: "Arial" });
    slide.addText(b[1], { x: 5.0, y: y + 0.1, w: 2, h: 0.35, fontSize: 13, color: b[3], bold: true, fontFace: "Arial" });
    slide.addText(b[2], { x: 0.8, y: y + 0.5, w: 11, h: 0.4, ...bodyOpts, fontSize: 12 });
  });
}

// ===== SLIDE 8: SCALING ACTIONS =====
{
  const slide = addSlide("Scaling Actions Taken");
  const actions = [
    ["code-server", "5 → 20 pods", "2 CPU → 500m", "2000 users supported"],
    ["litellm", "3 → 11 pods", "1 CPU → 200m", "5000 users attempted"],
    ["dify-api", "1 → 5 pods", "unchanged", "Platform stability"],
    ["dify-web", "3 → 5 pods", "unchanged", "Platform stability"],
    ["dify-worker", "1 → 5 pods", "unchanged", "Background tasks"],
    ["Ingress", "Rate limits removed", "30→unlimited RPS", "Eliminated bottleneck"]
  ];
  // Header
  const headers = ["Service", "Replicas", "CPU Request", "Result"];
  const hx = [0.8, 4.5, 7.5, 10.5];
  headers.forEach((h, i) => slide.addText(h, { x: hx[i], y: 1.3, w: 3, h: 0.4, fontSize: 13, color: ACCENT, bold: true, fontFace: "Arial" }));
  actions.forEach((a, i) => {
    const y = 1.9 + i * 0.8;
    addCard(slide, 0.5, y, 12.3, 0.65);
    a.forEach((v, j) => slide.addText(v, { x: hx[j], y: y + 0.1, w: 3, h: 0.4, ...bodyOpts, fontSize: 12 }));
  });
}

// ===== SLIDE 9: RECOMMENDATIONS =====
{
  const slide = addSlide("Recommendations");
  const recs = [
    ["IMMEDIATE", "Add GPU Infrastructure", "2x A100 or 4x A10 GPUs for LLM inference — single most impactful improvement"],
    ["IMMEDIATE", "Offload ollama-master", "Move from control plane to dedicated worker to free master CPU"],
    ["SHORT-TERM", "Configure HPA", "HorizontalPodAutoscaler with working metrics for auto-scaling"],
    ["SHORT-TERM", "Smart Rate Limiting", "Per-user/IP rate limits instead of global caps"],
    ["SHORT-TERM", "Add Worker Node", "Third node for load distribution and scaling headroom"],
    ["LONG-TERM", "CDN for Static Assets", "Offload code-server JS/CSS to CDN for faster loads"],
    ["LONG-TERM", "Model Response Cache", "Redis cache for frequent LLM completions"],
    ["LONG-TERM", "Multi-Region Deployment", "Geographic distribution for DR and latency"]
  ];
  recs.forEach((r, i) => {
    const y = 1.2 + i * 0.72;
    const color = r[0] === "IMMEDIATE" ? RED : r[0] === "SHORT-TERM" ? YELLOW : ACCENT;
    addCard(slide, 0.5, y, 12.3, 0.6);
    slide.addText(r[0], { x: 0.7, y: y + 0.08, w: 1.5, h: 0.4, fontSize: 10, color, bold: true, fontFace: "Arial" });
    slide.addText(r[1], { x: 2.3, y: y + 0.08, w: 3, h: 0.4, fontSize: 13, color: WHITE, bold: true, fontFace: "Arial" });
    slide.addText(r[2], { x: 5.5, y: y + 0.08, w: 7, h: 0.4, ...bodyOpts, fontSize: 11 });
  });
}

// ===== SLIDE 10: SUMMARY =====
{
  const slide = addSlide("Summary & Next Steps");
  
  addCard(slide, 0.5, 1.3, 5.8, 2.5);
  slide.addText("What Went Well", { x: 0.8, y: 1.4, w: 5, h: 0.4, fontSize: 18, color: GREEN, bold: true, fontFace: "Arial" });
  slide.addText("✓ Code-server handles 2000 users\n✓ All critical bugs fixed\n✓ 20+ services deployed\n✓ Full monitoring stack\n✓ Ingress bottleneck resolved\n✓ 5 issues identified & fixed", { x: 0.8, y: 1.9, w: 5, h: 1.8, ...bodyOpts, fontSize: 13 });

  addCard(slide, 7.0, 1.3, 5.8, 2.5);
  slide.addText("What Needs Work", { x: 7.3, y: 1.4, w: 5, h: 0.4, fontSize: 18, color: RED, bold: true, fontFace: "Arial" });
  slide.addText("✗ LLM services need GPU\n✗ Master node CPU saturated\n✗ No auto-scaling (HPA broken)\n✗ Static asset paths incorrect\n✗ No CDN for static content", { x: 7.3, y: 1.9, w: 5, h: 1.8, ...bodyOpts, fontSize: 13 });

  addCard(slide, 0.5, 4.1, 12.3, 2.5);
  slide.addText("Next Steps", { x: 0.8, y: 4.2, w: 5, h: 0.4, fontSize: 18, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("1. Procure GPU hardware (2x A100 80GB minimum)\n2. Add third worker node for load distribution\n3. Configure HPA with proper metrics for all services\n4. Implement per-user rate limiting strategy\n5. Set up CDN for code-server static assets\n6. Move ollama-master off control plane node\n7. Schedule follow-up load test with GPU infrastructure", { x: 0.8, y: 4.7, w: 11, h: 1.8, ...bodyOpts, fontSize: 13 });
}

// ===== SLIDE 11: KEY METRICS DASHBOARD =====
{
  const slide = addSlide("Key Metrics Dashboard");
  
  addMetricCard(slide, 0.5, 1.3, 2.8, 1.5, "2,000", "Code-Server Users", GREEN);
  addMetricCard(slide, 3.6, 1.3, 2.8, 1.5, "0%", "Service Failures", GREEN);
  addMetricCard(slide, 6.7, 1.3, 2.8, 1.5, "5,000", "LLM Users Tested", YELLOW);
  addMetricCard(slide, 9.8, 1.3, 2.8, 1.5, "62.6%", "LLM Failure Rate", RED);

  addMetricCard(slide, 0.5, 3.1, 2.8, 1.5, "20", "Code-Server Pods", ACCENT);
  addMetricCard(slide, 3.6, 3.1, 2.8, 1.5, "11", "Litellm Pods", ACCENT);
  addMetricCard(slide, 6.7, 3.1, 2.8, 1.5, "13", "Ollama Models", ACCENT2);
  addMetricCard(slide, 9.8, 3.1, 2.8, 1.5, "0", "GPUs Available", RED);

  addCard(slide, 0.5, 4.9, 12.3, 1.8);
  slide.addText("Cluster Resources", { x: 0.8, y: 5.0, w: 5, h: 0.4, fontSize: 16, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("Master: 16 CPU / 64 GB (96% CPU used)    |    Worker: 32 CPU / 128 GB (1% CPU, 43% mem)", { x: 0.8, y: 5.5, w: 11, h: 0.4, ...bodyOpts, fontSize: 13 });
  slide.addText("Rancher: https://10.167.2.175  (admin / Rancher@2026)    |    Grafana: http://10.167.2.175:30082", { x: 0.8, y: 6.0, w: 11, h: 0.4, ...bodyOpts, fontSize: 12 });
}

// Save
pptx.writeFile({ fileName: "D:\\dify-install\\load-test\\AI_Platform_Enterprise_Report.pptx" })
  .then(() => console.log("PPTX created successfully!"))
  .catch(err => console.error("Error:", err));