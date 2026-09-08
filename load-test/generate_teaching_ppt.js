const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

// ===== THEME =====
const DARK_BG = "0F172A";
const CARD_BG = "1E293B";
const ACCENT = "3B82F6";
const ACCENT2 = "8B5CF6";
const GREEN = "22C55E";
const RED = "EF4444";
const YELLOW = "F59E0B";
const WHITE = "F8FAFC";
const GRAY = "94A3B8";
const CODE_BG = "0D1117";

pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";

const titleOpts = { fontSize: 36, color: WHITE, bold: true, fontFace: "Arial" };
const subtitleOpts = { fontSize: 18, color: GRAY, fontFace: "Arial" };
const bodyOpts = { fontSize: 14, color: WHITE, fontFace: "Arial" };
const smallOpts = { fontSize: 12, color: GRAY, fontFace: "Arial" };
const metricBig = { fontSize: 44, color: ACCENT, bold: true, fontFace: "Arial" };
const metricLabel = { fontSize: 13, color: GRAY, fontFace: "Arial" };
const codeOpts = { fontSize: 10, color: "E6EDF3", fontFace: "Consolas" };

function addSlide(title) {
  const slide = pptx.addSlide();
  slide.background = { color: DARK_BG };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.06, fill: { color: ACCENT } });
  slide.addText(title, { x: 0.5, y: 0.2, w: 12, h: 0.6, ...titleOpts, fontSize: 26 });
  slide.addText("code-server \u5B9E\u6218\u90E8\u7F72\u6307\u5357 | K8s Cluster | June 2026", { x: 0.5, y: 7.05, w: 12, h: 0.35, ...smallOpts });
  return slide;
}

function addCard(slide, x, y, w, h, color) {
  slide.addShape(pptx.ShapeType.rect, { x, y, w, h, fill: { color: color || CARD_BG }, rectRadius: 0.08 });
}

function addMetricCard(slide, x, y, w, h, value, label, color) {
  addCard(slide, x, y, w, h);
  slide.addText(value, { x, y: y + 0.1, w, h: 0.65, align: "center", ...metricBig, color: color || ACCENT, fontSize: 38 });
  slide.addText(label, { x, y: y + 0.8, w, h: 0.45, align: "center", ...metricLabel });
}

function addCodeBlock(slide, x, y, w, h, code) {
  addCard(slide, x, y, w, h, CODE_BG);
  slide.addText(code, { x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2, ...codeOpts, fontSize: 9, lineSpacingMultiple: 1.1 });
}

// ===== SLIDE 1: TITLE =====
{
  const slide = pptx.addSlide();
  slide.background = { color: DARK_BG };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.1, fill: { color: ACCENT } });
  slide.addText("code-server", { x: 1, y: 1.2, w: 11, h: 1.2, fontSize: 56, color: WHITE, bold: true, fontFace: "Arial" });
  slide.addText("\u5B9E\u6218\u90E8\u7F72\u6307\u5357", { x: 1, y: 2.3, w: 11, h: 0.8, fontSize: 32, color: ACCENT, fontFace: "Arial" });
  slide.addShape(pptx.ShapeType.rect, { x: 1, y: 3.3, w: 2.5, h: 0.05, fill: { color: ACCENT2 } });
  slide.addText("\u57FA\u4E8E Kubernetes \u7684\u4F01\u4E1A\u7EA7\u6D4F\u89C8\u5668 IDE \u90E8\u7F72\u4E0E\u8FD0\u7EF4", { x: 1, y: 3.7, w: 11, h: 0.6, fontSize: 18, color: GRAY, fontFace: "Arial" });
  slide.addText("2-Node K8s Cluster | 20 Pods | 2,000 \u5E76\u53D1\u7528\u6237 | 0% \u670D\u52A1\u5931\u8D25\u7387", { x: 1, y: 4.4, w: 11, h: 0.5, fontSize: 15, color: GREEN, fontFace: "Arial" });
  slide.addText("June 14, 2026", { x: 1, y: 5.2, w: 11, h: 0.4, fontSize: 13, color: GRAY, fontFace: "Arial" });
}

// ===== SLIDE 2: WHAT IS CODE-SERVER =====
{
  const slide = addSlide("\u4EC0\u4E48\u662F code-server\uFF1F");
  slide.addText("VS Code in the browser \u2014 \u5F00\u6E90\u3001\u81EA\u6258\u7BA1\u3001\u968F\u5904\u53EF\u7528", { x: 0.5, y: 1.0, w: 12, h: 0.5, fontSize: 16, color: ACCENT, fontFace: "Arial" });

  const features = [
    ["\uD83C\uDF10 \u6D4F\u89C8\u5668 IDE", "\u65E0\u9700\u5B89\u88C5\uFF0C\u6253\u5F00\u6D4F\u89C8\u5668\u5373\u53EF\u7F16\u7801", ACCENT],
    ["\uD83D\uDD10 \u7EDF\u4E00\u73AF\u5883", "\u6240\u6709\u5F00\u53D1\u8005\u4F7F\u7528\u76F8\u540C\u914D\u7F6E\uFF0C\u6D88\u9664\u201C\u6211\u8FD9\u91CC\u80FD\u8DD1\u201D\u95EE\u9898", ACCENT2],
    ["\uD83D\uDE80 \u8FDC\u7A0B\u5F00\u53D1", "\u4ECE\u4EFB\u4F55\u8BBE\u5907\u8BBF\u95EE\u5F3A\u5927\u7684\u5F00\u53D1\u73AF\u5883", GREEN],
    ["\uD83D\uDCC8 \u5F39\u6027\u4F38\u7F29", "K8s \u81EA\u52A8\u7F29\u5BB9\uFF0C\u652F\u6301\u6570\u5343\u5E76\u53D1\u7528\u6237", YELLOW],
    ["\uD83D\uDEE1\uFE0F \u5B89\u5168\u53EF\u63A7", "\u5BC6\u7801\u8BA4\u8BC1 + TLS + \u975E root \u7528\u6237 + \u5B89\u5168\u4E0A\u4E0B\u6587", RED],
    ["\uD83D\uDCCA \u53EF\u89C2\u6D4B", "Prometheus \u76D1\u63A7 + Grafana \u5927\u76D8 + \u544A\u8B66\u89C4\u5219", ACCENT]
  ];
  features.forEach((f, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 4.2;
    const y = 1.7 + row * 2.6;
    addCard(slide, x, y, 3.8, 2.2);
    slide.addText(f[0], { x: x + 0.2, y: y + 0.15, w: 3.4, h: 0.45, fontSize: 15, color: f[2], bold: true, fontFace: "Arial" });
    slide.addText(f[1], { x: x + 0.2, y: y + 0.7, w: 3.4, h: 1.3, ...bodyOpts, fontSize: 12 });
  });
}

