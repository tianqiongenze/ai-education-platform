const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

const DARK = "0F172A", CARD = "1E293B", ACC = "3B82F6", A2 = "8B5CF6";
const GRN = "22C55E", RED = "EF4444", YEL = "F59E0B", WHT = "F8FAFC", GRY = "94A3B8";
const CODE = "0D1117";

pptx.defineLayout({ name: "WIDE", width: 13.33, height: 7.5 });
pptx.layout = "WIDE";

const t = (s,o) => ({...o,fontFace:"Arial"});
const T = (s,o) => ({fontSize:26,color:WHT,bold:true,...o,fontFace:"Arial"});
const B = (s,o) => ({fontSize:13,color:WHT,...o,fontFace:"Arial"});
const S = (s,o) => ({fontSize:11,color:GRY,...o,fontFace:"Arial"});
const M = (s,o) => ({fontSize:38,color:ACC,bold:true,...o,fontFace:"Arial"});
const C = (s,o) => ({fontSize:9,color:"E6EDF3",fontFace:"Consolas",...o});

function slide(title) {
  const s = pptx.addSlide();
  s.background = {color:DARK};
  s.addShape("rect",{x:0,y:0,w:13.33,h:0.06,fill:{color:ACC}});
  s.addText(title,{x:0.5,y:0.2,w:12,h:0.6,...T(null,{fontSize:24})});
  s.addText("Enterprise Monitoring Manual | Prometheus + Grafana | June 2026",{x:0.5,y:7.05,w:12,h:0.35,...S()});
  return s;
}
function card(s,x,y,w,h,c) { s.addShape("rect",{x,y,w,h,fill:{color:c||CARD},rectRadius:0.08}); }
function metric(s,x,y,w,h,v,l,c) {
  card(s,x,y,w,h);
  s.addText(v,{x,y:y+0.1,w,h:0.6,align:"center",...M(null,{color:c||ACC,fontSize:34})});
  s.addText(l,{x,y:y+0.75,w,h:0.4,align:"center",...S(null,{fontSize:12})});
}
function code(s,x,y,w,h,txt) {
  card(s,x,y,w,h,CODE);
  s.addText(txt,{x:x+0.15,y:y+0.1,w:w-0.3,h:h-0.2,...C()});
}

// ===== SLIDE 1: TITLE =====
{
  const s = pptx.addSlide();
  s.background = {color:DARK};
  s.addShape("rect",{x:0,y:0,w:13.33,h:0.1,fill:{color:ACC}});
  s.addText("Enterprise Monitoring",{x:1,y:1.2,w:11,h:1.2,fontSize:52,color:WHT,bold:true,fontFace:"Arial"});
  s.addText("Prometheus + Grafana \u4F01\u4E1A\u7EA7\u76D1\u63A7\u4F7F\u7528\u624B\u518C",{x:1,y:2.3,w:11,h:0.8,fontSize:28,color:ACC,fontFace:"Arial"});
  s.addShape("rect",{x:1,y:3.3,w:2.5,h:0.05,fill:{color:A2}});
  s.addText("39 ServiceMonitors | 40 PrometheusRules | 4 Custom Dashboards | 70+ Panels",{x:1,y:3.7,w:11,h:0.6,fontSize:16,color:GRY,fontFace:"Arial"});
  s.addText("2-Node K8s Cluster | Dify + LLM + code-server + Infrastructure",{x:1,y:4.3,w:11,h:0.5,fontSize:14,color:GRN,fontFace:"Arial"});
  s.addText("June 14, 2026",{x:1,y:5.0,w:11,h:0.4,fontSize:12,color:GRY,fontFace:"Arial"});
}

