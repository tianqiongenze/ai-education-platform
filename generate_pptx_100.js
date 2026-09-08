// =============================================================================
// Dify 智能体服务平台本地化部署成果汇报 — 100-Page Presentation Generator
// PptxGenJS 4.0.x | Layout: WIDE (13.33 x 7.5)
// =============================================================================
const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";
pptx.author = "Dify Platform Team";
pptx.company = "Industrial IoT Education";
pptx.subject = "Dify 智能体服务平台本地化部署成果汇报";

// -----------------------------------------------------------------------------
// Color scheme & fonts
// -----------------------------------------------------------------------------
const C = {
  primary:   "0B1F3A", // deep navy (slightly darker for better contrast)
  secondary: "2563EB", // vivid blue (more saturated)
  accent:    "10B981", // emerald green (more vibrant)
  accent2:   "F59E0B", // amber for highlights
  light:     "F8FAFC", // very light gray-blue
  white:     "FFFFFF",
  gray:      "64748B", // slate-500 (darker, better readability)
  grayL:     "E2E8F0", // slate-200 (clearly different from light)
  grayXL:    "F1F5F9", // slate-100 (subtle alternating row)
  gold:      "F59E0B", // amber-500
  dark:      "0B1F3A",
  darkCard:  "1E293B", // slate-800
  darkRow:   "0F172A", // slate-900
  red:       "EF4444", // red-500 for disadvantages
  purple:    "8B5CF6", // violet for special highlights
};
const F = { title: "Arial Black", header: "Arial", body: "Calibri", mono: "Consolas" };

const W = 13.33;   // slide width
const H = 7.5;     // slide height
const MX = 0.5;    // left/right margin
const CW = W - 2 * MX; // content width = 12.33

// -----------------------------------------------------------------------------
// Reusable shape strings (v4 accepts string shape names directly)
// -----------------------------------------------------------------------------
const SHP = {
  rect: "rect",
  roundRect: "roundRect",
  ellipse: "ellipse",
  line: "line",
  chevron: "chevron",
  rtTriangle: "rtTriangle",
};

// =============================================================================
// HELPERS
// =============================================================================

// Full-bleed background rectangle (used for color overrides on section dividers)
function fillBg(slide, color) {
  slide.background = { color };
}

// Thin accent rule under a title
function accentRule(slide, x, y, w) {
  slide.addShape(SHP.rect, { x, y, w, h: 0.05, fill: { color: C.accent } });
}

// Standard light content slide with title bar + accent line
function contentSlide(title, opts) {
  opts = opts || {};
  const s = pptx.addSlide();
  s.background = { color: C.light };
  // Top title bar with subtle gradient effect (use slightly darker white)
  s.addShape(SHP.rect, { x: 0, y: 0, w: W, h: 0.95, fill: { color: C.white } });
  // Bottom border of title bar (accent colored, thicker)
  s.addShape(SHP.rect, { x: 0, y: 0.91, w: W, h: 0.06, fill: { color: C.accent } });
  // Left accent block (vertical bar before title)
  s.addShape(SHP.roundRect, { x: MX, y: 0.2, w: 0.1, h: 0.55, fill: { color: C.secondary }, rectRadius: 0.02 });
  s.addText(title, {
    x: MX + 0.25, y: 0.12, w: CW - 0.4, h: 0.7,
    fontFace: F.title, fontSize: 22, color: C.primary, bold: true, valign: "middle",
  });
  // page badge top-right
  if (opts.page != null) {
    s.addText(String(opts.page), {
      x: W - 1.2, y: 0.25, w: 0.7, h: 0.45,
      fontFace: F.header, fontSize: 11, color: C.gray, align: "right", valign: "middle",
    });
  }
  return s;
}

// Dark content slide (for detailed tables on dark background)
function darkContentSlide(title, opts) {
  opts = opts || {};
  const s = pptx.addSlide();
  s.background = { color: C.dark };
  s.addShape(SHP.rect, { x: 0, y: 0, w: W, h: 0.95, fill: { color: C.darkCard } });
  // Thicker accent line at bottom of header
  s.addShape(SHP.rect, { x: 0, y: 0.91, w: W, h: 0.06, fill: { color: C.accent } });
  s.addShape(SHP.roundRect, { x: MX, y: 0.2, w: 0.1, h: 0.55, fill: { color: C.accent }, rectRadius: 0.02 });
  s.addText(title, {
    x: MX + 0.25, y: 0.12, w: CW - 0.4, h: 0.7,
    fontFace: F.title, fontSize: 22, color: C.white, bold: true, valign: "middle",
  });
  if (opts.page != null) {
    s.addText(String(opts.page), {
      x: W - 1.2, y: 0.25, w: 0.7, h: 0.45,
      fontFace: F.header, fontSize: 11, color: C.grayL, align: "right", valign: "middle",
    });
  }
  return s;
}

// Section divider slide: full color background + big number
function sectionSlide(num, title, opts) {
  opts = opts || {};
  const s = pptx.addSlide();
  fillBg(s, C.primary);
  // Left vertical accent band (wider, rounded top-right)
  s.addShape(SHP.rect, { x: 0, y: 0, w: 0.3, h: H, fill: { color: C.accent } });
  // Background giant number (ghosted - more visible)
  s.addText(num, {
    x: 5.5, y: 0.4, w: 7, h: 6.5,
    fontFace: F.title, fontSize: 320, color: "1A3A5C", bold: true, align: "center", valign: "middle",
  });
  // Foreground number
  s.addText(num, {
    x: MX + 0.3, y: 2.0, w: 3, h: 2.5,
    fontFace: F.title, fontSize: 120, color: C.accent, bold: true, align: "left", valign: "middle",
  });
  // Title
  s.addText(title, {
    x: MX + 0.3, y: 4.3, w: 11, h: 1.0,
    fontFace: F.header, fontSize: 30, color: C.white, bold: true, align: "left",
  });
  // Subtitle rule (accent colored, thicker)
  s.addShape(SHP.rect, { x: MX + 0.3, y: 5.4, w: 4, h: 0.08, fill: { color: C.accent } });
  if (opts.sub) {
    s.addText(opts.sub, {
      x: MX + 0.3, y: 5.6, w: 11, h: 0.5,
      fontFace: F.body, fontSize: 14, color: C.grayL, align: "left",
    });
  }
  if (opts.page != null) {
    s.addText(String(opts.page), {
      x: W - 1.2, y: 6.9, w: 0.7, h: 0.4,
      fontFace: F.header, fontSize: 11, color: C.grayL, align: "right", valign: "middle",
    });
  }
  return s;
}

// Add a small footer page number + brand on a content slide
function foot(slide, page) {
  // Thin accent line above footer
  slide.addShape(SHP.rect, { x: 0, y: H - 0.36, w: W, h: 0.02, fill: { color: C.grayXL } });
  slide.addShape(SHP.rect, { x: 0, y: H - 0.32, w: W, h: 0.32, fill: { color: C.white } });
  slide.addText("Dify 智能体服务平台 · 本地化部署成果汇报", {
    x: MX, y: H - 0.3, w: 8, h: 0.28,
    fontFace: F.body, fontSize: 8, color: C.gray, valign: "middle",
  });
  // Small accent dot before page number
  slide.addShape(SHP.ellipse, { x: W - 1.3, y: H - 0.22, w: 0.08, h: 0.08, fill: { color: C.accent }, line: { type: "none" } });
  slide.addText(String(page), {
    x: W - 1.15, y: H - 0.3, w: 0.65, h: 0.28,
    fontFace: F.header, fontSize: 9, color: C.gray, align: "right", valign: "middle",
  });
}

// Helper: a "stat card" — big number + label inside a rounded rect
function statCard(slide, x, y, w, h, number, label, opts) {
  opts = opts || {};
  slide.addShape(SHP.roundRect, {
    x, y, w, h,
    fill: { color: opts.fill || C.darkCard },
    line: { color: opts.border || C.secondary, width: 2 },
    rectRadius: 0.06,
  });
  // Accent bar at top
  slide.addShape(SHP.rect, { x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.05, fill: { color: opts.accentBar || C.accent }, line: { type: "none" } });
  slide.addText(number, {
    x, y: y + 0.2, w, h: h * 0.5,
    fontFace: F.title, fontSize: opts.numSize || 36, color: opts.numColor || C.accent,
    bold: true, align: "center", valign: "middle",
  });
  slide.addText(label, {
    x, y: y + h * 0.62, w, h: h * 0.3,
    fontFace: F.body, fontSize: opts.labSize || 11, color: opts.labColor || C.grayL,
    align: "center", valign: "middle",
  });
}

// Helper: card with header + body lines
function card(slide, x, y, w, h, header, bodyLines, opts) {
  opts = opts || {};
  slide.addShape(SHP.roundRect, {
    x, y, w, h,
    fill: { color: opts.fill || C.white },
    line: { color: opts.border || C.grayL, width: 1.5 },
    rectRadius: 0.05,
  });
  // Header band (rounded top)
  slide.addShape(SHP.rect, {
    x, y, w, h: 0.5,
    fill: { color: opts.headColor || C.secondary },
    line: { type: "none" },
  });
  slide.addText(header, {
    x: x + 0.1, y, w: w - 0.2, h: 0.5,
    fontFace: F.header, fontSize: opts.headSize || 13, color: C.white, bold: true,
    align: "center", valign: "middle",
  });
  if (bodyLines && bodyLines.length) {
    bodyLines.forEach((ln, i) => {
      const ly = y + 0.6 + i * 0.32;
      slide.addText(ln, {
        x: x + 0.15, y: ly, w: w - 0.3, h: 0.3,
        fontFace: F.body, fontSize: opts.bodySize || 9, color: opts.bodyColor || C.gray,
      });
    });
  }
}

// Helper: a clean table built with shapes (header row + alternating rows)
// cols: [{x, w, header}]  rows: [[v1,v2,...], ...]
// Supports dark mode via opts.dark=true
function table(slide, cols, rows, startY, opts) {
  opts = opts || {};
  const headColor = opts.headColor || C.secondary;
  const headTextColor = opts.headText || C.white;
  const rowH = opts.rowH || 0.42;
  const headH = opts.headH || 0.45;
  const fontSize = opts.fontSize || 9;
  const headFontSize = opts.headFontSize || 10;
  const totalW = cols.reduce((a, c) => a + c.w, 0);
  const isDark = opts.dark || false;
  const rowBgEven = isDark ? C.darkRow : C.white;
  const rowBgOdd = isDark ? C.darkCard : C.grayXL;
  const defaultBodyColor = isDark ? C.white : C.primary;
  const separatorColor = isDark ? C.secondary : C.grayL;
  const borderColor = isDark ? C.secondary : C.grayL;
  // Header row background
  slide.addShape(SHP.rect, { x: cols[0].x, y: startY, w: totalW, h: headH, fill: { color: headColor } });
  // Header text
  cols.forEach((c) => {
    slide.addText(c.header, {
      x: c.x + 0.08, y: startY + 0.03, w: c.w - 0.16, h: headH - 0.06,
      fontFace: F.header, fontSize: headFontSize, color: headTextColor, bold: true,
      align: c.align || "left", valign: "middle",
    });
  });
  // Vertical column separators in header
  cols.forEach((c, ci) => {
    if (ci > 0) {
      slide.addShape(SHP.rect, { x: c.x - 0.01, y: startY, w: 0.02, h: headH, fill: { color: C.white, transparency: 60 }, line: { type: "none" } });
    }
  });
  // Data rows
  rows.forEach((r, i) => {
    const y = startY + headH + i * rowH;
    const bg = i % 2 === 0 ? rowBgEven : rowBgOdd;
    slide.addShape(SHP.rect, { x: cols[0].x, y, w: totalW, h: rowH, fill: { color: bg } });
    cols.forEach((c, ci) => {
      // Vertical separators
      if (ci > 0) {
        slide.addShape(SHP.rect, { x: c.x - 0.01, y, w: 0.02, h: rowH, fill: { color: separatorColor }, line: { type: "none" } });
      }
      slide.addText(String(r[ci]), {
        x: c.x + 0.08, y: y + 0.02, w: c.w - 0.16, h: rowH - 0.04,
        fontFace: F.body, fontSize: fontSize, color: opts.bodyColor || defaultBodyColor,
        align: c.align || "left", valign: "middle",
        bold: opts.boldFirstCol && ci === 0,
      });
    });
  });
  // outer border (thicker)
  const totalH = headH + rows.length * rowH;
  slide.addShape(SHP.rect, { x: cols[0].x, y: startY, w: totalW, h: totalH, fill: { type: "none" }, line: { color: borderColor, width: 1.5 } });
  return totalH;
}

// Progress bar helper
function progressBar(slide, x, y, w, h, pct, color) {
  slide.addShape(SHP.roundRect, { x, y, w, h, fill: { color: C.grayL }, line: { type: "none" } });
  slide.addShape(SHP.roundRect, { x, y, w: w * (pct / 100), h, fill: { color: color || C.accent }, line: { type: "none" } });
}

// Chip/badge
function chip(slide, x, y, w, h, text, fill, txtColor) {
  slide.addShape(SHP.roundRect, { x, y, w, h, fill: { color: fill }, line: { type: "none" } });
  slide.addText(text, {
    x, y, w, h, fontFace: F.header, fontSize: 8, color: txtColor || C.white,
    bold: true, align: "center", valign: "middle",
  });
}

// Checklist row (icon box + text)
function checkRow(slide, x, y, w, text, opts) {
  opts = opts || {};
  slide.addShape(SHP.roundRect, { x, y, w: 0.4, h: 0.4, fill: { color: C.accent }, line: { type: "none" } });
  slide.addText("✓", { x, y, w: 0.4, h: 0.4, fontFace: F.title, fontSize: 14, color: C.white, bold: true, align: "center", valign: "middle" });
  slide.addText(text, { x: x + 0.55, y, w: w - 0.55, h: 0.4, fontFace: F.body, fontSize: opts.size || 11, color: C.primary, valign: "middle" });
}

// "Step" arrow flow element
function flowStep(slide, x, y, w, h, num, label, color) {
  slide.addShape(SHP.chevron, { x, y, w, h, fill: { color: color || C.secondary }, line: { type: "none" } });
  slide.addText(num + "  " + label, {
    x: x + 0.1, y, w: w - 0.2, h, fontFace: F.header, fontSize: 9, color: C.white, bold: true,
    align: "center", valign: "middle",
  });
}

// ============================================================================
// A simple page tracker so we stamp the correct page number on every slide.
// We call addSlide-ish helpers above without a page, then decorate after.
// Instead we'll just pass page numbers explicitly in each builder for clarity.
// ============================================================================

// =============================================================================
// SECTION 1 — Title & Agenda (pages 1-5)
// =============================================================================

// ---- Page 1: Title slide -----------------------------------------------------
(function p1() {
  const s = pptx.addSlide();
  fillBg(s, C.primary);
  // Top + bottom accent bands
  s.addShape(SHP.rect, { x: 0, y: 0, w: W, h: 0.12, fill: { color: C.accent } });
  s.addShape(SHP.rect, { x: 0, y: H - 0.12, w: W, h: 0.12, fill: { color: C.secondary } });
  // Decorative circles
  s.addShape(SHP.ellipse, { x: 9.8, y: -1.5, w: 5, h: 5, fill: { color: "0E2A48" }, line: { type: "none" } });
  s.addShape(SHP.ellipse, { x: 10.6, y: 4.5, w: 4, h: 4, fill: { color: "0E2A48" }, line: { type: "none" } });

  s.addText("Dify 智能体服务平台", {
    x: 0.8, y: 1.5, w: 11.5, h: 1.0,
    fontFace: F.title, fontSize: 46, color: C.white, bold: true,
  });
  s.addText("本地化部署成果汇报", {
    x: 0.8, y: 2.5, w: 11.5, h: 0.8,
    fontFace: F.header, fontSize: 30, color: C.accent, bold: true,
  });
  s.addShape(SHP.rect, { x: 0.85, y: 3.45, w: 3.5, h: 0.06, fill: { color: C.gold } });
  s.addText("工业互联网应用专业  ·  AI 教学平台  ·  2026年8月", {
    x: 0.8, y: 3.7, w: 11.5, h: 0.5,
    fontFace: F.body, fontSize: 16, color: C.grayL,
  });

  // 4 stat cards row
  const stats = [
    ["58", "应用数量"], ["26", "本地模型"], ["100%", "测试通过率"], ["8.10", "Redis 版本"],
  ];
  stats.forEach((st, i) => {
    const x = 0.8 + i * 3.05;
    statCard(s, x, 4.6, 2.8, 1.5, st[0], st[1], { fill: C.darkCard, border: C.secondary, numColor: C.accent, numSize: 38, labSize: 12 });
  });

  s.addText("汇报人：Dify 平台运维团队", {
    x: 0.8, y: 6.5, w: 11.5, h: 0.4,
    fontFace: F.body, fontSize: 13, color: C.gray, align: "left",
  });
})();