// ===== SLIDE 3: WHY KUBERNETES =====
{
  const slide = addSlide("\u4E3A\u4EC0\u4E48\u9009\u62E9 Kubernetes\uFF1F");
  const rows = [
    ["\u90E8\u7F72\u65B9\u5F0F", "\u4F18\u70B9", "\u7F3A\u70B9", "\u9002\u7528\u573A\u666F"],
    ["\u88F8\u91D1\u5C5E / VM", "\u7B80\u5355\u76F4\u63A5", "\u65E0\u6269\u5C55\u6027\uFF0C\u8D44\u6E90\u6D6A\u8D39", "\u4E2A\u4EBA\u5F00\u53D1"],
    ["Docker Compose", "\u5FEB\u901F\u542F\u52A8", "\u5355\u673A\u9650\u5236\uFF0C\u65E0\u9AD8\u53EF\u7528", "\u5C0F\u56E2\u961F\u6D4B\u8BD5"],
    ["Kubernetes", "\u81EA\u52A8\u7F29\u5BB9\u3001HA\u3001\u6EDA\u52A8\u66F4\u65B0", "\u590D\u6742\u5EA6\u9AD8", "\u4F01\u4E1A\u751F\u4EA7\u73AF\u5883"]
  ];
  const cols = [0.8, 3.5, 6.5, 9.5];
  rows.forEach((r, i) => {
    const y = 1.2 + i * 0.7;
    if (i === 0) {
      r.forEach((c, j) => slide.addText(c, { x: cols[j], y, w: 3, h: 0.4, fontSize: 13, color: ACCENT, bold: true, fontFace: "Arial" }));
    } else {
      addCard(slide, 0.5, y, 12.3, 0.55);
      r.forEach((c, j) => slide.addText(c, { x: cols[j], y: y + 0.08, w: 3, h: 0.35, ...bodyOpts, fontSize: 12 }));
    }
  });

  addCard(slide, 0.5, 4.2, 12.3, 2.5);
  slide.addText("\u6211\u4EEC\u7684\u751F\u4EA7\u89C4\u6A21", { x: 0.8, y: 4.35, w: 5, h: 0.4, fontSize: 16, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 20 \u4E2A Pod \u5B9E\u4F8B\uFF0C\u5206\u5E03\u5728\u5DE5\u4F5C\u8282\u70B9\u4E0A\n\u2022 \u652F\u6301 2,000 \u540D\u5E76\u53D1\u7528\u6237\uFF0C0% \u670D\u52A1\u5931\u8D25\u7387\n\u2022 \u6BCF\u4E2A Pod: 500m CPU / 4Gi \u5185\u5B58\uFF08\u4ECE 2 CPU \u4F18\u5316\u800C\u6765\uFF09\n\u2022 \u8282\u70B9\u53CD\u4EB2\u548C\u6027\u786E\u4FDD\u5747\u5300\u5206\u5E03\n\u2022 \u6EDA\u52A8\u66F4\u65B0\u7B56\u7565\uFF0C\u96F6\u5B95\u673A\u66F4\u65B0", { x: 0.8, y: 4.85, w: 11, h: 1.7, ...bodyOpts, fontSize: 13 });
}

// ===== SLIDE 4: ARCHITECTURE =====
{
  const slide = addSlide("\u67B6\u6784\u56FE");
  // User
  addCard(slide, 4.5, 1.2, 4.3, 0.7, ACCENT2);
  slide.addText("\uD83D\uDC64 \u7528\u6237\u6D4F\u89C8\u5668", { x: 4.7, y: 1.3, w: 3.9, h: 0.5, fontSize: 14, color: WHITE, bold: true, fontFace: "Arial", align: "center" });
  // Arrow down
  slide.addText("\u25BC", { x: 6.2, y: 1.9, w: 1, h: 0.4, fontSize: 16, color: GRAY, align: "center", fontFace: "Arial" });
  // Ingress
  addCard(slide, 3.5, 2.3, 6.3, 1.0, "1E3A5F");
  slide.addText("Ingress (nginx NodePort :32231)", { x: 3.7, y: 2.4, w: 5.9, h: 0.35, fontSize: 13, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("TLS \u7EC8\u6B62 | Sticky Session | WebSocket \u652F\u6301 | \u8D1F\u8F7D\u5747\u8861", { x: 3.7, y: 2.8, w: 5.9, h: 0.35, ...bodyOpts, fontSize: 11 });
  // Arrow
  slide.addText("\u25BC", { x: 6.2, y: 3.3, w: 1, h: 0.4, fontSize: 16, color: GRAY, align: "center", fontFace: "Arial" });
  // Service
  addCard(slide, 4.5, 3.7, 4.3, 0.6, CARD_BG);
  slide.addText("Service (ClusterIP :8080)", { x: 4.7, y: 3.8, w: 3.9, h: 0.35, fontSize: 12, color: WHITE, fontFace: "Arial", align: "center" });
  // Arrows to pods
  slide.addText("\u25BC       \u25BC       \u25BC", { x: 4.5, y: 4.3, w: 4.3, h: 0.4, fontSize: 14, color: GRAY, align: "center", fontFace: "Arial" });
  // Pods
  for (let i = 0; i < 3; i++) {
    addCard(slide, 1.5 + i * 4.2, 4.7, 3.5, 1.2, CARD_BG);
    slide.addText(`Pod ${i+1}`, { x: 1.7 + i * 4.2, y: 4.8, w: 3.1, h: 0.3, fontSize: 12, color: GREEN, bold: true, fontFace: "Arial" });
    slide.addText("code-server :8080\n\u2022 /home/coder (PVC)\n\u2022 /etc/code-server (ConfigMap)\n\u2022 Password (Secret)", { x: 1.7 + i * 4.2, y: 5.15, w: 3.1, h: 0.65, ...bodyOpts, fontSize: 9 });
  }
  // PVC
  addCard(slide, 1.5, 6.1, 10.3, 0.6, "1E3A5F");
  slide.addText("PVC: code-server-data \u2192 /home/coder (\u6301\u4E45\u5316\u5B58\u50A8)  |  ConfigMap: code-server-config \u2192 entrypoint.sh  |  Secret: code-server-secrets \u2192 password", { x: 1.7, y: 6.2, w: 9.9, h: 0.4, ...bodyOpts, fontSize: 10 });
}

// ===== SLIDE 5: DEPLOYMENT YAML =====
{
  const slide = addSlide("\u90E8\u7F72\u914D\u7F6E\u8BE6\u89E3 (1/2)");
  const yaml1 = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: code-server
  namespace: ai-platform
  labels:
    app.kubernetes.io/name: code-server
spec:
  replicas: 20          # \u4ECE 5 \u6269\u5BB9\u5230 20
  strategy:
    rollingUpdate:      # \u6EDA\u52A8\u66F4\u65B0\uFF0C\u96F6\u5B95\u673A
      maxSurge: 25%
      maxUnavailable: 1
  template:
    spec:
      containers:
      - name: code-server
        image: codercom/code-server:latest
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: 500m       # \u4ECE 2 CPU \u4F18\u5316\u5230 500m
            memory: 4Gi
          limits:
            cpu: 4
            memory: 8Gi`;
  addCodeBlock(slide, 0.5, 1.1, 6.0, 5.8, yaml1);

  const yaml2 = `        securityContext:
          runAsUser: 1000        # \u975E root \u7528\u6237
          runAsGroup: 1000
          runAsNonRoot: true
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          seccompProfile:
            type: RuntimeDefault
        livenessProbe:           # \u5065\u5EB7\u68C0\u67E5
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 15
          periodSeconds: 10
        startupProbe:            # \u542F\u52A8\u63A2\u9488
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 30   # \u6700\u591A\u7B49\u5F85 150s`;
  addCodeBlock(slide, 6.8, 1.1, 6.0, 5.8, yaml2);
}

// ===== SLIDE 6: STORAGE & CONFIG =====
{
  const slide = addSlide("\u5B58\u50A8\u4E0E\u914D\u7F6E\u7BA1\u7406 (2/2)");
  const items = [
    ["PVC: code-server-data", "/home/coder", "\u7528\u6237\u5DE5\u4F5C\u533A\u6301\u4E45\u5316\uFF0CPod \u91CD\u542F\u4E0D\u4E22\u5931\u6570\u636E", GREEN],
    ["ConfigMap: code-server-config", "/etc/code-server", "entrypoint.sh \u542F\u52A8\u811A\u672C\uFF0C\u53EF\u5B9A\u5236\u73AF\u5883", ACCENT],
    ["Secret: code-server-secrets", "/etc/code-server-secrets", "\u5BC6\u7801\u5B58\u50A8\uFF0C\u4E0D\u660E\u6587\u5199\u5165 YAML", RED],
    ["emptyDir (Memory)", "/tmp", "512Mi \u5185\u5B58\u78C1\u76D8\uFF0C\u4E34\u65F6\u6587\u4EF6\u9AD8\u901F\u8BFB\u5199", YELLOW],
    ["emptyDir (Memory)", "/run/user/1000", "64Mi \u5185\u5B58\u78C1\u76D8\uFF0C\u8FDB\u7A0B\u8FD0\u884C\u6587\u4EF6", YELLOW]
  ];
  items.forEach((item, i) => {
    const y = 1.2 + i * 1.15;
    addCard(slide, 0.5, y, 12.3, 1.0);
    slide.addText(item[0], { x: 0.8, y: y + 0.1, w: 4, h: 0.35, fontSize: 14, color: item[3], bold: true, fontFace: "Arial" });
    slide.addText(item[1], { x: 5.0, y: y + 0.1, w: 3, h: 0.35, fontSize: 12, color: GRAY, fontFace: "Consolas" });
    slide.addText(item[2], { x: 0.8, y: y + 0.5, w: 11, h: 0.4, ...bodyOpts, fontSize: 12 });
  });
}

// ===== SLIDE 7: INGRESS CONFIG =====
{
  const slide = addSlide("Ingress \u914D\u7F6E\u8BE6\u89E3");
  const yaml = `apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: code-server
  annotations:
    # WebSocket \u652F\u6301\u2014\u2014code-server \u6838\u5FC3\u4F9D\u8D56
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/websocket-services: code-server
    # Sticky Session\u2014\u2014\u4FDD\u8BC1\u540C\u4E00\u7528\u6237\u5230\u540C\u4E00 Pod
    nginx.ingress.kubernetes.io/affinity: cookie
    nginx.ingress.kubernetes.io/session-cookie-name: CODESERVER_STICKY
    nginx.ingress.kubernetes.io/session-cookie-max-age: "10800"
    # \u5176\u4ED6
    nginx.ingress.kubernetes.io/proxy-body-size: 50m
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
spec:
  ingressClassName: nginx
  tls:
  - hosts: [code-server.ai-platform.local]
    secretName: code-server-tls
  rules:
  - host: code-server.ai-platform.local  # \u5E26 Host \u5934\u89C4\u5219
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: code-server
            port: { number: 8080 }
  - http:                                # \u2605 Catch-All \u89C4\u5219
      paths:                             #   \u89E3\u51B3 404 \u95EE\u9898\u7684\u5173\u952E!
      - path: /
        pathType: Prefix
        backend:
          service:
            name: code-server
            port: { number: 8080 }`;
  addCodeBlock(slide, 0.5, 1.1, 7.5, 5.8, yaml);

  // Annotation explanations
  addCard(slide, 8.3, 1.1, 4.7, 5.8);
  slide.addText("\u5173\u952E\u6CE8\u89E3", { x: 8.5, y: 1.2, w: 4.3, h: 0.4, fontSize: 15, color: ACCENT, bold: true, fontFace: "Arial" });
  const notes = [
    ["WebSocket", "code-server \u901A\u8BAF\u4F9D\u8D56 WebSocket\uFF0C\u5FC5\u987B\u914D\u7F6E\u8D85\u957F\u8D85\u65F6", GREEN],
    ["Sticky Session", "\u7528\u6237\u4F1A\u8BDD\u7ED1\u5B9A\u5230\u540C\u4E00 Pod\uFF0C\u907F\u514D\u72B6\u6001\u4E22\u5931", ACCENT],
    ["TLS", "\u52A0\u5BC6\u4F20\u8F93\uFF0C\u4FDD\u62A4\u5BC6\u7801\u548C\u4EE3\u7801\u5B89\u5168", RED],
    ["Catch-All Rule", "\u65E0 Host \u5934\u7684\u8BF7\u6C42\u4E5F\u80FD\u8DEF\u7531\uFF0C\u89E3\u51B3 404 \u95EE\u9898", YELLOW],
    ["proxy-buffering", "\u5173\u95ED\u7F13\u51B2\u4EE5\u652F\u6301\u5B9E\u65F6\u4EA4\u4E92", GRAY]
  ];
  notes.forEach((n, i) => {
    slide.addText(n[0], { x: 8.5, y: 1.8 + i * 1.0, w: 4.3, h: 0.3, fontSize: 12, color: n[2], bold: true, fontFace: "Arial" });
    slide.addText(n[1], { x: 8.5, y: 2.1 + i * 1.0, w: 4.3, h: 0.6, ...bodyOpts, fontSize: 10 });
  });
}

// ===== SLIDE 8: TROUBLESHOOTING #1 - 404 =====
{
  const slide = addSlide("\uD83D\uDD0D \u6545\u969C\u6392\u67E5 #1\uFF1A404 \u8C1C\u9898");
  addCard(slide, 0.5, 1.1, 5.8, 2.5, "2D1B1B");
  slide.addText("\u274C \u95EE\u9898", { x: 0.8, y: 1.2, w: 5, h: 0.4, fontSize: 16, color: RED, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 \u901A\u8FC7 IP \u76F4\u63A5\u8BBF\u95EE code-server \u8FD4\u56DE 404\n\u2022 curl http://10.167.2.175:32231 \u2192 404\n\u2022 \u4F46\u901A\u8FC7\u57DF\u540D\u8BBF\u95EE\u6B63\u5E38\n\u2022 \u8D1F\u8F7D\u6D4B\u8BD5\u4E2D 88.6% \u8BF7\u6C42\u5931\u8D25", { x: 0.8, y: 1.7, w: 5, h: 1.7, ...bodyOpts, fontSize: 12 });

  addCard(slide, 7.0, 1.1, 5.8, 2.5, "1B2D1B");
  slide.addText("\u2705 \u89E3\u51B3", { x: 7.3, y: 1.2, w: 5, h: 0.4, fontSize: 16, color: GREEN, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 Ingress \u53EA\u5339\u914D\u5E26 Host \u5934\u7684\u8BF7\u6C42\n\u2022 \u6DFB\u52A0\u7B2C\u4E8C\u6761\u65E0 Host \u7684\u89C4\u5219\n\u2022 \u6240\u6709\u8BF7\u6C42\u5747\u88AB\u8DEF\u7531\u2192 0% \u5931\u8D25\n\u2022 \u8D1F\u8F7D\u6D4B\u8BD5\u901A\u8FC7\uFF0C145 RPS \u7A33\u5B9A", { x: 7.3, y: 1.7, w: 5, h: 1.7, ...bodyOpts, fontSize: 12 });

  addCard(slide, 0.5, 3.9, 12.3, 2.8);
  slide.addText("\u6839\u56E0\u5206\u6790", { x: 0.8, y: 4.0, w: 5, h: 0.4, fontSize: 15, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("Ingress \u89C4\u5219\u4F9D\u8D56 Host \u5934\u5339\u914D\u3002\u5F53\u8BF7\u6C42\u4E0D\u5E26 Host \u5934\uFF08\u5982 curl \u76F4\u63A5\u8BBF\u95EE IP\uFF09\u65F6\uFF0CIngress \u65E0\u6CD5\u5339\u914D\u4EFB\u4F55\u89C4\u5219\uFF0C\u8FD4\u56DE 404\u3002", { x: 0.8, y: 4.5, w: 11, h: 0.4, ...bodyOpts, fontSize: 12 });
  slide.addText("\u89E3\u51B3\u65B9\u6848\uFF1A\u6DFB\u52A0\u4E00\u6761\u4E0D\u5E26 host \u5B57\u6BB5\u7684\u989D\u5916\u89C4\u5219\u4F5C\u4E3A\u9ED8\u8BA4\u540E\u7AEF\u3002\u8FD9\u6837\u65E0\u8BBA\u8BF7\u6C42\u662F\u5426\u5E26 Host \u5934\uFF0C\u90FD\u80FD\u6B63\u786E\u8DEF\u7531\u5230 code-server\u3002", { x: 0.8, y: 5.0, w: 11, h: 0.4, ...bodyOpts, fontSize: 12 });
  slide.addText("\u6559\u8BAD\uFF1A\u59CB\u7EC8\u4E3A NodePort \u670D\u52A1\u6DFB\u52A0\u9ED8\u8BA4\u540E\u7AEF\u89C4\u5219\uFF0C\u6216\u786E\u4FDD\u6240\u6709\u5BA2\u6237\u7AEF\u90FD\u5E26\u6B63\u786E\u7684 Host \u5934\u3002", { x: 0.8, y: 5.5, w: 11, h: 0.4, ...bodyOpts, fontSize: 12, color: YELLOW });
}

// ===== SLIDE 9: TROUBLESHOOTING #2 - RATE LIMIT =====
{
  const slide = addSlide("\uD83D\uDD0D \u6545\u969C\u6392\u67E5 #2\uFF1A\u901F\u7387\u9650\u5236\u9677\u9631");
  addCard(slide, 0.5, 1.1, 5.8, 2.5, "2D1B1B");
  slide.addText("\u274C \u95EE\u9898", { x: 0.8, y: 1.2, w: 5, h: 0.4, fontSize: 16, color: RED, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 \u8D1F\u8F7D\u6D4B\u8BD5\u663E\u793A 88.6% \u5931\u8D25\u7387\n\u2022 \u5E76\u53D1\u8D85\u8FC7 30 RPS \u65F6\u5168\u90E8\u62D2\u7EDD\n\u2022 \u539F\u56E0\uFF1Alimit-rps=30 \u6CE8\u89E3\n\u2022 \u9650\u5236\u4E86\u6240\u6709\u8BF7\u6C42\uFF0C\u4E0D\u662F\u5355 IP", { x: 0.8, y: 1.7, w: 5, h: 1.7, ...bodyOpts, fontSize: 12 });

  addCard(slide, 7.0, 1.1, 5.8, 2.5, "1B2D1B");
  slide.addText("\u2705 \u89E3\u51B3", { x: 7.3, y: 1.2, w: 5, h: 0.4, fontSize: 16, color: GREEN, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 \u79FB\u9664 limit-rps \u6CE8\u89E3\n\u2022 \u4FDD\u7559 limit-burst=50\n\u2022 \u4FDD\u7559 limit-connections=20\n\u2022 \u5931\u8D25\u7387\u4ECE 88.6% \u2192 0%", { x: 7.3, y: 1.7, w: 5, h: 1.7, ...bodyOpts, fontSize: 12 });

  // Before/After metrics
  addMetricCard(slide, 0.5, 3.9, 2.8, 1.5, "88.6%", "\u4FEE\u590D\u524D\u5931\u8D25\u7387", RED);
  slide.addText("\u2192", { x: 3.5, y: 4.3, w: 0.8, h: 0.6, fontSize: 28, color: GRAY, align: "center", fontFace: "Arial" });
  addMetricCard(slide, 4.3, 3.9, 2.8, 1.5, "0%", "\u4FEE\u590D\u540E\u5931\u8D25\u7387", GREEN);
  addMetricCard(slide, 7.5, 3.9, 2.8, 1.5, "30 RPS", "\u9650\u5236\u524D\u5CF0\u503C", RED);
  slide.addText("\u2192", { x: 10.5, y: 4.3, w: 0.8, h: 0.6, fontSize: 28, color: GRAY, align: "center", fontFace: "Arial" });
  addMetricCard(slide, 11.3, 3.9, 1.5, 1.5, "145", "\u4FEE\u590D\u540E", GREEN);

  addCard(slide, 0.5, 5.7, 12.3, 1.0);
  slide.addText("\u6559\u8BAD\uFF1Anginx ingress \u7684 limit-rps \u662F\u5168\u5C40\u9650\u5236\uFF0C\u4E0D\u662F\u6BCF IP \u9650\u5236\u3002\u751F\u4EA7\u73AF\u5883\u5E94\u4F7F\u7528\u66F4\u7CBE\u7EC6\u7684\u9650\u6D41\u7B56\u7565\uFF08\u5982 limit-req-zone-per-ip\uFF09\uFF0C\u6216\u5728\u5E94\u7528\u5C42\u5B9E\u73B0\u9650\u6D41\u3002", { x: 0.8, y: 5.8, w: 11, h: 0.8, ...bodyOpts, fontSize: 12, color: YELLOW });
}

// ===== SLIDE 10: SCALING =====
{
  const slide = addSlide("\u6269\u5BB9\u7B56\u7565");
  const headers = ["\u53C2\u6570", "\u4F18\u5316\u524D", "\u4F18\u5316\u540E", "\u6548\u679C"];
  const hx = [0.8, 4.0, 7.0, 10.0];
  headers.forEach((h, i) => slide.addText(h, { x: hx[i], y: 1.2, w: 3, h: 0.4, fontSize: 13, color: ACCENT, bold: true, fontFace: "Arial" }));

  const rows = [
    ["Pod \u6570\u91CF", "5", "20", "\u2191 4x"],
    ["CPU Request", "2 CPU", "500m", "\u2193 75%"],
    ["\u6700\u5927 Pod\u6570", "5 (\u53D7\u9650\u4E8E CPU)", "20+", "\u2191 4x+"],
    ["\u5E76\u53D1\u7528\u6237", "~500", "2,000+", "\u2191 4x"],
    ["\u5931\u8D25\u7387", "88.6%", "0%", "\u2193 100%"],
    ["\u5CF0\u503C RPS", "30", "145.7", "\u2191 4.8x"]
  ];
  rows.forEach((r, i) => {
    const y = 1.8 + i * 0.7;
    addCard(slide, 0.5, y, 12.3, 0.55);
    r.forEach((v, j) => {
      const color = j === 3 ? (v.includes("\u2191") ? GREEN : GREEN) : WHITE;
      slide.addText(v, { x: hx[j], y: y + 0.08, w: 3, h: 0.35, ...bodyOpts, fontSize: 12, color });
    });
  });

  addCard(slide, 0.5, 6.1, 12.3, 0.7);
  slide.addText("\u5173\u952E\u7B56\u7565\uFF1A\u964D\u4F4E CPU Request \u4ECE 2 \u2192 500m\uFF0C\u91CA\u653E\u8282\u70B9\u8D44\u6E90\uFF0C\u4F7F\u540C\u7B49\u786C\u4EF6\u53EF\u8FD0\u884C 4 \u500D Pod\u3002\u914D\u5408 Pod \u53CD\u4EB2\u548C\u6027\u5747\u5300\u5206\u5E03\u3002", { x: 0.8, y: 6.2, w: 11, h: 0.5, ...bodyOpts, fontSize: 12 });
}

// ===== SLIDE 11: LOAD TEST =====
{
  const slide = addSlide("\u8D1F\u8F7D\u6D4B\u8BD5\u7ED3\u679C");
  slide.addText("\u2705 \u901A\u8FC7 \u2014 2,000 \u5E76\u53D1\u7528\u6237\uFF0C0% \u670D\u52A1\u5931\u8D25", { x: 0.5, y: 1.0, w: 12, h: 0.5, fontSize: 18, color: GREEN, bold: true, fontFace: "Arial" });

  addMetricCard(slide, 0.5, 1.7, 2.8, 1.4, "19,595", "\u603B\u8BF7\u6C42\u6570", ACCENT);
  addMetricCard(slide, 3.6, 1.7, 2.8, 1.4, "0%", "\u670D\u52A1\u5931\u8D25\u7387", GREEN);
  addMetricCard(slide, 6.7, 1.7, 2.8, 1.4, "145.7", "\u5CF0\u503C RPS", ACCENT);
  addMetricCard(slide, 9.8, 1.7, 2.8, 1.4, "20", "Pod \u5B9E\u4F8B", ACCENT2);

  addCard(slide, 0.5, 3.4, 12.3, 3.3);
  slide.addText("\u63A5\u53E3\u6027\u80FD\u8BE6\u60C5", { x: 0.8, y: 3.5, w: 5, h: 0.4, fontSize: 15, color: ACCENT, bold: true, fontFace: "Arial" });
  const headers2 = ["\u63A5\u53E3", "\u8BF7\u6C42\u6570", "\u5931\u8D25\u7387", "\u5E73\u5747\u54CD\u5E94", "\u72B6\u6001"];
  const hx2 = [0.8, 4.0, 6.5, 8.5, 11.0];
  headers2.forEach((h, i) => slide.addText(h, { x: hx2[i], y: 4.0, w: 2.5, h: 0.35, fontSize: 12, color: GRAY, bold: true, fontFace: "Arial" }));

  const endpoints = [
    ["GET /healthz", "4,551", "0%", "10ms", "PASS", GREEN],
    ["GET /login", "2,000", "0%", "9.1s", "PASS", GREEN],
    ["POST /login", "2,000", "0%", "8.0s", "PASS", GREEN],
    ["GET / (workspace)", "5,556", "0%", "56s", "PASS", YELLOW]
  ];
  endpoints.forEach((e, i) => {
    const y = 4.5 + i * 0.5;
    e.forEach((v, j) => {
      slide.addText(v, { x: hx2[j], y, w: 2.5, h: 0.4, ...bodyOpts, fontSize: 12, color: j === 4 ? e[5] : WHITE });
    });
  });
  slide.addText("\u6CE8\uFF1A\u5DE5\u4F5C\u533A\u52A0\u8F7D 56s \u662F\u6B63\u5E38\u7684\uFF08\u9759\u6001\u8D44\u6E90\u4E0B\u8F7D\uFF09\uFF0C\u5EFA\u8BAE\u4F7F\u7528 CDN \u52A0\u901F", { x: 0.8, y: 6.5, w: 11, h: 0.3, ...smallOpts, color: YELLOW });
}

// ===== SLIDE 12: SECURITY =====
{
  const slide = addSlide("\u5B89\u5168\u6700\u4F73\u5B9E\u8DF5");
  const secItems = [
    ["\uD83D\uDD12 \u5BC6\u7801\u8BA4\u8BC1", "Kubernetes Secret \u5B58\u50A8\u5BC6\u7801\uFF0C\u4E0D\u660E\u6587\u5199\u5165 YAML\u3002\u901A\u8FC7\u73AF\u5883\u53D8\u91CF PASSWORD \u6CE8\u5165\u3002", GREEN],
    ["\uD83D\uDD10 TLS \u52A0\u5BC6", "Ingress \u5C42 TLS \u7EC8\u6B62\uFF0C\u4FDD\u62A4\u4F20\u8F93\u6570\u636E\u3002\u4F7F\u7528 cert-manager \u81EA\u52A8\u7B7E\u53D1\u8BC1\u4E66\u3002", GREEN],
    ["\uD83D\uDC64 \u975E Root \u7528\u6237", "runAsUser: 1000, runAsNonRoot: true\u3002\u5373\u4F7F\u5BB9\u5668\u88AB\u653B\u7834\uFF0C\u653B\u51FB\u8005\u4E5F\u65E0 root \u6743\u9650\u3002", GREEN],
    ["\uD83D\uDEE1\uFE0F \u5B89\u5168\u4E0A\u4E0B\u6587", "allowPrivilegeEscalation: false, drop ALL capabilities, seccomp: RuntimeDefault\u3002\u6700\u5C0F\u5316\u653B\u51FB\u9762\u3002", GREEN],
    ["\uD83D\uDCC5 \u955C\u50CF\u66F4\u65B0", "imagePullPolicy: Always\uFF0C\u786E\u4FDD\u4F7F\u7528\u6700\u65B0\u955C\u50CF\u3002\u5B9A\u671F\u66F4\u65B0\u4FEE\u590D\u5B89\u5168\u6F0F\u6D1E\u3002", YELLOW],
    ["\uD83D\uDEDC\uFE0F \u7F51\u7EDC\u7B56\u7565", "\u5EFA\u8BAE\u914D\u7F6E NetworkPolicy\uFF0C\u9650\u5236 Pod \u95F4\u901A\u4FE1\uFF0C\u53EA\u5141\u8BB8\u5FC5\u8981\u7684\u6D41\u91CF\u3002", YELLOW]
  ];
  secItems.forEach((item, i) => {
    const y = 1.1 + i * 1.0;
    addCard(slide, 0.5, y, 12.3, 0.85);
    slide.addText(item[0], { x: 0.8, y: y + 0.1, w: 3, h: 0.35, fontSize: 14, color: item[2], bold: true, fontFace: "Arial" });
    slide.addText(item[1], { x: 4.0, y: y + 0.1, w: 8.5, h: 0.6, ...bodyOpts, fontSize: 12 });
  });
}

// ===== SLIDE 13: MONITORING =====
{
  const slide = addSlide("\u76D1\u63A7\u4E0E\u53EF\u89C2\u6D4B\u6027");
  addCard(slide, 0.5, 1.1, 5.8, 2.8);
  slide.addText("Prometheus \u76D1\u63A7", { x: 0.8, y: 1.2, w: 5, h: 0.4, fontSize: 15, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 ServiceMonitor \u81EA\u52A8\u53D1\u73B0\n\u2022 /metrics \u7AEF\u70B9\u6BCF 30s \u91C7\u96C6\n\u2022 \u5173\u952E\u6307\u6807\uFF1APod \u6570\u3001CPU\u3001\u5185\u5B58\u3001RPS\n\u2022 \u544A\u8B66\u89C4\u5219\uFF1A\u526F\u672C\u6570 < 3 \u89E6\u53D1 warning", { x: 0.8, y: 1.7, w: 5, h: 2.0, ...bodyOpts, fontSize: 12 });

  addCard(slide, 7.0, 1.1, 5.8, 2.8);
  slide.addText("Grafana \u5927\u76D8", { x: 7.3, y: 1.2, w: 5, h: 0.4, fontSize: 15, color: ACCENT2, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 \u5B9E\u65F6 Pod \u5065\u5EB7\u72B6\u6001\n\u2022 \u8BF7\u6C42\u901F\u7387\u4E0E\u9519\u8BEF\u7387\u8D8B\u52BF\n\u2022 \u8D44\u6E90\u4F7F\u7528\u7387\u70ED\u529B\u56FE\n\u2022 \u8BBF\u95EE\uFF1Ahttp://10.167.2.175:30082", { x: 7.3, y: 1.7, w: 5, h: 2.0, ...bodyOpts, fontSize: 12 });

  addCard(slide, 0.5, 4.2, 12.3, 2.5);
  slide.addText("\u544A\u8B66\u89C4\u5219\u793A\u4F8B", { x: 0.8, y: 4.3, w: 5, h: 0.4, fontSize: 15, color: ACCENT, bold: true, fontFace: "Arial" });
  const alertYaml = `- alert: CodeServerReplicasLow
  expr: kube_deployment_status_replicas_ready{
    namespace="ai-platform",
    deployment="code-server"} < 3
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "code-server \u526F\u672C\u6570\u4F4E\u4E8E\u6700\u5C0F\u503C"
    description: "\u5F53\u524D\u4EC5 {{ $value }} \u4E2A\u5C31\u7EEA\u526F\u672C"`;
  addCodeBlock(slide, 0.8, 4.8, 5.5, 1.8, alertYaml);
  slide.addText("\u5176\u4ED6\u5EFA\u8BAE\u544A\u8B66\uFF1A\n\u2022 \u9519\u8BEF\u7387 > 5% \u89E6\u53D1 critical\n\u2022 P99 \u54CD\u5E94\u65F6\u95F4 > 2s \u89E6\u53D1 warning\n\u2022 Pod \u91CD\u542F\u7387\u8FC7\u9AD8\u89E6\u53D1 warning\n\u2022 PVC \u4F7F\u7528\u7387 > 80% \u89E6\u53D1 warning", { x: 6.8, y: 4.8, w: 5.5, h: 1.8, ...bodyOpts, fontSize: 12 });
}

// ===== SLIDE 14: CHECKLIST =====
{
  const slide = addSlide("\u751F\u4EA7\u90E8\u7F72\u68C0\u67E5\u6E05\u5355");
  const checks = [
    ["\u2705 \u8D44\u6E90\u9650\u5236\u4E0E\u8BF7\u6C42", "CPU: 500m req / 4 limit, Memory: 4Gi req / 8Gi limit", GREEN],
    ["\u2705 \u5065\u5EB7\u68C0\u67E5", "startupProbe + livenessProbe + readinessProbe \u5168\u90E8\u914D\u7F6E", GREEN],
    ["\u2705 \u9AD8\u53EF\u7528", "Pod \u53CD\u4EB2\u548C\u6027 + \u591A\u526F\u672C + \u6EDA\u52A8\u66F4\u65B0", GREEN],
    ["\u2705 \u6301\u4E45\u5316\u5B58\u50A8", "PVC \u4FDD\u62A4\u7528\u6237\u6570\u636E\uFF0CPod \u91CD\u542F\u4E0D\u4E22\u5931", GREEN],
    ["\u2705 TLS \u52A0\u5BC6", "Ingress \u5C42 TLS \u7EC8\u6B62\uFF0C\u4FDD\u62A4\u4F20\u8F93\u5B89\u5168", GREEN],
    ["\u2705 Sticky Session", "Cookie \u7ED1\u5B9A\uFF0C\u4FDD\u8BC1 WebSocket \u8FDE\u63A5\u7A33\u5B9A", GREEN],
    ["\u2705 \u76D1\u63A7\u544A\u8B66", "Prometheus + Grafana + \u81EA\u5B9A\u4E49\u544A\u8B66\u89C4\u5219", GREEN],
    ["\u2705 \u975E Root \u7528\u6237", "UID 1000 + SecurityContext \u786C\u5316", GREEN],
    ["\u26A0\uFE0F CDN \u52A0\u901F", "\u9759\u6001\u8D44\u6E90\u52A0\u8F7D\u8F83\u6162\uFF0856s\uFF09\uFF0C\u5EFA\u8BAE\u4F7F\u7528 CDN", YELLOW],
    ["\u26A0\uFE0F HPA \u81EA\u52A8\u7F29\u5BB9", "\u5EFA\u8BAE\u914D\u7F6E HPA \u6839\u636E CPU/\u5185\u5B58\u81EA\u52A8\u8C03\u6574\u526F\u672C\u6570", YELLOW]
  ];
  checks.forEach((c, i) => {
    const y = 1.1 + i * 0.58;
    addCard(slide, 0.5, y, 12.3, 0.48);
    slide.addText(c[0], { x: 0.7, y: y + 0.05, w: 3.5, h: 0.35, fontSize: 12, color: c[2], bold: true, fontFace: "Arial" });
    slide.addText(c[1], { x: 4.3, y: y + 0.05, w: 8.2, h: 0.35, ...bodyOpts, fontSize: 11 });
  });
}

// ===== SLIDE 15: SUMMARY =====
{
  const slide = addSlide("\u603B\u7ED3\u4E0E\u8D44\u6E90");
  addCard(slide, 0.5, 1.1, 5.8, 2.5);
  slide.addText("\u6838\u5FC3\u8981\u70B9", { x: 0.8, y: 1.2, w: 5, h: 0.4, fontSize: 18, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 code-server = VS Code \u5728\u6D4F\u89C8\u5668\u4E2D\n\u2022 K8s \u63D0\u4F9B\u5F39\u6027\u4F38\u7F29\u4E0E\u9AD8\u53EF\u7528\n\u2022 \u5408\u7406\u7684\u8D44\u6E90\u914D\u7F6E\u662F\u5173\u952E\n\u2022 Ingress \u914D\u7F6E\u76F4\u63A5\u5F71\u54CD\u53EF\u7528\u6027\n\u2022 \u5B89\u5168\u4E0E\u76D1\u63A7\u4E0D\u53EF\u6216\u7F3A", { x: 0.8, y: 1.7, w: 5, h: 1.7, ...bodyOpts, fontSize: 13 });

  addCard(slide, 7.0, 1.1, 5.8, 2.5);
  slide.addText("\u5B66\u4E60\u8D44\u6E90", { x: 7.3, y: 1.2, w: 5, h: 0.4, fontSize: 18, color: ACCENT2, bold: true, fontFace: "Arial" });
  slide.addText("\u2022 github.com/coder/code-server\n\u2022 coder.com/docs/code-server\n\u2022 kubernetes.io/docs\n\u2022 \u672C\u96C6\u7FA4 Grafana\uFF1A:30082\n\u2022 \u672C\u96C6\u7FA4 Rancher\uFF1A:443", { x: 7.3, y: 1.7, w: 5, h: 1.7, ...bodyOpts, fontSize: 13 });

  addCard(slide, 0.5, 3.9, 12.3, 2.8);
  slide.addText("\u90E8\u7F72\u56DE\u987E", { x: 0.8, y: 4.0, w: 5, h: 0.4, fontSize: 18, color: ACCENT, bold: true, fontFace: "Arial" });
  slide.addText("\u6211\u4EEC\u7684\u6210\u679C\uFF1A\n\u2022 2 \u4E2A\u8282\u70B9 K8s \u96C6\u7FA4\uFF0C\u65E0 GPU\uFF0C\u5168\u90E8 CPU \u8FD0\u884C\n\u2022 20 \u4E2A code-server Pod\uFF0C\u652F\u6301 2,000 \u5E76\u53D1\u7528\u6237\n\u2022 0% \u670D\u52A1\u5931\u8D25\u7387\uFF0C145 RPS \u5CF0\u503C\n\u2022 \u89E3\u51B3\u4E86 2 \u4E2A\u5173\u952E\u6545\u969C\uFF1A404 \u8C1C\u9898 + \u901F\u7387\u9650\u5236\u9677\u9631\n\u2022 \u5B8C\u6574\u7684\u76D1\u63A7\u544A\u8B66\u4F53\u7CFB\n\u2022 \u4F01\u4E1A\u7EA7\u5B89\u5168\u914D\u7F6E", { x: 0.8, y: 4.5, w: 11, h: 2.0, ...bodyOpts, fontSize: 13 });
}

// Save
pptx.writeFile({ fileName: "D:\\dify-install\\load-test\\Code_Server_Teaching_Guide.pptx" })
  .then(() => console.log("PPTX created successfully!"))
  .catch(err => console.error("Error:", err));