// ===== SLIDE 2: MONITORING ARCHITECTURE =====
{
  const s = slide("Monitoring Architecture");
  // Prometheus
  card(s,0.5,1.2,3.5,1.5,ACC);
  s.addText("Prometheus",{x:0.7,y:1.3,w:3.1,h:0.4,fontSize:16,color:WHT,bold:true,fontFace:"Arial"});
  s.addText("Metrics Collection\n30s scrape interval\nTSDB storage",{x:0.7,y:1.8,w:3.1,h:0.8,...B(null,{fontSize:11})});
  // Arrow
  s.addText("\u2192",{x:4.2,y:1.6,w:0.8,h:0.5,fontSize:24,color:GRY,align:"center",fontFace:"Arial"});
  // Grafana
  card(s,5.0,1.2,3.5,1.5,A2);
  s.addText("Grafana",{x:5.2,y:1.3,w:3.1,h:0.4,fontSize:16,color:WHT,bold:true,fontFace:"Arial"});
  s.addText("Visualization\n4 Custom Dashboards\n70+ Panels",{x:5.2,y:1.8,w:3.1,h:0.8,...B(null,{fontSize:11})});
  // Arrow
  s.addText("\u2192",{x:8.7,y:1.6,w:0.8,h:0.5,fontSize:24,color:GRY,align:"center",fontFace:"Arial"});
  // Alertmanager
  card(s,9.5,1.2,3.5,1.5,RED);
  s.addText("Alertmanager",{x:9.7,y:1.3,w:3.1,h:0.4,fontSize:16,color:WHT,bold:true,fontFace:"Arial"});
  s.addText("Alert Routing\n40 Rule Groups\nCritical/Warning/Info",{x:9.7,y:1.8,w:3.1,h:0.8,...B(null,{fontSize:11})});

  // ServiceMonitors
  card(s,0.5,3.0,12.3,1.5);
  s.addText("ServiceMonitors (39 total)",{x:0.8,y:3.1,w:5,h:0.4,fontSize:15,color:ACC,bold:true,fontFace:"Arial"});
  s.addText("ai-platform: ollama-master, ollama-worker, ollama-exporter, litellm, litellm-log-exporter, open-webui, code-server, health-check-exporter\n"+
    "dify: dify-api, dify-web, dify-worker, dify-plugin-daemon, smtp-debug\n"+
    "dify-plus: dify-plus-api, dify-plus-weaviate, dify-plus-postgres, dify-plus-redis, dify-plus-mail-server, dify-db, dify-redis\n"+
    "infra: ingress-nginx-controller, rancher-cluster-agent, local-path-provisioner\n"+
    "kube-system: alertmanager, apiserver, coredns, grafana, controller-manager, etcd, kube-proxy, kube-state-metrics, kubelet, operator, prometheus, node-exporter",
    {x:0.8,y:3.6,w:11.5,h:0.8,...B(null,{fontSize:9})});

  // PrometheusRules
  card(s,0.5,4.8,12.3,1.5);
  s.addText("PrometheusRules (40 total)",{x:0.8,y:4.9,w:5,h:0.4,fontSize:15,color:A2,bold:true,fontFace:"Arial"});
  s.addText("Custom: dify-platform-alerts, dify-plus-alerts, llm-services-alerts, enterprise-alert-rules\n"+
    "Enterprise groups: ollama-alerts(4), ingress-alerts(4), storage-alerts(3), dify-namespace-alerts(5), rancher-alerts(1), infrastructure-alerts(5)\n"+
    "K8s built-in: 35 rule groups covering nodes, pods, deployments, statefulsets, apiserver, etcd, scheduler, kubelet, networking, storage",
    {x:0.8,y:5.4,w:11.5,h:0.8,...B(null,{fontSize:9})});

  // Access
  card(s,0.5,6.5,12.3,0.5);
  s.addText("Grafana: http://10.167.2.175:30082 (admin/prom-operator) | Prometheus: http://10.167.2.175:9090 | Alertmanager: http://10.167.2.175:9093",
    {x:0.8,y:6.55,w:11.5,h:0.4,...S(null,{fontSize:10,color:GRN})});
}

