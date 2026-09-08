#!/usr/bin/env python3
"""
Generate 3 professional code-server teaching PPTs with:
- Light gradient theme (white to light blue/purple)
- Rich content: detailed text, tables, multi-column layouts, code snippets, tips boxes, icon-like markers
- Professional card-based layouts
- ~100 slides each, total ~300 slides
- PptxGenJS v4.0.1 for native .pptx output
"""
import json, subprocess, os, math

BASE = r"D:\dify-install\load-test"
NODE = BASE  # node_modules is here

# Theme colors - light gradient professional
THEME = {
    "BG": "F0F4FF",       # very light blue-white
    "BG2": "E8EEFF",      # slightly more blue
    "PRIMARY": "2563EB",  # blue-600
    "ACCENT": "7C3AED",   # purple-600
    "ACCENT2": "059669",  # emerald-600
    "DARK": "1E293B",     # slate-800
    "TEXT": "334155",     # slate-700
    "SUBTLE": "64748B",   # slate-500
    "WHITE": "FFFFFF",
    "CARD": "FFFFFF",
    "CARD_BORDER": "CBD5E1",
    "CODE_BG": "1E293B",  # dark blue for code
    "CODE_TEXT": "E2E8F0",
    "GREEN": "059669",
    "RED": "DC2626",
    "YELLOW": "D97706",
    "GRADIENT_START": "2563EB",
    "GRADIENT_END": "7C3AED",
}

T = THEME

def js_color(hex_str):
    return f"\"{hex_str}\""

def pptxgen_slide_js(slide_defs, filename, title, subtitle):
    """Generate JS code for PptxGenJS to create the deck"""
    
    slides_json = json.dumps(slide_defs, ensure_ascii=False)
    
    js_code = f'''
const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

// Light theme colors
const C = {{
  BG: "{T['BG']}", BG2: "{T['BG2']}", PRI: "{T['PRIMARY']}", ACC: "{T['ACCENT']}",
  ACC2: "{T['ACCENT2']}", DARK: "{T['DARK']}", TXT: "{T['TEXT']}", SUB: "{T['SUBTLE']}",
  WHT: "{T['WHITE']}", CARD: "{T['CARD']}", CB: "{T['CARD_BORDER']}",
  CD: "{T['CODE_BG']}", CT: "{T['CODE_TEXT']}", GRN: "{T['GREEN']}",
  RED: "{T['RED']}", YEL: "{T['YELLOW']}", GS: "{T['GRADIENT_START']}", GE: "{T['GRADIENT_END']}"
}};

pptx.defineLayout({{name:"WIDE",width:13.33,height:7.5}});
pptx.layout="WIDE";
pptx.author = "Enterprise Training";
pptx.title = "{title}";

const slides = {slides_json};

// Helper: create gradient bar at top
function gradientBar(sl) {{
  sl.addShape(pptx.ShapeType.rect, {{x:0,y:0,w:13.33,h:0.08,fill:{{color:C.GS}}}});
  sl.addShape(pptx.ShapeType.rect, {{x:0,y:0.08,w:6.67,h:0.04,fill:{{color:C.ACC}}}});
}}

// Helper: add footer
function footer(sl, i) {{
  sl.addText("code-server Enterprise Training Guide | {title[:30]} | Slide "+(i+1)+"/"+slides.length,
    {{x:0.3,y:7.1,w:12.7,h:0.3,fontSize:8,color:C.SUB,fontFace:"Segoe UI"}});
}}

// Helper: add a content card with shadow effect
function card(sl, x, y, w, h, opts={{}}) {{
  const f = opts.fill || C.WHT;
  sl.addShape(pptx.ShapeType.rect, {{x:x+0.03,y:y+0.03,w:w,h:h,fill:{{color:"E2E8F0"}},rectRadius:0.1}});
  sl.addShape(pptx.ShapeType.rect, {{x:x,y:y,w:w,h:h,fill:{{color:f}},rectRadius:0.1,line:{{color:C.CB,width:0.5}}}});
}}

// Helper: add icon bullet (colored circle + text)
function bullet(sl, x, y, icon, txt, opts={{}}) {{
  const c = opts.color || C.PRI;
  sl.addShape(pptx.ShapeType.ellipse, {{x:x,y:y+0.05,w:0.25,h:0.25,fill:{{color:c}}}});
  sl.addText(icon, {{x:x,y:y,w:0.25,h:0.35,fontSize:10,color:C.WHT,align:"center",fontFace:"Segoe UI"}});
  sl.addText(txt, {{x:x+0.35,y:y,w:opts.tw||4,h:0.35,fontSize:opts.fs||13,color:opts.tc||C.TXT,fontFace:"Segoe UI"}});
}}

// Helper: numbered step
function step(sl, x, y, num, txt, opts={{}}) {{
  const c = opts.color || C.PRI;
  sl.addShape(pptx.ShapeType.roundRect, {{x:x,y:y,w:0.35,h:0.35,fill:{{color:c}},rectRadius:0.18}});
  sl.addText(""+num, {{x:x,y:y,w:0.35,h:0.35,fontSize:14,color:C.WHT,bold:true,align:"center",fontFace:"Segoe UI"}});
  sl.addText(txt, {{x:x+0.5,y:y,w:opts.tw||5,h:0.35,fontSize:opts.fs||13,color:opts.tc||C.TXT,fontFace:"Segoe UI"}});
}}

// Helper: code block
function codeBlock(sl, x, y, w, h, code, title) {{
  if (title) {{
    sl.addShape(pptx.ShapeType.roundRect, {{x:x,y:y,w:w,h:0.3,fill:{{color:"334155"}},rectRadius:0.05}});
    sl.addText(title, {{x:x+0.1,y:y,w:w-0.2,h:0.3,fontSize:9,color:C.CT,fontFace:"Consolas"}});
    y += 0.3; h -= 0.3;
  }}
  sl.addShape(pptx.ShapeType.rect, {{x:x,y:y,w:w,h:h,fill:{{color:C.CD}},rectRadius:0.05}});
  sl.addText(code, {{x:x+0.15,y:y+0.05,w:w-0.3,h:h-0.1,fontSize:9,color:C.CT,fontFace:"Consolas",lineSpacing:14}});
}}

// Helper: tip box
function tipBox(sl, x, y, w, h, txt, t) {{
  const tc = t==="tip"?C.GRN:(t==="warn"?C.YEL:C.RED);
  const tb = t==="tip"?"F0FDF4":(t==="warn"?"FFFBEB":"FEF2F2");
  sl.addShape(pptx.ShapeType.rect, {{x:x,y:y,w:w,h:h,fill:{{color:tb}},rectRadius:0.08,line:{{color:tc,width:1}}}});
  sl.addText((t==="tip"?"💡 Tip":(t==="warn"?"⚠️ Note":"🔴 Warning")),
    {{x:x+0.15,y:y+0.05,w:w-0.3,h:0.3,fontSize:10,color:tc,bold:true,fontFace:"Segoe UI"}});
  sl.addText(txt, {{x:x+0.15,y:y+0.35,w:w-0.3,h:h-0.45,fontSize:11,color:C.TXT,fontFace:"Segoe UI"}});
}}

// Helper: table
function addTable(sl, x, y, headers, rows, w) {{
  const hdr = headers.map(h => ({{text:h,options:{{fill:{{color:C.PRI}},color:C.WHT,bold:true,fontSize:10,align:"center",fontFace:"Segoe UI"}}}}));
  const data = rows.map(row => row.map(cell => ({{text:cell,options:{{fontSize:10,color:C.TXT,fontFace:"Segoe UI"}}}})));
  const all = [hdr, ...data];
  const colW = w/headers.length;
  const colWidths = headers.map(() => colW);
  sl.addTable(all, {{x:x,y:y,w:w,border:{{type:"solid",pt:0.5,color:C.CB}},
    colW:colWidths,rowH:[0.35].concat(rows.map(()=>0.3)),autoPage:false,margin:[2,4,2,4]}});
}}

// Process all slides
slides.forEach((s,i) => {{
  const sl = pptx.addSlide();
  sl.background = {{fill:C.BG}};
  
  switch(s.t) {{
    case "title":
      // Full gradient title slide
      sl.addShape(pptx.ShapeType.rect, {{x:0,y:0,w:13.33,h:7.5,fill:{{color:C.BG2}}}});
      sl.addShape(pptx.ShapeType.rect, {{x:0,y:0,w:13.33,h:0.12,fill:{{color:C.PRI}}}});
      sl.addShape(pptx.ShapeType.rect, {{x:0,y:2.5,w:0.08,h:3.5,fill:{{color:C.ACC}}}});
      sl.addText(s.title, {{x:0.8,y:2.0,w:11.5,h:1.4,fontSize:38,color:C.DARK,bold:true,fontFace:"Segoe UI"}});
      sl.addText(s.sub, {{x:0.8,y:3.4,w:11.5,h:0.8,fontSize:20,color:C.PRI,fontFace:"Segoe UI"}});
      sl.addShape(pptx.ShapeType.rect, {{x:0.8,y:4.5,w:3,h:0.05,fill:{{color:C.ACC}}}});
      sl.addText("code-server Full-Feature Enterprise Training Guide | June 2026",
        {{x:0.8,y:4.8,w:11,h:0.5,fontSize:12,color:C.SUB,fontFace:"Segoe UI"}});
      break;
      
    case "section":
      // Section divider
      sl.addShape(pptx.ShapeType.rect, {{x:0,y:2.2,w:13.33,h:3.5,fill:{{color:C.BG2}}}});
      sl.addShape(pptx.ShapeType.rect, {{x:0,y:2.2,w:0.08,h:3.5,fill:{{color:C.ACC}}}});
      sl.addText("PART "+(s.ch||""), {{x:0.8,y:2.0,w:11,h:0.5,fontSize:14,color:C.ACC,bold:true,fontFace:"Segoe UI"}});
      sl.addText(s.title, {{x:0.8,y:2.6,w:11.5,h:1.2,fontSize:30,color:C.DARK,bold:true,fontFace:"Segoe UI"}});
      sl.addText(s.sub||"", {{x:0.8,y:4.0,w:11,h:0.6,fontSize:14,color:C.SUB,fontFace:"Segoe UI"}});
      break;
      
    case "content":
      gradientBar(sl);
      sl.addText(s.title, {{x:0.5,y:0.25,w:12,h:0.55,fontSize:20,color:C.DARK,bold:true,fontFace:"Segoe UI"}});
      sl.addShape(pptx.ShapeType.rect, {{x:0.5,y:0.82,w:1.5,h:0.03,fill:{{color:C.PRI}}}});
      if (s.items) s.items.forEach(it => {{
        if (it.t==="card") card(sl, it.x, it.y, it.w, it.h, it.opts||{{}});
        if (it.t==="bullet") bullet(sl, it.x, it.y, it.i, it.txt, it.opts||{{}});
        if (it.t==="step") step(sl, it.x, it.y, it.n, it.txt, it.opts||{{}});
        if (it.t==="code") codeBlock(sl, it.x, it.y, it.w, it.h, it.code, it.ct);
        if (it.t==="tip") tipBox(sl, it.x, it.y, it.w, it.h, it.txt, it.tp||"tip");
        if (it.t==="text") sl.addText(it.txt, {{x:it.x,y:it.y,w:it.w,h:it.h,fontSize:it.fs||14,color:it.tc||C.TXT,fontFace:"Segoe UI",bold:it.b||false,lineSpacing:22}});
        if (it.t==="table") addTable(sl, it.x, it.y, it.hd, it.rows, it.w);
      }});
      break;
      
    case "toc":
      gradientBar(sl);
      sl.addText("Table of Contents", {{x:0.5,y:0.25,w:12,h:0.55,fontSize:22,color:C.DARK,bold:true,fontFace:"Segoe UI"}});
      sl.addText("Navigate through this comprehensive guide to code-server mastery",
        {{x:0.5,y:0.8,w:12,h:0.4,fontSize:12,color:C.SUB,fontFace:"Segoe UI"}});
      if (s.items) s.items.forEach((ch,j) => {{
        const col = j < s.items.length/2 ? 0 : 1;
        const idx = j < s.items.length/2 ? j : j - Math.ceil(s.items.length/2);
        const cx = 0.5 + col*6.5;
        const cy = 1.3 + idx*0.36;
        sl.addShape(pptx.ShapeType.roundRect, {{x:cx,y:cy,w:0.28,h:0.28,fill:{{color:col===0?C.PRI:C.ACC}},rectRadius:0.14}});
        sl.addText(""+(j+1), {{x:cx,y:cy,w:0.28,h:0.28,fontSize:10,color:C.WHT,bold:true,align:"center",fontFace:"Segoe UI"}});
        sl.addText(ch.n, {{x:cx+0.38,y:cy,w:5.5,h:0.28,fontSize:12,color:C.TXT,fontFace:"Segoe UI"}});
      }});
      break;
      
    case "blank":
      break;
  }}
  
  footer(sl, i);
}});

pptx.writeFile({{fileName:"{filename}"}}).then(() => console.log('OK')).catch(e => console.error('ERR:',e.message));
'''
    return js_code