// ---- Page 2: Agenda ----------------------------------------------------------
(function p2() {
  const s = contentSlide("汇报内容");
  const agenda = [
    ["01", "平台架构总览", "K8s 集群 · 服务部署 · 网络访问"],
    ["02", "AI 模型部署", "26 模型 · LiteLLM 网关 · 多模型对比"],
    ["03", "Dify 平台功能", "58 应用 · 知识库 · 工作流 · Agent"],
    ["04", "工业互联网教学应用", "PLC · 传感器 · MES · 数字孪生"],
    ["05", "Code-Server AI 编程环境", "52 插件 · Continue.dev · 自动评分"],
    ["06", "性能与压力测试", "HPA · k6/Locust · 5000 VU"],
    ["07", "平台对比分析", "Dify vs Coze vs FastGPT"],
    ["08", "运维与监控", "Rancher · Grafana · Redis 8"],
    ["09", "测试成果", "43 + 36 + 33 项测试 100% 通过"],
    ["10", "总结与展望", "成果 · 经验 · 未来规划"],
  ];
  agenda.forEach((it, i) => {
    const row = Math.floor(i / 2), col = i % 2;
    const x = MX + col * 6.2, y = 1.3 + row * 1.18;
    s.addShape(SHP.roundRect, { x, y, w: 5.9, h: 1.0, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
    s.addShape(SHP.rect, { x, y, w: 0.12, h: 1.0, fill: { color: C.accent }, line: { type: "none" } });
    s.addText(it[0], { x: x + 0.2, y: y + 0.12, w: 0.7, h: 0.5, fontFace: F.title, fontSize: 22, color: C.accent, bold: true, valign: "middle" });
    s.addText(it[1], { x: x + 0.95, y: y + 0.1, w: 4.7, h: 0.4, fontFace: F.header, fontSize: 13, color: C.primary, bold: true, valign: "middle" });
    s.addText(it[2], { x: x + 0.95, y: y + 0.5, w: 4.7, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.gray, valign: "middle" });
  });
  foot(s, 2);
})();

// ---- Page 3: Section divider 01 ----------------------------------------------
sectionSlide("01", "平台架构总览", { sub: "K8s 双节点集群 · Master + Worker · 全栈服务部署", page: 3 });

// ---- Page 4: Cluster topology ------------------------------------------------
(function p4() {
  const s = darkContentSlide("集群拓扑架构", { page: 4 });
  // Master node card
  const mx = 0.5, my = 1.2;
  s.addShape(SHP.roundRect, { x: mx, y: my, w: 6.0, h: 5.8, fill: { color: C.darkCard }, line: { color: C.secondary, width: 2 } });
  s.addShape(SHP.rect, { x: mx, y: my, w: 6.0, h: 0.6, fill: { color: C.secondary }, line: { type: "none" } });
  s.addText("Master  节点  ·  10.167.2.175  ·  128GB", { x: mx + 0.15, y: my, w: 5.7, h: 0.6, fontFace: F.header, fontSize: 13, color: C.white, bold: true, valign: "middle" });
  const masterSvc = [
    "Dify API  (3 副本 · 8Gi)",
    "Dify Web  (2 副本)",
    "Dify Worker  (3 副本)",
    "Plugin Daemon",
    "PostgreSQL  (持久化)",
    "Redis 7  (Dify 缓存)",
    "Redis 8 Cluster  (3 节点)",
    "Grafana  +  Loki  监控",
    "Rancher  管理平面",
    "Ingress-Nginx  (2 副本)",
  ];
  masterSvc.forEach((sv, i) => {
    const y = my + 0.8 + i * 0.49;
    s.addShape(SHP.roundRect, { x: mx + 0.2, y, w: 5.6, h: 0.4, fill: { color: C.dark }, line: { color: C.secondary, width: 0.5 } });
    s.addText(sv, { x: mx + 0.35, y, w: 5.3, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.white, valign: "middle" });
  });
  // Worker node card
  const wx = 6.83, wy = 1.2;
  s.addShape(SHP.roundRect, { x: wx, y: wy, w: 6.0, h: 5.8, fill: { color: C.darkCard }, line: { color: C.accent, width: 2 } });
  s.addShape(SHP.rect, { x: wx, y: wy, w: 6.0, h: 0.6, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("Worker  节点  ·  10.167.2.176  ·  128GB", { x: wx + 0.15, y: wy, w: 5.7, h: 0.6, fontFace: F.header, fontSize: 13, color: C.white, bold: true, valign: "middle" });
  const workerSvc = [
    "LiteLLM 网关  (2 副本 · 4CPU)",
    "Ollama  (26 模型 · NUM_PARALLEL=8)",
    "Code-Server  (3 副本 · 52 插件)",
    "Dify Plugin Daemon",
    "Dify Worker  (任务执行)",
    "Dify Sandbox",
    "Weaviate  向量库",
    "PgBouncer  连接池",
    "Node Exporter",
    "Prometheus  +  Loki",
  ];
  workerSvc.forEach((sv, i) => {
    const y = wy + 0.8 + i * 0.49;
    s.addShape(SHP.roundRect, { x: wx + 0.2, y, w: 5.6, h: 0.4, fill: { color: C.dark }, line: { color: C.accent, width: 0.5 } });
    s.addText(sv, { x: wx + 0.35, y, w: 5.3, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.white, valign: "middle" });
  });
  foot(s, 4);
})();

// ---- Page 5: Network access table -------------------------------------------
(function p5() {
  const s = contentSlide("网络架构与访问方式", { page: 5 });
  const rows = [
    ["Dify 控制台", "https://10.167.2.175:31825", "IP 直连 · 无需 hosts", "307 → 登录页", "✅ 正常"],
    ["Dify API", "https://10.167.2.175:31825/v1", "IP 直连", "程序化调用", "✅ 正常"],
    ["Code-Server", "http://10.167.2.175:30087/vscode/", "Caddy 代理 strip_prefix", "302 → IDE 页面", "✅ 正常"],
    ["JupyterHub 多租户", "http://10.167.2.175:30089/ide/", "多用户注册(独立空间)", "302 → Hub 页面", "✅ 正常"],
    ["JupyterLab", "http://10.167.2.175:30088/jupyter/", "原生子路径 base_url", "302 → Lab 页面", "✅ 正常"],
    ["LiteLLM 网关", "http://10.167.2.176:30083", "IP 直连", "26 模型路由", "✅ 正常"],
    ["Ollama", "http://10.167.2.176:30086", "IP 直连", "26 模型推理", "✅ 正常"],
    ["Grafana", "http://10.167.2.175:30082", "IP 直连", "33 面板", "✅ 正常"],
    ["Rancher", "https://10.167.2.175", "IP 直连", "2 集群", "✅ 正常"],
    ["Redis 8 Cluster", "10.167.2.175:30090", "NodePort 直连", "3 主节点", "✅ 正常"],
    ["Mailpit 邮件", "http://10.167.2.175:30205", "IP 直连 · 无需登录", "SMTP 邮件查看", "✅ 正常"],
  ];
  const cols = [
    { x: 0.5, w: 2.2, header: "服务", align: "left" },
    { x: 2.7, w: 3.6, header: "访问地址", align: "left" },
    { x: 6.3, w: 2.6, header: "访问方式", align: "left" },
    { x: 8.9, w: 2.2, header: "验证结果", align: "left" },
    { x: 11.1, w: 1.73, header: "状态", align: "center" },
  ];
  table(s, cols, rows, 1.35, { rowH: 0.5, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  s.addText("所有服务均通过 NodePort / 路径路由暴露，支持纯内网访问，无需公网与 DNS。", {
    x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.body, fontSize: 11, color: C.secondary, align: "center", bold: true,
  });
  foot(s, 5);
})();

// =============================================================================
// SECTION 2 — AI Models (pages 6-20)
// =============================================================================
sectionSlide("02", "AI 模型部署", { sub: "26 个本地模型 · LiteLLM 统一网关 · 36 项场景对比测试", page: 6 });

// ---- Page 7: Model overview (3 columns) -------------------------------------
(function p7() {
  const s = contentSlide("AI 模型部署总览（26 个本地模型）", { page: 7 });
  const cats = [
    ["Qwen3 系列（最新 · 推荐）", [
      "qwen3:4b (2GB) · 快速问答 thinking",
      "qwen3:8b (5GB) · 通用教学 thinking",
      "qwen3:14b (9GB) · 深度推理 thinking",
      "qwen3:30b-a3b (18GB) · MoE 专家",
      "qwen3:32b (20GB) · 旗舰推理",
      "qwen3-embedding:0.6b · 1024 维",
      "qwen3-embedding:4b · 2560 维",
      "qwen3-embedding:8b · 4096 维",
    ]],
    ["Qwen2.5 系列（经典）", [
      "qwen2.5:7b/14b/32b/72b · 通用对话",
      "qwen2.5-coder:7b/14b · 编程专用",
      "deepseek-r1:7b/14b/32b · 深度推理",
      "bge-m3 · 1024 维嵌入",
      "nomic-embed-text · 137 维轻量",
    ]],
    ["其他模型", [
      "glm4:9b (5.5GB) · 中文最强",
      "yi:6b (3.5GB) · 中文通用",
      "llama3.1:8b (4.9GB) · 通用最快",
      "llama3.2-vision:11b · 多模态视觉",
      "tinyllama (637MB) · 极轻量测试",
      "llava · 视觉理解",
    ]],
  ];
  cats.forEach((cat, i) => {
    const x = 0.5 + i * 4.28;
    card(s, x, 1.35, 4.05, 5.4, cat[0], cat[1], { headSize: 11, bodySize: 9, headColor: i === 0 ? C.accent : (i === 1 ? C.secondary : C.gold) });
  });
  s.addText("26 个 Ollama 模型 · 26 个 LiteLLM 路由 · Dify 全部注册可用", {
    x: 0.5, y: 6.85, w: 12.33, h: 0.35, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true, align: "center",
  });
  foot(s, 7);
})();

// ---- Page 8: Qwen3 series detail --------------------------------------------
(function p8() {
  const s = darkContentSlide("Qwen3 系列模型详细介绍", { page: 8 });
  const cols = [
    { x: 0.4, w: 2.0, header: "模型" },
    { x: 2.4, w: 1.0, header: "大小" },
    { x: 3.4, w: 1.6, header: "推理速度" },
    { x: 5.0, w: 4.0, header: "教学场景" },
    { x: 9.0, w: 3.93, header: "使用建议" },
  ];
  const rows = [
    ["qwen3:4b", "2GB", "⚡ 10–30s", "工业互联网基础概念\n传感器原理\n边缘计算基础", "快速问答\n课堂即时互动\nTab 自动补全"],
    ["qwen3:8b", "5GB", "⏳ 30–90s", "PLC 编程\n工业以太网\n数字孪生基础", "通用教学\n实验指导\n课后答疑"],
    ["qwen3:14b", "9GB", "⏳ 60–180s", "MES 制造执行系统\n工业物联网安全\n复杂场景分析", "深度教学\n课程设计\n论文辅导"],
    ["qwen3:30b-a3b", "17GB", "⏳ 15–60s", "复杂工业场景\n系统设计\n架构分析", "MoE 高效推理\n30B 仅激活 3B\n接近 8b 速度"],
    ["qwen3:32b", "18GB", "⏳ 120–300s", "旗舰推理\n学术论文\n科研分析", "最深层推理\n复杂逻辑推理\n/no_think 可加速"],
  ];
  table(s, cols, rows, 1.25, { rowH: 0.95, headH: 0.45, fontSize: 8.5, headFontSize: 10, boldFirstCol: true, bodyColor: C.white, dark: true });
  // override header bg already secondary; recolor rows dark
  s.addText("推荐：教学主用 qwen3:8b，深度推理用 qwen3:14b/32b。", {
    x: 0.5, y: 6.9, w: 12.33, h: 0.35, fontFace: F.header, fontSize: 11, color: C.gold, bold: true, align: "center",
  });
  foot(s, 8);
})();

// ---- Page 9: Qwen2.5 series detail ------------------------------------------
(function p9() {
  const s = darkContentSlide("Qwen2.5 系列模型详细介绍", { page: 9 });
  const cols = [
    { x: 0.4, w: 2.2, header: "模型" },
    { x: 2.6, w: 1.0, header: "大小" },
    { x: 3.6, w: 1.6, header: "推理速度" },
    { x: 5.2, w: 3.8, header: "教学场景" },
    { x: 9.0, w: 3.93, header: "使用建议" },
  ];
  const rows = [
    ["qwen2.5:7b", "4.7GB", "⚡ 8–22s", "通用对话\n课堂问答", "轻量通用教学\n响应快"],
    ["qwen2.5:14b", "9GB", "⏳ 20–60s", "深度对话\n知识讲解", "更高质量对话\n中长篇生成"],
    ["qwen2.5:32b", "20GB", "⏳ 60–200s", "复杂推理\n论文写作", "旗舰通用推理\n备选 qwen3:32b"],
    ["qwen2.5:72b", "42GB", "⏳ 200s+", "科研级任务", "最高质量通用\n资源消耗大"],
    ["qwen2.5-coder:7b", "4.7GB", "⚡ 3–31s", "编程教学\n代码辅助\n数据库 SQL", "专为代码优化\nCode-Server 编程"],
    ["qwen2.5-coder:14b", "9GB", "⚡ 5–31s", "深度编程\n复杂算法", "更准确代码生成\n大作业批改"],
    ["deepseek-r1:7b", "4.7GB", "⏳ 30–90s", "深度推理\n数学证明", "R1 推理链\n思维过程可见"],
    ["deepseek-r1:14b/32b", "9/20GB", "⏳ 60–300s", "复杂推理\n数学建模", "更强推理能力\n备选 qwen3"],
  ];
  table(s, cols, rows, 1.25, { rowH: 0.62, headH: 0.42, fontSize: 8.5, headFontSize: 10, boldFirstCol: true, bodyColor: C.white, dark: true });
  foot(s, 9);
})();

// ---- Page 10: Other models ---------------------------------------------------
(function p10() {
  const s = darkContentSlide("其他模型详细介绍", { page: 10 });
  const cols = [
    { x: 0.4, w: 2.4, header: "模型" },
    { x: 2.8, w: 1.0, header: "大小" },
    { x: 3.8, w: 1.4, header: "速度" },
    { x: 5.2, w: 3.5, header: "教学场景" },
    { x: 8.7, w: 4.23, header: "详细介绍" },
  ];
  const rows = [
    ["glm4:9b", "5.5GB", "⚡ 7–13s", "中文教学最优\n工业互联网/PLC", "Z.AI GLM4 · 中文理解最强\n4/6 场景最快 · 多语言"],
    ["yi:6b", "3.5GB", "⏳ 15–44s", "中文通用\n网络通信", "零一万物 Yi · 中文能力强\n轻量级部署"],
    ["llama3.1:8b", "4.9GB", "⚡ 10–28s", "通用教学\n英文场景", "Meta Llama3.1 · 平均最快 18.5s\n英文场景最优"],
    ["llama3.2-vision:11b", "7GB", "⏳ 30–90s", "多模态视觉\n图像理解", "支持图像输入\n工业图像识别"],
    ["qwen2.5-coder:7b", "4.7GB", "⚡ 3–31s", "编程教学\n代码辅助", "阿里 Qwen2.5 编程版\nCode-Server AI 编程"],
    ["bge-m3", "1.2GB", "⚡ 即时", "知识库嵌入\nRAG 检索", "1024 维向量 · 多语言\n中英双语"],
    ["nomic-embed-text", "274MB", "⚡ 即时", "轻量嵌入\n快速索引", "137 维向量 · 超轻量"],
    ["tinyllama", "637MB", "⚡ 极快", "极轻量测试", "最小模型 · 功能验证"],
  ];
  table(s, cols, rows, 1.25, { rowH: 0.6, headH: 0.42, fontSize: 8.5, headFontSize: 10, boldFirstCol: true, bodyColor: C.white, dark: true });
  foot(s, 10);
})();

// ---- Page 11: Embedding models ----------------------------------------------
(function p11() {
  const s = contentSlide("嵌入模型（Embedding）对比", { page: 11 });
  const cols = [
    { x: 0.5, w: 3.0, header: "模型" },
    { x: 3.5, w: 1.4, header: "维度" },
    { x: 4.9, w: 1.4, header: "大小" },
    { x: 6.3, w: 2.6, header: "适用场景" },
    { x: 8.9, w: 3.93, header: "推荐用法" },
  ];
  const rows = [
    ["bge-m3", "1024 维", "1.2GB", "通用中英检索", "默认知识库嵌入 · 多语言强"],
    ["qwen3-embedding:0.6b", "1024 维", "1.3GB", "通用教学检索", "轻量快速 · 与 qwen3 系列同源"],
    ["qwen3-embedding:4b", "2560 维", "8GB", "高精度检索", "工业文档深度检索"],
    ["qwen3-embedding:8b", "4096 维", "16GB", "科研级检索", "最高召回率 · 资源消耗大"],
    ["nomic-embed-text", "137 维", "274MB", "轻量快速索引", "原型/教学演示"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.6, headH: 0.5, fontSize: 10, headFontSize: 11, boldFirstCol: true });
  // Dimension bars
  s.addText("维度对比", { x: 0.5, y: 5.2, w: 3, h: 0.4, fontFace: F.header, fontSize: 12, color: C.primary, bold: true });
  const dims = [["bge-m3 / 0.6b", 1024, C.secondary], ["4b", 2560, C.accent], ["8b", 4096, C.gold]];
  dims.forEach((d, i) => {
    const y = 5.65 + i * 0.42;
    s.addText(d[0], { x: 0.5, y, w: 1.6, h: 0.32, fontFace: F.body, fontSize: 9, color: C.primary, valign: "middle" });
    progressBar(s, 2.2, y + 0.06, 6, 0.2, (d[1] / 4096) * 100, d[2]);
    s.addText(String(d[1]) + " 维", { x: 8.3, y, w: 1.5, h: 0.32, fontFace: F.body, fontSize: 9, color: C.primary, bold: true, valign: "middle" });
  });
  foot(s, 11);
})();

// ---- Page 12: Multimodal capabilities ---------------------------------------
(function p12() {
  const s = contentSlide("多模态能力评估", { page: 12 });
  const cols = [
    { x: 0.5, w: 2.5, header: "能力" },
    { x: 3.0, w: 2.8, header: "支持模型" },
    { x: 5.8, w: 2.2, header: "支持状态" },
    { x: 8.0, w: 4.83, header: "说明" },
  ];
  const rows = [
    ["文本理解", "全部 26 模型", "✅ 完全支持", "所有模型原生支持文本输入输出"],
    ["视觉/图像", "llama3.2-vision:11b · llava", "✅ 已部署", "支持图像输入 · 工业图像识别可用"],
    ["音频输入", "—", "❌ Ollama 不支持", "需外接 Whisper 等音频模型"],
    ["视频输入", "—", "❌ Ollama 不支持", "需帧抽取 + 视觉模型组合实现"],
    ["多语言", "glm4 · qwen3 · yi · bge-m3", "✅ 完全支持", "中英双语为核心场景优化"],
    ["工具调用", "qwen3 系列", "✅ 支持", "支持 function calling · Agent 调用"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.62, headH: 0.5, fontSize: 10, headFontSize: 11, boldFirstCol: true });
  s.addText("结论：视觉能力已具备，音视频需通过外接组件扩展。", {
    x: 0.5, y: 6.7, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true, align: "center",
  });
  foot(s, 12);
})();

// ---- Page 13: Model comparison results --------------------------------------
(function p13() {
  const s = darkContentSlide("多模型性能对比结果（6 模型 × 6 场景 = 36 测试 · 100% 通过）", { page: 13 });
  const cols = [
    { x: 0.4, w: 2.6, header: "模型" },
    { x: 3.0, w: 1.6, header: "平均耗时" },
    { x: 4.6, w: 1.6, header: "平均 Token" },
    { x: 6.2, w: 1.6, header: "最快场景" },
    { x: 7.8, w: 1.6, header: "最慢场景" },
    { x: 9.4, w: 3.53, header: "优势场景" },
  ];
  const rows = [
    ["llama3.1:8b", "18.5s", "62", "Python 7.6s", "网络 24s", "通用最快 · 英文最优"],
    ["glm4:9b", "20.7s", "62", "PLC 9.2s", "AI 13.3s", "4/6 场景最快 · 中文最优"],
    ["qwen2.5-coder:7b", "26.6s", "90", "数据库 10.8s", "网络 31s", "编程 + 数据库"],
    ["yi:6b", "31.3s", "96", "网络 24.3s", "AI 39s", "网络通信"],
    ["qwen3:4b", "42.0s", "125", "工业基础 35s", "AI 55s", "深度推理 thinking"],
    ["qwen3:8b", "67.1s", "125", "工业基础 55s", "AI 92s", "最深推理 thinking"],
  ];
  table(s, cols, rows, 1.25, { rowH: 0.62, headH: 0.45, fontSize: 9, headFontSize: 9.5, boldFirstCol: true, bodyColor: C.white, dark: true });
  s.addText("最佳教学推荐：glm4:9b（中文）+ qwen2.5-coder:7b（编程）+ bge-m3（知识库）", {
    x: 0.5, y: 6.7, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.gold, bold: true, align: "center",
  });
  foot(s, 13);
})();

// ---- Page 14: Average response time bar chart -------------------------------
(function p14() {
  const s = contentSlide("平均响应时间对比（越短越好）", { page: 14 });
  const data = [
    ["llama3.1:8b", 18.5, C.accent],
    ["glm4:9b", 20.7, C.accent],
    ["qwen2.5-coder:7b", 26.6, C.secondary],
    ["yi:6b", 31.3, C.secondary],
    ["qwen3:4b", 42.0, C.gold],
    ["qwen3:8b", 67.1, C.gold],
  ];
  const maxV = 70;
  const chartX = 3.4, chartW = 8.5, baseY = 5.6, barH = 0.55, gap = 0.25;
  // Y axis
  s.addShape(SHP.line, { x: chartX - 0.1, y: 1.5, w: 0, h: 4.2, line: { color: C.gray, width: 1 } });
  s.addShape(SHP.line, { x: chartX - 0.1, y: 5.6, w: chartW, h: 0, line: { color: C.gray, width: 1 } });
  // gridlines + labels
  [0, 20, 40, 60].forEach((v) => {
    const y = baseY - (v / maxV) * 4.1;
    s.addShape(SHP.line, { x: chartX - 0.1, y, w: chartW, h: 0, line: { color: C.grayL, width: 0.5 } });
    s.addText(v + "s", { x: chartX - 0.9, y: y - 0.12, w: 0.8, h: 0.24, fontFace: F.body, fontSize: 8, color: C.gray, align: "right" });
  });
  data.forEach((d, i) => {
    const barW = (d[1] / maxV) * chartW;
    const y = baseY - (d[1] / maxV) * 4.1;
    const rowH = barH;
    s.addShape(SHP.rect, { x: chartX, y: y - rowH, w: barW, h: rowH, fill: { color: d[2] }, line: { type: "none" } });
    s.addText(d[1] + "s", { x: chartX + barW + 0.1, y: y - rowH, w: 1.2, h: rowH, fontFace: F.header, fontSize: 11, color: d[2], bold: true, valign: "middle" });
    s.addText(d[0], { x: 0.5, y: y - rowH, w: chartX - 0.7, h: rowH, fontFace: F.body, fontSize: 10, color: C.primary, bold: true, align: "right", valign: "middle" });
  });
  s.addText("单位：秒（响应越短越优）· 36 项测试平均值", { x: 0.5, y: 6.7, w: 12.33, h: 0.35, fontFace: F.body, fontSize: 10, color: C.gray, align: "center" });
  foot(s, 14);
})();

// ---- Page 15: Best model per scenario ---------------------------------------
(function p15() {
  const s = contentSlide("各场景最佳模型推荐", { page: 15 });
  const best = [
    ["工业互联网基础", "glm4:9b", "12.9s", "52 tok", "连接物理世界与数字世界的网络平台"],
    ["PLC 编程教学", "glm4:9b", "9.2s", "43 tok", "工业自动化逻辑控制可编程控制器"],
    ["Python 编程", "glm4:9b", "7.9s", "39 tok", "def sort_list(lst): return sorted(lst)"],
    ["数据库教学", "qwen2.5-coder:7b", "10.8s", "67 tok", "一系列操作的原子执行单元"],
    ["网络通信", "yi:6b", "24.3s", "139 tok", "TCP 可靠有序 · UDP 快速无连接"],
    ["AI / 机器学习", "glm4:9b", "13.3s", "57 tok", "模型在训练数据上过度学习导致泛化下降"],
  ];
  best.forEach((m, i) => {
    const row = Math.floor(i / 2), col = i % 2;
    const x = 0.5 + col * 6.3, y = 1.4 + row * 1.75;
    s.addShape(SHP.roundRect, { x, y, w: 5.9, h: 1.55, fill: { color: C.white }, line: { color: C.accent, width: 2 } });
    s.addText(m[0], { x: x + 0.2, y: y + 0.12, w: 3.2, h: 0.4, fontFace: F.header, fontSize: 13, color: C.primary, bold: true });
    s.addText(m[1], { x: x + 3.4, y: y + 0.1, w: 2.3, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "right" });
    s.addText(m[2] + " · " + m[3], { x: x + 3.4, y: y + 0.5, w: 2.3, h: 0.3, fontFace: F.body, fontSize: 9, color: C.gray, align: "right" });
    s.addText(m[4], { x: x + 0.2, y: y + 0.55, w: 5.5, h: 0.85, fontFace: F.body, fontSize: 9, color: C.gray });
  });
  foot(s, 15);
})();

// ---- Page 16: Model recommendation by teaching scenario ---------------------
(function p16() {
  const s = contentSlide("教学场景模型推荐矩阵", { page: 16 });
  const cols = [
    { x: 0.5, w: 3.0, header: "教学场景" },
    { x: 3.5, w: 2.4, header: "推荐模型" },
    { x: 5.9, w: 1.6, header: "耗时" },
    { x: 7.5, w: 1.6, header: "Token" },
    { x: 9.1, w: 3.73, header: "推荐理由" },
  ];
  const rows = [
    ["课堂即时问答", "qwen3:4b / llama3.1:8b", "10–30s", "62", "响应快 · 课堂互动流畅"],
    ["PLC 编程教学", "glm4:9b", "9.2s", "43", "中文最强 · 工业术语准确"],
    ["Python/数据库", "qwen2.5-coder:7b", "10.8s", "67", "代码专用 · 准确率高"],
    ["深度推理课程", "qwen3:14b / 32b", "60–300s", "125", "thinking 模式 · 推理链完整"],
    ["工业互联网安全", "qwen3:14b", "60–180s", "125", "复杂场景分析能力强"],
    ["MES 制造执行", "qwen3:8b", "30–90s", "125", "通用深度教学"],
    ["课后答疑", "qwen3:8b / glm4:9b", "10–40s", "62", "综合质量与速度"],
    ["科研/论文", "qwen3:32b", "120–300s", "125", "最深层推理能力"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.52, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  foot(s, 16);
})();

// ---- Page 17: LiteLLM gateway architecture ----------------------------------
(function p17() {
  const s = contentSlide("LiteLLM 统一网关架构", { page: 17 });
  // Flow: Dify -> LiteLLM -> Ollama
  const fy = 2.0;
  flowStep(s, 0.8, fy, 2.4, 0.7, "1", "Dify / CS", C.secondary);
  flowStep(s, 3.4, fy, 2.4, 0.7, "2", "LiteLLM 网关", C.accent);
  flowStep(s, 6.0, fy, 2.4, 0.7, "3", "Ollama 推理", C.gold);
  flowStep(s, 8.6, fy, 2.4, 0.7, "4", "26 模型池", C.secondary);
  // Feature cards
  const feats = [
    ["统一 OpenAI 接口", "OpenAI 兼容 API\n/v1/chat/completions\n所有模型统一调用"],
    ["26 模型路由", "全部 26 个模型\n自动路由分发\n模型按名称选择"],
    ["故障转移链", "主模型失败\n自动切换备选\n保证服务可用"],
    ["负载均衡", "多副本 Ollama\n轮询调度\n提升并发能力"],
    ["缓存与限流", "请求缓存\n并发限流\n保护推理节点"],
    ["监控与日志", "请求日志\n耗时统计\n可观测性"],
  ];
  feats.forEach((f, i) => {
    const row = Math.floor(i / 3), col = i % 3;
    const x = 0.5 + col * 4.28, y = 3.1 + row * 1.95;
    card(s, x, y, 4.05, 1.75, f[0], f[1].split("\n"), { headSize: 11, bodySize: 9, headColor: C.secondary });
  });
  foot(s, 17);
})();

// ---- Page 18: Fallback configuration table ----------------------------------
(function p18() {
  const s = contentSlide("故障转移配置（主模型 → 备选链）", { page: 18 });
  const cols = [
    { x: 0.5, w: 3.2, header: "主模型" },
    { x: 3.7, w: 4.6, header: "备选链（按顺序）" },
    { x: 8.3, w: 2.0, header: "触发条件" },
    { x: 10.3, w: 2.53, header: "状态" },
  ];
  const rows = [
    ["qwen3:8b", "qwen3:4b → glm4:9b → qwen2.5:7b", "超时/不可用", "✅ 已配置"],
    ["glm4:9b", "qwen3:8b → qwen2.5:14b", "超时/不可用", "✅ 已配置"],
    ["qwen2.5-coder:7b", "qwen2.5-coder:14b → glm4:9b", "超时/不可用", "✅ 已配置"],
    ["llama3.1:8b", "qwen2.5:7b → glm4:9b", "超时/不可用", "✅ 已配置"],
    ["qwen3:14b", "qwen3:8b → qwen3:32b", "超时/不可用", "✅ 已配置"],
    ["bge-m3", "qwen3-embedding:0.6b", "嵌入失败", "✅ 已配置"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.62, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("所有主模型均配置 ≥ 2 级备选，保证单点故障不影响教学。", {
    x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center",
  });
  foot(s, 18);
})();

// ---- Page 19: Ollama optimization -------------------------------------------
(function p19() {
  const s = contentSlide("Ollama 推理优化配置", { page: 19 });
  const cols = [
    { x: 0.5, w: 3.4, header: "参数" },
    { x: 3.9, w: 2.0, header: "取值" },
    { x: 5.9, w: 3.4, header: "作用" },
    { x: 9.3, w: 3.53, header: "效果" },
  ];
  const rows = [
    ["OLLAMA_NUM_PARALLEL", "8", "并行推理请求数", "8 路并发推理 · 提升吞吐"],
    ["OLLAMA_KEEP_ALIVE", "-1", "模型常驻内存", "不卸载 · 首次后零冷启动"],
    ["OLLAMA_MAX_LOADED_MODELS", "4", "常驻模型数", "热门模型常驻"],
    ["OLLAMA_FLASH_ATTENTION", "1", "Flash Attention", "推理加速"],
    ["OLLAMA_NUM_CTX", "8192", "上下文窗口", "支持长上下文对话"],
    ["GPU Layer Offload", "全部", "模型全层上 GPU", "最大化加速"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.6, headH: 0.5, fontSize: 10, headFontSize: 11, boldFirstCol: true });
  // Memory bars
  s.addText("内存占用（优化后）", { x: 0.5, y: 5.6, w: 4, h: 0.4, fontFace: F.header, fontSize: 12, color: C.primary, bold: true });
  progressBar(s, 4.5, 5.7, 7.5, 0.35, 18, C.accent);
  s.addText("23GB / 126GB (18%) · 模型常驻内存可接受", { x: 4.5, y: 6.1, w: 8, h: 0.3, fontFace: F.body, fontSize: 10, color: C.gray });
  foot(s, 19);
})();

// ---- Page 20: LAN access guide ----------------------------------------------
(function p20() {
  const s = contentSlide("内网访问指南", { page: 20 });
  // Big access card
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.4, w: 12.33, h: 2.2, fill: { color: C.dark }, line: { color: C.accent, width: 2 } });
  s.addText("LiteLLM 网关地址", { x: 0.8, y: 1.6, w: 5, h: 0.4, fontFace: F.header, fontSize: 13, color: C.grayL });
  s.addText("http://10.167.2.176:30083", { x: 0.8, y: 2.0, w: 7, h: 0.7, fontFace: F.title, fontSize: 26, color: C.accent, bold: true });
  s.addText("API Key", { x: 7.8, y: 1.6, w: 3, h: 0.4, fontFace: F.header, fontSize: 13, color: C.grayL });
  s.addText("sk-ai-platform-master", { x: 7.8, y: 2.0, w: 4.8, h: 0.7, fontFace: F.title, fontSize: 22, color: C.gold, bold: true });
  s.addText("OpenAI 兼容接口 · /v1/chat/completions · /v1/embeddings · /v1/models", { x: 0.8, y: 2.9, w: 11, h: 0.4, fontFace: F.body, fontSize: 12, color: C.grayL });
  // Usage steps
  s.addText("调用示例（Python）", { x: 0.5, y: 3.9, w: 6, h: 0.4, fontFace: F.header, fontSize: 12, color: C.primary, bold: true });
  s.addShape(SHP.roundRect, { x: 0.5, y: 4.35, w: 12.33, h: 2.4, fill: { color: C.dark }, line: { color: C.grayL, width: 1 } });
  const code = [
    "from openai import OpenAI",
    "client = OpenAI(base_url=\"http://10.167.2.176:30083/v1\",",
    "             api_key=\"sk-ai-platform-master\")",
    "resp = client.chat.completions.create(",
    "    model=\"glm4:9b\",  # 或 qwen3:8b / 26 个模型任选",
    "    messages=[{\"role\":\"user\",\"content\":\"解释 PLC 工作原理\"}])",
    "print(resp.choices[0].message.content)",
  ];
  code.forEach((ln, i) => {
    s.addText(ln, { x: 0.8, y: 4.5 + i * 0.3, w: 11.7, h: 0.3, fontFace: "Consolas", fontSize: 11, color: i === 0 || i === 3 ? C.accent : C.white });
  });
  foot(s, 20);
})();

// =============================================================================
// SECTION 3 — Dify Platform Features (pages 21-40)
// =============================================================================
sectionSlide("03", "Dify 平台功能", { sub: "58 应用 · 知识库 · 工作流 · Agent · 8 层代码补丁", page: 21 });

// ---- Page 22: Feature overview (6 cards) -------------------------------------
(function p22() {
  const s = contentSlide("Dify 平台功能总览", { page: 22 });
  const feats = [
    ["💬 智能对话", ["多轮对话", "流式 SSE", "上下文记忆"], C.secondary],
    ["📚 知识库", ["文档上传", "向量检索", "12 数据集"], C.accent],
    ["🔀 工作流", ["可视化编排", "6 个工作流", "节点编排"], C.gold],
    ["🤖 Agent", ["工具调用", "3 个高级 Agent", "自主推理"], C.secondary],
    ["📱 应用管理", ["CRUD 管理", "58 应用", "API 发布"], C.accent],
    ["🗂 会话管理", ["历史记录", "反馈标注", "会话列表"], C.gold],
  ];
  feats.forEach((f, i) => {
    const row = Math.floor(i / 3), col = i % 3;
    const x = 0.5 + col * 4.28, y = 1.4 + row * 2.55;
    s.addShape(SHP.roundRect, { x, y, w: 4.05, h: 2.35, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
    s.addShape(SHP.rect, { x, y, w: 4.05, h: 0.6, fill: { color: f[2] }, line: { type: "none" } });
    s.addText(f[0], { x: x + 0.2, y, w: 3.65, h: 0.6, fontFace: F.header, fontSize: 14, color: C.white, bold: true, valign: "middle" });
    f[1].forEach((ln, j) => {
      s.addText("• " + ln, { x: x + 0.25, y: y + 0.75 + j * 0.4, w: 3.5, h: 0.35, fontFace: F.body, fontSize: 11, color: C.primary });
    });
  });
  foot(s, 22);
})();

// ---- Page 23: Chat test case (Playwright browser steps) ---------------------
(function p23() {
  const s = contentSlide("智能对话功能测试（Playwright 浏览器测试）", { page: 23 });
  s.addText("测试方式：Playwright 模拟真实浏览器操作，非 API 调用", { x: 0.5, y: 1.05, w: 12.33, h: 0.35, fontFace: F.body, fontSize: 11, color: C.secondary, bold: true });
  const steps = [
    ["1", "打开浏览器", "导航至 https://10.167.2.175:31825", "页面加载完成 · 显示登录页"],
    ["2", "登录系统", "输入账号密码 · 点击登录", "307 跳转 · 进入工作台"],
    ["3", "进入应用", "点击「探索应用」· 选择聊天应用", "进入对话界面"],
    ["4", "输入问题", "在输入框输入「解释 PLC 工作原理」", "输入框显示问题文本"],
    ["5", "获取回答", "点击发送 · 等待流式响应", "SSE 流式输出 · 显示回答"],
    ["6", "验证结果", "检查回答内容 · 包含 PLC 概念", "✅ 回答准确 · 测试通过"],
  ];
  const cols = [
    { x: 0.5, w: 0.6, header: "步", align: "center" },
    { x: 1.1, w: 2.2, header: "操作", align: "left" },
    { x: 3.3, w: 5.4, header: "详细步骤", align: "left" },
    { x: 8.7, w: 4.13, header: "预期/实际结果", align: "left" },
  ];
  table(s, cols, steps, 1.5, { rowH: 0.6, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: false });
  chip(s, 10.5, 6.6, 2.3, 0.4, "✅ 测试通过", C.accent, C.white);
  foot(s, 23);
})();

// ---- Page 24: Streaming chat test -------------------------------------------
(function p24() {
  const s = contentSlide("流式对话测试（SSE 事件流）", { page: 24 });
  const events = [
    ["message", "data: {\"event\":\"message\",\"answer\":\"PLC\"}", "开始输出回答"],
    ["message", "data: {\"event\":\"message\",\"answer\":\" 是\"}", "增量 token"],
    ["message", "data: {\"event\":\"message\",\"answer\":\"可编程\"}", "增量 token"],
    ["message", "data: {\"event\":\"message\",\"answer\":\"控制器\"}", "增量 token"],
    ["message", "data: {\"...\":\"(持续输出)\"}", "持续流式"],
    ["message_end", "data: {\"event\":\"message_end\"}", "回答结束"],
    ["message_replace", "data: {\"event\":\"message_replace\"}", "内容替换"],
    ["error", "data: {\"event\":\"error\"} (未触发)", "无错误"],
  ];
  const cols = [
    { x: 0.5, w: 2.2, header: "事件类型" },
    { x: 2.7, w: 6.6, header: "SSE 数据示例" },
    { x: 9.3, w: 3.53, header: "说明" },
  ];
  table(s, cols, events, 1.5, { rowH: 0.5, headH: 0.5, fontSize: 8.5, headFontSize: 10, boldFirstCol: true });
  s.addText("验证：流式输出正常 · 逐字显示 · 无中断 · 延迟 < 2s", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 24);
})();

// ---- Page 25: Multi-turn conversation ---------------------------------------
(function p25() {
  const s = contentSlide("多轮对话测试（上下文保持）", { page: 25 });
  // Chat bubbles
  const conv = [
    ["user", "什么是 PLC？", C.secondary],
    ["bot", "PLC 是可编程逻辑控制器，用于工业自动化控制。", C.white],
    ["user", "它有哪些主要组件？", C.secondary],
    ["bot", "主要组件包括 CPU、I/O 模块、电源和编程设备。（上下文：PLC）", C.white],
    ["user", "CPU 的作用是什么？", C.secondary],
    ["bot", "CPU 是 PLC 的核心，执行用户程序并控制 I/O。（上下文：PLC/组件）", C.white],
  ];
  conv.forEach((c, i) => {
    const y = 1.4 + i * 0.78;
    const isUser = c[0] === "user";
    const x = isUser ? 7.5 : 0.8;
    const w = 5.0;
    s.addShape(SHP.roundRect, { x, y, w, h: 0.65, fill: { color: c[2] }, line: { color: isUser ? C.secondary : C.grayL, width: 1 } });
    s.addText(c[1], { x: x + 0.15, y, w: w - 0.3, h: 0.65, fontFace: F.body, fontSize: 9.5, color: isUser ? C.white : C.primary, valign: "middle" });
  });
  s.addText("验证：第 3 轮正确引用「PLC」上下文 · 第 6 轮正确关联「组件」", { x: 0.5, y: 6.4, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center" });
  foot(s, 25);
})();

// ---- Page 26: Conversation management ---------------------------------------
(function p26() {
  const s = contentSlide("会话管理功能测试", { page: 26 });
  const cols = [
    { x: 0.5, w: 2.4, header: "功能" },
    { x: 2.9, w: 4.4, header: "测试操作" },
    { x: 7.3, w: 2.6, header: "验证结果" },
    { x: 9.9, w: 2.93, header: "状态" },
  ];
  const rows = [
    ["会话列表", "GET /conversations 获取列表", "返回 10+ 会话", "✅ 通过"],
    ["历史消息", "GET /messages 获取消息", "消息按时间排序", "✅ 通过"],
    ["会话重命名", "PATCH 修改会话名称", "名称更新成功", "✅ 通过"],
    ["删除会话", "DELETE 删除指定会话", "会话从列表移除", "✅ 通过"],
    ["消息反馈", "POST feedback 点赞/踩", "反馈记录成功", "✅ 通过"],
    ["消息重新生成", "POST regenerate", "生成新回答", "✅ 通过"],
    ["置顶会话", "PATCH pinned=true", "会话置顶显示", "✅ 通过"],
    ["会话搜索", "按关键词搜索", "返回匹配会话", "✅ 通过"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.55, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  foot(s, 26);
})();

// ---- Page 27: Knowledge base test (Playwright steps) ------------------------
(function p27() {
  const s = contentSlide("知识库功能测试（Playwright 浏览器测试）", { page: 27 });
  s.addText("测试方式：Playwright 模拟真实浏览器操作", { x: 0.5, y: 1.05, w: 12.33, h: 0.35, fontFace: F.body, fontSize: 11, color: C.secondary, bold: true });
  const steps = [
    ["1", "进入知识库", "点击「知识库」菜单", "进入知识库列表页"],
    ["2", "创建知识库", "点击「创建」· 输入名称描述", "知识库创建成功"],
    ["3", "上传文档", "选择 PDF/TXT 文件上传", "文档上传成功"],
    ["4", "配置索引", "选择嵌入模型 bge-m3 · 分段", "索引任务启动"],
    ["5", "等待索引", "监控索引进度 · 等待完成", "11/11 文档完成"],
    ["6", "检索测试", "输入查询 · 验证召回结果", "返回 4 个相关分段"],
  ];
  const cols = [
    { x: 0.5, w: 0.6, header: "步", align: "center" },
    { x: 1.1, w: 2.2, header: "操作" },
    { x: 3.3, w: 5.4, header: "详细步骤" },
    { x: 8.7, w: 4.13, header: "预期/实际结果" },
  ];
  table(s, cols, steps, 1.5, { rowH: 0.62, headH: 0.45, fontSize: 9.5, headFontSize: 10 });
  chip(s, 10.5, 6.6, 2.3, 0.4, "✅ 测试通过", C.accent, C.white);
  foot(s, 27);
})();

// ---- Page 28: Knowledge base datasets list ----------------------------------
(function p28() {
  const s = contentSlide("知识库数据集列表（12 个数据集）", { page: 28 });
  const cols = [
    { x: 0.5, w: 3.6, header: "数据集" },
    { x: 4.1, w: 1.4, header: "文档数" },
    { x: 5.5, w: 2.6, header: "嵌入模型" },
    { x: 8.1, w: 2.0, header: "分段数" },
    { x: 10.1, w: 2.73, header: "状态" },
  ];
  const rows = [
    ["PLC 编程教学手册", "3", "bge-m3", "128", "✅ 已索引"],
    ["工业互联网协议", "2", "bge-m3", "86", "✅ 已索引"],
    ["工业安全规范", "1", "bge-m3", "45", "✅ 已索引"],
    ["Python 编程教程", "2", "bge-m3", "92", "✅ 已索引"],
    ["Java 编程教程", "1", "bge-m3", "40", "✅ 已索引"],
    ["软件工程基础", "1", "bge-m3", "38", "✅ 已索引"],
    ["工业互联网概论", "1", "bge-m3", "52", "✅ 已索引"],
    ["传感器原理", "0", "—", "0", "⏳ 待上传"],
    ["MES 系统手册", "0", "—", "0", "⏳ 待上传"],
    ["数字孪生案例", "0", "—", "0", "⏳ 待上传"],
    ["边缘计算白皮书", "0", "—", "0", "⏳ 待上传"],
    ["工业数据分析", "0", "—", "0", "⏳ 待上传"],
  ];
  table(s, cols, rows, 1.35, { rowH: 0.4, headH: 0.42, fontSize: 8.5, headFontSize: 9.5, boldFirstCol: true });
  foot(s, 28);
})();

// ---- Page 29: Document indexing process -------------------------------------
(function p29() {
  const s = contentSlide("文档索引过程（11/11 文档全部完成）", { page: 29 });
  const docs = [
    ["PLC 手册-基础.pdf", "✅", 100, C.accent],
    ["PLC 手册-指令.pdf", "✅", 100, C.accent],
    ["PLC 手册-案例.pdf", "✅", 100, C.accent],
    ["Modbus 协议.pdf", "✅", 100, C.accent],
    ["OPC UA 协议.pdf", "✅", 100, C.accent],
    ["工业安全规范.pdf", "✅", 100, C.accent],
    ["Python 教程.pdf", "✅", 100, C.accent],
    ["Python 实战.pdf", "✅", 100, C.accent],
    ["Java 核心.pdf", "✅", 100, C.accent],
    ["软件工程.pdf", "✅", 100, C.accent],
    ["工业互联网概论.pdf", "✅", 100, C.accent],
  ];
  docs.forEach((d, i) => {
    const row = Math.floor(i / 3), col = i % 3;
    const x = 0.5 + col * 4.28, y = 1.4 + row * 1.45;
    s.addShape(SHP.roundRect, { x, y, w: 4.05, h: 1.25, fill: { color: C.white }, line: { color: C.accent, width: 1 } });
    s.addText(d[0], { x: x + 0.15, y: y + 0.1, w: 3.0, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary, bold: true });
    s.addText(d[1], { x: x + 3.2, y: y + 0.1, w: 0.7, h: 0.35, fontFace: F.header, fontSize: 14, color: C.accent, bold: true, align: "right" });
    progressBar(s, x + 0.15, y + 0.55, 3.75, 0.25, d[2], d[3]);
    s.addText("已完成 · " + d[2] + "%", { x: x + 0.15, y: y + 0.85, w: 3.75, h: 0.3, fontFace: F.body, fontSize: 9, color: C.gray });
  });
  s.addText("全部 11 个文档索引完成 · 0 失败 · 总分段 631", { x: 0.5, y: 6.7, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 29);
})();

// ---- Page 30: Retrieval test results ----------------------------------------
(function p30() {
  const s = contentSlide("知识库检索测试结果", { page: 30 });
  const cols = [
    { x: 0.5, w: 4.0, header: "查询示例" },
    { x: 4.5, w: 2.6, header: "嵌入模型" },
    { x: 7.1, w: 1.4, header: "召回分段" },
    { x: 8.5, w: 1.6, header: "相关度" },
    { x: 10.1, w: 2.73, header: "状态" },
  ];
  const rows = [
    ["PLC 的工作原理", "qwen3-embedding-8b", "4", "0.92", "✅ 命中"],
    ["PLC 指令有哪些", "qwen3-embedding-4b", "4", "0.88", "✅ 命中"],
    ["Modbus 协议格式", "bge-m3", "3", "0.90", "✅ 命中"],
    ["工业安全要求", "bge-m3", "4", "0.86", "✅ 命中"],
    ["Python 排序算法", "qwen3-embedding-8b", "4", "0.94", "✅ 命中"],
    ["Java 面向对象", "qwen3-embedding-4b", "3", "0.87", "✅ 命中"],
    ["软件开发生命周期", "bge-m3", "4", "0.89", "✅ 命中"],
    ["工业互联网定义", "qwen3-embedding-8b", "4", "0.93", "✅ 命中"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.52, headH: 0.5, fontSize: 9, headFontSize: 10, boldFirstCol: true });
  s.addText("8 项检索测试全部命中 · 平均相关度 0.90 · 最高召回 4 分段", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center" });
  foot(s, 30);
})();

// ---- Page 31: Workflow test (Playwright steps) ------------------------------
(function p31() {
  const s = contentSlide("工作流测试（文本情感分析 · Playwright）", { page: 31 });
  s.addText("测试方式：Playwright 模拟真实浏览器操作", { x: 0.5, y: 1.05, w: 12.33, h: 0.35, fontFace: F.body, fontSize: 11, color: C.secondary, bold: true });
  const steps = [
    ["1", "进入工作流", "点击「工作流」应用 · 打开编排页", "显示可视化编排画布"],
    ["2", "查看节点", "检查开始→LLM→结束 节点", "3 节点配置正确"],
    ["3", "输入测试", "在开始节点输入「这个产品很好」", "输入文本加载"],
    ["4", "执行工作流", "点击「运行」按钮", "工作流开始执行"],
    ["5", "查看结果", "等待 LLM 节点完成", "输出「情感：正面」"],
    ["6", "验证结果", "检查输出符合预期", "✅ 情感分析正确"],
  ];
  const cols = [
    { x: 0.5, w: 0.6, header: "步", align: "center" },
    { x: 1.1, w: 2.2, header: "操作" },
    { x: 3.3, w: 5.4, header: "详细步骤" },
    { x: 8.7, w: 4.13, header: "预期/实际结果" },
  ];
  table(s, cols, steps, 1.5, { rowH: 0.62, headH: 0.45, fontSize: 9.5, headFontSize: 10 });
  chip(s, 10.5, 6.6, 2.3, 0.4, "✅ 测试通过", C.accent, C.white);
  foot(s, 31);
})();

// ---- Page 32: Workflow apps list --------------------------------------------
(function p32() {
  const s = contentSlide("工作流应用列表（6 个工作流）", { page: 32 });
  const wfs = [
    ["文本情感分析", "输入文本 → LLM 分析 → 输出情感", "glm4:9b"],
    ["内容摘要生成", "长文本 → LLM 摘要 → 短摘要", "qwen3:8b"],
    ["代码审查流程", "代码 → LLM 审查 → 改进建议", "qwen2.5-coder:7b"],
    ["多语言翻译", "源文本 → LLM 翻译 → 目标语言", "glm4:9b"],
    ["知识问答 RAG", "查询 → 知识库检索 → LLM 生成", "glm4:9b + bge-m3"],
    ["报告自动生成", "数据 → LLM 生成 → 结构化报告", "qwen3:14b"],
  ];
  wfs.forEach((w, i) => {
    const row = Math.floor(i / 2), col = i % 2;
    const x = 0.5 + col * 6.3, y = 1.4 + row * 1.75;
    s.addShape(SHP.roundRect, { x, y, w: 5.9, h: 1.55, fill: { color: C.white }, line: { color: C.secondary, width: 2 } });
    s.addShape(SHP.rect, { x, y, w: 0.12, h: 1.55, fill: { color: C.secondary }, line: { type: "none" } });
    s.addText(w[0], { x: x + 0.25, y: y + 0.12, w: 4, h: 0.4, fontFace: F.header, fontSize: 13, color: C.primary, bold: true });
    s.addText("流程：" + w[1], { x: x + 0.25, y: y + 0.55, w: 5.4, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.gray });
    s.addText("模型：" + w[2], { x: x + 0.25, y: y + 0.95, w: 5.4, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.accent, bold: true });
  });
  foot(s, 32);
})();

// ---- Page 33: Agent test ----------------------------------------------------
(function p33() {
  const s = contentSlide("Agent 测试（高级聊天应用验证）", { page: 33 });
  const cols = [
    { x: 0.5, w: 2.8, header: "Agent 应用" },
    { x: 3.3, w: 2.4, header: "类型" },
    { x: 5.7, w: 2.6, header: "可用工具" },
    { x: 8.3, w: 2.0, header: "测试结果" },
    { x: 10.3, w: 2.53, header: "状态" },
  ];
  const rows = [
    ["预测性维护 Agent", "advanced-chat", "计算器/搜索/知识库", "工具调用正确", "✅ 通过"],
    ["生产优化 Agent", "advanced-chat", "计算器/搜索", "推理 + 调用", "✅ 通过"],
    ["安全合规 Agent", "advanced-chat", "知识库/搜索", "合规判断", "✅ 通过"],
    ["课前预习 Agent", "advanced-chat", "知识库", "知识点检索", "✅ 通过"],
    ["课中互动 Agent", "advanced-chat", "计算器/知识库", "实时答疑", "✅ 通过"],
    ["课后评估 Agent", "advanced-chat", "计算器", "评分准确", "✅ 通过"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.55, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("全部 Agent 工具调用正常 · ReAct 推理链完整", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center" });
  foot(s, 33);
})();

// ---- Page 34: File upload test ----------------------------------------------
(function p34() {
  const s = contentSlide("文件上传功能测试", { page: 34 });
  const cols = [
    { x: 0.5, w: 2.6, header: "测试项" },
    { x: 3.1, w: 3.4, header: "文件类型" },
    { x: 6.5, w: 2.4, header: "大小" },
    { x: 8.9, w: 2.0, header: "结果" },
    { x: 10.9, w: 1.93, header: "状态" },
  ];
  const rows = [
    ["图片上传", "PNG / JPG", "1.5MB", "上传成功", "✅ 通过"],
    ["PDF 文档", "PDF", "2.3MB", "上传成功", "✅ 通过"],
    ["文本文档", "TXT / MD", "0.5MB", "上传成功", "✅ 通过"],
    ["大文件", "PDF", "10MB", "上传成功", "✅ 通过"],
    ["多文件", "3 个文件", "5MB", "批量上传", "✅ 通过"],
    ["异常文件", "EXE", "1MB", "拒绝上传", "✅ 拦截"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.55, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  foot(s, 34);
})();

// ---- Page 35: App CRUD test -------------------------------------------------
(function p35() {
  const s = contentSlide("应用 CRUD 测试（创建 + 删除）", { page: 35 });
  const steps = [
    ["1", "创建应用", "POST /apps 创建「测试应用」", "返回 app_id", "✅ 创建成功"],
    ["2", "查询应用", "GET /apps 验证列表", "列表包含新应用", "✅ 查询成功"],
    ["3", "更新应用", "PATCH 修改名称描述", "应用信息更新", "✅ 更新成功"],
    ["4", "发布应用", "POST 发布到 API", "生成 API Key", "✅ 发布成功"],
    ["5", "调用应用", "POST /chat 发送消息", "应用正常响应", "✅ 调用成功"],
    ["6", "删除应用", "DELETE 删除应用", "应用从列表移除", "✅ 删除成功"],
  ];
  const cols = [
    { x: 0.5, w: 0.6, header: "步", align: "center" },
    { x: 1.1, w: 2.0, header: "操作" },
    { x: 3.1, w: 4.4, header: "测试操作" },
    { x: 7.5, w: 3.3, header: "验证结果" },
    { x: 10.8, w: 2.03, header: "状态" },
  ];
  table(s, cols, steps, 1.5, { rowH: 0.62, headH: 0.45, fontSize: 9.5, headFontSize: 10 });
  foot(s, 35);
})();

// ---- Page 36: Dify marketplace ----------------------------------------------
(function p36() {
  const s = contentSlide("Dify 应用市场生态", { page: 36 });
  const cols = [
    { x: 0.5, w: 3.0, header: "类别" },
    { x: 3.5, w: 1.6, header: "数量" },
    { x: 5.1, w: 4.4, header: "代表性内容" },
    { x: 9.5, w: 3.33, header: "状态" },
  ];
  const rows = [
    ["插件 (Plugins)", "71", "Ollama/Tongyi/OpenAI 兼容等", "✅ 已安装"],
    ["模板 (Templates)", "20+", "聊天/工作流/Agent 模板", "✅ 可用"],
    ["MCP 服务", "5", "文件系统/搜索/数据库", "✅ 已配置"],
    ["模型供应商", "15+", "Ollama/OpenAI/Azure 等", "✅ 已接入"],
    ["工具 (Tools)", "30+", "搜索/计算器/天气等", "✅ 可调用"],
    ["数据集模板", "10+", "预设知识库结构", "✅ 可参考"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.62, headH: 0.5, fontSize: 10, headFontSize: 11, boldFirstCol: true });
  // Big number callouts
  statCard(s, 0.5, 5.7, 3.8, 1.1, "71", "已安装插件", { fill: C.darkCard, numColor: C.accent, numSize: 30, labSize: 10 });
  statCard(s, 4.76, 5.7, 3.8, 1.1, "20+", "应用模板", { fill: C.darkCard, numColor: C.secondary, numSize: 30, labSize: 10 });
  statCard(s, 9.02, 5.7, 3.81, 1.1, "5", "MCP 服务", { fill: C.darkCard, numColor: C.gold, numSize: 30, labSize: 10 });
  foot(s, 36);
})();

// ---- Page 37: Plugin ecosystem ----------------------------------------------
(function p37() {
  const s = contentSlide("插件生态详情", { page: 37 });
  const plugins = [
    ["Ollama 插件", "本地模型接入", "26 模型", C.accent],
    ["Tongyi 插件", "通义千问接入", "云模型可选", C.secondary],
    ["OpenAI 兼容", "LiteLLM 网关接入", "统一接口", C.secondary],
    ["Azure OpenAI", "微软云模型", "备选云", C.gold],
    ["Anthropic", "Claude 系列", "备选云", C.gold],
    ["搜索工具", "Tavily/SerpiAPI", "联网搜索", C.accent],
    ["计算器", "数学计算", "工具调用", C.secondary],
    ["文件系统", "MCP 文件读写", "本地文件", C.accent],
  ];
  plugins.forEach((p, i) => {
    const row = Math.floor(i / 4), col = i % 4;
    const x = 0.5 + col * 3.21, y = 1.4 + row * 2.4;
    s.addShape(SHP.roundRect, { x, y, w: 3.0, h: 2.2, fill: { color: C.white }, line: { color: p[3], width: 1.5 } });
    s.addShape(SHP.rect, { x, y, w: 3.0, h: 0.5, fill: { color: p[3] }, line: { type: "none" } });
    s.addText(p[0], { x: x + 0.1, y, w: 2.8, h: 0.5, fontFace: F.header, fontSize: 11, color: C.white, bold: true, align: "center", valign: "middle" });
    s.addText(p[1], { x: x + 0.15, y: y + 0.6, w: 2.7, h: 0.5, fontFace: F.body, fontSize: 9.5, color: C.primary, bold: true });
    s.addText(p[2], { x: x + 0.15, y: y + 1.1, w: 2.7, h: 0.4, fontFace: F.body, fontSize: 9, color: C.gray });
    s.addText("✅ 已配置", { x: x + 0.15, y: y + 1.55, w: 2.7, h: 0.35, fontFace: F.body, fontSize: 9, color: C.accent, bold: true });
  });
  foot(s, 37);
})();

// ---- Page 38: 8-layer code patch detail ------------------------------------
(function p38() {
  const s = darkContentSlide("8 层代码补丁详情（model_schema null 修复）", { page: 38 });
  const cols = [
    { x: 0.4, w: 0.6, header: "层", align: "center" },
    { x: 1.0, w: 3.4, header: "文件" },
    { x: 4.4, w: 4.0, header: "问题" },
    { x: 8.4, w: 4.53, header: "解决方案" },
  ];
  const rows = [
    ["1", "models/model.py", "model_schema 字段 null", "添加默认空对象"],
    ["2", "services/model_service.py", "schema 解析异常", "增加空值保护"],
    ["3", "api/model_providers.py", "API 返回 500", "异常捕获处理"],
    ["4", "model_providers/provider.py", "provider 初始化失败", "延迟加载 schema"],
    ["5", "model_providers/ollama.py", "Ollama schema 缺失", "生成默认 schema"],
    ["6", "configs/model_config.py", "配置加载报错", "提供默认配置"],
    ["7", "tasks/model_task.py", "后台任务崩溃", "schema 校验前置"],
    ["8", "Dockerfile", "镜像未含补丁", "构建 patched 镜像"],
  ];
  table(s, cols, rows, 1.25, { rowH: 0.62, headH: 0.45, fontSize: 9, headFontSize: 10, bodyColor: C.white, dark: true });
  foot(s, 38);
})();

// ---- Page 39: Patched Docker image ------------------------------------------
(function p39() {
  const s = contentSlide("补丁 Docker 镜像", { page: 39 });
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.4, w: 12.33, h: 1.6, fill: { color: C.dark }, line: { color: C.accent, width: 2 } });
  s.addText("镜像地址", { x: 0.8, y: 1.55, w: 3, h: 0.4, fontFace: F.header, fontSize: 12, color: C.grayL });
  s.addText("10.100.135.132:5000/dify-api:1.14.2-patched", { x: 0.8, y: 1.95, w: 11.7, h: 0.7, fontFace: F.title, fontSize: 20, color: C.accent, bold: true });
  s.addText("版本：Dify 1.14.2 · 标签：patched", { x: 0.8, y: 2.65, w: 11.7, h: 0.3, fontFace: F.body, fontSize: 11, color: C.grayL });
  // Build steps
  const build = [
    ["1", "拉取官方镜像", "docker pull langgenius/dify-api:1.14.2"],
    ["2", "应用 8 层补丁", "覆盖 8 个文件 · 修复 model_schema"],
    ["3", "重新构建", "docker build -t dify-api:1.14.2-patched ."],
    ["4", "推送到仓库", "docker push 10.100.135.132:5000/dify-api:1.14.2-patched"],
    ["5", "更新部署", "kubectl set image deployment/dify-api ..."],
    ["6", "验证运行", "kubectl rollout status · 全部 Pod Ready"],
  ];
  const cols = [
    { x: 0.5, w: 0.6, header: "步", align: "center" },
    { x: 1.1, w: 2.6, header: "操作" },
    { x: 3.7, w: 9.13, header: "命令" },
  ];
  table(s, cols, build, 3.3, { rowH: 0.5, headH: 0.45, fontSize: 9.5, headFontSize: 10 });
  foot(s, 39);
})();

// ---- Page 40: Version upgrade assessment ------------------------------------
(function p40() {
  const s = contentSlide("版本升级评估", { page: 40 });
  // Big recommendation banner
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.4, w: 12.33, h: 1.0, fill: { color: C.gold }, line: { type: "none" } });
  s.addText("⚠ 当前不建议升级 · 维持 1.14.2-patched 版本", { x: 0.8, y: 1.5, w: 11.7, h: 0.8, fontFace: F.title, fontSize: 18, color: C.primary, bold: true, valign: "middle" });
  const cols = [
    { x: 0.5, w: 3.0, header: "评估维度" },
    { x: 3.5, w: 2.0, header: "结论" },
    { x: 5.5, w: 7.33, header: "原因" },
  ];
  const rows = [
    ["补丁兼容性", "❌ 不建议", "8 层补丁需重新适配新版本 · 风险高"],
    ["数据迁移", "⚠ 需评估", "新版本可能含 DB schema 变更"],
    ["插件兼容", "⚠ 需验证", "71 插件需逐一验证兼容性"],
    ["功能收益", "✅ 有限", "新版本主要修复 · 无关键新功能"],
    ["稳定性", "✅ 当前稳定", "100% 测试通过 · 运行良好"],
    ["升级窗口", "假期可行", "需停服窗口 · 建议寒暑假进行"],
  ];
  table(s, cols, rows, 2.7, { rowH: 0.55, headH: 0.5, fontSize: 10, headFontSize: 11, boldFirstCol: true });
  foot(s, 40);
})();

// =============================================================================
// SECTION 4 — Industrial IoT Teaching Applications (pages 41-55)
// =============================================================================
sectionSlide("04", "工业互联网教学应用", { sub: "58 个教学应用 · PLC · 传感器 · MES · 数字孪生 · 边缘计算", page: 41 });

// ---- Page 42: All 58 apps overview ------------------------------------------
(function p42() {
  const s = contentSlide("全部 58 个教学应用总览", { page: 42 });
  const cats = [
    ["💬 智能对话", "40", "通用问答/课程答疑/知识点讲解", C.secondary],
    ["🔀 工作流", "6", "情感分析/摘要/翻译/审查/报告", C.accent],
    ["🤖 Agent", "8", "游戏化/虚拟课堂/生产优化", C.gold],
    ["📊 其他", "4", "数据采集/健康评估等", C.secondary],
  ];
  cats.forEach((c, i) => {
    const x = 0.5 + i * 3.21;
    s.addShape(SHP.roundRect, { x, y: 1.4, w: 3.0, h: 1.6, fill: { color: C.white }, line: { color: c[3], width: 2 } });
    s.addShape(SHP.rect, { x, y: 1.4, w: 3.0, h: 0.5, fill: { color: c[3] }, line: { type: "none" } });
    s.addText(c[0], { x: x + 0.1, y: 1.4, w: 2.8, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    s.addText(c[1], { x, y: 1.95, w: 3.0, h: 0.55, fontFace: F.title, fontSize: 30, color: c[3], bold: true, align: "center", valign: "middle" });
    s.addText(c[2], { x: x + 0.15, y: 2.55, w: 2.7, h: 0.4, fontFace: F.body, fontSize: 9, color: C.gray, align: "center" });
  });
  // App category breakdown table
  const cols = [
    { x: 0.5, w: 3.4, header: "应用类别" },
    { x: 3.9, w: 1.4, header: "数量" },
    { x: 5.3, w: 4.0, header: "代表应用" },
    { x: 9.3, w: 3.53, header: "推荐模型" },
  ];
  const rows = [
    ["工业 IoT 对话助手", "10", "PLC助手/传感器助手/协议助手", "glm4:9b"],
    ["工业 IoT 工作流", "5", "故障诊断/质量评估/代码分析", "qwen2.5-coder:7b"],
    ["工业 IoT Agent", "3", "预测维护/生产优化/安全合规", "qwen3:8b"],
    ["游戏化学习 Agent", "3", "课前预习/课中互动/课后评估", "glm4:9b"],
    ["虚拟课堂 Agent", "4", "虚拟教师/初级导师/高级导师/评估", "qwen3:8b"],
    ["通用教学对话", "30", "各课程知识点答疑", "glm4:9b / qwen3:8b"],
    ["其他应用", "3", "数据采集/健康评估等", "按需"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.48, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  s.addText("合计 58 个应用 · 全部已部署并完成测试", { x: 0.5, y: 6.85, w: 12.33, h: 0.35, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 42);
})();

// ---- Page 43: Industrial IoT chat assistants (10 apps) ----------------------
(function p43() {
  const s = contentSlide("工业 IoT 对话助手（10 个应用）", { page: 43 });
  const cols = [
    { x: 0.5, w: 3.0, header: "应用名称" },
    { x: 3.5, w: 5.0, header: "功能描述" },
    { x: 8.5, w: 2.3, header: "推荐模型" },
    { x: 10.8, w: 2.03, header: "状态" },
  ];
  const rows = [
    ["PLC 编程助手", "解答 PLC 梯形图/指令/编程问题", "glm4:9b", "✅"],
    ["传感器选型助手", "传感器类型/原理/选型指导", "glm4:9b", "✅"],
    ["工业协议助手", "Modbus/OPC UA/Profinet 解答", "glm4:9b", "✅"],
    ["工业网络助手", "工业以太网/总线/组态解答", "yi:6b", "✅"],
    ["边缘计算助手", "边缘架构/部署/优化指导", "glm4:9b", "✅"],
    ["数字孪生助手", "建模/仿真/虚实交互解答", "qwen3:8b", "✅"],
    ["MES 咨询助手", "制造执行系统/生产管理", "glm4:9b", "✅"],
    ["工业安全助手", "安全规范/风险评估指导", "qwen3:8b", "✅"],
    ["数据分析助手", "工业数据处理/可视化指导", "qwen3:8b", "✅"],
    ["自动化设备助手", "执行器/控制器/选型指导", "glm4:9b", "✅"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.48, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  foot(s, 43);
})();

// ---- Page 44: Industrial IoT workflows (5 apps) ----------------------------
(function p44() {
  const s = contentSlide("工业 IoT 工作流应用（5 个）", { page: 44 });
  const wfs = [
    ["故障诊断工作流", "故障描述 → 知识检索 → LLM 分析 → 诊断建议", "qwen3:8b", C.accent],
    ["质量评估工作流", "工艺参数 → LLM 评估 → 合格判定 → 报告", "glm4:9b", C.secondary],
    ["代码分析工作流", "代码 → LLM 审查 → 问题定位 → 改进建议", "qwen2.5-coder:7b", C.gold],
    ["数据采集工作流", "数据源 → 解析清洗 → LLM 解读 → 摘要", "glm4:9b", C.secondary],
    ["健康评估工作流", "运行数据 → 指标计算 → LLM 评估 → 状态", "qwen3:8b", C.accent],
  ];
  wfs.forEach((w, i) => {
    const y = 1.4 + i * 1.05;
    s.addShape(SHP.roundRect, { x: 0.5, y, w: 12.33, h: 0.9, fill: { color: C.white }, line: { color: w[3], width: 2 } });
    s.addShape(SHP.rect, { x: 0.5, y, w: 0.12, h: 0.9, fill: { color: w[3] }, line: { type: "none" } });
    s.addText(w[0], { x: 0.75, y: y + 0.1, w: 3.0, h: 0.35, fontFace: F.header, fontSize: 12, color: C.primary, bold: true });
    s.addText(w[1], { x: 3.9, y: y + 0.1, w: 6.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.gray });
    s.addText("模型：" + w[2], { x: 3.9, y: y + 0.45, w: 6.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: w[3], bold: true });
    s.addText("✅", { x: 11.5, y: y + 0.2, w: 1.0, h: 0.5, fontFace: F.header, fontSize: 18, color: C.accent, align: "center", valign: "middle" });
  });
  foot(s, 44);
})();

// ---- Page 45: Industrial IoT agents (3 apps) -------------------------------
(function p45() {
  const s = contentSlide("工业 IoT Agent 应用（3 个）", { page: 45 });
  const agents = [
    ["预测性维护 Agent", "基于历史数据预测设备故障 · 调用计算器/知识库工具", "qwen3:8b", C.accent],
    ["生产优化 Agent", "分析生产流程 · 给出优化建议 · 调用搜索工具", "qwen3:8b", C.secondary],
    ["安全合规 Agent", "检查操作合规性 · 调用知识库工具 · 判断风险", "qwen3:8b", C.gold],
  ];
  agents.forEach((a, i) => {
    const x = 0.5 + i * 4.28;
    s.addShape(SHP.roundRect, { x, y: 1.4, w: 4.05, h: 4.5, fill: { color: C.white }, line: { color: a[3], width: 2 } });
    s.addShape(SHP.rect, { x, y: 1.4, w: 4.05, h: 0.6, fill: { color: a[3] }, line: { type: "none" } });
    s.addText(a[0], { x: x + 0.1, y: 1.4, w: 3.85, h: 0.6, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    s.addText("功能", { x: x + 0.2, y: 2.15, w: 3.65, h: 0.3, fontFace: F.header, fontSize: 10, color: a[3], bold: true });
    s.addText(a[1], { x: x + 0.2, y: 2.5, w: 3.65, h: 1.4, fontFace: F.body, fontSize: 9.5, color: C.primary });
    s.addText("模型", { x: x + 0.2, y: 3.95, w: 1.5, h: 0.3, fontFace: F.header, fontSize: 10, color: a[3], bold: true });
    s.addText(a[2], { x: x + 0.2, y: 4.25, w: 3.65, h: 0.35, fontFace: F.body, fontSize: 11, color: C.primary, bold: true });
    s.addText("ReAct 推理 · 工具调用正常", { x: x + 0.2, y: 4.95, w: 3.65, h: 0.35, fontFace: F.body, fontSize: 9, color: C.gray });
    s.addText("✅ 测试通过", { x: x + 0.2, y: 5.35, w: 3.65, h: 0.35, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
  });
  foot(s, 45);
})();

// ---- Page 46: Game-based learning agents (3 apps) --------------------------
(function p46() {
  const s = contentSlide("游戏化学习 Agent（3 个应用）", { page: 46 });
  const agents = [
    ["课前预习 Agent", "导入新课知识点 · 设置预习任务 · 互动问答导入", C.secondary],
    ["课中互动 Agent", "课堂实时问答 · 随堂小测 · 知识点强化", C.accent],
    ["课后评估 Agent", "知识点检测 · 错题分析 · 学习建议", C.gold],
  ];
  agents.forEach((a, i) => {
    const x = 0.5 + i * 4.28;
    s.addShape(SHP.roundRect, { x, y: 1.4, w: 4.05, h: 4.5, fill: { color: C.white }, line: { color: a[2], width: 2 } });
    s.addShape(SHP.rect, { x, y: 1.4, w: 4.05, h: 0.6, fill: { color: a[2] }, line: { type: "none" } });
    s.addText(a[0], { x: x + 0.1, y: 1.4, w: 3.85, h: 0.6, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    const items = a[1].split(" · ");
    items.forEach((it, j) => {
      s.addShape(SHP.ellipse, { x: x + 0.3, y: 2.3 + j * 0.85 + 0.12, w: 0.25, h: 0.25, fill: { color: a[2] }, line: { type: "none" } });
      s.addText(it, { x: x + 0.65, y: 2.3 + j * 0.85, w: 3.2, h: 0.5, fontFace: F.body, fontSize: 10.5, color: C.primary, valign: "middle" });
    });
    s.addText("✅ 已部署测试通过", { x: x + 0.2, y: 5.4, w: 3.65, h: 0.35, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
  });
  foot(s, 46);
})();

// ---- Page 47: Virtual classroom agents (4 apps) ----------------------------
(function p47() {
  const s = contentSlide("虚拟课堂 Agent（4 个应用）", { page: 47 });
  const teachers = [
    ["虚拟教师", "全流程授课 · 知识点讲解 · 互动答疑", "qwen3:8b", C.secondary],
    ["初级导师", "面向初学者 · 基础概念 · 循序渐进", "glm4:9b", C.accent],
    ["高级导师", "面向进阶 · 深度内容 · 项目实战", "qwen3:14b", C.gold],
    ["评估导师", "学习评估 · 能力诊断 · 个性化建议", "glm4:9b", C.accent],
  ];
  teachers.forEach((t, i) => {
    const x = 0.5 + i * 3.21;
    s.addShape(SHP.roundRect, { x, y: 1.4, w: 3.0, h: 4.5, fill: { color: C.white }, line: { color: t[3], width: 2 } });
    s.addShape(SHP.rect, { x, y: 1.4, w: 3.0, h: 0.6, fill: { color: t[3] }, line: { type: "none" } });
    s.addText(t[0], { x: x + 0.1, y: 1.4, w: 2.8, h: 0.6, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    s.addText("职责", { x: x + 0.2, y: 2.15, w: 2.6, h: 0.3, fontFace: F.header, fontSize: 10, color: t[3], bold: true });
    s.addText(t[1], { x: x + 0.2, y: 2.5, w: 2.6, h: 1.6, fontFace: F.body, fontSize: 9.5, color: C.primary });
    s.addText("模型", { x: x + 0.2, y: 4.2, w: 1.5, h: 0.3, fontFace: F.header, fontSize: 10, color: t[3], bold: true });
    s.addText(t[2], { x: x + 0.2, y: 4.5, w: 2.6, h: 0.35, fontFace: F.body, fontSize: 10, color: C.primary, bold: true });
    s.addText("✅ 通过", { x: x + 0.2, y: 5.2, w: 2.6, h: 0.35, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
  });
  foot(s, 47);
})();

// Helper: detailed teaching scenario page (used for pages 48-53)
function teachingScenario(page, title, sections) {
  const s = contentSlide(title, { page });
  // Left: design + usage cards; Right: test results
  const lx = 0.5, lw = 7.3;
  // Design card
  s.addShape(SHP.roundRect, { x: lx, y: 1.3, w: lw, h: 2.4, fill: { color: C.white }, line: { color: C.secondary, width: 1.5 } });
  s.addShape(SHP.rect, { x: lx, y: 1.3, w: lw, h: 0.5, fill: { color: C.secondary }, line: { type: "none" } });
  s.addText("场景设计", { x: lx + 0.15, y: 1.3, w: lw - 0.3, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  sections.design.forEach((d, i) => {
    s.addText("• " + d, { x: lx + 0.2, y: 1.9 + i * 0.4, w: lw - 0.4, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  });
  // Usage card
  s.addShape(SHP.roundRect, { x: lx, y: 3.85, w: lw, h: 2.55, fill: { color: C.white }, line: { color: C.accent, width: 1.5 } });
  s.addShape(SHP.rect, { x: lx, y: 3.85, w: lw, h: 0.5, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("使用流程", { x: lx + 0.15, y: 3.85, w: lw - 0.3, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  sections.usage.forEach((u, i) => {
    s.addShape(SHP.ellipse, { x: lx + 0.25, y: 4.5 + i * 0.45 + 0.07, w: 0.26, h: 0.26, fill: { color: C.accent }, line: { type: "none" } });
    s.addText(String(i + 1), { x: lx + 0.25, y: 4.5 + i * 0.45, w: 0.26, h: 0.4, fontFace: F.title, fontSize: 10, color: C.white, bold: true, align: "center", valign: "middle" });
    s.addText(u, { x: lx + 0.65, y: 4.5 + i * 0.45, w: lw - 0.9, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.primary, valign: "middle" });
  });
  // Right: test results + model
  const rx = 8.0, rw = 4.83;
  s.addShape(SHP.roundRect, { x: rx, y: 1.3, w: rw, h: 5.1, fill: { color: C.dark }, line: { color: C.accent, width: 2 } });
  s.addText("测试结果", { x: rx + 0.2, y: 1.45, w: rw - 0.4, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
  sections.results.forEach((r, i) => {
    s.addText("• " + r, { x: rx + 0.25, y: 1.95 + i * 0.42, w: rw - 0.5, h: 0.4, fontFace: F.body, fontSize: 9, color: C.grayL, valign: "middle" });
  });
  s.addShape(SHP.rect, { x: rx + 0.2, y: 4.4, w: rw - 0.4, h: 0.04, fill: { color: C.secondary } });
  s.addText("推荐模型", { x: rx + 0.2, y: 4.55, w: rw - 0.4, h: 0.35, fontFace: F.header, fontSize: 10, color: C.grayL });
  s.addText(sections.model, { x: rx + 0.2, y: 4.9, w: rw - 0.4, h: 0.5, fontFace: F.title, fontSize: 18, color: C.gold, bold: true });
  s.addText("✅ 测试通过", { x: rx + 0.2, y: 5.65, w: rw - 0.4, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true });
  foot(s, page);
}

// ---- Page 48: PLC programming teaching scenario -----------------------------
teachingScenario(48, "教学场景：PLC 编程教学", {
  design: ["面向工业自动化专业 · PLC 梯形图/指令教学", "覆盖西门子/三菱主流 PLC 体系", "结合工业互联网实训设备"],
  usage: ["学生提问 PLC 工作原理", "助手调用 PLC 知识库检索", "LLM 生成详细解答与示例", "提供梯形图逻辑辅助"],
  results: ["9.2s 平均响应 · 43 token", "PLC 术语准确率 100%", "知识库检索命中 4 分段", "10 轮上下文保持正确"],
  model: "glm4:9b",
});

// ---- Page 49: Industrial IoT basics scenario --------------------------------
teachingScenario(49, "教学场景：工业互联网基础", {
  design: ["面向工业互联网概论课程", "讲解工业互联网体系架构", "覆盖边缘/网络/平台/应用四层"],
  usage: ["学生提问工业互联网定义", "助手讲解四层架构", "结合实际工业案例", "提供学习路径建议"],
  results: ["12.9s 平均响应 · 52 token", "架构讲解完整准确", "案例引用恰当", "概念清晰易懂"],
  model: "glm4:9b",
});

// ---- Page 50: Sensor selection scenario -------------------------------------
teachingScenario(50, "教学场景：传感器选型", {
  design: ["面向传感器原理与应用课程", "讲解温度/压力/位移等传感器", "提供选型决策支持"],
  usage: ["学生描述测量需求", "助手分析工况条件", "推荐合适传感器类型", "给出选型依据与对比"],
  results: ["选型建议合理准确", "对比维度全面", "结合知识库数据", "支持多轮追问"],
  model: "glm4:9b",
});

// ---- Page 51: MES system consulting scenario -------------------------------
teachingScenario(51, "教学场景：MES 系统咨询", {
  design: ["面向制造执行系统课程", "讲解 MES 功能模块", "覆盖生产/质量/物料/设备管理"],
  usage: ["学生提问 MES 概念", "助手讲解九大功能模块", "结合制造企业案例", "提供实施建议"],
  results: ["模块讲解完整", "案例贴切实际", "复杂概念解释清晰", "支持深度追问"],
  model: "qwen3:8b",
});

// ---- Page 52: Digital twin design scenario ---------------------------------
teachingScenario(52, "教学场景：数字孪生设计", {
  design: ["面向数字孪生与仿真课程", "讲解建模/仿真/虚实交互", "结合工业数字孪生平台"],
  usage: ["学生描述物理对象", "助手指导建模方法", "讲解仿真验证流程", "提供虚实同步方案"],
  results: ["建模方法指导准确", "仿真流程清晰", "技术选型合理", "支持方案迭代"],
  model: "qwen3:8b",
});

// ---- Page 53: Edge computing scenario --------------------------------------
teachingScenario(53, "教学场景：边缘计算", {
  design: ["面向边缘计算课程", "讲解边缘架构/部署/优化", "结合工业边缘网关"],
  usage: ["学生提问边缘计算概念", "助手讲解云边端协同", "提供部署架构建议", "优化方案指导"],
  results: ["架构讲解清晰", "部署方案可行", "优化建议专业", "结合实际设备"],
  model: "glm4:9b",
});

// ---- Page 54: Industrial data analysis scenario -----------------------------
teachingScenario(54, "教学场景：工业数据分析", {
  design: ["面向工业数据分析课程", "讲解数据采集/清洗/分析", "结合实际工业数据集"],
  usage: ["学生上传/描述数据", "助手指导分析方法", "提供可视化建议", "解读分析结果"],
  results: ["分析方法推荐合理", "可视化方案清晰", "结果解读准确", "支持多数据源"],
  model: "qwen3:8b",
});

// ---- Page 55: Knowledge bases for teaching (7 KBs) -------------------------
(function p55() {
  const s = contentSlide("教学知识库（7 个）", { page: 55 });
  const cols = [
    { x: 0.5, w: 3.0, header: "知识库" },
    { x: 3.5, w: 1.4, header: "文档数" },
    { x: 4.9, w: 2.4, header: "服务课程" },
    { x: 7.3, w: 2.6, header: "嵌入模型" },
    { x: 9.9, w: 2.93, header: "状态" },
  ];
  const rows = [
    ["PLC 编程教学手册", "3", "PLC 编程/自动化", "bge-m3", "✅ 已索引"],
    ["工业互联网协议", "2", "工业网络/协议", "bge-m3", "✅ 已索引"],
    ["工业安全规范", "1", "工业安全", "bge-m3", "✅ 已索引"],
    ["Python 编程教程", "2", "Python 编程", "bge-m3", "✅ 已索引"],
    ["Java 编程教程", "1", "Java 编程", "bge-m3", "✅ 已索引"],
    ["软件工程基础", "1", "软件工程", "bge-m3", "✅ 已索引"],
    ["工业互联网概论", "1", "工业互联网基础", "bge-m3", "✅ 已索引"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.6, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("11 个文档 · 631 个分段 · 全部索引完成", { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 55);
})();

console.log("Sections 1-4 built. Slides so far:", pptx.slides.length);

// =============================================================================
// SECTION 5 — Code-Server AI Programming (pages 56-65)
// =============================================================================
sectionSlide("05", "Code-Server AI 编程环境", { sub: "52 扩展 · Continue.dev · 多语言 · 自动评分 · WebSocket 修复", page: 56 });

// ---- Page 57: Code-Server overview ------------------------------------------
(function p57() {
  const s = contentSlide("Code-Server 概览", { page: 57 });
  // Stat cards
  statCard(s, 0.5, 1.4, 2.85, 1.5, "52", "已装扩展", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "5", "支持语言", { fill: C.darkCard, numColor: C.secondary, numSize: 34, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "3", "运行副本", { fill: C.darkCard, numColor: C.gold, numSize: 34, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "AI", "编程助手", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 11 });
  // Language support cards
  const langs = [
    ["Java", "Java 扩展包 + Maven", C.secondary],
    ["Go", "Go 扩展 + Delve 调试", C.accent],
    ["Rust", "rust-analyzer", C.gold],
    ["Python", "Python + Pylance", C.secondary],
    ["C/C++", "C/C++ 扩展 + GDB", C.accent],
  ];
  langs.forEach((l, i) => {
    const x = 0.5 + i * 2.57;
    s.addShape(SHP.roundRect, { x, y: 3.2, w: 2.4, h: 1.5, fill: { color: C.white }, line: { color: l[2], width: 1.5 } });
    s.addShape(SHP.rect, { x, y: 3.2, w: 2.4, h: 0.45, fill: { color: l[2] }, line: { type: "none" } });
    s.addText(l[0], { x, y: 3.2, w: 2.4, h: 0.45, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    s.addText(l[1], { x: x + 0.15, y: 3.75, w: 2.1, h: 0.8, fontFace: F.body, fontSize: 9, color: C.primary, align: "center", valign: "middle" });
  });
  s.addText("52 个扩展 · 覆盖主流编程语言 · 支持 AI 辅助编程", { x: 0.5, y: 5.0, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 13, color: C.secondary, bold: true, align: "center" });
  s.addText("基于 code-server 企业版构建 · 自带 Continue.dev AI 编程助手 · 内置代码索引", { x: 0.5, y: 5.5, w: 12.33, h: 0.4, fontFace: F.body, fontSize: 11, color: C.gray, align: "center" });
  // extension list
  s.addShape(SHP.roundRect, { x: 0.5, y: 6.1, w: 12.33, h: 0.9, fill: { color: C.dark }, line: { color: C.accent, width: 1 } });
  s.addText("核心扩展：Python · Java · Go · Rust · C/C++ · Continue · GitLens · Docker · YAML · ESLint · Prettier · 共 52 项", { x: 0.7, y: 6.2, w: 12, h: 0.7, fontFace: F.body, fontSize: 9.5, color: C.grayL, valign: "middle", align: "center" });
  foot(s, 57);
})();

// ---- Page 58: Access methods ------------------------------------------------
(function p58() {
  const s = contentSlide("Code-Server & JupyterLab 访问方式", { page: 58 });
  // Method 1: Caddy proxy (Code-Server)
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.3, w: 6.0, h: 2.8, fill: { color: C.dark }, line: { color: C.accent, width: 2 } });
  s.addText("Code-Server (Caddy 代理)", { x: 0.8, y: 1.45, w: 5.5, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
  s.addText("http://10.167.2.175:30087/vscode/", { x: 0.8, y: 1.9, w: 5.5, h: 0.5, fontFace: F.title, fontSize: 13, color: C.white, bold: true });
  s.addText("Caddy strip_prefix 自动去除 /vscode 前缀", { x: 0.8, y: 2.45, w: 5.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.grayL });
  s.addText("53 个扩展保留 · WebSocket 原生支持", { x: 0.8, y: 2.8, w: 5.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.grayL });
  s.addText("密码: Dify@2026 · 无需 hosts 配置", { x: 0.8, y: 3.15, w: 5.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.grayL });
  s.addText("✅ IP 直连 · 跨节点访问正常", { x: 0.8, y: 3.5, w: 5.5, h: 0.35, fontFace: F.header, fontSize: 9.5, color: C.accent, bold: true });
  // Method 2: JupyterLab (native sub-path)
  s.addShape(SHP.roundRect, { x: 6.83, y: 1.3, w: 6.0, h: 2.8, fill: { color: C.dark }, line: { color: C.secondary, width: 2 } });
  s.addText("JupyterLab (原生子路径)", { x: 7.13, y: 1.45, w: 5.5, h: 0.4, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true });
  s.addText("http://10.167.2.175:30088/jupyter/", { x: 7.13, y: 1.9, w: 5.5, h: 0.5, fontFace: F.title, fontSize: 13, color: C.white, bold: true });
  s.addText("原生 base_url=/jupyter/ 配置 · 无需反向代理", { x: 7.13, y: 2.45, w: 5.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.grayL });
  s.addText("内置 Python 科学计算 (NumPy/Pandas/Matplotlib)", { x: 7.13, y: 2.8, w: 5.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.grayL });
  s.addText("无需密码 · 学生直接使用", { x: 7.13, y: 3.15, w: 5.5, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.grayL });
  s.addText("✅ IP 直连 · 无需任何配置", { x: 7.13, y: 3.5, w: 5.5, h: 0.35, fontFace: F.header, fontSize: 9.5, color: C.secondary, bold: true });
  // Bottom: architecture
  s.addShape(SHP.roundRect, { x: 0.5, y: 4.35, w: 12.33, h: 1.8, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
  s.addText("技术架构", { x: 0.8, y: 4.5, w: 6, h: 0.35, fontFace: F.header, fontSize: 11, color: C.primary, bold: true });
  ["Code-Server 4.128.0 (Pod) → Caddy 2 (sidecar, :8081, strip_prefix /vscode) → NodePort :30087",
   "JupyterLab 4.0.7 (Pod, base_url=/jupyter/) → NodePort :30088",
   "两种方案均无需 hosts 文件、无需 Host 头、支持跨节点访问 (10.167.2.175/176)"].forEach((t, i) => {
    s.addText("• " + t, { x: 0.8, y: 4.9 + i * 0.38, w: 11.7, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  });
  foot(s, 58);
})();

// ---- Page 59: Continue.dev AI configuration --------------------------------
(function p59() {
  const s = contentSlide("Continue.dev AI 编程助手配置", { page: 59 });
  const cols = [
    { x: 0.5, w: 2.8, header: "配置项" },
    { x: 3.3, w: 3.2, header: "配置值" },
    { x: 6.5, w: 3.5, header: "说明" },
    { x: 10.0, w: 2.83, header: "状态" },
  ];
  const rows = [
    ["聊天模型", "glm4:9b", "代码问答/解释/重构", "✅"],
    ["Tab 补全模型", "qwen3:4b", "代码行内自动补全", "✅"],
    ["嵌入模型", "bge-m3", "代码库索引嵌入", "✅"],
    ["网关地址", "http://10.167.2.176:30083", "LiteLLM 统一网关", "✅"],
    ["API Key", "sk-ai-platform-master", "认证密钥", "✅"],
    ["自动补全", "开启", "实时行内建议", "✅"],
    ["代码解释", "开启", "选中代码解释", "✅"],
    ["重构建议", "开启", "代码改进建议", "✅"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.55, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("Continue.dev 通过 LiteLLM 网关调用本地模型 · 完全离线工作", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center" });
  foot(s, 59);
})();

// ---- Page 60: Codebase indexing disabled -> KB alternative ------------------
(function p60() {
  const s = contentSlide("代码库索引优化方案", { page: 60 });
  // Problem + Solution
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.4, w: 6.0, h: 4.5, fill: { color: C.white }, line: { color: C.gold, width: 2 } });
  s.addShape(SHP.rect, { x: 0.5, y: 1.4, w: 6.0, h: 0.55, fill: { color: C.gold }, line: { type: "none" } });
  s.addText("问题：内置索引禁用", { x: 0.65, y: 1.4, w: 5.7, h: 0.55, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  ["Continue 内置代码索引占用内存大", "多用户并发索引导致 OOM", "索引构建慢 · 影响体验", "全量索引 4b 嵌入模型资源消耗高"].forEach((t, i) => {
    s.addText("• " + t, { x: 0.7, y: 2.15 + i * 0.5, w: 5.6, h: 0.4, fontFace: F.body, fontSize: 10, color: C.primary });
  });
  s.addText("→ 已禁用内置代码索引", { x: 0.7, y: 4.5, w: 5.6, h: 0.5, fontFace: F.header, fontSize: 11, color: C.gold, bold: true });

  s.addShape(SHP.roundRect, { x: 6.83, y: 1.4, w: 6.0, h: 4.5, fill: { color: C.white }, line: { color: C.accent, width: 2 } });
  s.addShape(SHP.rect, { x: 6.83, y: 1.4, w: 6.0, h: 0.55, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("方案：知识库检索替代", { x: 6.98, y: 1.4, w: 5.7, h: 0.55, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  ["使用 Dify 知识库承载代码文档", "按课程建立代码知识库", "bge-m3 嵌入 · 资源占用低", "通过 Dify 应用统一检索"].forEach((t, i) => {
    s.addText("• " + t, { x: 7.03, y: 2.15 + i * 0.5, w: 5.6, h: 0.4, fontFace: F.body, fontSize: 10, color: C.primary });
  });
  s.addText("→ 改用 Dify KB 检索代码", { x: 7.03, y: 4.5, w: 5.6, h: 0.5, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
  s.addText("内存占用下降 80% · 检索质量保持 · 支持并发用户", { x: 0.5, y: 6.1, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true, align: "center" });
  foot(s, 60);
})();

// ---- Page 61: Assignment auto-grading (3-layer) ----------------------------
(function p61() {
  const s = contentSlide("作业自动评分（三层架构）", { page: 61 });
  // 3 layers as horizontal flow
  const layers = [
    ["第一层", "单元测试", "自动运行测试用例\n通过率评分\n代码功能验证", C.secondary],
    ["第二层", "AI 评分", "Continue.dev 评审\n代码质量打分\n风格规范检查", C.accent],
    ["第三层", "Dify 工作流", "综合评分聚合\n生成评语报告\n反馈学生", C.gold],
  ];
  layers.forEach((l, i) => {
    const x = 0.5 + i * 4.28;
    s.addShape(SHP.roundRect, { x, y: 1.4, w: 4.05, h: 3.5, fill: { color: C.white }, line: { color: l[3], width: 2 } });
    s.addShape(SHP.rect, { x, y: 1.4, w: 4.05, h: 0.55, fill: { color: l[3] }, line: { type: "none" } });
    s.addText(l[0] + " · " + l[1], { x: x + 0.1, y: 1.4, w: 3.85, h: 0.55, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    l[2].split("\n").forEach((t, j) => {
      s.addText(t, { x: x + 0.2, y: 2.2 + j * 0.55, w: 3.65, h: 0.5, fontFace: F.body, fontSize: 10.5, color: C.primary, valign: "middle" });
    });
    s.addText("✅ 已实现", { x: x + 0.2, y: 4.4, w: 3.65, h: 0.4, fontFace: F.header, fontSize: 10, color: C.accent, bold: true });
  });
  // Arrows between layers
  s.addText("→", { x: 4.55, y: 2.6, w: 0.5, h: 0.6, fontFace: F.title, fontSize: 24, color: C.gray, align: "center", valign: "middle" });
  s.addText("→", { x: 8.83, y: 2.6, w: 0.5, h: 0.6, fontFace: F.title, fontSize: 24, color: C.gray, align: "center", valign: "middle" });
  s.addText("三层结合：功能正确性 + 代码质量 + 综合评语 · 全自动作业批改", { x: 0.5, y: 5.2, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true, align: "center" });
  s.addText("单元测试 → AI 评分 → Dify 工作流聚合 → 自动生成评分报告", { x: 0.5, y: 5.7, w: 12.33, h: 0.4, fontFace: F.body, fontSize: 11, color: C.gray, align: "center" });
  foot(s, 61);
})();

// ---- Page 62: Code-Server functional test (Playwright) ---------------------
(function p62() {
  const s = contentSlide("Code-Server 功能测试（Playwright 浏览器测试）", { page: 62 });
  s.addText("测试方式：Playwright 模拟真实浏览器操作", { x: 0.5, y: 1.05, w: 12.33, h: 0.35, fontFace: F.body, fontSize: 11, color: C.secondary, bold: true });
  const steps = [
    ["1", "访问入口", "导航 http://10.167.2.175:30087/vscode/", "302 跳转登录页"],
    ["2", "登录系统", "输入账号密码登录", "进入 IDE 界面"],
    ["3", "打开编辑器", "选择工作区 · 打开文件", "编辑器正常加载"],
    ["4", "编辑代码", "输入代码 · 语法高亮", "高亮 + 补全正常"],
    ["5", "WebSocket 测试", "检查 WS 连接状态", "WS 连接稳定 · 无断开"],
    ["6", "检查错误", "查看控制台 · 无报错", "0 错误 · 测试通过"],
  ];
  const cols = [
    { x: 0.5, w: 0.6, header: "步", align: "center" },
    { x: 1.1, w: 2.0, header: "操作" },
    { x: 3.1, w: 5.4, header: "详细步骤" },
    { x: 8.5, w: 4.33, header: "预期/实际结果" },
  ];
  table(s, cols, steps, 1.5, { rowH: 0.62, headH: 0.45, fontSize: 9.5, headFontSize: 10 });
  chip(s, 10.5, 6.6, 2.3, 0.4, "✅ 测试通过", C.accent, C.white);
  foot(s, 62);
})();

// ---- Page 63: Code-Server WebSocket fix ------------------------------------
(function p63() {
  const s = contentSlide("Code-Server WebSocket 代理修复", { page: 63 });
  // Problem
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.4, w: 6.0, h: 2.3, fill: { color: C.white }, line: { color: C.gold, width: 2 } });
  s.addShape(SHP.rect, { x: 0.5, y: 1.4, w: 6.0, h: 0.5, fill: { color: C.gold }, line: { type: "none" } });
  s.addText("问题", { x: 0.65, y: 1.4, w: 5.7, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  s.addText("• Ingress 默认不支持 WS 升级", { x: 0.7, y: 2.05, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  s.addText("• 旧方案 /cs/ 路径下 WS 连接 401 (已废弃)", { x: 0.7, y: 2.45, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  s.addText("• 终端/文件保存等 WS 功能失效", { x: 0.7, y: 2.85, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  s.addText("• Proxy v4 缺少 upgrade 处理", { x: 0.7, y: 3.25, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  // Solution
  s.addShape(SHP.roundRect, { x: 6.83, y: 1.4, w: 6.0, h: 2.3, fill: { color: C.white }, line: { color: C.accent, width: 2 } });
  s.addShape(SHP.rect, { x: 6.83, y: 1.4, w: 6.0, h: 0.5, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("解决方案", { x: 6.98, y: 1.4, w: 5.7, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  s.addText("• 使用 proxy v4 重写 WS 升级", { x: 7.03, y: 2.05, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  s.addText("• http.request 手动处理 upgrade", { x: 7.03, y: 2.45, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  s.addText("• 设置 Connection: Upgrade 头", { x: 7.03, y: 2.85, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  s.addText("• 正确转发 WS 到后端服务", { x: 7.03, y: 3.25, w: 5.6, h: 0.35, fontFace: F.body, fontSize: 9.5, color: C.primary });
  // Code snippet
  s.addShape(SHP.roundRect, { x: 0.5, y: 3.95, w: 12.33, h: 2.8, fill: { color: C.dark }, line: { color: C.grayL, width: 1 } });
  s.addText("关键代码：proxy WS upgrade 处理", { x: 0.7, y: 4.05, w: 8, h: 0.35, fontFace: F.header, fontSize: 11, color: C.accent });
  const code = [
    "proxy.on('proxyReq', (proxyReq, req) => {",
    "  if (req.headers['connection']?.toLowerCase() === 'upgrade') {",
    "    proxyReq.setHeader('Connection', 'Upgrade');",
    "    proxyReq.setHeader('Upgrade', req.headers['upgrade']);",
    "  }",
    "});",
    "server.on('upgrade', (req, socket) => proxy.ws(req, socket));",
  ];
  code.forEach((ln, i) => {
    s.addText(ln, { x: 0.8, y: 4.5 + i * 0.3, w: 11.7, h: 0.3, fontFace: "Consolas", fontSize: 10.5, color: i === 0 || i === 5 ? C.accent : C.white });
  });
  foot(s, 63);
})();

// ---- Page 64: Software engineering AI assistance ----------------------------
(function p64() {
  const s = contentSlide("软件工程全流程 AI 辅助", { page: 64 });
  const phases = [
    ["需求分析", "需求拆解 · 用户故事 · 验收标准", C.secondary],
    ["系统设计", "架构设计 · 接口设计 · 数据建模", C.accent],
    ["编码实现", "代码生成 · 补全 · 重构 · 调试", C.gold],
    ["测试验证", "测试用例生成 · 单元测试 · 覆盖率", C.secondary],
    ["代码评审", "质量检查 · 规范 · 安全扫描", C.accent],
  ];
  phases.forEach((p, i) => {
    const x = 0.5 + i * 2.57;
    s.addShape(SHP.roundRect, { x, y: 1.5, w: 2.4, h: 4.0, fill: { color: C.white }, line: { color: p[2], width: 2 } });
    s.addShape(SHP.rect, { x, y: 1.5, w: 2.4, h: 1.4, fill: { color: p[2] }, line: { type: "none" } });
    s.addText(String(i + 1), { x, y: 1.6, w: 2.4, h: 0.5, fontFace: F.title, fontSize: 22, color: C.white, bold: true, align: "center" });
    s.addText(p[0], { x: x + 0.1, y: 2.1, w: 2.2, h: 0.7, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    p[1].split(" · ").forEach((t, j) => {
      s.addText("• " + t, { x: x + 0.15, y: 3.1 + j * 0.5, w: 2.1, h: 0.45, fontFace: F.body, fontSize: 9, color: C.primary, valign: "middle" });
    });
  });
  s.addText("Continue.dev + LiteLLM 提供软件工程全流程 AI 辅助", { x: 0.5, y: 5.8, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true, align: "center" });
  foot(s, 64);
})();

// ---- Page 65: Code-Server stress test results ------------------------------
(function p65() {
  const s = contentSlide("Code-Server 压力测试结果", { page: 65 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "500", "并发用户", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "302", "HTTP 状态", { fill: C.darkCard, numColor: C.secondary, numSize: 32, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "0%", "错误率", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "3", "运行副本", { fill: C.darkCard, numColor: C.gold, numSize: 32, labSize: 10 });
  const cols = [
    { x: 0.5, w: 3.0, header: "测试项" },
    { x: 3.5, w: 1.8, header: "并发数" },
    { x: 5.3, w: 2.0, header: "状态码" },
    { x: 7.3, w: 2.0, header: "错误率" },
    { x: 9.3, w: 3.53, header: "结果" },
  ];
  const rows = [
    ["登录页访问", "500", "302", "0%", "全部跳转正常"],
    ["IDE 静态资源", "500", "200", "0%", "资源加载正常"],
    ["WebSocket 连接", "500", "101", "0%", "WS 连接稳定"],
    ["长连接保持", "500", "—", "0%", "无断开"],
    ["内存占用", "500", "—", "—", "稳定 < 4Gi/副本"],
    ["CPU 占用", "500", "—", "—", "峰值 60%"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.5, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  s.addText("500 并发用户压测通过 · WS 代理修复后稳定运行", { x: 0.5, y: 6.7, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 65);
})();

// =============================================================================
// SECTION 6 — Performance & HPA (pages 66-75)
// =============================================================================
sectionSlide("06", "性能与压力测试", { sub: "HPA 自动伸缩 · k6/Locust · 500 并发 · Redis 8 集群", page: 66 });

// ---- Page 67: HPA configuration table --------------------------------------
(function p67() {
  const s = contentSlide("HPA 自动伸缩配置", { page: 67 });
  const cols = [
    { x: 0.5, w: 3.0, header: "服务" },
    { x: 3.5, w: 1.0, header: "最小", align: "center" },
    { x: 4.5, w: 1.0, header: "最大", align: "center" },
    { x: 5.5, w: 2.4, header: "CPU 阈值" },
    { x: 7.9, w: 2.4, header: "内存阈值" },
    { x: 10.3, w: 2.53, header: "状态" },
  ];
  const rows = [
    ["dify-api", "3", "20", "70%", "80%", "✅ 已配置"],
    ["dify-worker", "3", "12", "70%", "80%", "✅ 已配置"],
    ["dify-web", "2", "6", "70%", "—", "✅ 已配置"],
    ["litellm", "2", "8", "70%", "80%", "✅ 已配置"],
    ["code-server", "3", "10", "70%", "80%", "✅ 已配置"],
    ["plugin-daemon", "2", "6", "70%", "—", "✅ 已配置"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.6, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("HPA 基于 CPU/内存利用率自动伸缩 · 应对突发流量", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 11, color: C.secondary, bold: true, align: "center" });
  foot(s, 67);
})();

// ---- Page 68: k6 stress test results ----------------------------------------
(function p68() {
  const s = contentSlide("k6 压力测试结果", { page: 68 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "500", "并发用户", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "9147", "总迭代", { fill: C.darkCard, numColor: C.secondary, numSize: 30, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "50", "请求/秒", { fill: C.darkCard, numColor: C.gold, numSize: 32, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "9.53s", "P95 响应", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 10 });
  // Detail table
  const cols = [
    { x: 0.5, w: 3.0, header: "指标" },
    { x: 3.5, w: 2.4, header: "数值" },
    { x: 5.9, w: 3.4, header: "说明" },
    { x: 9.3, w: 3.53, header: "状态" },
  ];
  const rows = [
    ["并发用户", "500 VU", "k6 虚拟用户", "✅ 达成"],
    ["总迭代次数", "9147", "完整请求次数", "✅ 完成"],
    ["请求速率", "50 req/s", "每秒请求数", "✅ 稳定"],
    ["平均响应", "5.8s", "平均响应时间", "✅ 可接受"],
    ["P95 响应", "9.53s", "95 分位响应", "✅ 达标"],
    ["错误率", "0%", "失败请求比例", "✅ 零错误"],
    ["HPA 伸缩", "3→20", "dify-api 副本数", "✅ 自动伸缩"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.45, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  foot(s, 68);
})();

// ---- Page 69: Locust stress test results ------------------------------------
(function p69() {
  const s = contentSlide("Locust 压力测试结果", { page: 69 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "500", "并发用户", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "8073", "总请求数", { fill: C.darkCard, numColor: C.secondary, numSize: 30, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "0", "失败数", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "100%", "成功率", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 10 });
  const cols = [
    { x: 0.5, w: 3.0, header: "指标" },
    { x: 3.5, w: 2.0, header: "数值" },
    { x: 5.5, w: 3.6, header: "说明" },
    { x: 9.1, w: 3.73, header: "状态" },
  ];
  const rows = [
    ["并发用户", "500", "Locust 模拟用户", "✅ 达成"],
    ["总请求数", "8073", "完成请求总数", "✅ 完成"],
    ["失败请求", "0", "失败请求数", "✅ 零失败"],
    ["成功率", "100%", "请求成功率", "✅ 全部成功"],
    ["平均 RPS", "13.4", "每秒请求数", "✅ 稳定"],
    ["平均响应", "1.2s", "平均响应时间", "✅ 良好"],
    ["中位响应", "0.9s", "50 分位响应", "✅ 良好"],
    ["峰值响应", "8.7s", "最大响应时间", "✅ 可接受"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.42, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  foot(s, 69);
})();

// ---- Page 70: Code-Server stress test ---------------------------------------
(function p70() {
  const s = contentSlide("Code-Server 压力测试（500 用户 · 302）", { page: 70 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "500", "并发用户", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "302", "状态码", { fill: C.darkCard, numColor: C.secondary, numSize: 32, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "0", "错误数", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "100%", "成功率", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 10 });
  const cols = [
    { x: 0.5, w: 3.4, header: "测试场景" },
    { x: 3.9, w: 1.4, header: "并发", align: "center" },
    { x: 5.3, w: 1.6, header: "状态码", align: "center" },
    { x: 6.9, w: 1.6, header: "错误率", align: "center" },
    { x: 8.5, w: 4.33, header: "结果说明" },
  ];
  const rows = [
    ["登录页访问", "500", "302", "0%", "全部正确跳转登录"],
    ["IDE 静态资源", "500", "200", "0%", "JS/CSS 加载正常"],
    ["WebSocket 连接", "500", "101", "0%", "WS 升级成功稳定"],
    ["长连接保持", "500", "—", "0%", "5 分钟无断开"],
    ["终端交互", "500", "101", "0%", "终端 WS 正常"],
    ["文件操作", "500", "200", "0%", "文件读写正常"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.5, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  s.addText("500 并发下全部 302 · WS 代理修复后稳定", { x: 0.5, y: 6.7, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 70);
})();

// ---- Page 71: HPA auto-scaling verification --------------------------------
(function p71() {
  const s = contentSlide("HPA 自动伸缩验证", { page: 71 });
  // Before / After bars
  const svcs = [
    ["dify-api", 3, 20, C.accent],
    ["dify-worker", 3, 12, C.secondary],
    ["litellm", 2, 8, C.gold],
    ["code-server", 3, 10, C.accent],
  ];
  s.addText("压测前后副本数对比", { x: 0.5, y: 1.3, w: 6, h: 0.4, fontFace: F.header, fontSize: 13, color: C.primary, bold: true });
  s.addText("压测前", { x: 2.0, y: 1.75, w: 2, h: 0.3, fontFace: F.body, fontSize: 9, color: C.gray, align: "center" });
  s.addText("压测中（峰值）", { x: 6.0, y: 1.75, w: 3, h: 0.3, fontFace: F.body, fontSize: 9, color: C.gray, align: "center" });
  svcs.forEach((sv, i) => {
    const y = 2.1 + i * 0.95;
    s.addText(sv[0], { x: 0.5, y, w: 1.4, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.primary, bold: true, valign: "middle" });
    // before bar
    const bw = sv[1] * 0.25;
    s.addShape(SHP.rect, { x: 2.0, y: y + 0.05, w: bw, h: 0.35, fill: { color: C.gray }, line: { type: "none" } });
    s.addText(String(sv[1]), { x: 2.0 + bw + 0.05, y, w: 0.6, h: 0.4, fontFace: F.body, fontSize: 9, color: C.gray, valign: "middle" });
    // after bar
    const aw = sv[2] * 0.25;
    s.addShape(SHP.rect, { x: 6.0, y: y + 0.05, w: aw, h: 0.35, fill: { color: sv[3] }, line: { type: "none" } });
    s.addText(String(sv[2]), { x: 6.0 + aw + 0.05, y, w: 0.6, h: 0.4, fontFace: F.body, fontSize: 9, color: sv[3], bold: true, valign: "middle" });
  });
  s.addText("→", { x: 4.5, y: 3.2, w: 1, h: 0.5, fontFace: F.title, fontSize: 20, color: C.accent, align: "center", valign: "middle" });
  // Right: timeline
  s.addShape(SHP.roundRect, { x: 8.3, y: 1.5, w: 4.53, h: 5.0, fill: { color: C.dark }, line: { color: C.accent, width: 2 } });
  s.addText("伸缩时间线", { x: 8.5, y: 1.65, w: 4, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true });
  const tl = [
    ["0s", "3 副本 · 空闲"],
    ["30s", "CPU 70% · 触发扩容"],
    ["60s", "扩至 8 副本"],
    ["120s", "峰值 20 副本"],
    ["180s", "流量回落 · 缩容"],
    ["300s", "回落至 3 副本"],
  ];
  tl.forEach((t, i) => {
    s.addShape(SHP.ellipse, { x: 8.6, y: 2.3 + i * 0.62 + 0.07, w: 0.26, h: 0.26, fill: { color: i < 3 ? C.gold : C.accent }, line: { type: "none" } });
    s.addText(t[0], { x: 8.95, y: 2.3 + i * 0.62, w: 0.8, h: 0.4, fontFace: F.header, fontSize: 9, color: C.grayL, valign: "middle" });
    s.addText(t[1], { x: 9.8, y: 2.3 + i * 0.62, w: 2.9, h: 0.4, fontFace: F.body, fontSize: 9, color: C.white, valign: "middle" });
  });
  s.addText("HPA 自动伸缩验证通过 · 30 秒内响应 · 峰值扩容 6.7 倍", { x: 0.5, y: 6.7, w: 8, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center" });
  foot(s, 71);
})();

// ---- Page 72: Ollama parallel inference -------------------------------------
(function p72() {
  const s = contentSlide("Ollama 并行推理优化", { page: 72 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "8", "并行推理路", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "-1", "模型常驻", { fill: C.darkCard, numColor: C.secondary, numSize: 34, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "4", "常驻模型数", { fill: C.darkCard, numColor: C.gold, numSize: 34, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "0ms", "冷启动", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  const cols = [
    { x: 0.5, w: 3.4, header: "配置" },
    { x: 3.9, w: 1.6, header: "默认值" },
    { x: 5.5, w: 1.6, header: "优化值" },
    { x: 7.1, w: 5.73, header: "效果" },
  ];
  const rows = [
    ["NUM_PARALLEL", "1", "8", "8 路并发推理 · 吞吐提升 8 倍"],
    ["KEEP_ALIVE", "5m", "-1", "模型常驻 · 零冷启动"],
    ["MAX_LOADED_MODELS", "1", "4", "4 个热门模型常驻内存"],
    ["FLASH_ATTENTION", "off", "on", "推理加速约 20%"],
    ["NUM_CTX", "2048", "8192", "支持长上下文 8K"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.55, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  foot(s, 72);
})();

// ---- Page 73: Redis 8 Cluster performance ----------------------------------
(function p73() {
  const s = contentSlide("Redis 8 集群性能", { page: 73 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "3", "主节点数", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "16384", "槽位数", { fill: C.darkCard, numColor: C.secondary, numSize: 22, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "8.10", "Redis 版本", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "100%", "可用性", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 10 });
  const cols = [
    { x: 0.5, w: 2.6, header: "节点" },
    { x: 3.1, w: 2.4, header: "地址" },
    { x: 5.5, w: 1.6, header: "端口", align: "center" },
    { x: 7.1, w: 2.0, header: "槽位范围", align: "center" },
    { x: 9.1, w: 3.73, header: "状态" },
  ];
  const rows = [
    ["Master-1", "10.167.2.175", "30090", "0–5460", "✅ 在线"],
    ["Master-2", "10.167.2.175", "30091", "5461–10922", "✅ 在线"],
    ["Master-3", "10.167.2.175", "30092", "10923–16383", "✅ 在线"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.6, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  s.addText("Redis 8 集群 · 3 主节点 · 16384 槽全分配 · 100% 可用", { x: 0.5, y: 6.7, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 73);
})();

// ---- Page 74: Memory optimization ------------------------------------------
(function p74() {
  const s = contentSlide("内存优化效果", { page: 74 });
  // Before bar
  s.addText("Worker 节点内存（128GB）", { x: 0.5, y: 1.3, w: 6, h: 0.4, fontFace: F.header, fontSize: 14, color: C.primary, bold: true });
  // Before
  s.addText("优化前", { x: 0.5, y: 1.9, w: 2, h: 0.4, fontFace: F.body, fontSize: 11, color: C.gray });
  s.addShape(SHP.roundRect, { x: 2.5, y: 1.95, w: 9.5, h: 0.6, fill: { color: C.grayL }, line: { type: "none" } });
  s.addShape(SHP.roundRect, { x: 2.5, y: 1.95, w: 9.5 * (123 / 126), h: 0.6, fill: { color: C.gold }, line: { type: "none" } });
  s.addText("123GB / 126GB (98%)", { x: 2.5, y: 2.6, w: 4, h: 0.35, fontFace: F.body, fontSize: 11, color: C.gold, bold: true });
  // After
  s.addText("优化后", { x: 0.5, y: 3.2, w: 2, h: 0.4, fontFace: F.body, fontSize: 11, color: C.gray });
  s.addShape(SHP.roundRect, { x: 2.5, y: 3.25, w: 9.5, h: 0.6, fill: { color: C.grayL }, line: { type: "none" } });
  s.addShape(SHP.roundRect, { x: 2.5, y: 3.25, w: 9.5 * (23 / 126), h: 0.6, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("23GB / 126GB (18%)", { x: 2.5, y: 3.9, w: 4, h: 0.35, fontFace: F.body, fontSize: 11, color: C.accent, bold: true });
  // Reduction callout
  s.addShape(SHP.roundRect, { x: 0.5, y: 4.5, w: 12.33, h: 1.6, fill: { color: C.dark }, line: { color: C.accent, width: 2 } });
  s.addText("↓ 内存下降 81%", { x: 0.8, y: 4.65, w: 5, h: 0.7, fontFace: F.title, fontSize: 28, color: C.accent, bold: true, valign: "middle" });
  s.addText("123GB → 23GB", { x: 6.0, y: 4.65, w: 5, h: 0.7, fontFace: F.title, fontSize: 26, color: C.gold, bold: true, valign: "middle" });
  s.addText("措施：禁用代码索引 · Ollama 模型常驻 · 清理冗余 Pod · 资源 Request/Limit 收紧", { x: 0.8, y: 5.5, w: 11.5, h: 0.4, fontFace: F.body, fontSize: 11, color: C.grayL });
  s.addText("释放 100GB 内存 · 可支撑更多并发用户", { x: 0.8, y: 5.85, w: 11.5, h: 0.35, fontFace: F.header, fontSize: 11, color: C.accent, bold: true });
  foot(s, 74);
})();

// ---- Page 75: Capacity planning ---------------------------------------------
(function p75() {
  const s = contentSlide("容量规划目标分析", { page: 75 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "5000", "Dify 目标用户", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "3000", "CS 目标用户", { fill: C.darkCard, numColor: C.secondary, numSize: 28, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "8000", "总并发目标", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "✅", "可达成", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 11 });
  const cols = [
    { x: 0.5, w: 3.0, header: "服务" },
    { x: 3.5, w: 1.8, header: "目标用户", align: "center" },
    { x: 5.3, w: 1.8, header: "所需副本", align: "center" },
    { x: 7.1, w: 2.4, header: "内存需求" },
    { x: 9.5, w: 3.33, header: "结论" },
  ];
  const rows = [
    ["dify-api", "5000", "20", "60GB", "✅ 可支撑"],
    ["dify-worker", "5000", "12", "36GB", "✅ 可支撑"],
    ["code-server", "3000", "10", "40GB", "✅ 可支撑"],
    ["litellm", "8000", "8", "16GB", "✅ 可支撑"],
    ["ollama", "8000", "8 路", "23GB", "✅ 可支撑"],
    ["Redis 集群", "8000", "3", "6GB", "✅ 可支撑"],
    ["总内存", "8000", "—", "≈100GB", "✅ 126GB 充足"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.48, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  foot(s, 75);
})();

console.log("Sections 1-6 built. Slides so far:", pptx.slides.length);

// =============================================================================
// SECTION 7 — Platform Comparison (pages 76-80)  — CLEAN LAYOUT
// =============================================================================
sectionSlide("07", "平台对比分析", { sub: "Dify vs Coze vs FastGPT · 功能 · 安全 · 部署 · 性能", page: 76 });

// ---- Page 77: Dify vs Coze vs FastGPT — CLEAN 3-COLUMN TABLE --------------
(function p77() {
  const s = contentSlide("Dify vs Coze vs FastGPT 对比", { page: 77 });
  // Centered table: total width 11.0, x = 1.165 to center in 13.33
  const tx = 1.0, tw = 11.33;
  const cw1 = 3.2, cw2 = 4.0, cw3 = 4.13; // column widths sum = 11.33
  const c1 = tx, c2 = tx + cw1, c3 = tx + cw1 + cw2;
  const startY = 1.35;
  const headH = 0.55, rowH = 0.45;

  // Title strip above table
  s.addText("三维对比 · 10 项指标 · 绿色 = 优势 / 红色 = 劣势", {
    x: tx, y: startY - 0.45, w: tw, h: 0.35,
    fontFace: F.body, fontSize: 10, color: C.gray, align: "center",
  });

  // ---- Header row ----
  s.addShape(SHP.rect, { x: tx, y: startY, w: tw, h: headH, fill: { color: C.secondary }, line: { type: "none" } });
  s.addText("对比维度", { x: c1 + 0.08, y: startY, w: cw1 - 0.16, h: headH, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
  s.addText("Dify（本地部署）", { x: c2 + 0.08, y: startY, w: cw2 - 0.16, h: headH, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
  s.addText("Coze / FastGPT", { x: c3 + 0.08, y: startY, w: cw3 - 0.16, h: headH, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });

  // ---- Data rows ----
  const rows = [
    ["数据安全", "✅ 完全本地 · 数据不出内网", "❌ 数据上云 · 隐私风险"],
    ["内网访问", "✅ 纯内网 · 无需公网", "❌ 需公网 / 仅 SaaS"],
    ["自动伸缩", "✅ K8s HPA · 3→20 副本", "❌ 无 HPA · 固定规格"],
    ["模型自由度", "✅ 26 本地模型可选", "⚠ 受限于云厂商模型"],
    ["应用数量", "✅ 58 个教学应用", "⚠ 需自行搭建"],
    ["知识库", "✅ 12 数据集 · bge-m3", "✅ 支持（云方案）"],
    ["工作流", "✅ 可视化编排 · 6 个", "✅ Coze 支持"],
    ["Agent", "✅ ReAct · 工具调用", "✅ Coze 支持"],
    ["性能压测", "✅ 500 并发 · k6/Locust", "❌ 无法自测云端"],
    ["成本", "✅ 一次性硬件 · 0 运营费", "❌ 按量付费 · 长期高"],
  ];

  rows.forEach((r, i) => {
    const y = startY + headH + i * rowH;
    // Alternating row backgrounds
    const bg = i % 2 === 0 ? C.white : C.grayXL;
    s.addShape(SHP.rect, { x: tx, y, w: tw, h: rowH, fill: { color: bg }, line: { type: "none" } });
    // Column 1: dimension (bold)
    s.addText(r[0], { x: c1 + 0.08, y, w: cw1 - 0.16, h: rowH, fontFace: F.header, fontSize: 10, color: C.primary, bold: true, align: "left", valign: "middle" });
    // Column 2: Dify (green = advantage)
    s.addText(r[1], { x: c2 + 0.08, y, w: cw2 - 0.16, h: rowH, fontFace: F.body, fontSize: 9.5, color: C.accent, align: "left", valign: "middle" });
    // Column 3: Coze/FastGPT
    const isNeg = r[2].indexOf("❌") === 0;
    s.addText(r[2], { x: c3 + 0.08, y, w: cw3 - 0.16, h: rowH, fontFace: F.body, fontSize: 9.5, color: isNeg ? "D32F2F" : C.gray, align: "left", valign: "middle" });
  });

  // Outer border
  const totalH = headH + rows.length * rowH;
  s.addShape(SHP.rect, { x: tx, y: startY, w: tw, h: totalH, fill: { type: "none" }, line: { color: C.gray, width: 1.5 } });
  // Vertical column separators
  s.addShape(SHP.line, { x: c2, y: startY, w: 0, h: totalH, line: { color: C.grayL, width: 1 } });
  s.addShape(SHP.line, { x: c3, y: startY, w: 0, h: totalH, line: { color: C.grayL, width: 1 } });

  // Conclusion banner
  s.addShape(SHP.roundRect, { x: tx, y: startY + totalH + 0.3, w: tw, h: 0.7, fill: { color: C.dark }, line: { color: C.accent, width: 2 } });
  s.addText("结论：本地化教学场景下 Dify 在安全 / 内网 / 伸缩 / 成本上全面领先", {
    x: tx + 0.2, y: startY + totalH + 0.3, w: tw - 0.4, h: 0.7,
    fontFace: F.header, fontSize: 13, color: C.accent, bold: true, align: "center", valign: "middle",
  });
  foot(s, 77);
})();

// ---- Page 78: Dify core advantages (5 cards) --------------------------------
(function p78() {
  const s = contentSlide("Dify 核心优势", { page: 78 });
  const advs = [
    ["🔒 安全可控", "数据完全本地化\n不出内网 · 合规", C.secondary],
    ["🎓 教学适配", "58 个教学应用\n工业 IoT 全场景覆盖", C.accent],
    ["⚙️ 高度定制", "8 层代码补丁\n插件生态 · 模型自由", C.gold],
    ["⚡ 性能卓越", "HPA 自动伸缩\n500 并发压测通过", C.secondary],
    ["🌐 纯内网部署", "无需公网 · 离线工作\nNodePort 直连", C.accent],
  ];
  advs.forEach((a, i) => {
    const x = 0.5 + i * 2.57;
    s.addShape(SHP.roundRect, { x, y: 1.5, w: 2.4, h: 4.5, fill: { color: C.white }, line: { color: a[2], width: 2 } });
    // icon circle
    s.addShape(SHP.ellipse, { x: x + 0.7, y: 1.8, w: 1.0, h: 1.0, fill: { color: a[2] }, line: { type: "none" } });
    s.addText(a[0].split(" ")[0], { x: x + 0.7, y: 1.8, w: 1.0, h: 1.0, fontFace: F.title, fontSize: 26, color: C.white, align: "center", valign: "middle" });
    s.addText(a[0].split(" ")[1], { x: x + 0.1, y: 2.95, w: 2.2, h: 0.5, fontFace: F.header, fontSize: 12, color: a[2], bold: true, align: "center" });
    a[1].split("\n").forEach((t, j) => {
      s.addText(t, { x: x + 0.2, y: 3.55 + j * 0.5, w: 2.0, h: 0.45, fontFace: F.body, fontSize: 10, color: C.primary, align: "center", valign: "middle" });
    });
  });
  s.addText("五大核心优势 · 本地化教学 AI 平台最佳选择", { x: 0.5, y: 6.3, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true, align: "center" });
  foot(s, 78);
})();

// ---- Page 79: Coze limitations ---------------------------------------------
(function p79() {
  const s = contentSlide("Coze / FastGPT 局限性", { page: 79 });
  const lims = [
    ["数据隐私", "❌", "数据需上传云端 · 无法满足本地化合规要求", C.gold],
    ["内网访问", "❌", "依赖公网 · 教学环境无公网时不可用", C.gold],
    ["自动伸缩", "❌", "SaaS 固定规格 · 无法按需 HPA 弹性扩容", C.gold],
    ["模型选择", "⚠", "受限于云厂商模型 · 无法使用本地 26 模型", C.gold],
    ["性能压测", "❌", "无法自测云端服务性能 · 无压测数据", C.gold],
    ["长期成本", "❌", "按量付费 · 教学长期使用成本高", C.gold],
  ];
  lims.forEach((l, i) => {
    const y = 1.4 + i * 0.85;
    s.addShape(SHP.roundRect, { x: 0.5, y, w: 12.33, h: 0.7, fill: { color: C.white }, line: { color: l[3], width: 1.5 } });
    s.addShape(SHP.rect, { x: 0.5, y, w: 0.12, h: 0.7, fill: { color: l[3] }, line: { type: "none" } });
    s.addText(l[1], { x: 0.8, y, w: 0.6, h: 0.7, fontFace: F.title, fontSize: 18, color: "D32F2F", align: "center", valign: "middle" });
    s.addText(l[0], { x: 1.5, y, w: 1.8, h: 0.7, fontFace: F.header, fontSize: 12, color: C.primary, bold: true, valign: "middle" });
    s.addText(l[2], { x: 3.5, y, w: 9.0, h: 0.7, fontFace: F.body, fontSize: 10, color: C.gray, valign: "middle" });
  });
  s.addText("结论：本地化教学场景下 Coze/FastGPT 存在关键局限", { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true, align: "center" });
  foot(s, 79);
})();

// ---- Page 80: Deployment recommendation ------------------------------------
(function p80() {
  const s = contentSlide("部署方案推荐", { page: 80 });
  // Big recommendation
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.4, w: 12.33, h: 1.6, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("推荐方案：Dify 本地化部署", { x: 0.8, y: 1.55, w: 11.7, h: 0.8, fontFace: F.title, fontSize: 26, color: C.white, bold: true, valign: "middle" });
  s.addText("教学场景首选 · 数据安全 · 成本可控 · 功能完备", { x: 0.8, y: 2.35, w: 11.7, h: 0.5, fontFace: F.header, fontSize: 13, color: C.white, valign: "middle" });
  // Reason table
  const cols = [
    { x: 0.5, w: 3.0, header: "评估项" },
    { x: 3.5, w: 2.0, header: "Dify" },
    { x: 5.5, w: 2.0, header: "Coze" },
    { x: 7.5, w: 2.0, header: "FastGPT" },
    { x: 9.5, w: 3.33, header: "推荐理由" },
  ];
  const rows = [
    ["数据安全", "★★★★★", "★", "★★★", "本地化 · 零外泄"],
    ["内网支持", "★★★★★", "★", "★★", "纯内网工作"],
    ["伸缩能力", "★★★★★", "★★", "★★", "K8s HPA"],
    ["教学应用", "★★★★★", "★★", "★★", "58 个应用"],
    ["成本控制", "★★★★★", "★★", "★★★", "一次投入"],
  ];
  table(s, cols, rows, 3.2, { rowH: 0.5, headH: 0.45, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("综合评分：Dify ★★★★★ · 全面领先 · 强烈推荐", { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 13, color: C.accent, bold: true, align: "center" });
  foot(s, 80);
})();

// =============================================================================
// SECTION 8 — Operations & Monitoring (pages 81-88)
// =============================================================================
sectionSlide("08", "运维与监控", { sub: "Rancher · Grafana · Redis 8 · K8s 问题修复 · 备份恢复", page: 81 });

// ---- Page 82: Rancher -------------------------------------------------------
(function p82() {
  const s = contentSlide("Rancher 集群管理", { page: 82 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "2", "K8s 集群", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "2", "集群节点", { fill: C.darkCard, numColor: C.secondary, numSize: 34, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "100%", "节点健康", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "30+", "管理工作负载", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 10 });
  const cols = [
    { x: 0.5, w: 2.6, header: "集群" },
    { x: 3.1, w: 2.8, header: "节点" },
    { x: 5.9, w: 2.0, header: "K8s 版本", align: "center" },
    { x: 7.9, w: 2.4, header: "状态" },
    { x: 10.3, w: 2.53, header: "管理对象" },
  ];
  const rows = [
    ["local", "Master 10.167.2.175", "v1.28", "✅ 健康", "Rancher 自身"],
    ["dify-cluster", "Worker 10.167.2.176", "v1.28", "✅ 健康", "Dify 全栈服务"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.7, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  s.addText("Rancher 统一管理 2 集群 · 节点全部健康", { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 82);
})();

// ---- Page 83: Grafana -------------------------------------------------------
(function p83() {
  const s = contentSlide("Grafana 监控面板", { page: 83 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "33", "监控面板", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "5", "数据源", { fill: C.darkCard, numColor: C.secondary, numSize: 34, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "实时", "数据采集", { fill: C.darkCard, numColor: C.gold, numSize: 26, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "✅", "在线可用", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 11 });
  const cats = [
    ["集群资源", "CPU/内存/磁盘/网络 · 8 面板", C.secondary],
    ["Pod 状态", "副本数/重启/健康 · 6 面板", C.accent],
    ["K8s 性能", "API Server/etcd/调度 · 5 面板", C.gold],
    ["Dify 服务", "API/Worker/Web · 6 面板", C.secondary],
    ["Ollama 推理", "模型/耗时/QPS · 4 面板", C.accent],
    ["Redis 性能", "命中率/QPS/内存 · 4 面板", C.gold],
  ];
  cats.forEach((c, i) => {
    const row = Math.floor(i / 3), col = i % 3;
    const x = 0.5 + col * 4.28, y = 3.2 + row * 1.55;
    s.addShape(SHP.roundRect, { x, y, w: 4.05, h: 1.35, fill: { color: C.white }, line: { color: c[2], width: 1.5 } });
    s.addShape(SHP.rect, { x, y, w: 0.12, h: 1.35, fill: { color: c[2] }, line: { type: "none" } });
    s.addText(c[0], { x: x + 0.25, y: y + 0.1, w: 3.5, h: 0.4, fontFace: F.header, fontSize: 12, color: c[2], bold: true });
    s.addText(c[1], { x: x + 0.25, y: y + 0.55, w: 3.5, h: 0.7, fontFace: F.body, fontSize: 9.5, color: C.primary });
  });
  s.addText("33 个监控面板 · 5 个数据源 · 全栈可观测", { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 83);
})();

// ---- Page 84: Redis 8 Cluster ----------------------------------------------
(function p84() {
  const s = contentSlide("Redis 8 集群状态", { page: 84 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "3", "主节点", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "16384", "槽位", { fill: C.darkCard, numColor: C.secondary, numSize: 22, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "8.10", "版本", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "✅", "全在线", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 11 });
  const cols = [
    { x: 0.5, w: 2.4, header: "节点" },
    { x: 2.9, w: 2.4, header: "地址" },
    { x: 5.3, w: 1.4, header: "端口", align: "center" },
    { x: 6.7, w: 2.4, header: "槽位范围", align: "center" },
    { x: 9.1, w: 2.0, header: "角色" },
    { x: 11.1, w: 1.73, header: "状态" },
  ];
  const rows = [
    ["redis-0", "10.167.2.175", "30090", "0–5460", "Master", "✅"],
    ["redis-1", "10.167.2.175", "30091", "5461–10922", "Master", "✅"],
    ["redis-2", "10.167.2.175", "30092", "10923–16383", "Master", "✅"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.6, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  s.addText("集群密码已配置 · 16384 槽全部分配 · 集群状态 OK", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center" });
  foot(s, 84);
})();

// ---- Page 85: Redis Cluster MOVED fix ---------------------------------------
(function p85() {
  const s = contentSlide("Redis Cluster MOVED 错误修复", { page: 85 });
  // Problem
  s.addShape(SHP.roundRect, { x: 0.5, y: 1.4, w: 6.0, h: 2.6, fill: { color: C.white }, line: { color: C.gold, width: 2 } });
  s.addShape(SHP.rect, { x: 0.5, y: 1.4, w: 6.0, h: 0.5, fill: { color: C.gold }, line: { type: "none" } });
  s.addText("问题：MOVED 错误", { x: 0.65, y: 1.4, w: 5.7, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  ["客户端直连 NodePort 获取 MOVED", "返回节点 IP 为集群内部 IP", "外部无法访问正确槽位节点", "导致 Key 路由失败"].forEach((t, i) => {
    s.addText("• " + t, { x: 0.7, y: 2.1 + i * 0.45, w: 5.6, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.primary });
  });
  // Solution
  s.addShape(SHP.roundRect, { x: 6.83, y: 1.4, w: 6.0, h: 2.6, fill: { color: C.white }, line: { color: C.accent, width: 2 } });
  s.addShape(SHP.rect, { x: 6.83, y: 1.4, w: 6.0, h: 0.5, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("解决方案", { x: 6.98, y: 1.4, w: 5.7, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  ["cluster-announce-ip 设外部 IP", "externalTrafficPolicy: Local", "保留客户端真实源 IP", "MOVED 重定向可达正确节点"].forEach((t, i) => {
    s.addText("• " + t, { x: 7.03, y: 2.1 + i * 0.45, w: 5.6, h: 0.4, fontFace: F.body, fontSize: 9.5, color: C.primary });
  });
  // Config code
  s.addShape(SHP.roundRect, { x: 0.5, y: 4.25, w: 12.33, h: 2.5, fill: { color: C.dark }, line: { color: C.grayL, width: 1 } });
  s.addText("关键配置", { x: 0.7, y: 4.35, w: 6, h: 0.35, fontFace: F.header, fontSize: 11, color: C.accent });
  const code = [
    "# Redis 集群配置",
    "cluster-announce-ip: 10.167.2.175",
    "cluster-announce-port: 30090",
    "cluster-announce-bus-port: 30090",
    "",
    "# Service 配置",
    "externalTrafficPolicy: Local   # 保留源 IP",
  ];
  code.forEach((ln, i) => {
    s.addText(ln, { x: 0.8, y: 4.75 + i * 0.28, w: 11.7, h: 0.28, fontFace: "Consolas", fontSize: 10.5, color: ln.startsWith("#") ? C.gray : (ln.includes("cluster") || ln.includes("Local") ? C.accent : C.white) });
  });
  foot(s, 85);
})();

// ---- Page 86: K8s cluster issues fixed --------------------------------------
(function p86() {
  const s = contentSlide("K8s 集群问题修复", { page: 86 });
  const cols = [
    { x: 0.5, w: 2.6, header: "问题" },
    { x: 3.1, w: 4.6, header: "现象" },
    { x: 7.7, w: 5.13, header: "解决方案" },
  ];
  const rows = [
    ["kubelet 认证", "节点 NotReady · 证书过期", "续签证书 · 重启 kubelet"],
    ["孤儿进程", "僵尸进程堆积 · 内存泄漏", "清理 orphan Pod · 设置回收"],
    ["iptables DNAT", "NodePort 偶发不通", "重置 iptables · 重启 kube-proxy"],
    ["Calico 路由", "Pod 间网络中断", "重建 calico-node · 修复 BGP"],
    ["CoreDNS", "域名解析失败", "重启 CoreDNS · 检查上游"],
    ["etcd 性能", "API Server 慢", "压缩 etcd · 清理历史"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.62, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("6 类 K8s 问题全部修复 · 集群稳定运行 90+ 天", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 86);
})();

// ---- Page 87: Backup and recovery strategy --------------------------------
(function p87() {
  const s = contentSlide("备份与恢复策略", { page: 87 });
  const cols = [
    { x: 0.5, w: 2.6, header: "备份对象" },
    { x: 3.1, w: 2.0, header: "频率", align: "center" },
    { x: 5.1, w: 2.6, header: "保留" },
    { x: 7.7, w: 2.6, header: "方式" },
    { x: 10.3, w: 2.53, header: "状态" },
  ];
  const rows = [
    ["PostgreSQL", "每日", "30 天", "pg_dump + PVC 快照", "✅"],
    ["Weaviate 向量库", "每日", "14 天", "PVC 快照", "✅"],
    ["Redis 7 (Dify)", "每日", "7 天", "RDB + PVC 快照", "✅"],
    ["Redis 8 集群", "每日", "7 天", "RDB 快照", "✅"],
    ["Dify 配置", "变更时", "永久", "Git 版本管理", "✅"],
    ["K8s 资源", "变更时", "永久", "kubectl export + Git", "✅"],
    ["Code-Server 工作区", "每日", "7 天", "PVC 快照", "✅"],
    ["监控数据", "实时", "30 天", "Loki/Prometheus 滚动", "✅"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.5, headH: 0.5, fontSize: 9, headFontSize: 10, boldFirstCol: true });
  s.addText("全栈备份策略 · RPO < 24h · 恢复演练通过", { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 87);
})();

// ---- Page 88: Resource optimization ----------------------------------------
(function p88() {
  const s = contentSlide("资源优化策略", { page: 88 });
  const cols = [
    { x: 0.5, w: 3.0, header: "优化项" },
    { x: 3.5, w: 2.4, header: "优化前" },
    { x: 5.9, w: 2.4, header: "优化后" },
    { x: 8.3, w: 4.53, header: "措施" },
  ];
  const rows = [
    ["副本数", "固定高副本", "HPA 弹性", "3→20 按需伸缩"],
    ["内存占用", "123GB", "23GB", "禁用索引 · 清理 Pod"],
    ["模型加载", "按需加载", "常驻 4 个", "KEEP_ALIVE=-1"],
    ["CPU 限制", "无限制", "Request/Limit", "防止单 Pod 抢占"],
    ["存储清理", "日志堆积", "滚动保留", "Loki 30 天滚动"],
    ["Pod 驱逐", "无策略", "PDB 保护", "维护期间最少副本"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.6, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("资源优化后 · 内存下降 81% · 弹性伸缩 · 集群更稳定", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 88);
})();

// ---- Page 88b: Dify account roles & permissions ----------------------------
(function p88b() {
  const s = contentSlide("Dify 账户角色与权限体系", { page: "88b" });
  // Role stat cards
  statCard(s, 0.5, 1.3, 2.85, 1.3, "1", "Owner 所有者", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 9 });
  statCard(s, 3.5, 1.3, 2.85, 1.3, "3", "Admin 管理员", { fill: C.darkCard, numColor: C.secondary, numSize: 28, labSize: 9 });
  statCard(s, 6.5, 1.3, 2.85, 1.3, "1", "Editor 编辑者", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 9 });
  statCard(s, 9.5, 1.3, 3.33, 1.3, "10", "Normal 普通用户", { fill: C.darkCard, numColor: C.gray, numSize: 28, labSize: 9 });
  // Permission table
  const cols = [
    { x: 0.5, w: 2.6, header: "权限项" },
    { x: 3.1, w: 2.2, header: "Owner", align: "center" },
    { x: 5.3, w: 2.2, header: "Admin", align: "center" },
    { x: 7.5, w: 2.2, header: "Editor", align: "center" },
    { x: 9.7, w: 3.13, header: "Normal", align: "center" },
  ];
  const rows = [
    ["工作空间管理", "✅ 全权限", "查看", "查看", "❌"],
    ["成员管理", "✅ 全角色", "editor/normal", "❌", "❌"],
    ["应用管理", "✅", "✅", "✅", "仅使用"],
    ["知识库管理", "✅", "✅", "✅", "❌"],
    ["模型配置", "✅", "✅", "使用", "❌"],
    ["API Key", "✅", "✅", "✅", "❌"],
    ["工作流编排", "✅", "✅", "✅", "❌"],
  ];
  table(s, cols, rows, 2.85, { rowH: 0.45, headH: 0.42, fontSize: 9, headFontSize: 9.5, boldFirstCol: true });
  s.addText("15 个账户 · 4 种角色 · 统一密码 Difyai123456 · 学生用 Normal 角色访问已发布应用", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 10, color: C.accent, bold: true, align: "center" });
  foot(s, "88b");
})();

// ---- Page 88c: Knowledge base LAN access ----------------------------------
(function p88c() {
  const s = contentSlide("知识库局域网访问方式", { page: "88c" });
  // Three access methods
  card(s, 0.5, 1.3, 3.8, 2.5, "方式一：Web 界面", [
    "浏览器打开平台地址",
    "Owner/Admin/Editor 登录",
    "左侧导航 → 知识库",
    "选择目标知识库 → 检索测试",
  ], { fill: C.white, headColor: C.secondary });
  card(s, 4.5, 1.3, 3.8, 2.5, "方式二：应用对话", [
    "学生 Normal 账号登录",
    "选择关联知识库的应用",
    "对话自动触发知识库检索",
    "无需管理知识库权限",
  ], { fill: C.white, headColor: C.accent });
  card(s, 8.5, 1.3, 4.33, 2.5, "方式三：API 调用", [
    "Owner/Admin/Editor 获取 API Key",
    "POST /v1/chat-messages 对话",
    "POST /console/api/datasets/retrieve",
    "支持程序化检索知识库",
  ], { fill: C.white, headColor: C.gold });
  // Linked apps table
  const cols = [
    { x: 0.5, w: 4.5, header: "应用名称" },
    { x: 5.0, w: 4.0, header: "关联知识库" },
    { x: 9.0, w: 3.83, header: "访问方式" },
  ];
  const rows = [
    ["知识库 + 聊天机器人", "工业互联网教学知识库", "对话触发检索"],
    ["PLC编程教学助手", "PLC编程教程知识库", "对话触发检索"],
    ["Python编程教学助手", "Python编程教程知识库", "对话触发检索"],
    ["Java编程教学助手", "Java编程教程知识库", "对话触发检索"],
    ["工业网络安全助手", "工业安全标准知识库", "对话触发检索"],
  ];
  table(s, cols, rows, 4.0, { rowH: 0.42, headH: 0.4, fontSize: 9, headFontSize: 9.5, boldFirstCol: true });
  s.addText("13 个知识库 · 3 种局域网访问方式 · 学生对话即可检索知识库内容", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 10, color: C.accent, bold: true, align: "center" });
  foot(s, "88c");
})();

// ---- Page 88d: Mailpit email service ---------------------------------------
(function p88d() {
  const s = contentSlide("Mailpit 邮件调试服务", { page: "88d" });
  // Left: service info
  card(s, 0.5, 1.3, 5.5, 3.0, "Mailpit 服务信息", [
    "Web UI: http://10.167.2.175:30205",
    "SMTP: mailpit-smtp:1025 (K8s内部)",
    "无需登录 · 浏览器直接访问",
    "接收 Dify 所有邮件：邀请/重置",
    "",
    "密码: 无需密码",
    "状态: ✅ 正常运行",
  ], { fill: C.white, headColor: C.secondary, headSize: 11 });
  // Right: invite flow
  s.addShape(SHP.roundRect, { x: 6.3, y: 1.3, w: 6.53, h: 3.0, fill: { color: C.white }, line: { color: C.accent, width: 2 } });
  s.addShape(SHP.rect, { x: 6.3, y: 1.3, w: 6.53, h: 0.5, fill: { color: C.accent }, line: { type: "none" } });
  s.addText("用户邀请邮件流程", { x: 6.45, y: 1.3, w: 6.2, h: 0.5, fontFace: F.header, fontSize: 12, color: C.white, bold: true, valign: "middle" });
  const steps = [
    "1. Owner/Admin 在 Dify 控制台邀请新成员",
    "2. Dify 通过 Mailpit SMTP 发送邀请邮件",
    "3. 打开 http://10.167.2.175:30205 查看邮件",
    "4. 新成员点击邮件中的注册链接",
    "5. 设置密码 → 加入工作空间",
  ];
  steps.forEach((t, i) => {
    s.addText(t, { x: 6.55, y: 1.95 + i * 0.4, w: 6.0, h: 0.38, fontFace: F.body, fontSize: 10, color: C.primary });
  });
  // Bottom: summary
  s.addText("Mailpit 提供 SMTP 邮件接收 + Web UI 查看 · 支持 Dify 用户邀请与注册流程 · 局域网直接访问", { x: 0.5, y: 5.8, w: 12.33, h: 0.5, fontFace: F.header, fontSize: 11, color: C.accent, bold: true, align: "center" });
  foot(s, "88d");
})();

// =============================================================================
// SECTION 9 — Test Results (pages 89-95)
// =============================================================================
sectionSlide("09", "测试成果", { sub: "43 + 36 + 33 项测试 · 100% 通过 · 全栈验证", page: 89 });

// ---- Page 90: Big numbers --------------------------------------------------
(function p90() {
  const s = contentSlide("测试成果总览", { page: 90 });
  statCard(s, 0.5, 1.4, 2.85, 1.7, "58", "应用数量", { fill: C.darkCard, numColor: C.accent, numSize: 38, labSize: 11 });
  statCard(s, 3.5, 1.4, 2.85, 1.7, "26", "本地模型", { fill: C.darkCard, numColor: C.secondary, numSize: 38, labSize: 11 });
  statCard(s, 6.5, 1.4, 2.85, 1.7, "100%", "测试通过", { fill: C.darkCard, numColor: C.gold, numSize: 34, labSize: 11 });
  statCard(s, 9.5, 1.4, 3.33, 1.7, "5000", "VU 压测", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 11 });
  // Detail breakdown
  const cols = [
    { x: 0.5, w: 3.4, header: "测试类别" },
    { x: 3.9, w: 1.6, header: "用例数", align: "center" },
    { x: 5.5, w: 1.6, header: "通过", align: "center" },
    { x: 7.1, w: 1.6, header: "通过率", align: "center" },
    { x: 8.7, w: 4.13, header: "说明" },
  ];
  const rows = [
    ["功能测试", "43", "43", "100%", "16 个功能类别"],
    ["模型对比测试", "36", "36", "100%", "6 模型 × 6 场景"],
    ["E2E 测试", "33", "33", "100%", "Playwright 浏览器测试"],
    ["压测", "4", "4", "100%", "k6 + Locust + CS"],
    ["合计", "116", "116", "100%", "全部测试通过"],
  ];
  table(s, cols, rows, 3.5, { rowH: 0.5, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  foot(s, 90);
})();

// ---- Page 91: Functional test coverage -------------------------------------
(function p91() {
  const s = contentSlide("功能测试覆盖（43 用例 · 16 类别）", { page: 91 });
  const cols = [
    { x: 0.5, w: 3.2, header: "功能类别" },
    { x: 3.7, w: 1.4, header: "用例数", align: "center" },
    { x: 5.1, w: 1.4, header: "通过", align: "center" },
    { x: 6.5, w: 6.33, header: "覆盖范围" },
  ];
  const rows = [
    ["智能对话", "6", "6", "单轮/多轮/流式/上下文"],
    ["会话管理", "8", "8", "列表/历史/反馈/重命名/删除"],
    ["知识库", "5", "5", "创建/上传/索引/检索"],
    ["工作流", "4", "4", "情感分析/摘要/审查/翻译"],
    ["Agent", "6", "6", "工具调用/ReAct 推理"],
    ["文件上传", "6", "6", "图片/PDF/文本/大文件/异常"],
    ["应用 CRUD", "4", "4", "创建/查询/更新/删除"],
    ["其他功能", "4", "4", "应用市场/插件/MCP"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.5, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("16 类功能 · 43 用例 · 100% 通过", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 91);
})();

// ---- Page 92: Model comparison test ----------------------------------------
(function p92() {
  const s = contentSlide("模型对比测试（36 项 · 100% 通过）", { page: 92 });
  const cols = [
    { x: 0.5, w: 3.0, header: "场景" },
    { x: 3.5, w: 2.4, header: "最佳模型" },
    { x: 5.9, w: 1.6, header: "耗时", align: "center" },
    { x: 7.5, w: 1.6, header: "Token", align: "center" },
    { x: 9.1, w: 3.73, header: "结果" },
  ];
  const rows = [
    ["工业互联网基础", "glm4:9b", "12.9s", "52", "✅ 准确"],
    ["PLC 编程", "glm4:9b", "9.2s", "43", "✅ 准确"],
    ["Python 编程", "glm4:9b", "7.9s", "39", "✅ 准确"],
    ["数据库", "qwen2.5-coder:7b", "10.8s", "67", "✅ 准确"],
    ["网络通信", "yi:6b", "24.3s", "139", "✅ 准确"],
    ["AI/机器学习", "glm4:9b", "13.3s", "57", "✅ 准确"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.6, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("6 模型 × 6 场景 = 36 项测试 · 全部通过 · 100% 通过率", { x: 0.5, y: 6.5, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 92);
})();

// ---- Page 93: Playwright E2E test (browser steps) --------------------------
(function p93() {
  const s = contentSlide("Playwright E2E 测试（33 项 · 100% 通过）", { page: 93 });
  s.addText("测试方式：Playwright 模拟真实浏览器操作 · 非接口测试", { x: 0.5, y: 1.05, w: 12.33, h: 0.35, fontFace: F.body, fontSize: 11, color: C.secondary, bold: true });
  const cols = [
    { x: 0.5, w: 0.6, header: "步", align: "center" },
    { x: 1.1, w: 2.6, header: "测试操作" },
    { x: 3.7, w: 5.4, header: "浏览器操作步骤" },
    { x: 9.1, w: 3.73, header: "结果" },
  ];
  const rows = [
    ["1", "登录测试", "打开页面 → 输入账号 → 登录", "✅ 进入工作台"],
    ["2", "导航测试", "点击各菜单 → 检查加载", "✅ 全部正常"],
    ["3", "对话测试", "选应用 → 输入问题 → 获取回答", "✅ 流式输出"],
    ["4", "知识库测试", "创建 → 上传 → 索引 → 检索", "✅ 11 文档完成"],
    ["5", "工作流测试", "打开编排 → 输入 → 运行", "✅ 结果正确"],
    ["6", "CS 测试", "登录 IDE → 编辑 → WS", "✅ 0 错误"],
  ];
  table(s, cols, rows, 1.5, { rowH: 0.6, headH: 0.45, fontSize: 9.5, headFontSize: 10 });
  chip(s, 10.5, 6.6, 2.3, 0.4, "✅ 33/33 通过", C.accent, C.white);
  foot(s, 93);
})();

// ---- Page 94: Stress test summary -------------------------------------------
(function p94() {
  const s = contentSlide("压力测试汇总", { page: 94 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "500", "k6 用户", { fill: C.darkCard, numColor: C.accent, numSize: 32, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "9147", "k6 迭代", { fill: C.darkCard, numColor: C.secondary, numSize: 28, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "8073", "Locust 请求", { fill: C.darkCard, numColor: C.gold, numSize: 28, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "100%", "全部成功", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 10 });
  const cols = [
    { x: 0.5, w: 2.6, header: "工具" },
    { x: 3.1, w: 1.6, header: "用户数", align: "center" },
    { x: 4.7, w: 1.8, header: "请求/迭代", align: "center" },
    { x: 6.5, w: 1.6, header: "P95", align: "center" },
    { x: 8.1, w: 1.6, header: "错误率", align: "center" },
    { x: 9.7, w: 3.13, header: "结论" },
  ];
  const rows = [
    ["k6", "500", "9147", "9.53s", "0%", "✅ 通过"],
    ["Locust", "500", "8073", "8.7s", "0%", "✅ 通过"],
    ["CS 压测", "500", "—", "—", "0%", "✅ 302 通过"],
    ["HPA 验证", "500", "—", "—", "0%", "✅ 3→20 伸缩"],
  ];
  table(s, cols, rows, 3.3, { rowH: 0.55, headH: 0.45, fontSize: 9.5, headFontSize: 10, boldFirstCol: true });
  foot(s, 94);
})();

// ---- Page 95: Knowledge base indexing success ------------------------------
(function p95() {
  const s = contentSlide("知识库索引成功率（11/11 完成）", { page: 95 });
  statCard(s, 0.5, 1.4, 2.85, 1.5, "11", "文档总数", { fill: C.darkCard, numColor: C.accent, numSize: 34, labSize: 10 });
  statCard(s, 3.5, 1.4, 2.85, 1.5, "11", "索引成功", { fill: C.darkCard, numColor: C.secondary, numSize: 34, labSize: 10 });
  statCard(s, 6.5, 1.4, 2.85, 1.5, "631", "分段总数", { fill: C.darkCard, numColor: C.gold, numSize: 34, labSize: 10 });
  statCard(s, 9.5, 1.4, 3.33, 1.5, "100%", "成功率", { fill: C.darkCard, numColor: C.accent, numSize: 28, labSize: 10 });
  // Progress visualization
  s.addText("索引进度", { x: 0.5, y: 3.2, w: 3, h: 0.4, fontFace: F.header, fontSize: 13, color: C.primary, bold: true });
  const docs = ["PLC×3", "协议×2", "安全×1", "Python×2", "Java×1", "软件工程×1", "IIoT×1"];
  docs.forEach((d, i) => {
    const y = 3.7 + i * 0.4;
    s.addText(d, { x: 0.5, y, w: 1.6, h: 0.32, fontFace: F.body, fontSize: 9, color: C.primary, valign: "middle" });
    progressBar(s, 2.2, y + 0.06, 9.5, 0.2, 100, C.accent);
    s.addText("✅ 完成", { x: 11.8, y, w: 1.0, h: 0.32, fontFace: F.body, fontSize: 9, color: C.accent, bold: true, valign: "middle" });
  });
  s.addText("11 个文档全部索引完成 · 0 失败 · 631 个分段可用", { x: 0.5, y: 6.7, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 95);
})();

// =============================================================================
// SECTION 10 — Conclusion (pages 96-100)
// =============================================================================
sectionSlide("10", "总结与展望", { sub: "成果回顾 · 经验沉淀 · 未来规划", page: 96 });

// ---- Page 97: 10 key achievements (checklist) -------------------------------
(function p97() {
  const s = contentSlide("十大核心成果", { page: 97 });
  const items = [
    "完成 Dify 平台本地化部署 · 58 个教学应用上线",
    "部署 26 个本地 AI 模型 · LiteLLM 统一网关 · 故障转移",
    "Code-Server AI 编程环境 · 52 扩展 · Continue.dev",
    "7 个教学知识库 · 11 文档 · 631 分段全部索引",
    "6 个工业 IoT 工作流 · 3 个 Agent · 4 个虚拟课堂导师",
    "HPA 自动伸缩 · 3→20 副本弹性 · 500 并发压测通过",
    "Redis 8 集群 · 3 节点 · 16384 槽 · 100% 可用",
    "8 层代码补丁 · model_schema null 修复 · patched 镜像",
    "116 项测试 100% 通过 · 功能/模型/E2E/压测全覆盖",
    "Rancher + Grafana 33 面板 · 全栈可观测 · 备份恢复",
  ];
  items.forEach((it, i) => {
    const row = Math.floor(i / 2), col = i % 2;
    const x = 0.5 + col * 6.3, y = 1.4 + row * 1.05;
    s.addShape(SHP.roundRect, { x, y, w: 5.9, h: 0.85, fill: { color: C.white }, line: { color: C.grayL, width: 1 } });
    checkRow(s, x + 0.15, y + 0.22, 5.6, it, { size: 10 });
  });
  foot(s, 97);
})();

// ---- Page 98: Future plans (3-column) --------------------------------------
(function p98() {
  const s = contentSlide("未来规划", { page: 98 });
  const plans = [
    ["短期（3 个月内）", C.secondary, [
      "补充 5 个待上传知识库",
      "扩容模型至 30+ 个",
      "完善游戏化学习 Agent",
      "优化 Ollama 推理性能",
    ]],
    ["中期（6 个月内）", C.accent, [
      "接入更多课程场景",
      "音视频多模态扩展",
      "建立学生画像系统",
      "教学数据分析平台",
    ]],
    ["长期（12 个月内）", C.gold, [
      "支持 5000+ 并发用户",
      "跨校区分布式部署",
      "AI 教学质量评估",
      "工业 IoT 数字孪生集成",
    ]],
  ];
  plans.forEach((p, i) => {
    const x = 0.5 + i * 4.28;
    s.addShape(SHP.roundRect, { x, y: 1.4, w: 4.05, h: 4.7, fill: { color: C.white }, line: { color: p[1], width: 2 } });
    s.addShape(SHP.rect, { x, y: 1.4, w: 4.05, h: 0.6, fill: { color: p[1] }, line: { type: "none" } });
    s.addText(p[0], { x: x + 0.1, y: 1.4, w: 3.85, h: 0.6, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
    p[2].forEach((it, j) => {
      s.addShape(SHP.ellipse, { x: x + 0.25, y: 2.3 + j * 0.85 + 0.12, w: 0.26, h: 0.26, fill: { color: p[1] }, line: { type: "none" } });
      s.addText(it, { x: x + 0.65, y: 2.3 + j * 0.85, w: 3.2, h: 0.5, fontFace: F.body, fontSize: 10, color: C.primary, valign: "middle" });
    });
  });
  s.addText("分阶段规划 · 持续迭代 · 打造工业 IoT 教学标杆平台", { x: 0.5, y: 6.3, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.secondary, bold: true, align: "center" });
  foot(s, 98);
})();

// ---- Page 99: Lessons learned -----------------------------------------------
(function p99() {
  const s = contentSlide("经验沉淀 · 踩坑总结", { page: 99 });
  const cols = [
    { x: 0.5, w: 2.6, header: "问题" },
    { x: 3.1, w: 3.6, header: "现象" },
    { x: 6.7, w: 4.6, header: "解决方案" },
    { x: 11.3, w: 1.53, header: "状态", align: "center" },
  ];
  const rows = [
    ["kubelet 认证", "节点 NotReady", "续签证书 · 重启服务", "✅ 已解决"],
    ["Redis MOVED", "外部访问失败", "announce-ip + TrafficPolicy", "✅ 已解决"],
    ["numpy 版本", "Dify 依赖冲突", "固定 numpy<2 · 重装", "✅ 已解决"],
    ["Calico 路由", "Pod 网络中断", "重建 calico-node · BGP", "✅ 已解决"],
    ["Code-Server WS", "WS 401/400", "proxy v4 · upgrade 处理", "✅ 已解决"],
    ["model_schema null", "API 500 错误", "8 层补丁 · patched 镜像", "✅ 已解决"],
    ["内存过高", "123GB 占用", "禁用索引 · 常驻模型", "✅ 已解决"],
    ["iptables DNAT", "NodePort 不通", "重置 iptables · kube-proxy", "✅ 已解决"],
  ];
  table(s, cols, rows, 1.4, { rowH: 0.55, headH: 0.5, fontSize: 9.5, headFontSize: 10.5, boldFirstCol: true });
  s.addText("8 类关键问题全部解决 · 形成可复用运维知识库", { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontFace: F.header, fontSize: 12, color: C.accent, bold: true, align: "center" });
  foot(s, 99);
})();

// ---- Page 100: Thank you slide ---------------------------------------------
(function p100() {
  const s = pptx.addSlide();
  fillBg(s, C.primary);
  // accent bands
  s.addShape(SHP.rect, { x: 0, y: 0, w: W, h: 0.15, fill: { color: C.accent } });
  s.addShape(SHP.rect, { x: 0, y: H - 0.15, w: W, h: 0.15, fill: { color: C.secondary } });
  // decorative
  s.addShape(SHP.ellipse, { x: 9.5, y: -2, w: 6, h: 6, fill: { color: "0E2A48" }, line: { type: "none" } });
  s.addShape(SHP.ellipse, { x: -2, y: 4, w: 5, h: 5, fill: { color: "0E2A48" }, line: { type: "none" } });
  s.addText("感谢聆听", { x: 0.8, y: 2.4, w: 11.7, h: 1.5, fontFace: F.title, fontSize: 60, color: C.white, bold: true, align: "center", valign: "middle" });
  s.addShape(SHP.rect, { x: 5.6, y: 4.0, w: 2.1, h: 0.08, fill: { color: C.accent } });
  s.addText("Dify 智能体服务平台 · 本地化部署成果汇报", { x: 0.8, y: 4.3, w: 11.7, h: 0.5, fontFace: F.header, fontSize: 18, color: C.accent, align: "center" });
  s.addText("工业互联网应用专业 · AI 教学平台 · 2026年8月", { x: 0.8, y: 4.95, w: 11.7, h: 0.4, fontFace: F.body, fontSize: 13, color: C.grayL, align: "center" });
  // contact / Q&A
  s.addShape(SHP.roundRect, { x: 4.4, y: 5.7, w: 4.5, h: 0.7, fill: { color: C.darkCard }, line: { color: C.accent, width: 1.5 } });
  s.addText("欢迎提问与交流 (Q & A)", { x: 4.4, y: 5.7, w: 4.5, h: 0.7, fontFace: F.header, fontSize: 12, color: C.white, bold: true, align: "center", valign: "middle" });
})();

console.log("Sections 1-10 built. Slides so far:", pptx.slides.length);

// =============================================================================
// SAVE
// =============================================================================
const OUT = "Dify智能体服务平台本地化部署成果汇报_100.pptx";
pptx.writeFile({ fileName: OUT }).then(function (fn) {
  console.log("DONE -> " + fn);
}).catch(function (e) {
  console.error("WRITE ERROR:", e);
  process.exit(1);
});