// ===== SLIDE 3: DASHBOARD 1 - LLM SERVICES =====
{
  const s = slide("Dashboard 1: LLM Services");
  card(s,0.5,1.1,12.3,5.8);
  s.addText("LLM Services - Enterprise Monitoring",{x:0.8,y:1.2,w:11,h:0.4,fontSize:18,color:ACC,bold:true,fontFace:"Arial"});
  s.addText("Dashboard UID: llm-services | 17 Panels | Refresh: 30s",{x:0.8,y:1.6,w:11,h:0.3,...S()});

  const rows = [
    ["Ollama Runtime Engine","Master Status, Worker Status, Memory %, CPU Usage, Memory Usage","6 panels"],
    ["Litellm Gateway","Pod Count, 5xx Rate, Error %, Request Rate, Error Rate, P95 Latency","7 panels"],
    ["Open-WebUI","Status, Request Rate, CPU Usage","3 panels"]
  ];
  rows.forEach((r,i)=>{
    const y=2.1+i*1.2;
    card(s,0.8,y,11.7,1.0);
    s.addText(r[0],{x:1.0,y:y+0.1,w:4,h:0.35,fontSize:14,color:GRN,bold:true,fontFace:"Arial"});
    s.addText(r[1],{x:1.0,y:y+0.5,w:7,h:0.4,...B(null,{fontSize:11})});
    s.addText(r[2],{x:10,y:y+0.1,w:2.5,h:0.35,fontSize:11,color:ACC,fontFace:"Arial"});
  });

  s.addText("Key Metrics: Ollama Worker (12 models, CPU-only), Litellm (10 pods, 13 model routes), Open-WebUI (chat interface)",
    {x:0.8,y:5.8,w:11,h:0.4,...B(null,{fontSize:11,color:YEL})});
}

// ===== SLIDE 4: DASHBOARD 2 - DIFY =====
{
  const s = slide("Dashboard 2: Dify Platform");
  card(s,0.5,1.1,12.3,5.8);
  s.addText("Dify Platform - Enterprise Monitoring",{x:0.8,y:1.2,w:11,h:0.4,fontSize:18,color:A2,bold:true,fontFace:"Arial"});
  s.addText("Dashboard UID: dify-platform | 19 Panels | Refresh: 30s",{x:0.8,y:1.6,w:11,h:0.3,...S()});

  const rows = [
    ["Dify Core (dify ns)","API(3), Web(3), Worker(3), Plugin Daemon(1), SMTP Debug(1) - Status + Request Rate + Error Rate + Latency + CPU + Memory","11 panels"],
    ["Dify Infra (dify-plus ns)","PostgreSQL, Redis, Weaviate, Mail Server - Status + Memory Usage","8 panels"]
  ];
  rows.forEach((r,i)=>{
    const y=2.1+i*1.2;
    card(s,0.8,y,11.7,1.0);
    s.addText(r[0],{x:1.0,y:y+0.1,w:4,h:0.35,fontSize:14,color:GRN,bold:true,fontFace:"Arial"});
    s.addText(r[1],{x:1.0,y:y+0.5,w:7,h:0.4,...B(null,{fontSize:11})});
    s.addText(r[2],{x:10,y:y+0.1,w:2.5,h:0.35,fontSize:11,color:ACC,fontFace:"Arial"});
  });

  s.addText("Key Alerts: DifyAPIDown(critical), DifyWorkerDown(warning), DifyDBDown(critical), DifyRedisDown(critical), DifyNsHighErrorRate(critical)",
    {x:0.8,y:5.0,w:11,h:0.4,...B(null,{fontSize:11,color:YEL})});
}

// ===== SLIDE 5: DASHBOARD 3 - INFRA =====
{
  const s = slide("Dashboard 3: Infrastructure");
  card(s,0.5,1.1,12.3,5.8);
  s.addText("Infrastructure - Enterprise Monitoring",{x:0.8,y:1.2,w:11,h:0.4,fontSize:18,color:GRN,bold:true,fontFace:"Arial"});
  s.addText("Dashboard UID: infrastructure | 19 Panels | Refresh: 30s",{x:0.8,y:1.6,w:11,h:0.3,...S()});

  const rows = [
    ["Ingress NGINX","Controller Status, 5xx/4xx Rates, Error %, Request Rate, P99 Latency, Error Breakdown","8 panels"],
    ["Nodes","Node Count, CPU %, Memory %, Disk %, CPU/Memory Trends","7 panels"],
    ["Storage & Rancher","PVC Usage Table, Rancher Agent Status, Local Path Provisioner","4 panels"]
  ];
  rows.forEach((r,i)=>{
    const y=2.1+i*1.2;
    card(s,0.8,y,11.7,1.0);
    s.addText(r[0],{x:1.0,y:y+0.1,w:4,h:0.35,fontSize:14,color:GRN,bold:true,fontFace:"Arial"});
    s.addText(r[1],{x:1.0,y:y+0.5,w:7,h:0.4,...B(null,{fontSize:11})});
    s.addText(r[2],{x:10,y:y+0.1,w:2.5,h:0.35,fontSize:11,color:ACC,fontFace:"Arial"});
  });

  s.addText("Key Alerts: IngressControllerDown(critical), IngressHigh5xxRate(critical), PVCUsageCritical(critical), NodeDiskSpaceLow(warning)",
    {x:0.8,y:5.8,w:11,h:0.4,...B(null,{fontSize:11,color:YEL})});
}