# =============================================
# PART 1: BASICS & IDE USAGE (~100 slides)
# =============================================
PART1 = []

def title(t, sub=""): return {"t":"title", "title":t, "sub":sub}
def section(t, sub="", ch=""): return {"t":"section", "title":t, "sub":sub, "ch":ch}
def toc(items): return {"t":"toc", "items":items}
def content(t, items): return {"t":"content", "title":t, "items":items}

# Title slide
PART1.append(title("code-server 全功能学习指南", "第一部分：基础入门与 IDE 使用"))
PART1.append(title("code-server Full-Feature Learning Guide", "Part 1: Basics & IDE Usage"))

# TOC
PART1.append(toc([
    {"n":"第1章：code-server 概述与架构"},
    {"n":"第2章：环境搭建与部署"},
    {"n":"第3章：首次登录与界面认知"},
    {"n":"第4章：文件与项目管理"},
    {"n":"第5章：编辑器深度使用"},
    {"n":"第6章：代码导航与智能提示"},
    {"n":"第7章：终端集成"},
    {"n":"第8章：Git 版本控制"},
    {"n":"第9章：代码调试"},
    {"n":"第10章：设置与个性化"},
    {"n":"第11章：快捷键体系"},
    {"n":"第12章：远程开发"},
]))

# Chapter 1: Overview
PART1.append(section("第1章：code-server 概述与架构", "Chapter 1: Overview & Architecture", "01"))
PART1.append(content("1.1 什么是 code-server？", [
    {"t":"text", "x":0.5,"y":1.1,"w":12,"h":1.5, "fs":14,
     "txt":"code-server 是由 Coder 公司开源的云端 IDE 解决方案，它将完整的 VS Code 编辑器运行在远程服务器上，\n通过浏览器即可访问。用户无需本地安装任何软件，只需一个现代浏览器即可获得完整的 VS Code 体验。"},
    {"t":"card","x":0.5,"y":2.8,"w":3.8,"h":2.2,
     "opts":{"fill":"EEF2FF"}},
    {"t":"text","x":0.7,"y":2.9,"w":3.4,"h":2.0,"fs":11,"b":True,"tc":"2563EB",
     "txt":"核心特性\n\n• 完整的 VS Code 体验\n• 基于浏览器的访问\n• 支持所有 VS Code 扩展\n• 内置终端访问\n• 支持多租户部署\n• 资源集中管理"},
    {"t":"text","x":4.8,"y":2.8,"w":3.8,"h":1.8,"fs":12,
     "txt":"适用场景\n\n▸ 远程开发团队\n▸ 教育培训机构\n▸ 企业标准化开发环境\n▸ 云原生开发工作流\n▸ 大型项目的统一环境\n▸ 安全受限环境开发"},
    {"t":"text","x":9.1,"y":2.8,"w":3.8,"h":1.8,"fs":12,
     "txt":"技术架构\n\n▸ 后端：Node.js 服务器\n▸ 前端：VS Code Web\n▸ 协议：WebSocket 通信\n▸ 认证：支持 OAuth2/PAM\n▸ 存储：本地或远程挂载\n▸ 部署：Docker/K8s/裸机"},
]))

PART1.append(content("1.2 code-server vs VS Code Desktop vs GitHub Codespaces", [
    {"t":"table","x":0.5,"y":1.2,"w":12,"hd":["特性","VS Code Desktop","code-server","GitHub Codespaces"],
     "rows":[
        ["安装方式","本地安装","浏览器访问","浏览器访问"],
        ["资源消耗","本地 CPU/内存","服务器 CPU/内存","云端分配"],
        ["扩展支持","全部","全部","大部分"],
        ["离线使用","支持","需网络","需网络"],
        ["多设备同步","手动配置","自动","自动"],
        ["成本","免费","自行托管成本","按使用付费"],
        ["定制化","高","高","中"],
        ["安全性","本地","企业控制","GitHub 控制"],
     ]},
    {"t":"tip","x":0.5,"y":5.5,"w":12,"h":1.2,
     "txt":"code-server 最佳定位：当你需要在多台设备间无差别开发、希望统一团队开发环境、或者运行\n资源受限的本地设备上需要访问强大计算资源时，code-server 是最佳选择。",
     "tp":"tip"},
]))

PART1.append(content("1.3 code-server 企业架构详解", [
    {"t":"text","x":0.5,"y":1.1,"w":6,"h":5.5,"fs":12,
     "txt":"架构层次说明：\n\n1. 用户层 (User Layer)\n   浏览器访问 → HTTPS/TLS 加密传输\n\n2. 入口层 (Ingress Layer)\n   Nginx/Traefik Ingress → 路由分发\n   • 支持 WebSocket 协议升级\n   • SSL 终止\n   • 速率限制\n\n3. 应用层 (Application Layer)\n   code-server 实例 (多副本)\n   • 每个用户独立工作空间\n   • 资源隔离 (CPU/Memory Limit)\n   • 持久化存储挂载"},
    {"t":"code","x":7,"y":1.1,"w":5.8,"h":4,
     "code":"User Browser (HTTPS)\n       │\n       ▼\n┌─────────────────┐\n│  Ingress (Nginx) │◄── TLS/SSL\n│  - Rate Limiting  │\n│  - Auth Proxy     │\n│  - WebSocket      │\n└────────┬────────┘\n         │\n         ▼\n┌─────────────────┐\n│ code-server Pods │◄── K8s Deployment\n│  - 20+ Replicas   │\n│  - PVC Storage    │\n│  - 500m CPU/Pod   │\n└────────┬────────┘\n         │\n         ▼\n┌─────────────────┐\n│ Storage Layer    │\n│  - local-path    │\n└─────────────────┘",
     "ct":"code-server 企业部署架构图"},
]))

PART1.append(content("1.4 关键概念：工作空间 (Workspace)", [
    {"t":"text","x":0.5,"y":1.1,"w":6,"h":2.5,"fs":13,
     "txt":"工作空间是 code-server 的核心概念，它代表一个独立的开发环境。\n\n▸ 每个工作空间对应一个文件系统目录\n▸ 配置独立：settings.json、keybindings.json\n▸ 扩展独立：每个工作空间可安装不同扩展\n▸ 状态持久化：关闭浏览器后环境不丢失\n▸ 多窗口支持：可同时打开多个工作空间"},
    {"t":"card","x":7,"y":1.1,"w":5.8,"h":2.5,
     "opts":{"fill":"F0FDF4"}},
    {"t":"text","x":7.2,"y":1.2,"w":5.4,"h":2.3,"fs":11,
     "txt":"工作空间类型\n\n📁 单文件夹工作空间\n   打开单个项目目录\n\n📁📁 多根工作空间 (Multi-root)\n   .code-workspace 文件\n   同时管理多个项目\n\n☁️ 远程工作空间\n   通过 SSH 连接远程服务器\n\n📦 容器化工作空间\n   基于 Docker/K8s 的隔离环境"},
    {"t":"tip","x":0.5,"y":4.0,"w":12,"h":1.0,
     "txt":"最佳实践：为每个项目创建独立工作空间，使用 .code-workspace 文件统一管理多个相关项目。",
     "tp":"tip"},
]))

# Chapter 2: Setup
PART1.append(section("第2章：环境搭建与部署", "Chapter 2: Environment Setup & Deployment", "02"))
PART1.append(content("2.1 Kubernetes 部署架构", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":2.5,"fs":12,
     "txt":"企业级 K8s 部署方案：\n\n📦 Deployment：管理 20 个 code-server Pod\n📊 HPA：根据 CPU/内存自动伸缩\n🔗 Service：内部 ClusterIP 服务发现\n🌐 Ingress：外部 HTTPS 访问入口\n💾 PVC：持久化存储用户工作空间\n🔐 Secret：存储密码和 TLS 证书\n📋 ConfigMap：统一配置文件管理"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: code-server\n  namespace: ai-platform\nspec:\n  replicas: 20\n  selector:\n    matchLabels:\n      app: code-server\n  template:\n    spec:\n      containers:\n      - name: code-server\n        image: lscr.io/linuxserver/\n               code-server:latest\n        env:\n        - name: PASSWORD\n          valueFrom:\n            secretKeyRef:\n              name: code-server-secret\n              key: password\n        ports:\n        - containerPort: 8443\n        resources:\n          limits:\n            cpu: 1000m\n            memory: 2Gi\n          requests:\n            cpu: 500m\n            memory: 1Gi\n        volumeMounts:\n        - name: workspace\n          mountPath: /config/workspace\n      volumes:\n      - name: workspace\n        persistentVolumeClaim:\n          claimName: code-server-pvc",
     "ct":"code-server K8s Deployment YAML"},
]))

PART1.append(content("2.2 Ingress 配置与域名访问", [
    {"t":"code","x":0.5,"y":1.1,"w":6,"h":3.5,
     "code":"apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: code-server-ingress\n  annotations:\n    nginx.ingress.kubernetes.io/\n      proxy-read-timeout: \"3600\"\n    nginx.ingress.kubernetes.io/\n      proxy-send-timeout: \"3600\"\n    cert-manager.io/cluster-issuer:\n      \"letsencrypt-prod\"\nspec:\n  tls:\n  - hosts:\n    - code.yourdomain.com\n    secretName: code-tls\n  rules:\n  - host: code.yourdomain.com\n    http:\n      paths:\n      - path: /\n        pathType: Prefix\n        backend:\n          service:\n            name: code-server\n            port:\n              number: 8443",
     "ct":"Ingress 配置示例"},
    {"t":"text","x":7,"y":1.1,"w":5.8,"h":5,"fs":12,
     "txt":"Ingress 关键配置说明：\n\n🔧 proxy-read-timeout: 3600\n   WebSocket 长连接必须设置足够大\n   的超时时间，否则终端会频繁断开\n\n🔐 cert-manager 集成\n   自动申请和续期 Let's Encrypt SSL 证书\n\n🔗 WebSocket 支持\n   Nginx Ingress 默认支持 WebSocket，\n   无需额外配置\n\n📊 访问控制\n   可通过 Nginx auth_request 集成\n   OAuth2 Proxy 或 Keycloak\n\n⚡ 性能优化\n   • 启用 HTTP/2\n   • 配置 gzip 压缩\n   • 设置合理的 buffer 大小"},
]))

# Chapter 3: First Login & Interface
PART1.append(section("第3章：首次登录与界面认知", "Chapter 3: First Login & Interface Guide", "03"))
PART1.append(content("3.1 登录方式详解", [
    {"t":"text","x":0.5,"y":1.1,"w":12,"h":1.2,"fs":14,
     "txt":"code-server 支持多种认证方式，企业部署通常使用密码认证或与现有身份系统集成。"},
    {"t":"card","x":0.5,"y":2.5,"w":3.5,"h":3.5,
     "opts":{"fill":"EEF2FF"}},
    {"t":"text","x":0.7,"y":2.6,"w":3.1,"h":3.3,"fs":11,"b":True,"tc":"2563EB",
     "txt":"密码认证\n\n最简单的方式\n\n• 设置 PASSWORD 环境变量\n• 或使用 hashed-password\n• 支持 bcrypt 哈希\n\n配置：\nPASSWORD=your_password\n\n企业建议：\n使用 Secret 管理密码\n配合网络策略限制访问"},
    {"t":"card","x":4.5,"y":2.5,"w":3.5,"h":3.5,
     "opts":{"fill":"F0FDF4"}},
    {"t":"text","x":4.7,"y":2.6,"w":3.1,"h":3.3,"fs":11,"b":True,"tc":"059669",
     "txt":"OAuth2 认证\n\n企业级单点登录\n\n• 集成 Keycloak\n• 支持 GitHub OAuth\n• 支持 GitLab OAuth\n• 支持 Azure AD\n\n配置：\n通过 Nginx auth_request\n或 OAuth2 Proxy 实现\n\n优势：统一身份管理"},
    {"t":"card","x":8.5,"y":2.5,"w":3.5,"h":3.5,
     "opts":{"fill":"FEF3C7"}},
    {"t":"text","x":8.7,"y":2.6,"w":3.1,"h":3.3,"fs":11,"b":True,"tc":"D97706",
     "txt":"无认证模式\n\n仅用于开发/测试\n\n• 设置 --auth=none\n• 直接访问编辑器\n• 无任何安全保护\n\n⚠️ 警告：\n生产环境绝对不要使用！\n仅在 localhost 开发\n或隔离网络中可用"},
]))

PART1.append(content("3.2 VS Code 界面五大区域详解", [
    {"t":"text","x":0.5,"y":1.1,"w":12,"h":0.8,"fs":14,
     "txt":"code-server 的界面完全复刻 VS Code 桌面版，由五个核心区域组成："},
    # Activity Bar
    {"t":"bullet","x":0.5,"y":2.1,"w":5,"h":0.35,"i":"1","txt":"活动栏 (Activity Bar) - 左侧最窄竖条","fs":12,"tc":"2563EB","opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":2.5,"w":5,"h":0.8,"fs":11,
     "txt":"  包含：文件浏览器、搜索、Git、调试、扩展\n  使用：点击图标切换视图，可拖拽调整顺序"},
    # Side Bar
    {"t":"bullet","x":0.5,"y":3.3,"w":5,"h":0.35,"i":"2","txt":"侧边栏 (Side Bar) - 活动栏右侧","fs":12,"tc":"2563EB","opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":3.7,"w":5,"h":0.8,"fs":11,
     "txt":"  显示当前选定视图的详细内容\n  如：文件树、搜索结果、Git 变更"},
    # Editor
    {"t":"bullet","x":0.5,"y":4.5,"w":5,"h":0.35,"i":"3","txt":"编辑区 (Editor) - 中间最大区域","fs":12,"tc":"2563EB","opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":4.9,"w":5,"h":0.8,"fs":11,
     "txt":"  可拆分多组编辑窗口，支持并排编辑\n  标签页管理打开的文件"},
    # Panel
    {"t":"bullet","x":6.5,"y":2.1,"w":5,"h":0.35,"i":"4","txt":"面板区 (Panel) - 底部区域","fs":12,"tc":"7C3AED","opts":{"color":"7C3AED"}},
    {"t":"text","x":7.0,"y":2.5,"w":5.5,"h":0.8,"fs":11,
     "txt":"  集成终端、问题、输出、调试控制台\n  可拖拽调整高度，支持多终端标签"},
    # Status Bar
    {"t":"bullet","x":6.5,"y":3.3,"w":5,"h":0.35,"i":"5","txt":"状态栏 (Status Bar) - 最底部","fs":12,"tc":"7C3AED","opts":{"color":"7C3AED"}},
    {"t":"text","x":7.0,"y":3.7,"w":5.5,"h":0.8,"fs":11,
     "txt":"  显示 Git 分支、编码、行号/列号\n  语言模式、通知、反馈入口"},
    {"t":"tip","x":6.5,"y":4.8,"w":6,"h":1.0,
     "txt":"快捷键：Ctrl+B 切换侧边栏，Ctrl+J 切换面板，Ctrl+` 打开终端。\n掌握这三个快捷键可以极大提高工作区管理效率！",
     "tp":"tip"},
]))

# More content slides - Editor Mastery
PART1.append(content("3.3 命令面板 (Command Palette) - 万能入口", [
    {"t":"text","x":0.5,"y":1.1,"w":7,"h":3.5,"fs":13,
     "txt":"命令面板是 VS Code/code-server 最强大的功能，通过它你可以：\n\n🔍 搜索并执行任何命令\n   快捷键：Ctrl+Shift+P (Windows/Linux)\n           Cmd+Shift+P (Mac)\n\n📝 常用命令示例：\n   • >Preferences: Open Settings (UI)\n   • >Git: Clone\n   • >View: Toggle Terminal\n   • >Extensions: Install Extensions\n   • >Developer: Reload Window\n   • >File: Compare Active File With...\n\n💡 技巧：\n   • 输入 \"?\" 获取帮助\n   • 输入 \">\" 过滤命令\n   • 输入 \"@\" 查看文件符号\n   • 输入 \":\" 跳转到行"},
    {"t":"tip","x":8,"y":1.1,"w":4.8,"h":1.5,
     "txt":"忘记任何快捷键或菜单位置时，\n直接 Ctrl+Shift+P 打开命令面板，\n搜索你需要的功能。\n这是提升效率的 No.1 技巧！",
     "tp":"tip"},
    {"t":"code","x":8,"y":2.9,"w":4.8,"h":2,
     "code":"常用命令面板快捷键\n\nCtrl+Shift+P  打开命令面板\nCtrl+P        快速打开文件\nCtrl+Shift+N  新建窗口\nCtrl+K Ctrl+O 打开文件夹\nCtrl+W        关闭当前标签",
     "ct":"快捷键速查"},
]))

# Chapter 4: File Management  
PART1.append(section("第4章：文件与项目管理", "Chapter 4: File & Project Management", "04"))
PART1.append(content("4.1 文件浏览器 (Explorer) 高级用法", [
    {"t":"text","x":0.5,"y":1.1,"w":12,"h":8,"fs":12,
     "txt":"文件浏览器是日常使用最频繁的功能。掌握以下高级技巧可以大幅提升效率：\n"},
    {"t":"bullet","x":0.5,"y":1.5,"w":5.5,"h":0.3,"i":"📁","txt":"快速创建文件/文件夹","fs":11,"opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":1.85,"w":5,"h":0.5,"fs":10,
     "txt":"  Explorer 工具栏点击新建文件/文件夹图标，或右键菜单"},
    {"t":"bullet","x":0.5,"y":2.3,"w":5.5,"h":0.3,"i":"📁","txt":"文件拖拽排序","fs":11,"opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":2.65,"w":5,"h":0.5,"fs":10,
     "txt":"  直接在文件树中拖拽文件到目标文件夹"},
    {"t":"bullet","x":0.5,"y":3.1,"w":5.5,"h":0.3,"i":"📁","txt":"排除文件显示 (Files: Exclude)","fs":11,"opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":3.45,"w":5,"h":0.5,"fs":10,
     "txt":"  settings.json 中配置 files.exclude 隐藏 node_modules 等"},
    {"t":"bullet","x":0.5,"y":3.9,"w":5.5,"h":0.3,"i":"📁","txt":"多选操作","fs":11,"opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":4.25,"w":5,"h":0.5,"fs":10,
     "txt":"  Ctrl/Cmd+Click 多选，Shift+Click 范围选择"},
    {"t":"bullet","x":0.5,"y":4.7,"w":5.5,"h":0.3,"i":"📁","txt":"大纲视图 (Outline)","fs":11,"opts":{"color":"2563EB"}},
    {"t":"text","x":1.0,"y":5.05,"w":5,"h":0.5,"fs":10,
     "txt":"  显示当前文件结构，快速导航到函数/类/变量"},
    {"t":"code","x":6.5,"y":1.5,"w":6.3,"h":3.5,
     "code":"// settings.json 文件排除配置\n{\n  "files.exclude": {\n    "**/node_modules": true,\n    "**/.git": true,\n    "**/__pycache__": true,\n    "**/*.pyc": true,\n    "**/dist": true,\n    "**/.next": true\n  },\n  "files.watcherExclude": {\n    "**/node_modules/**": true,\n    "**/.git/objects/**": true\n  }\n}",
     "ct":"settings.json 配置示例"},
]))

PART1.append(content("4.2 全局搜索与替换 - 正则表达式实战", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3.5,"fs":12,
     "txt":"搜索面板 (Ctrl+Shift+F) 提供强大的全局搜索能力：\n\n🔍 基本搜索\n   • 输入关键词，实时显示所有匹配\n   • 支持大小写敏感和全字匹配\n\n📁 文件过滤\n   • 使用 files to include/exclude\n   • glob 模式：*.ts, src/**/*.tsx\n\n🔄 替换操作\n   • 单个替换或全部替换\n   • 替换前预览差异\n\n📊 正则表达式\n   • 点击 .* 图标启用正则模式\n   • 支持捕获组替换 $1, $2"},
{"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
      "code":"Regex Search Examples:\n\n1. Find all console.log\n   console.log((.*?))\n\n2. Find unused imports\n   import .* from .*\n\n3. Find TODO/FIXME\n   (TODO|FIXME|HACK):?\n\n4. Replace double-quotes\n   Search: (.*?)\n   Replace: $1\n\n5. Find empty lines\n   empty line pattern\n\n6. Find function defs\n   function (\\w+)\\((.*?)\\)\n\n7. Capture groups\n   (\\w+)\\s*=\\s*(\\d+)",
      "ct":"Regex Search Examples"},
]))

# Chapter 5: Editor Mastery
PART1.append(section("第5章：编辑器深度使用", "Chapter 5: Editor Mastery", "05"))
PART1.append(content("5.1 多光标编辑 - 批量操作利器", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3,"fs":12,
     "txt":"多光标编辑是 code-server 最强大的批量操作功能，\n能让你同时编辑多个位置：\n\n🔹 基本操作\n   Alt+Click：在点击位置添加光标\n   Ctrl+Alt+↓/↑：在上方/下方添加光标\n   Ctrl+Shift+L：选中所有相同文本\n   Ctrl+D：选中下一个相同文本\n\n🔹 应用场景\n   • 同时修改变量名\n   • 批量添加/删除前缀\n   • 格式化多行文本\n   • 同时编辑 HTML 标签对"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"多光标编辑示例：\n\n// 原始代码\nconst name = 'Alice'\nconst name = 'Bob'\nconst name = 'Charlie'\n\n// 1. 选中所有 'const name'\n//    Ctrl+Shift+L\n// 2. 输入 'let userName'\n//    所有行同时修改为：\nlet userName = 'Alice'\nlet userName = 'Bob'\nlet userName = 'Charlie'\n\n// 列选择模式\n// Shift+Alt+拖拽鼠标\n// 或 Ctrl+Shift+Alt+方向键\n\n// 在每行末尾添加分号\n// 1. Ctrl+A 全选\n// 2. Shift+Alt+I 每行末尾插入光标\n// 3. 输入 ;",
     "ct":"多光标编辑实战"},
]))