// ===== SLIDE 6: DASHBOARD 4 - CODE-SERVER =====
{
  const s = slide("Dashboard 4: Code-Server IDE");
  card(s,0.5,1.1,12.3,5.8);
  s.addText("Code-Server IDE - Enterprise Monitoring",{x:0.8,y:1.2,w:11,h:0.4,fontSize:18,color:ACC,bold:true,fontFace:"Arial"});
  s.addText("Dashboard UID: codeserver | 15 Panels | Refresh: 30s",{x:0.8,y:1.6,w:11,h:0.3,...S()});

  const rows = [
    ["Overview","Ready Pods, Desired Pods, Available Pods, Pod Restarts, Pod Count History, Pod Readiness %","6 panels"],
    ["Performance","CPU Usage per Pod, Memory Usage per Pod, Avg CPU %, Avg Memory %, CPU Throttling","5 panels"],
    ["Health","Pod Status Table (name, ready, restarts, age)","1 panel"]
  ];
  rows.forEach((r,i)=>{
    const y=2.1+i*1.2;
    card(s,0.8,y,11.7,1.0);
    s.addText(r[0],{x:1.0,y:y+0.1,w:4,h:0.35,fontSize:14,color:GRN,bold:true,fontFace:"Arial"});
    s.addText(r[1],{x:1.0,y:y+0.5,w:7,h:0.4,...B(null,{fontSize:11})});
    s.addText(r[2],{x:10,y:y+0.1,w:2.5,h:0.35,fontSize:11,color:ACC,fontFace:"Arial"});
  });

  s.addText("Key Metrics: 20 pods, 500m CPU/pod, 4Gi memory/pod, 0% service failures, 145.7 peak RPS",
    {x:0.8,y:5.8,w:11,h:0.4,...B(null,{fontSize:11,color:YEL})});
}

// ===== SLIDE 7: ALERT RULES OVERVIEW =====
{
  const s = slide("Alert Rules Overview");
  const groups = [
    ["ollama-alerts","OllamaMasterDown(c), OllamaWorkerDown(c), OllamaHighMemory(w), OllamaHighCPU(w)","4 rules"],
    ["ingress-alerts","IngressControllerDown(c), IngressHigh5xxRate(c), IngressHighLatency(w), IngressHigh4xxRate(w)","4 rules"],
    ["storage-alerts","PVCUsageHigh(w), PVCUsageCritical(c), NodeDiskSpaceLow(w)","3 rules"],
    ["dify-ns-alerts","DifyNsAPIDown(c), DifyNsWebDown(w), DifyNsWorkerDown(w), DifyNsPluginDaemonDown(w), DifyNsHighErrorRate(c)","5 rules"],
    ["rancher-alerts","RancherAgentDown(w)","1 rule"],
    ["infra-alerts","TooManyPodRestarts(w), PendingPodsHigh(w), CPUThrottlingHigh(w), DeploymentMismatch(w), StatefulSetMismatch(w)","5 rules"]
  ];
  groups.forEach((g,i)=>{
    const y=1.2+i*0.95;
    card(s,0.5,y,12.3,0.8);
    s.addText(g[0],{x:0.7,y:y+0.05,w:2.5,h:0.35,fontSize:13,color:ACC,bold:true,fontFace:"Arial"});
    s.addText(g[1],{x:3.3,y:y+0.05,w:7.5,h:0.35,...B(null,{fontSize:10})});
    s.addText(g[2],{x:11,y:y+0.05,w:1.5,h:0.35,fontSize:11,color:GRN,fontFace:"Arial"});
  });
  s.addText("Severity: (c)=critical (immediate action), (w)=warning (investigate), (i)=info (awareness) | Total: 22 custom + 35 K8s built-in rules",
    {x:0.5,y:7.0,w:12,h:0.3,...S(null,{fontSize:10})});
}

// ===== SLIDE 8: PROMQL CHEAT SHEET =====
{
  const s = slide("PromQL Quick Reference");
  const queries = [
    ["Pod Status","up{namespace=\"ai-platform\",pod=~\"service-.*\"}","1=UP, 0=DOWN"],
    ["Pod Count","count(up{namespace=\"ai-platform\"}==1)","Total running pods"],
    ["CPU Usage","rate(container_cpu_usage_seconds_total{namespace=\"ai-platform\"}[5m])","CPU cores/sec"],
    ["Memory Usage","container_memory_working_set_bytes{namespace=\"ai-platform\"}","Bytes in use"],
    ["Memory %","container_memory_working_set_bytes/container_spec_memory_limit_bytes*100","Percentage"],
    ["Request Rate","sum(rate(http_requests_total{namespace=\"ai-platform\"}[5m]))","Requests/sec"],
    ["Error Rate","sum(rate(http_requests_total{status=~\"5..\"}[5m]))/sum(rate(http_requests_total[5m]))*100","5xx percentage"],
    ["P95 Latency","histogram_quantile(0.95,sum(rate(http_request_duration_seconds_bucket[5m]))by(le))","Seconds"],
    ["Pod Restarts","rate(kube_pod_container_status_restarts_total[15m])","Restarts/sec"],
    ["PVC Usage","kubelet_volume_stats_used_bytes/kubelet_volume_stats_capacity_bytes*100","Percentage"]
  ];
  queries.forEach((q,i)=>{
    const y=1.2+i*0.58;
    card(s,0.5,y,12.3,0.5);
    s.addText(q[0],{x:0.7,y:y+0.05,w:2.5,h:0.35,fontSize:12,color:GRN,bold:true,fontFace:"Arial"});
    s.addText(q[1],{x:3.3,y:y+0.05,w:6.5,h:0.35,...C(null,{fontSize:8})});
    s.addText(q[2],{x:10,y:y+0.05,w:2.5,h:0.35,...S(null,{fontSize:10})});
  });
}

// ===== SLIDE 9: GRAFANA USAGE GUIDE =====
{
  const s = slide("Grafana Usage Guide");
  card(s,0.5,1.1,5.8,2.5);
  s.addText("Access",{x:0.8,y:1.2,w:5,h:0.4,fontSize:16,color:ACC,bold:true,fontFace:"Arial"});
  s.addText("URL: http://10.167.2.175:30082\nUsername: admin\nPassword: prom-operator\n\nDashboards \u2192 Browse \u2192 Select\n4 custom dashboards available",{x:0.8,y:1.7,w:5,h:1.7,...B(null,{fontSize:12})});

  card(s,7.0,1.1,5.8,2.5);
  s.addText("Time Range",{x:7.3,y:1.2,w:5,h:0.4,fontSize:16,color:A2,bold:true,fontFace:"Arial"});
  s.addText("Default: Last 6 hours\nQuick: Last 5m/15m/1h/6h/12h/24h\nCustom: Absolute time range\nAuto-refresh: 30s default\n\nTop-right corner controls",{x:7.3,y:1.7,w:5,h:1.7,...B(null,{fontSize:12})});

  card(s,0.5,3.9,5.8,2.5);
  s.addText("Panel Interaction",{x:0.8,y:4.0,w:5,h:0.4,fontSize:16,color:GRN,bold:true,fontFace:"Arial"});
  s.addText("Click legend to isolate series\nCtrl+Click for multi-select\nHover for tooltip values\nClick panel title \u2192 View/Edit\nDrag time range to zoom",{x:0.8,y:4.5,w:5,h:1.7,...B(null,{fontSize:12})});

  card(s,7.0,3.9,5.8,2.5);
  s.addText("Alerting",{x:7.3,y:4.0,w:5,h:0.4,fontSize:16,color:RED,bold:true,fontFace:"Arial"});
  s.addText("Alertmanager: :9093\nSilence: Alerting \u2192 Silences\nActive: Alerting \u2192 Alert rules\nHistory: Alerting \u2192 Alert history\n\n40 rule groups configured",{x:7.3,y:4.5,w:5,h:1.7,...B(null,{fontSize:12})});
}