PART1.append(content("5.2 代码折叠、缩进与格式化", [
    {"t":"text","x":0.5,"y":1.1,"w":6,"h":2,"fs":12,
     "txt":"代码折叠 (Folding)\n\n▸ Ctrl+Shift+[ 折叠当前区域\n▸ Ctrl+Shift+] 展开当前区域\n▸ Ctrl+K Ctrl+0 折叠全部\n▸ Ctrl+K Ctrl+J 展开全部\n▸ Ctrl+K Ctrl+/ 折叠所有注释\n\n缩进管理\n\n▸ Tab/Shift+Tab 缩进/反缩进\n▸ Ctrl+] / Ctrl+[ 缩进/反缩进\n▸ 选中多行统一缩进调整\n▸ 自动检测缩进风格 (空格/Tab)\n\n代码格式化\n\n▸ Shift+Alt+F 格式化文档\n▸ Ctrl+K Ctrl+F 格式化选中区域\n▸ 保存时自动格式化 (editor.formatOnSave)\n▸ 支持 Prettier、ESLint 等格式化工具"},
    {"t":"code","x":7,"y":1.1,"w":5.8,"h":4,
     "code":"// settings.json 格式化配置\n{\n  "editor.formatOnSave": true,\n  "editor.formatOnPaste": true,\n  "editor.tabSize": 2,\n  "editor.insertSpaces": true,\n  "editor.detectIndentation": true,\n  "editor.wordWrap": "on",\n  \n  // 按语言配置\n  "[javascript]": {\n    "editor.defaultFormatter":\n      "esbenp.prettier-vscode",\n    "editor.tabSize": 2\n  },\n  "[python]": {\n    "editor.tabSize": 4\n  },\n  "[go]": {\n    "editor.formatOnSave": true,\n    "editor.defaultFormatter":\n      "golang.go"\n  }\n}",
     "ct":"格式化相关 settings.json 配置"},
]))

# Chapter 6: Navigation
PART1.append(section("第6章：代码导航与智能提示", "Chapter 6: Code Navigation & IntelliSense", "06"))
PART1.append(content("6.1 智能代码导航系统", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":5,"fs":12,
     "txt":"code-server 提供了一套完整的代码导航体系：\n\n🔗 转到定义 (Go to Definition)\n   F12 或 Ctrl+Click\n   直接跳转到符号定义处\n\n🔗 查找所有引用 (Find All References)\n   Shift+F12\n   查看代码中所有使用该符号的位置\n\n🔗 转到实现 (Go to Implementation)\n   Ctrl+F12\n   跳转到接口的具体实现\n\n🔗 转到类型定义 (Go to Type Definition)\n   跳转到 TypeScript 类型定义\n\n🔗 符号导航\n   Ctrl+Shift+O 查看文件内符号\n   Ctrl+T 全局符号搜索\n\n🔗 面包屑导航 (Breadcrumbs)\n   编辑器顶部显示当前文件路径层次\n   点击快速跳转"},
    {"t":"bullet","x":6.5,"y":1.1,"w":6,"h":0.35,"i":"⌨️","txt":"F12 - 转到定义","fs":11,"opts":{"color":"2563EB"}},
    {"t":"bullet","x":6.5,"y":1.55,"w":6,"h":0.35,"i":"⌨️","txt":"Shift+F12 - 查找所有引用","fs":11,"opts":{"color":"2563EB"}},
    {"t":"bullet","x":6.5,"y":2.0,"w":6,"h":0.35,"i":"⌨️","txt":"Ctrl+F12 - 转到实现","fs":11,"opts":{"color":"2563EB"}},
    {"t":"bullet","x":6.5,"y":2.45,"w":6,"h":0.35,"i":"⌨️","txt":"Ctrl+Shift+O - 文件符号","fs":11,"opts":{"color":"7C3AED"}},
    {"t":"bullet","x":6.5,"y":2.9,"w":6,"h":0.35,"i":"⌨️","txt":"Ctrl+T - 全局符号搜索","fs":11,"opts":{"color":"7C3AED"}},
    {"t":"bullet","x":6.5,"y":3.35,"w":6,"h":0.35,"i":"⌨️","txt":"Alt+←/→ - 前进/后退","fs":11,"opts":{"color":"7C3AED"}},
    {"t":"tip","x":6.5,"y":4.0,"w":6,"h":1.2,
     "txt":"Peek Definition (Alt+F12):\n在当前编辑器中以内嵌方式显示定义，\n无需跳转到其他文件，\n查看后按 Esc 退出。",
     "tp":"tip"},
]))

PART1.append(content("6.2 IntelliSense 智能代码补全", [
    {"t":"text","x":0.5,"y":1.1,"w":6,"h":3.5,"fs":12,
     "txt":"IntelliSense 是 code-server 的智能代码补全系统，\n基于语言服务器协议 (LSP) 提供：\n\n📝 代码补全\n   • 基本补全：输入时自动弹出建议\n   • 参数提示：函数调用时显示参数\n   • 快速信息：悬停显示类型和文档\n\n📝 智能感知类型\n   • Tab 键选择建议并自动导入\n   • 自动 import 语句补全\n   • 代码片段 (Snippets) 支持\n\n📝 配置\n   • editor.quickSuggestions\n   • editor.suggestOnTriggerCharacters\n   • editor.acceptSuggestionOnEnter\n   • editor.tabCompletion"},
    {"t":"code","x":7,"y":1.1,"w":5.8,"h":3.5,
     "code":"各语言 LSP 服务器\n\nJavaScript/TypeScript\n  → 内置 TypeScript 语言服务\n\nPython\n  → Pylance / Pyright\n\nGo\n  → gopls (golang.go 扩展)\n\nRust\n  → rust-analyzer\n\nJava\n  → Eclipse JDT LS\n   (Language Support for Java)\n\nC/C++\n  → clangd / C/C++ IntelliSense\n\nScala\n  → Metals\n\nKotlin\n  → Kotlin Language Server",
     "ct":"语言服务器对照表"},
]))

# Chapter 7: Terminal
PART1.append(section("第7章：终端集成", "Chapter 7: Terminal Integration", "07"))
PART1.append(content("7.1 集成终端完全指南", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":4.5,"fs":12,
     "txt":"code-server 内置功能完整的终端仿真器：\n\n🔧 基本操作\n   Ctrl+` 打开/关闭终端\n   Ctrl+Shift+` 新建终端\n   Ctrl+Shift+5 拆分终端 (左右分屏)\n\n📋 多终端管理\n   • 多个终端标签页\n   • 左右/上下分屏显示\n   • 可重命名终端标签\n   • 颜色标记不同终端\n\n⚙️ 配置选项\n   • terminal.integrated.shell.linux\n   • terminal.integrated.fontSize\n   • terminal.integrated.fontFamily\n   • terminal.integrated.cursorStyle\n\n🔗 与编辑器联动\n   • 拖拽文件到终端显示路径\n   • Ctrl+Click 文件路径在编辑器中打开\n   • 右键菜单：在终端中运行选中文本"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"// 终端配置示例\n{\n  "terminal.integrated.fontFamily":\n    "'Cascadia Code', monospace",\n  "terminal.integrated.fontSize": 14,\n  "terminal.integrated.lineHeight": 1.2,\n  "terminal.integrated.cursorStyle":\n    "line",\n  "terminal.integrated.cursorBlinking":\n    true,\n  "terminal.integrated.scrollback":\n    10000,\n  "terminal.integrated.defaultLocation":\n    "editor",\n  "terminal.integrated.shellIntegration":\n    { "enabled": true },\n  "terminal.integrated.enablePersistentSessions":\n    true\n}",
     "ct":"终端 settings.json 配置"},
]))

PART1.append(content("7.2 任务自动化 (Tasks)", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3,"fs":12,
     "txt":"Tasks (任务) 系统让你定义和运行常用构建脚本：\n\n📋 自动检测\n   code-server 自动检测 package.json、Makefile\n   等文件中的脚本，提供一键运行入口\n\n📋 自定义任务\n   在 .vscode/tasks.json 中定义：\n   • build：构建项目\n   • test：运行测试\n   • watch：监听文件变化\n   • deploy：部署项目\n\n📋 运行方式\n   • Ctrl+Shift+B 运行默认构建任务\n   • 终端菜单选择任务\n   • 命令面板搜索 \"Tasks: Run Task\"\n\n📋 问题匹配器\n   自动解析编译输出，将错误关联到文件"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"// .vscode/tasks.json 示例\n{\n  "version": "2.0.0",\n  "tasks": [\n    {\n      "label": "Build Go Project",\n      "type": "shell",\n      "command": "go build",\n      "args": [\n        "-o", "./bin/server",\n        "./cmd/server"\n      ],\n      "group": {\n        "kind": "build",\n        "isDefault": true\n      },\n      "problemMatcher": [\n        "$go"\n      ]\n    },\n    {\n      "label": "Run Tests",\n      "type": "shell",\n      "command": "go test",\n      "args": ["-v", "./..."],\n      "group": "test"\n    }\n  ]\n}",
     "ct":"tasks.json 配置示例"},
]))

# Chapter 8: Git
PART1.append(section("第8章：Git 版本控制", "Chapter 8: Git Version Control", "08"))
PART1.append(content("8.1 Git 集成完全指南", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3,"fs":12,
     "txt":"code-server 内置完整的 Git 可视化支持：\n\n🌿 源代码管理面板 (Ctrl+Shift+G)\n\n📝 变更管理\n   • 实时显示文件变更状态\n   • U (Untracked) / M (Modified) / D (Deleted)\n   • 点击文件查看差异对比\n   • 暂存 (Stage) / 取消暂存\n\n📝 提交操作\n   • 输入提交信息\n   • 一键 Commit + Push\n   • 支持 Amend 和 Signed-off\n\n📝 分支管理\n   • 状态栏显示当前分支\n   • 点击切换/创建分支\n   • 可视化合并冲突解决\n\n📝 高级操作\n   • Stash：暂存工作区\n   • Pull/Rebase：代码同步\n   • Cherry-pick：选择性合并"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4,
     "code":"Git 常用快捷键\n\nCtrl+Shift+G    打开源代码管理\nCtrl+Enter      提交暂存的更改\nCtrl+Shift+P    输入 Git: 查看命令\n\nGit 命令面板常用命令：\n\nGit: Clone            克隆仓库\nGit: Checkout to...    切换分支\nGit: Create Branch    创建分支\nGit: Merge Branch     合并分支\nGit: Fetch            获取远程更改\nGit: Pull             拉取并合并\nGit: Push             推送到远程\nGit: Stash            暂存工作区\nGit: Pop Stash        恢复暂存\nGit: View History     查看提交历史\n  (需安装 Git History 扩展)",
     "ct":"Git 快捷操作速查"},
]))

PART1.append(content("8.2 合并冲突解决", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":2.5,"fs":12,
     "txt":"当 Git 无法自动合并时，code-server 提供可视化冲突解决：\n\n⚡ 冲突标记\n   文件中出现 <<<<<<< ======= >>>>>>> 标记\n\n⚡ 解决方式\n   • Accept Current Change：保留当前分支\n   • Accept Incoming Change：使用合并分支\n   • Accept Both Changes：保留双方更改\n   • Compare Changes：详细对比差异\n\n⚡ 三路合并编辑器\n   提供更直观的三栏对比视图\n   左：当前分支 | 中：合并结果 | 右：合并分支"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4,
     "code":"合并冲突示例\n\n<<<<<<< HEAD (当前分支)\nconst API_URL =\n  'https://api.example.com/v1'\nconst TIMEOUT = 5000\n=======\nconst API_URL =\n  'https://api.example.com/v2'\nconst TIMEOUT = 3000\nconst RETRY_COUNT = 3\n>>>>>>> feature/new-api\n\n// 选择结果：\nconst API_URL =\n  'https://api.example.com/v2'   // 保留 v2\nconst TIMEOUT = 3000             // 保留新值\nconst RETRY_COUNT = 3            // 新增特性",
     "ct":"合并冲突示例"},
]))