// ===== SLIDE 10: ALERT RESPONSE PLAYBOOK =====
{
  const s = slide("Alert Response Playbook");
  const alerts = [
    ["OllamaWorkerDown","CRITICAL","All 12 LLM models unavailable","1. Check pod: kubectl describe pod ollama-worker-xxx -n ai-platform\n2. Check logs: kubectl logs deploy/ollama-worker -n ai-platform\n3. Check node resources: kubectl top nodes\n4. Restart if needed: kubectl rollout restart deploy/ollama-worker -n ai-platform"],
    ["IngressControllerDown","CRITICAL","All external traffic blocked","1. Check pod: kubectl get pods -n ingress-nginx\n2. Check logs: kubectl logs deploy/ingress-nginx-controller -n ingress-nginx\n3. Check NodePort: netstat -tlnp | grep 32231\n4. Restart: kubectl rollout restart deploy/ingress-nginx-controller -n ingress-nginx"],
    ["DifyAPIDown","CRITICAL","Dify platform unavailable","1. Check pods: kubectl get pods -n dify | grep dify-api\n2. Check DB: kubectl get pods -n dify-plus | grep db-postgres\n3. Check logs: kubectl logs deploy/dify-api -n dify --tail=100\n4. Check config: kubectl describe deploy/dify-api -n dify"],
    ["PVCUsageCritical","CRITICAL","Risk of data loss","1. Check PVC: kubectl get pvc -A\n2. Check disk: df -h on nodes\n3. Clean up: Remove unused data/images\n4. Expand PVC if supported"],
    ["CPUThrottlingHigh","WARNING","Performance degradation","1. Check top pods: kubectl top pods -A --sort-by=cpu\n2. Review resource limits: kubectl describe deploy/xxx\n3. Increase CPU limits or scale pods\n4. Check node capacity: kubectl top nodes"]
  ];
  alerts.forEach((a,i)=>{
    const y=1.1+i*1.2;
    card(s,0.5,y,12.3,1.1);
    s.addText(a[0],{x:0.7,y:y+0.05,w:3,h:0.3,fontSize:13,color:WHT,bold:true,fontFace:"Arial"});
    s.addText(a[1],{x:3.8,y:y+0.05,w:1.5,h:0.3,fontSize:11,color:a[1]==="CRITICAL"?RED:YEL,bold:true,fontFace:"Arial"});
    s.addText(a[2],{x:5.5,y:y+0.05,w:3,h:0.3,...B(null,{fontSize:11,color:GRY})});
    s.addText(a[3],{x:0.7,y:y+0.4,w:11.5,h:0.65,...B(null,{fontSize:9})});
  });
}

// ===== SLIDE 11: MONITORING COVERAGE MATRIX =====
{
  const s = slide("Monitoring Coverage Matrix");
  const headers = ["Service","Namespace","ServiceMonitor","PrometheusRule","Grafana Dashboard","Status"];
  const hx = [0.5,3.0,5.5,8.0,10.5,12.5];
  headers.forEach((h,i)=>s.addText(h,{x:hx[i],y:1.1,w:2.5,h:0.35,fontSize:11,color:ACC,bold:true,fontFace:"Arial"}));

  const svcs = [
    ["ollama-master","ai-platform","\u2705","\u2705","\u2705 LLM","\u2705"],
    ["ollama-worker","ai-platform","\u2705","\u2705","\u2705 LLM","\u2705"],
    ["litellm","ai-platform","\u2705","\u2705","\u2705 LLM","\u2705"],
    ["open-webui","ai-platform","\u2705","\u2705","\u2705 LLM","\u2705"],
    ["code-server","ai-platform","\u2705","\u2705","\u2705 CS","\u2705"],
    ["dify-api","dify","\u2705","\u2705","\u2705 Dify","\u2705"],
    ["dify-web","dify","\u2705","\u2705","\u2705 Dify","\u2705"],
    ["dify-worker","dify","\u2705","\u2705","\u2705 Dify","\u2705"],
    ["dify-plugin-daemon","dify","\u2705","\u2705","\u2705 Dify","\u2705"],
    ["smtp-debug","dify","\u2705","-","\u2705 Dify","\u2705"],
    ["db-postgres","dify-plus","\u2705","\u2705","\u2705 Dify","\u2705"],
    ["redis","dify-plus","\u2705","\u2705","\u2705 Dify","\u2705"],
    ["weaviate","dify-plus","\u2705","\u2705","\u2705 Dify","\u2705"],
    ["ingress-nginx","ingress-nginx","\u2705","\u2705","\u2705 Infra","\u2705"],
    ["rancher-agent","cattle-system","\u2705","\u2705","\u2705 Infra","\u2705"],
    ["local-path","local-path-storage","\u2705","-","\u2705 Infra","\u2705"],
  ];
  svcs.forEach((r,i)=>{
    const y=1.55+i*0.35;
    r.forEach((v,j)=>s.addText(v,{x:hx[j],y,w:2.5,h:0.3,...B(null,{fontSize:9,color:j===5?GRN:WHT})}));
  });
}

// ===== SLIDE 12: SUMMARY =====
{
  const s = slide("Summary & Quick Reference");
  card(s,0.5,1.1,5.8,2.5);
  s.addText("Monitoring Stack",{x:0.8,y:1.2,w:5,h:0.4,fontSize:16,color:ACC,bold:true,fontFace:"Arial"});
  s.addText("\u2022 Prometheus: Metrics collection\n\u2022 Grafana: Visualization (4 dashboards)\n\u2022 Alertmanager: Alert routing\n\u2022 39 ServiceMonitors\n\u2022 40 PrometheusRules\n\u2022 70+ Dashboard panels",{x:0.8,y:1.7,w:5,h:1.7,...B(null,{fontSize:12})});

  card(s,7.0,1.1,5.8,2.5);
  s.addText("Quick Links",{x:7.3,y:1.2,w:5,h:0.4,fontSize:16,color:A2,bold:true,fontFace:"Arial"});
  s.addText("Grafana: http://10.167.2.175:30082\nPrometheus: http://10.167.2.175:9090\nAlertmanager: http://10.167.2.175:9093\nRancher: https://10.167.2.175\n\nCredentials: admin / prom-operator",{x:7.3,y:1.7,w:5,h:1.7,...B(null,{fontSize:12})});

  card(s,0.5,3.9,12.3,2.8);
  s.addText("Dashboard Quick Reference",{x:0.8,y:4.0,w:5,h:0.4,fontSize:16,color:GRN,bold:true,fontFace:"Arial"});
  const refs = [
    ["LLM Services","llm-services","Ollama + Litellm + Open-WebUI","17 panels"],
    ["Dify Platform","dify-platform","Dify Core + Database + Redis + Weaviate","19 panels"],
    ["Infrastructure","infrastructure","Ingress + Nodes + Storage + Rancher","19 panels"],
    ["Code-Server IDE","codeserver","Pod Status + Performance + Health","15 panels"]
  ];
  const rx = [0.8,3.5,6.5,10.5];
  refs.forEach((r,i)=>{
    const y=4.55+i*0.5;
    r.forEach((v,j)=>s.addText(v,{x:rx[j],y,w:3,h:0.4,...B(null,{fontSize:11,color:j===0?GRN:WHT})}));
  });
}

pptx.writeFile({fileName:"D:\\dify-install\\monitoring\\Enterprise_Monitoring_Manual.pptx"})
  .then(()=>console.log("Monitoring manual PPT created!"))
  .catch(e=>console.error("Error:",e));