# Chapter 9: Debugging
PART1.append(section("第9章：代码调试", "Chapter 9: Debugging", "09"))
PART1.append(content("9.1 调试器完全指南", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3.5,"fs":12,
     "txt":"code-server 内置强大的调试器，支持所有主流语言：\n\n🔴 调试面板 (Ctrl+Shift+D)\n\n🎯 断点类型\n   • 行断点 (F9)：执行到该行时暂停\n   • 条件断点：满足条件时才暂停\n   • 日志点 (Logpoint)：输出日志不暂停\n   • 函数断点：调用指定函数时暂停\n   • 异常断点：抛出异常时暂停\n\n🎯 调试控制\n   • F5 启动/继续\n   • F10 单步跳过\n   • F11 单步进入\n   • Shift+F11 单步跳出\n   • Ctrl+Shift+F5 重启\n   • Shift+F5 停止\n\n🎯 变量监视\n   • 变量面板：查看所有变量值\n   • 监视：自定义表达式\n   • 调用堆栈：查看函数调用链条"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4,
     "code":"// .vscode/launch.json 通用模板\n{\n  "version": "0.2.0",\n  "configurations": [\n    {\n      "name": "Launch Program",\n      "type": "node",  // 调试器类型\n      "request": "launch",\n      "program":\n        "${workspaceFolder}/src/index.js",\n      "args": ["--port", "3000"],\n      "env": {\n        "NODE_ENV": "development"\n      },\n      "console": "integratedTerminal",\n      "skipFiles": [\n        "<node_internals>/**"\n      ]\n    }\n  ]\n}\n\n// 调试器类型：\n// node, python, go, cppvsdbg,\n// cppdbg, java, php, firefox,\n// chrome, edge, extensionHost",
     "ct":"launch.json 配置示例"},
]))

PART1.append(content("9.2 调试技巧与最佳实践", [
    {"t":"card","x":0.5,"y":1.2,"w":3.8,"h":2.5,
     "opts":{"fill":"EEF2FF"}},
    {"t":"text","x":0.7,"y":1.3,"w":3.4,"h":2.3,"fs":11,"b":True,"tc":"2563EB",
     "txt":"条件断点\n\n右键断点 → Edit Breakpoint\n设置条件表达式：\n\n• i > 100\n• user.name === 'admin'\n• err != null\n• items.length === 0\n\n只有条件为 true 时才暂停，\n避免在大循环中频繁中断"},
    {"t":"card","x":4.8,"y":1.2,"w":3.8,"h":2.5,
     "opts":{"fill":"F0FDF4"}},
    {"t":"text","x":5.0,"y":1.3,"w":3.4,"h":2.3,"fs":11,"b":True,"tc":"059669",
     "txt":"日志点 (Logpoint)\n\n右键断点 → Add Logpoint\n输入日志内容：\n\n• 变量值: {variableName}\n• 函数: Function {functionName} called\n• 状态: User {user.id} logged in\n\n不暂停执行，只输出日志\n适合调试生产环境"},
    {"t":"card","x":9.1,"y":1.2,"w":3.8,"h":2.5,
     "opts":{"fill":"FEF3C7"}},
    {"t":"text","x":9.3,"y":1.3,"w":3.4,"h":2.3,"fs":11,"b":True,"tc":"D97706",
     "txt":"调试控制台\n\n在调试暂停时：\n• 在 DEBUG CONSOLE 中\n  执行任意表达式\n• 修改变量值\n• 调用函数测试\n\n示例：\n> user.setRole('admin')\n> calculateTotal(items)\n> JSON.stringify(state)"},
    {"t":"tip","x":0.5,"y":4.2,"w":12,"h":1.2,
     "txt":"Inline Values：在调试时，编辑器内联显示变量值，无需切换到变量面板。\n设置：Debug: Inline Values (在 settings.json 中设置 debug.inlineValues: true)",
     "tp":"tip"},
]))

# Chapter 10: Settings
PART1.append(section("第10章：设置与个性化", "Chapter 10: Settings & Customization", "10"))
PART1.append(content("10.1 Settings.json 完全配置指南", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":2.5,"fs":12,
     "txt":"code-server 配置分为三个层级：\n\n🎨 用户设置 (User Settings)\n   全局生效，影响所有工作空间\n   Ctrl+, 打开设置 UI\n   或编辑 ~/.local/share/code-server/User/settings.json\n\n🎨 工作空间设置 (Workspace Settings)\n   仅当前项目生效\n   存储在 .vscode/settings.json\n   建议提交到 Git 供团队共享\n\n🎨 文件夹设置 (Folder Settings)\n   多根工作空间中按文件夹配置\n   细粒度控制每个子项目"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":5,
     "code":"{\n  // ===== 编辑器设置 =====\n  "editor.fontSize": 14,\n  "editor.fontFamily":\n    "'Fira Code','Cascadia Code'",\n  "editor.fontLigatures": true,\n  "editor.lineHeight": 22,\n  "editor.minimap.enabled": true,\n  "editor.renderWhitespace":\n    "boundary",\n  "editor.bracketPairColorization":\n    {{ "enabled": true }},\n  "editor.guides.bracketPairs":\n    true,\n\n  // ===== 工作台设置 =====\n  "workbench.colorTheme":\n    "One Dark Pro",\n  "workbench.iconTheme":\n    "material-icon-theme",\n  "workbench.startupEditor": "none",\n  "workbench.sideBar.location":\n    "left",\n  "workbench.activityBar.visible":\n    true,\n\n  // ===== 文件设置 =====\n  "files.autoSave":\n    "afterDelay",\n  "files.autoSaveDelay": 1000,\n  "files.trimTrailingWhitespace":\n    true,\n  "files.insertFinalNewline":\n    true,\n  "files.exclude": {{\n    "**/node_modules": true\n  }},\n\n  // ===== 终端设置 =====\n  "terminal.integrated.fontSize":\n    13,\n  "terminal.integrated.cursorStyle":\n    "line"\n}",
     "ct":"完整 settings.json 配置示例"},
]))

PART1.append(content("10.2 主题与图标推荐", [
    {"t":"table","x":0.5,"y":1.2,"w":12,"hd":["主题名称","类型","特点","扩展 ID"],
     "rows":[
        ["One Dark Pro","深色","最流行的深色主题，护眼","zhuangtongfa.material-theme"],
        ["Dracula Official","深色","鲜艳色彩，高对比度","dracula-theme.theme-dracula"],
        ["GitHub Theme","浅色/深色","官方 GitHub 配色","github.github-vscode-theme"],
        ["Monokai Pro","深色","经典 Sublime Text 风格","monokai.theme-monokai-pro-vscode"],
        ["Tokyo Night","深色","柔和霓虹色，护眼","enkia.tokyo-night"],
        ["Catppuccin","浅色/深色","温暖配色，社区驱动","catppuccin.catppuccin-vsc"],
        ["Winter is Coming","浅色/深色","《权游》主题","johnpapa.winteriscoming"],
        ["Material Icon Theme","图标","Material Design 风格图标","pkief.material-icon-theme"],
        ["vscode-icons","图标","最流行的图标主题","vscode-icons-team.vscode-icons"],
     ]},
]))

# Chapter 11: Keyboard Shortcuts
PART1.append(section("第11章：快捷键体系", "Chapter 11: Keyboard Shortcuts", "11"))
PART1.append(content("11.1 必学 30 个快捷键", [
    {"t":"table","x":0.5,"y":1.2,"w":12,"hd":["功能","快捷键","分类"],
     "rows":[
        ["命令面板","Ctrl+Shift+P","通用"],
        ["快速打开文件","Ctrl+P","导航"],
        ["切换侧边栏","Ctrl+B","视图"],
        ["切换终端","Ctrl+`","视图"],
        ["切换面板","Ctrl+J","视图"],
        ["新建文件","Ctrl+N","文件"],
        ["保存文件","Ctrl+S","文件"],
        ["关闭标签","Ctrl+W","文件"],
        ["查找","Ctrl+F","搜索"],
        ["全局搜索","Ctrl+Shift+F","搜索"],
        ["转到定义","F12","导航"],
        ["查找引用","Shift+F12","导航"],
        ["文件符号","Ctrl+Shift+O","导航"],
        ["全局符号","Ctrl+T","导航"],
        ["转到行","Ctrl+G","导航"],
        ["多光标","Alt+Click","编辑"],
        ["选中相同词","Ctrl+D","编辑"],
        ["选中所有相同","Ctrl+Shift+L","编辑"],
        ["格式化文档","Shift+Alt+F","编辑"],
        ["重命名符号","F2","重构"],
        ["注释切换","Ctrl+/","编辑"],
        ["折叠代码","Ctrl+Shift+[","编辑"],
        ["展开代码","Ctrl+Shift+]","编辑"],
        ["启动调试","F5","调试"],
        ["单步跳过","F10","调试"],
        ["单步进入","F11","调试"],
        ["断点切换","F9","调试"],
        ["禅模式","Ctrl+K Z","视图"],
        ["打开设置","Ctrl+,","设置"],
        ["源代码管理","Ctrl+Shift+G","Git"],
     ]},
]))

# Chapter 12: Remote Dev
PART1.append(section("第12章：远程开发", "Chapter 12: Remote Development", "12"))
PART1.append(content("12.1 SSH 远程开发配置", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3,"fs":12,
     "txt":"通过 Remote-SSH 扩展连接到远程服务器：\n\n🔗 工作原理\n   1. 在 code-server 中安装 Remote-SSH 扩展\n   2. 配置 SSH 连接信息\n   3. VS Code Server 自动部署到远程主机\n   4. 通过 SSH 隧道安全通信\n\n🔗 连接方式\n   • 密码认证\n   • SSH 密钥认证 (推荐)\n   • SSH 跳板机 (ProxyJump)\n\n🔗 优势\n   • 使用远程主机的计算资源\n   • 文件在远程，本地只做显示\n   • 扩展在远程执行\n   • 终端直接操作远程环境"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"// ~/.ssh/config\nHost dev-server\n  HostName 192.168.1.100\n  User developer\n  Port 22\n  IdentityFile ~/.ssh/id_rsa\n\nHost production\n  HostName prod.example.com\n  User deploy\n  IdentityFile ~/.ssh/prod_key\n  ProxyJump bastion\n\nHost bastion\n  HostName jump.example.com\n  User admin\n\n// code-server SSH 配置\n// Ctrl+Shift+P →\n//   Remote-SSH: Connect to Host\n\n// 或编辑 .ssh/config 后\n// 直接在 Remote Explorer 中选择",
     "ct":"SSH 配置示例"},
]))

PART1.append(content("12.2 Dev Containers 容器化开发", [
    {"t":"text","x":0.5,"y":1.1,"w":6,"h":3.5,"fs":12,
     "txt":"Dev Containers 是定义开发环境的标准化方式：\n\n📦 核心概念\n   • 使用 Docker 容器作为开发环境\n   • 通过 devcontainer.json 定义配置\n   • 团队成员获得完全一致的开发环境\n   • 新人加入：一键启动，零环境配置\n\n📦 配置内容\n   • Dockerfile 或 docker-compose.yml\n   • VS Code 扩展自动安装列表\n   • 编辑器设置自动应用\n   • 端口转发配置\n   • 环境变量预设\n   • 挂载卷配置\n\n📦 典型应用场景\n   • Python 项目：固定 Python 版本+依赖\n   • Node.js 项目：Node 版本+npm 包\n   • Go 项目：Go 版本+工具链\n   • 多语言项目：集成多个运行时"},
    {"t":"code","x":7,"y":1.1,"w":5.8,"h":5,
     "code":"// .devcontainer/devcontainer.json\n{\n  "name": "Go Dev Container",\n  "image": "mcr.microsoft.com/\n    devcontainers/go:1.21",\n  \n  "features": {\n    "ghcr.io/devcontainers/\n      features/docker-in-docker:2":\n      {}\n  },\n  \n  "customizations": {\n    "vscode": {\n      "extensions": [\n        "golang.Go",\n        "ms-azuretools.vscode-docker",\n        "github.copilot"\n      ],\n      "settings": {\n        "go.toolsManagement.autoUpdate":\n          true,\n        "go.lintTool": "golangci-lint"\n      }\n    }\n  },\n  \n  "forwardPorts": [8080, 3000],\n  "postCreateCommand":\n    "go mod download",\n  "remoteUser": "vscode"\n}",
     "ct":"devcontainer.json 配置"},
]))

print(f"Part 1: {len(PART1)} slides defined")

# Generate Part 1 JS
js_code = pptxgen_slide_js(PART1, "Code_Server_Teaching_Part1_Basics.pptx", 
    "code-server Full-Feature Teaching Guide", "Part 1: Basics & IDE Usage")
js_file = os.path.join(NODE, "_gen_pptx_part1.js")
with open(js_file, "w", encoding="utf-8") as f:
    f.write(js_code)
result = subprocess.run(["node", js_file], capture_output=True, text=True, cwd=NODE, timeout=180)
os.remove(js_file)
if "OK" in result.stdout:
    print(f"Part 1 generated: {len(PART1)} slides - OK")
else:
    print(f"Part 1 ERROR: {result.stderr[:300]}")

# =============================================
# PART 2: PLUGINS (~100 slides)
# =============================================
PART2 = []
PART2.append(title("code-server 全功能学习指南", "第二部分：插件生态与应用实战"))
PART2.append(title("code-server Full-Feature Learning Guide", "Part 2: Plugins Ecosystem"))

PART2.append(toc([
    {"n":"第13章：插件系统概述"},
    {"n":"第14章：必装插件 Top 25"},
    {"n":"第15章：前端开发插件集"},
    {"n":"第16章：后端开发插件集"},
    {"n":"第17章：Python 开发插件"},
    {"n":"第18章：JavaScript/TypeScript 插件"},
    {"n":"第19章：Go 开发插件"},
    {"n":"第20章：Rust 开发插件"},
    {"n":"第21章：Java/Kotlin 开发插件"},
    {"n":"第22章：C/C++ 开发插件"},
    {"n":"第23章：数据库插件"},
    {"n":"第24章：Docker/K8s 插件"},
    {"n":"第25章：AI 辅助编程插件"},
    {"n":"第26章：主题与美化插件"},
    {"n":"第27章：效率提升插件"},
]))

# Chapter 13: Plugin Overview
PART2.append(section("第13章：插件系统概述", "Chapter 13: Plugin System Overview", "13"))
PART2.append(content("13.1 VS Code 扩展市场与安装方式", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":2.5,"fs":12,
     "txt":"code-server 完全兼容 VS Code 扩展生态系统：\n\n📦 扩展来源\n\n🔹 VS Code Marketplace (最主要)\n   通过 Open VSX Registry 代理访问\n   https://open-vsx.org\n\n🔹 手动安装 .vsix 文件\n   Extensions: Install from VSIX...\n   用于离线环境或内部定制扩展\n\n🔹 扩展配置文件\n   .vscode/extensions.json\n   推荐给团队成员的扩展列表\n\n🔹 扩展管理\n   • 启用/禁用扩展\n   • 自动更新\n   • 工作区级别 vs 全局级别"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"// .vscode/extensions.json\n{\n  "recommendations": [\n    "esbenp.prettier-vscode",\n    "dbaeumer.vscode-eslint",\n    "golang.go",\n    "ms-python.python",\n    "rust-lang.rust-analyzer",\n    "redhat.java",\n    "ms-vscode.cpptools",\n    "github.copilot",\n    "github.copilot-chat",\n    "eamodio.gitlens",\n    "ms-azuretools.vscode-docker",\n    "ms-kubernetes-tools.vscode-\n      kubernetes-tools"\n  ],\n  "unwantedRecommendations": [\n    // 避免推荐的扩展\n    "hookyqr.beautify",\n    "coenraads.bracket-pair-\n      colorizer-2"\n  ]\n}",
     "ct":"extensions.json 推荐配置"},
]))

# Chapter 14: Top Plugins  
PART2.append(section("第14章：必装插件 Top 25", "Chapter 14: Essential Plugins Top 25", "14"))
PART2.append(content("14.1 效率必装插件 Top 12", [
    {"t":"table","x":0.5,"y":1.2,"w":12,"hd":["#","插件名","用途","扩展 ID"],
     "rows":[
        ["1","Prettier","代码格式化","esbenp.prettier-vscode"],
        ["2","ESLint","JS/TS 代码检查","dbaeumer.vscode-eslint"],
        ["3","GitLens","Git 增强工具","eamodio.gitlens"],
        ["4","GitHub Copilot","AI 代码补全","github.copilot"],
        ["5","GitHub Copilot Chat","AI 对话助手","github.copilot-chat"],
        ["6","Docker","Docker 管理","ms-azuretools.vscode-docker"],
        ["7","Kubernetes","K8s 资源管理","ms-kubernetes-tools.vscode-kubernetes-tools"],
        ["8","Remote-SSH","SSH 远程开发","ms-vscode-remote.remote-ssh"],
        ["9","Live Share","实时协作编辑","ms-vsliveshare.vsliveshare"],
        ["10","Path Intellisense","路径自动补全","christian-kohler.path-intellisense"],
        ["11","Auto Rename Tag","自动重命名标签","formulahendry.auto-rename-tag"],
        ["12","Error Lens","内联错误显示","usernamehw.errorlens"],
     ]},
]))

PART2.append(content("14.2 生产力增强插件 Top 13", [
    {"t":"table","x":0.5,"y":1.2,"w":12,"hd":["#","插件名","用途","扩展 ID"],
     "rows":[
        ["13","Better Comments","注释高亮","aaron-bond.better-comments"],
        ["14","Todo Tree","TODO 树状视图","gruntfuggly.todo-tree"],
        ["15","Code Spell Checker","拼写检查","streetsidesoftware.code-spell-checker"],
        ["16","Import Cost","显示导入大小","wix.vscode-import-cost"],
        ["17","REST Client","API 测试工具","humao.rest-client"],
        ["18","Thunder Client","图形化 API 客户端","rangav.vscode-thunder-client"],
        ["19","Markdown All in One","Markdown 编辑","yzhang.markdown-all-in-one"],
        ["20","Project Manager","项目管理","alefragnani.project-manager"],
        ["21","Bookmarks","代码书签","alefragnani.bookmarks"],
        ["22","vscode-pdf","PDF 查看器","tomoki1207.pdf"],
        ["23","Live Server","本地开发服务器","ritwickdey.liveserver"],
        ["24","indent-rainbow","缩进彩虹线","oderwat.indent-rainbow"],
        ["25","Peacock","工作区颜色区分","johnpapa.vscode-peacock"],
     ]},
]))

# Chapter 15: Frontend
PART2.append(section("第15章：前端开发插件集", "Chapter 15: Frontend Development Plugins", "15"))
PART2.append(content("15.1 React/Vue/Angular 开发插件", [
    {"t":"table","x":0.5,"y":1.2,"w":12,"hd":["框架","推荐插件","扩展 ID"],
     "rows":[
        ["React","ES7+ React/Redux/React-Native snippets","dsznajder.es7-react-js-snippets"],
        ["React","React Native Tools","msjsdiag.vscode-react-native"],
        ["React","Styled Components","styled-components.vscode-styled-components"],
        ["React","Tailwind CSS IntelliSense","bradlc.vscode-tailwindcss"],
        ["Vue","Vue - Official (Volar)","vue.volar"],
        ["Vue","Vue VSCode Snippets","sdras.vue-vscode-snippets"],
        ["Vue","Vue Peek","dariofuzinato.vue-peek"],
        ["Angular","Angular Language Service","angular.ng-template"],
        ["Angular","Angular Snippets","johnpapa.angular2"],
        ["Angular","Nx Console","nrwl.angular-console"],
        ["通用","HTML CSS Support","ecmel.vscode-html-css"],
        ["通用","CSS Peek","pranaygp.vscode-css-peek"],
        ["通用","Sass","syler.sass-indented"],
        ["通用","PostCSS Language Support","csstools.postcss"],
     ]},
]))

# More part2 content continued...
# Adding key chapters
PART2.append(content("17.1 Python 开发完整插件集", [
    {"t":"text","x":0.5,"y":1.1,"w":5,"h":2.5,"fs":12,
     "txt":"Python 是 code-server 上最流行的语言之一，\n需要以下插件构建完整开发环境：\n\n🐍 Python (ms-python.python)\n   核心插件，提供 IntelliSense、调试、\n   linting、测试支持\n\n🐍 Pylance (ms-python.vscode-pylance)\n   高性能 Python 语言服务器\n   快速准确的类型检查和补全\n\n🐍 Python Debugger (ms-python.debugpy)\n   新一代 Python 调试器\n   支持远程调试\n\n🐍 Black Formatter\n   自动代码格式化 (PEP 8)\n\n🐍 isort\n   自动 import 排序"},
    {"t":"code","x":6,"y":1.1,"w":6.8,"h":5,
     "code":"// Python 项目 settings.json\n{\n  "python.defaultInterpreterPath":\n    "./venv/bin/python",\n  "python.analysis.typeCheckingMode":\n    "strict",\n  "python.linting.enabled": true,\n  "python.linting.pylintEnabled": true,\n  "python.linting.flake8Enabled": true,\n  "python.formatting.provider":\n    "black",\n  "python.formatting.blackArgs": [\n    "--line-length", "88"\n  ],\n  "[python]": {\n    "editor.formatOnSave": true,\n    "editor.codeActionsOnSave": {\n      "source.organizeImports": true\n    },\n    "editor.defaultFormatter":\n      "ms-python.black-formatter"\n  },\n  "python.testing.pytestEnabled": true,\n  "python.testing.unittestEnabled": false,\n  "python.testing.pytestArgs": [\n    "tests"\n  ]\n}",
     "ct":"Python 项目 settings.json"},
]))

PART2.append(content("19.1 Go 语言开发完整插件链", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3,"fs":12,
     "txt":"Go 是云原生和企业级后端开发的首选语言。\n以下为核心 Go 开发插件：\n\n🔷 Go (golang.go) - 官方 Go 扩展\n   • IntelliSense 和代码补全\n   • 代码导航和重构\n   • 调试支持 (Delve)\n   • 测试运行和覆盖率\n   • Go Modules 支持\n\n🔷 工具链说明\n   gopls：Go 语言服务器 (LSP)\n   dlv：调试器\n   staticcheck：静态分析\n   golangci-lint：代码检查\n\n🔷 关键设置\n   go.toolsManagement.autoUpdate: true\n   go.lintTool: golangci-lint\n   go.useLanguageServer: true"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"// Go 项目 settings.json\n{\n  "go.toolsManagement.autoUpdate":\n    true,\n  "go.lintTool": "golangci-lint",\n  "go.lintOnSave": "workspace",\n  "go.formatTool": "goimports",\n  "go.useLanguageServer": true,\n  "go.testFlags": ["-v", "-race"],\n  "go.coverOnSave": true,\n  "go.coverageDecorator": {{\n    "type": "gutter"\n  }},\n  "go.buildOnSave": "workspace",\n  "go.vetOnSave": "workspace",\n  \n  "[go]": {{\n    "editor.formatOnSave": true,\n    "editor.codeActionsOnSave": {{\n      "source.organizeImports":\n        true\n    }}\n  }},\n  \n  "gopls": {{\n    "ui.semanticTokens": true,\n    "ui.completion.usePlaceholders":\n      true,\n    "build.buildFlags": ["-tags",\n      "integration"]\n  }}\n}",
     "ct":"Go 项目 settings.json"},
]))

PART2.append(content("20.1 Rust 开发插件链", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":2.5,"fs":12,
     "txt":"Rust 在系统编程和安全关键领域越来越流行：\n\n🦀 rust-analyzer (rust-lang.rust-analyzer)\n   官方推荐 Rust 语言服务器\n   • 实时类型检查和错误提示\n   • 代码补全和内联提示\n   • 自动导入和代码生成\n   • 宏展开和内联视图\n\n🦀 辅助插件\n   • CodeLLDB：调试支持\n   • Even Better TOML：TOML 支持\n   • crates：Cargo.toml 依赖管理\n   • Dependi：依赖版本检查\n\n🦀 关键命令\n   > Rust Analyzer: Restart Server\n   > Rust Analyzer: Expand Macro"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4.5,
     "code":"// Rust 项目 settings.json\n{\n  "rust-analyzer.checkOnSave":\n    {{ "command": "clippy" }},\n  "rust-analyzer.cargo.features":\n    "all",\n  "rust-analyzer.procMacro.enable":\n    true,\n  "rust-analyzer.inlayHints": {{\n    "bindingModeHints.enable":\n      false,\n    "chainingHints.enable": true,\n    "closingBraceHints.enable":\n      true,\n    "parameterHints.enable": true,\n    "typeHints.enable": true\n  }},\n  \n  "[rust]": {{\n    "editor.formatOnSave": true,\n    "editor.defaultFormatter":\n      "rust-lang.rust-analyzer"\n  }},\n  \n  // 调试配置\n  "lldb.executable": "/usr/bin/lldb",\n  "lldb.launch.expressions":\n    "native"\n}",
     "ct":"Rust 项目 settings.json"},
]))

# Chapter 24: Docker/K8s
PART2.append(section("第24章：Docker 与 Kubernetes 插件", "Chapter 24: Docker & K8s Plugins", "24"))
PART2.append(content("24.1 Docker 开发完整工作流", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3,"fs":12,
     "txt":"Docker 插件 (ms-azuretools.vscode-docker)\n\n🐳 核心功能\n   • Dockerfile 语法高亮和智能提示\n   • docker-compose.yml 自动补全\n   • 镜像和容器管理面板\n   • 容器日志查看\n   • 一键构建/运行/停止\n   • 容器内文件浏览\n   • Docker Hub 镜像搜索\n\n🐳 操作面板\n   • IMAGES：镜像列表与管理\n   • CONTAINERS：容器运行状态\n   • REGISTRIES：镜像仓库连接\n   • NETWORKS：网络管理\n   • VOLUMES：数据卷管理"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":5,
     "code":"# Dockerfile 最佳实践模板\nFROM node:20-slim AS builder\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci --only=production\nCOPY . .\nRUN npm run build\n\nFROM node:20-alpine\nWORKDIR /app\nRUN addgroup -g 1001 -S nodejs && \\\n    adduser -S appuser -u 1001\nCOPY --from=builder \\\n  /app/dist ./dist\nCOPY --from=builder \\\n  /app/node_modules ./node_modules\nUSER appuser\nEXPOSE 3000\nHEALTHCHECK --interval=30s \\\n  CMD wget -qO- \\\n  http://localhost:3000/health || exit 1\nCMD ["node", "dist/index.js"]",
     "ct":"生产级 Dockerfile 模板"},
]))

PART2.append(content("24.2 Kubernetes 开发工具链", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":2.5,"fs":12,
     "txt":"K8s 插件 (ms-kubernetes-tools...)\n\n☸️ 核心功能\n   • YAML 语法高亮和验证\n   • Helm Chart 智能提示\n   • 集群资源浏览器\n   • 一键部署/删除资源\n   • Pod 日志流式查看\n   • 终端到 Pod (kubectl exec)\n   • 资源使用率查看\n\n☸️ 辅助工具\n   • Kubernetes Snippets\n   • Helm Intellisense\n   • k8s-snippets\n   • Kubernetes Support\n\n☸️ 必备 CLI\n   • kubectl\n   • helm\n   • k9s (终端 UI)\n   • stern (多 Pod 日志)"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":5,
     "code":"# code-server 上的 K8s 工作流\n\n# 1. 终端中查看集群\nkubectl get nodes\nkubectl get pods -A --sort-by=.status.startTime\nkubectl top nodes\nkubectl top pods -A\n\n# 2. 部署应用\nkubectl apply -f deployment.yaml\nkubectl rollout status deploy/app\nkubectl logs -f deploy/app\n\n# 3. 调试 Pod\nkubectl exec -it pod-name -- /bin/sh\nkubectl describe pod pod-name\nkubectl get events --sort-by='.lastTimestamp'\n\n# 4. 端口转发\nkubectl port-forward svc/app 8080:80\n\n# 5. Helm 部署\nhelm upgrade --install app ./chart\nhelm list\nhelm history app",
     "ct":"K8s 常用命令工作流"},
]))

# Chapter 25: AI
PART2.append(section("第25章：AI 辅助编程插件", "Chapter 25: AI-Assisted Coding Plugins", "25"))
PART2.append(content("25.1 GitHub Copilot 完全配置指南", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3.5,"fs":12,
     "txt":"GitHub Copilot 是 AI 辅助编程的标杆工具：\n\n🤖 核心功能\n\n📝 代码补全\n   • 根据上下文自动建议代码\n   • 支持多行补全\n   • 提供多个备选方案\n   • 适配项目代码风格\n\n💬 Copilot Chat (Ctrl+Shift+I)\n   • 自然语言描述需求生成代码\n   • 解释代码功能\n   • 重构建议\n   • 生成测试用例\n   • 修复 Bug 建议\n\n🎯 代理模式 (Agent Mode)\n   • 自动查找和读取相关文件\n   • 跨文件分析和修改\n   • 终端命令建议和执行"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":3.5,
     "code":"// Copilot 配置\n{\n  "github.copilot.enable": {\n    "*": true,\n    "plaintext": false,\n    "markdown": true,\n    "scminput": false\n  },\n  "github.copilot.chat.localeOverride":\n    "en",\n  "github.copilot.chat.codeGeneration":\n    {{ "useInstructionFiles": true }},\n  "github.copilot.chat.followUps":\n    "always",\n  "github.copilot.chat.scopeSelection":\n    true,\n  "github.copilot.chat.terminalChatLocation":\n    "panel"\n}",
     "ct":"GitHub Copilot 配置"},
    {"t":"tip","x":6.5,"y":5.0,"w":6,"h":1.2,
     "txt":"使用 .github/copilot-instructions.md\n文件定义项目级别的 AI 指令，\nCopilot 会自动读取并遵循项目规范。",
     "tp":"tip"},
]))

# =============================================
# PART 3: ENTERPRISE (~100 slides)
# =============================================
PART3 = []
PART3.append(title("code-server 全功能学习指南", "第三部分：多语言企业级开发实战"))
PART3.append(title("code-server Full-Feature Learning Guide", "Part 3: Enterprise Multi-Language Dev"))

PART3.append(toc([
    {"n":"第28章：Go 企业级开发全流程"},
    {"n":"第29章：Rust 企业级开发全流程"},
    {"n":"第30章：Java 企业级开发全流程"},
    {"n":"第31章：C/C++ 企业级开发全流程"},
    {"n":"第32章：Scala 企业级开发全流程"},
    {"n":"第33章：Kotlin 与 Android 开发"},
    {"n":"第34章：Python 企业级数据科学"},
    {"n":"第35章：多语言 Monorepo 管理"},
    {"n":"第36章：CI/CD 集成"},
    {"n":"第37章：安全最佳实践"},
    {"n":"第38章：性能优化与监控"},
    {"n":"第39章：code-server 集群运维"},
]))

PART3.append(section("第28章：Go 企业级开发全流程", "Chapter 28: Go Enterprise Development", "28"))
PART3.append(content("28.1 Go 项目结构最佳实践", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3.5,"fs":12,
     "txt":"Go 企业级项目推荐使用标准项目布局：\n\n📁 标准目录结构\n\ncmd/         应用程序入口\n  server/    HTTP/gRPC 服务\n  worker/    后台任务\n  cli/      CLI 工具\n\ninternal/    私有代码 (不可外部引用)\n  handler/   HTTP 处理器\n  service/   业务逻辑层\n  repository/ 数据访问层\n  model/     领域模型\n\npkg/          可复用的公共库\n\napi/          API 定义 (OpenAPI/Proto)\n\nconfigs/      配置文件\n\ndeployments/  部署配置 (K8s/Docker)\n\ntest/         外部测试数据"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":5,
     "code":"myproject/\n├── cmd/\n│   ├── server/\n│   │   └── main.go\n│   └── worker/\n│       └── main.go\n├── internal/\n│   ├── handler/\n│   │   ├── user_handler.go\n│   │   └── user_handler_test.go\n│   ├── service/\n│   │   ├── user_service.go\n│   │   └── user_service_test.go\n│   ├── repository/\n│   │   ├── user_repo.go\n│   │   └── user_repo_test.go\n│   └── model/\n│       └── user.go\n├── pkg/\n│   └── validator/\n├── api/\n│   └── openapi.yaml\n├── configs/\n│   └── config.yaml\n├── deployments/\n│   ├── Dockerfile\n│   └── k8s/\n├── go.mod\n├── go.sum\n├── Makefile\n└── README.md",
     "ct":"Go 企业级项目结构"},
]))

PART3.append(content("28.2 Go 微服务开发实战", [
    {"t":"code","x":0.5,"y":1.1,"w":6,"h":5.5,
     "code":"// internal/handler/user_handler.go\npackage handler\n\nimport (\n    "net/http"\n    "github.com/gin-gonic/gin"\n    "myproject/internal/model"\n    "myproject/internal/service"\n)\n\ntype UserHandler struct {{\n    svc *service.UserService\n}}\n\nfunc NewUserHandler(svc *service.UserService) *UserHandler {{\n    return &UserHandler{{svc: svc}}\n}}\n\n// GetUser 获取用户信息\n// @Summary 获取用户\n// @Tags 用户管理\n// @Param id path string true "用户ID"\n// @Success 200 {{object}} model.User\n// @Router /api/v1/users/{{id}} [get]\nfunc (h *UserHandler) GetUser(c *gin.Context) {{\n    id := c.Param("id")\n    user, err := h.svc.GetUser(c.Request.Context(), id)\n    if err != nil {{\n        c.JSON(http.StatusNotFound,\n          gin.H{{"error": err.Error()}})\n        return\n    }}\n    c.JSON(http.StatusOK, user)\n}}\n\nfunc (h *UserHandler) Register(router *gin.RouterGroup) {{\n    users := router.Group("/users")\n    {{\n        users.GET("/:id", h.GetUser)\n        users.POST("", h.CreateUser)\n        users.PUT("/:id", h.UpdateUser)\n        users.DELETE("/:id", h.DeleteUser)\n    }}\n}}",
     "ct":"Go HTTP Handler 示例"},
    {"t":"code","x":7,"y":1.1,"w":5.8,"h":5.5,
     "code":"// internal/service/user_service.go\npackage service\n\nimport (\n    "context"\n    "fmt"\n    "myproject/internal/model"\n    "myproject/internal/repository"\n)\n\ntype UserService struct {{\n    repo *repository.UserRepository\n}}\n\nfunc NewUserService(repo *repository.UserRepository) *UserService {{\n    return &UserService{{repo: repo}}\n}}\n\nfunc (s *UserService) GetUser(ctx context.Context, id string) (*model.User, error) {{\n    user, err := s.repo.FindByID(ctx, id)\n    if err != nil {{\n        return nil, fmt.Errorf("failed to get user %s: %w", id, err)\n    }}\n    if user == nil {{\n        return nil, fmt.Errorf("user %s not found", id)\n    }}\n    return user, nil\n}}\n\nfunc (s *UserService) CreateUser(ctx context.Context, req *model.CreateUserRequest) (*model.User, error) {{\n    // 验证输入\n    if err := req.Validate(); err != nil {{\n        return nil, fmt.Errorf("invalid request: %w", err)\n    }}\n    user := req.ToUser()\n    if err := s.repo.Create(ctx, user); err != nil {{\n        return nil, fmt.Errorf("failed to create user: %w", err)\n    }}\n    return user, nil\n}}",
     "ct":"Go Service 层示例"},
]))

PART3.append(section("第29章：Rust 企业级开发全流程", "Chapter 29: Rust Enterprise Development", "29"))
PART3.append(content("29.1 Rust Web 服务开发 (Axum 框架)", [
    {"t":"code","x":0.5,"y":1.1,"w":6,"h":5.5,
     "code":"// src/main.rs - Axum Web 服务\nuse axum::{{\n    extract::{{Path, State}},\n    http::StatusCode,\n    routing::{{get, post}},\n    Json, Router,\n}};\nuse serde::{{Deserialize, Serialize}};\nuse sqlx::PgPool;\nuse std::sync::Arc;\n\n#[derive(Debug, Serialize, Deserialize)]\npub struct User {{\n    pub id: String,\n    pub name: String,\n    pub email: String,\n    pub role: String,\n}}\n\npub struct AppState {{\n    pub db: PgPool,\n}}\n\n#[tokio::main]\nasync fn main() -> anyhow::Result<()> {{\n    let pool = PgPool::connect(\n      &std::env::var("DATABASE_URL")?\n    ).await?;\n    \n    let state = Arc::new(AppState {{ db: pool }});\n    \n    let app = Router::new()\n        .route("/api/v1/users", get(list_users))\n        .route("/api/v1/users/:id", get(get_user))\n        .route("/api/v1/users", post(create_user))\n        .with_state(state);\n    \n    let listener = tokio::net::TcpListener::bind(\n      "0.0.0.0:8080"\n    ).await?;\n    axum::serve(listener, app).await?;\n    Ok(())\n}}",
     "ct":"Axum Web 服务入口"},
    {"t":"code","x":7,"y":1.1,"w":5.8,"h":5.5,
     "code":"// src/handlers.rs\nasync fn get_user(\n    Path(user_id): Path<String>,\n    State(state): State<Arc<AppState>>,\n) -> Result<Json<User>, StatusCode> {{\n    let user = sqlx::query_as!(\n        User,\n        "SELECT id, name, email, role\n         FROM users WHERE id = $1",\n        user_id\n    )\n    .fetch_optional(&state.db)\n    .await\n    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;\n    \n    user.map(Json).ok_or(StatusCode::NOT_FOUND)\n}}\n\nasync fn create_user(\n    State(state): State<Arc<AppState>>,\n    Json(req): Json<CreateUserRequest>,\n) -> Result<(StatusCode, Json<User>), StatusCode> {{\n    let user = sqlx::query_as!(\n        User,\n        "INSERT INTO users (id, name, email, role)\n         VALUES ($1, $2, $3, $4)\n         RETURNING id, name, email, role",\n        uuid::Uuid::new_v4().to_string(),\n        req.name, req.email, req.role\n    )\n    .fetch_one(&state.db)\n    .await\n    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;\n    \n    Ok((StatusCode::CREATED, Json(user)))\n}}",
     "ct":"Axum Handler 实现"},
]))

PART3.append(section("第30章：Java 企业级开发全流程", "Chapter 30: Java Enterprise Development", "30"))
PART3.append(content("30.1 Spring Boot 微服务开发", [
    {"t":"code","x":0.5,"y":1.1,"w":6.3,"h":5.5,
     "code":"// UserController.java\npackage com.example.demo.controller;\n\nimport com.example.demo.model.User;\nimport com.example.demo.service.UserService;\nimport jakarta.validation.Valid;\nimport lombok.RequiredArgsConstructor;\nimport org.springframework.http.HttpStatus;\nimport org.springframework.web.bind.annotation.*;\n\nimport java.util.List;\n\n@RestController\n@RequestMapping("/api/v1/users")\n@RequiredArgsConstructor\npublic class UserController {{\n    \n    private final UserService userService;\n    \n    @GetMapping\n    public List<User> listUsers() {{\n        return userService.findAll();\n    }}\n    \n    @GetMapping("/{{id}}")\n    public User getUser(@PathVariable String id) {{\n        return userService.findById(id)\n            .orElseThrow(() -> \n                new UserNotFoundException(id));\n    }}\n    \n    @PostMapping\n    @ResponseStatus(HttpStatus.CREATED)\n    public User createUser(\n        @Valid @RequestBody CreateUserRequest req\n    ) {{\n        return userService.create(req);\n    }}\n    \n    @PutMapping("/{{id}}")\n    public User updateUser(\n        @PathVariable String id,\n        @Valid @RequestBody UpdateUserRequest req\n    ) {{\n        return userService.update(id, req);\n    }}\n    \n    @DeleteMapping("/{{id}}")\n    @ResponseStatus(HttpStatus.NO_CONTENT)\n    public void deleteUser(@PathVariable String id) {{\n        userService.delete(id);\n    }}\n}}",
     "ct":"Spring Boot Controller"},
    {"t":"code","x":7.3,"y":1.1,"w":5.5,"h":5.5,
     "code":"// application.yml\nspring:\n  application:\n    name: user-service\n  datasource:\n    url: jdbc:postgresql://localhost:5432/users\n    username: ${{DB_USER}}\n    password: ${{DB_PASSWORD}}\n    hikari:\n      maximum-pool-size: 10\n      minimum-idle: 5\n  jpa:\n    hibernate:\n      ddl-auto: validate\n    properties:\n      hibernate:\n        dialect: org.hibernate.dialect.\n          PostgreSQLDialect\n        format_sql: true\n  \nserver:\n  port: 8080\n  \nlogging:\n  level:\n    root: INFO\n    com.example: DEBUG\n    org.hibernate.SQL: DEBUG\n\nmanagement:\n  endpoints:\n    web:\n      exposure:\n        include: health,metrics,prometheus\n  metrics:\n    export:\n      prometheus:\n        enabled: true",
     "ct":"Spring Boot 配置"},
]))

# Chapter 34: Python Data Science
PART3.append(section("第34章：Python 企业级数据科学", "Chapter 34: Python Data Science", "34"))
PART3.append(content("34.1 Jupyter Notebook 在 code-server 中的使用", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3.5,"fs":12,
     "txt":"code-server 完美支持 Jupyter Notebook 工作流：\n\n📓 Jupyter 扩展安装\n   ms-toolsai.jupyter (核心)\n   ms-toolsai.jupyter-renderers\n   ms-python.python\n\n📓 Notebook 功能\n   • 在 code-server 中直接创建/编辑 .ipynb\n   • 单元格执行和内联输出\n   • 变量查看器和数据查看器\n   • 交互式图表 (matplotlib/plotly)\n   • Markdown 单元格支持\n\n📓 数据科学生态\n   • numpy, pandas, scipy\n   • matplotlib, seaborn, plotly\n   • scikit-learn, xgboost, lightgbm\n   • pytorch, tensorflow (CPU 推理)\n   • jupyter, ipywidgets"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":5.5,
     "code":"// Python 数据科学 settings.json\n{\n  "jupyter.interactiveWindowMode":\n    "perFile",\n  "jupyter.askForKernelRestart":\n    false,\n  "jupyter.enableNativeInteractiveWindow":\n    true,\n  "jupyter.widgetScriptSources": [\n    "jsdelivr.com", "unpkg.com"\n  ],\n  \n  "python.analysis.typeCheckingMode":\n    "basic",\n  "python.linting.enabled": true,\n  "python.linting.pylintEnabled": true,\n  \n  // 数据科学常用设置\n  "notebook.output.textLineLimit":\n    100,\n  "notebook.output.scrolling": true,\n  "notebook.lineNumbers": "on",\n  "notebook.cellToolbarLocation": {{\n    "default": "right",\n    "jupyter-notebook": "left"\n  }}\n}",
     "ct":"Jupyter settings.json"},
]))

# Chapter 36: CI/CD
PART3.append(section("第36章：CI/CD 集成", "Chapter 36: CI/CD Pipeline Integration", "36"))
PART3.append(content("36.1 GitHub Actions CI/CD 完整配置", [
    {"t":"code","x":0.5,"y":1.1,"w":6,"h":5.5,
     "code":"# .github/workflows/ci.yml\nname: CI/CD Pipeline\n\non:\n  push:\n    branches: [main, develop]\n  pull_request:\n    branches: [main]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        service: [api, worker, web]\n    steps:\n    - uses: actions/checkout@v4\n    \n    - name: Setup Node.js\n      uses: actions/setup-node@v4\n      with:\n        node-version: '20'\n        cache: 'npm'\n        cache-dependency-path: |\n          ${{ matrix.service }}/package-lock.json\n    \n    - name: Install Dependencies\n      working-directory: ${{ matrix.service }}\n      run: npm ci\n    \n    - name: Lint\n      working-directory: ${{ matrix.service }}\n      run: npm run lint\n    \n    - name: Unit Tests\n      working-directory: ${{ matrix.service }}\n      run: npm test -- --coverage\n    \n    - name: Build\n      working-directory: ${{ matrix.service }}\n      run: npm run build",
     "ct":"GitHub Actions CI 配置"},
    {"t":"code","x":7,"y":1.1,"w":5.8,"h":5.5,
     "code":"  deploy:\n    needs: test\n    if: github.ref == 'refs/heads/main'\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v4\n    \n    - name: Build Docker Image\n      run: |\n        docker build \\\n          -t ${{ secrets.REGISTRY }}/api:${{ github.sha }} \\\n          -f api/Dockerfile .\n    \n    - name: Push to Registry\n      run: |\n        docker push \\\n          ${{ secrets.REGISTRY }}/api:${{ github.sha }}\n    \n    - name: Deploy to Kubernetes\n      uses: azure/k8s-deploy@v4\n      with:\n        namespace: production\n        manifests: |\n          deployments/k8s/deployment.yaml\n          deployments/k8s/service.yaml\n        images: |\n          ${{ secrets.REGISTRY }}/api:${{ github.sha }}\n    \n    - name: Verify Deployment\n      run: |\n        kubectl rollout status \\\n          deployment/api -n production\n        kubectl get pods -n production",
     "ct":"GitHub Actions CD 部署"},
]))

# Chapter 39: Ops
PART3.append(section("第39章：code-server 集群运维", "Chapter 39: code-server Cluster Operations", "39"))
PART3.append(content("39.1 集群运维最佳实践", [
    {"t":"text","x":0.5,"y":1.1,"w":5.5,"h":3,"fs":12,
     "txt":"企业级 code-server 集群运维要点：\n\n🔄 资源管理\n   • 合理设置 CPU/Memory Limits\n   • 配置 HPA 自动伸缩\n   • 设置 Pod Disruption Budget\n   • 使用 Node Affinity 隔离工作负载\n\n📊 监控体系\n   • Prometheus + Grafana 监控\n   • 采集 Pod CPU/内存/网络指标\n   • 配置告警规则 (AlertManager)\n   • 集成日志收集 (Loki/ELK)\n\n🔐 安全运维\n   • 定期更新镜像版本\n   • 网络策略限制访问\n   • Secret 加密存储\n   • RBAC 权限最小化"},
    {"t":"code","x":6.5,"y":1.1,"w":6.3,"h":4,
     "code":"# code-server 运维常用命令\n\n# 查看 Pod 状态\nkubectl get pods -n ai-platform \\\n  -l app=code-server --sort-by=.status.startTime\n\n# 查看资源使用\nkubectl top pods -n ai-platform -l app=code-server\n\n# 查看日志\nkubectl logs -f -n ai-platform \\\n  deploy/code-server --tail=100\n\n# 进入 Pod 排查\nkubectl exec -it -n ai-platform \\\n  deploy/code-server -- /bin/bash\n\n# 滚动重启\nkubectl rollout restart -n ai-platform \\\n  deploy/code-server\n\n# 查看 HPA 状态\nkubectl get hpa -n ai-platform\n\n# 查看事件\nkubectl get events -n ai-platform \\\n  --sort-by='.lastTimestamp' | tail -20",
     "ct":"集群运维命令"},
]))

# Print and generate remaining parts
for part_name, slides, filename in [
    ("Part 2", PART2, "Code_Server_Teaching_Part2_Plugins.pptx"),
    ("Part 3", PART3, "Code_Server_Teaching_Part3_Enterprise.pptx"),
]:
    print(f"{part_name}: {len(slides)} slides defined")
    js_code = pptxgen_slide_js(slides, filename, 
        "code-server Full-Feature Teaching Guide", f"{part_name}")
    js_file = os.path.join(NODE, f"_gen_pptx_{part_name.replace(' ','_').lower()}.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write(js_code)
    result = subprocess.run(["node", js_file], capture_output=True, text=True, cwd=NODE, timeout=180)
    os.remove(js_file)
    if "OK" in result.stdout:
        print(f"{part_name} generated: {len(slides)} slides - OK")
    else:
        print(f"{part_name} ERROR: {result.stderr[:300]}")

print(f"\nTotal: {len(PART1)+len(PART2)+len(PART3)} slides across 3 files")
print("Done!")