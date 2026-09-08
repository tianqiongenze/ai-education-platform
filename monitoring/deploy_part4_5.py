#!/usr/bin/env python3
"""Part 4-5: Enhanced Grafana dashboards + PrometheusRules"""
import subprocess, json, os

BASE = r"D:\dify-install"
MONITORING = os.path.join(BASE, "monitoring")

def kapply(yaml_str):
    p = subprocess.run(["kubectl", "apply", "-f", "-"], input=yaml_str, capture_output=True, text=True, timeout=60)
    print(f"  {p.stdout.strip()}")
    if p.stderr.strip():
        print(f"  stderr: {p.stderr.strip()[:200]}")
    return p.returncode == 0

def create_cm(name, filename, data):
    return {
        "apiVersion": "v1", "kind": "ConfigMap",
        "metadata": {
            "name": name, "namespace": "monitoring",
            "labels": {"grafana_dashboard": "1", "app": "kube-prometheus-stack-grafana"}
        },
        "data": {filename: json.dumps(data, indent=2)}
    }

BASE_DS = {"type": "prometheus", "uid": "prometheus"}
def row(title, y):
    return {"collapsed": False, "datasource": BASE_DS, "gridPos": {"h": 1, "w": 24, "x": 0, "y": y}, "id": y+1, "panels": [], "title": title, "type": "row"}

def stat(title, expr, x, y, w=4, h=2, unit="none", thresholds=None):
    if thresholds is None:
        thresholds = {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 0}]}
    return {"datasource": BASE_DS, "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": thresholds, "unit": unit}}, "gridPos": {"h": h, "w": w, "x": x, "y": y}, "id": 100+x+y, "options": {"colorMode": "background", "graphMode": "area", "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "textMode": "auto"}, "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "stat"}

def ts(title, exprs, x, y, w=12, h=6, unit="short"):
    targets = [{"expr": e, "legendFormat": l, "refId": chr(65+i)} for i,(e,l) in enumerate(exprs)]
    return {"datasource": BASE_DS, "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "custom": {"drawStyle": "line", "fillOpacity": 10, "lineWidth": 2, "showPoints": "never", "spanNulls": True, "stacking": {"mode": "none", "group": "A"}}, "unit": unit}, "overrides": []}, "gridPos": {"h": h, "w": w, "x": x, "y": y}, "id": 200+x+y, "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "last"]}, "tooltip": {"mode": "multi"}}, "targets": targets, "title": title, "type": "timeseries"}

# ===================== INFRASTRUCTURE DASHBOARD =====================
print("Building Infrastructure Dashboard v2...")
infra_panels = [
    row("🟠 Cluster Nodes", 0),
    stat("Nodes Total", 'count(kube_node_info)', 0, 1, 3),
    stat("Nodes Ready", 'count(kube_node_status_condition{condition="Ready",status="true"})', 3, 1, 3),
    stat("CPU Cores", 'sum(kube_node_status_capacity{resource="cpu"})', 6, 1, 3),
    stat("Memory GB", 'sum(kube_node_status_capacity{resource="memory"})/1073741824', 9, 1, 3),
    stat("Pods Running", 'count(kube_pod_info)', 12, 1, 3),
    stat("Namespaces", 'count(kube_namespace_created)', 15, 1, 3),
    stat("PVs", 'count(kube_persistentvolume_info)', 18, 1, 3),
    stat("Services", 'count(kube_service_info)', 21, 1, 3),
    ts("Node CPU Usage %", [('100-avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))by(instance)*100', '{{instance}}')], 0, 4, 12, 6, "percent"),
    ts("Node Memory Usage %", [('100*(1-(node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes))', '{{instance}}')], 12, 4, 12, 6, "percent"),
    ts("Node Disk Usage %", [('100*(1-(node_filesystem_avail_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"}))', '{{instance}}')], 0, 10, 12, 6, "percent"),
    ts("Node Network RX/TX", [('rate(node_network_receive_bytes_total[5m])', '{{instance}} rx'), ('rate(node_network_transmit_bytes_total[5m])', '{{instance}} tx')], 12, 10, 12, 6, "Bps"),
    row("🟢 Namespace Resources", 16),
    ts("CPU by Namespace", [('sum(rate(container_cpu_usage_seconds_total[5m]))by(namespace)', '{{namespace}}')], 0, 17, 24, 7, "cpus"),
    ts("Memory by Namespace", [('sum(container_memory_working_set_bytes)by(namespace)', '{{namespace}}')], 0, 24, 24, 7, "bytes"),
    ts("Pod Count by Namespace", [('count(kube_pod_info)by(namespace)', '{{namespace}}')], 0, 31, 12, 6, "short"),
    ts("Restarts by Namespace", [('sum(rate(kube_pod_container_status_restarts_total[5m]))by(namespace)', '{{namespace}}')], 12, 31, 12, 6, "short"),
    row("🔴 Ingress & Network", 37),
    ts("Ingress Request Rate", [('sum(rate(nginx_ingress_controller_requests[5m]))by(ingress)', '{{ingress}}')], 0, 38, 12, 6, "reqps"),
    ts("Ingress 5xx Rate", [('sum(rate(nginx_ingress_controller_requests{status=~"5.."}[5m]))by(ingress)', '{{ingress}}')], 12, 38, 12, 6, "reqps"),
    ts("Ingress P99 Latency", [('histogram_quantile(0.99,sum(rate(nginx_ingress_controller_request_duration_seconds_bucket[5m]))by(le))', 'P99')], 0, 44, 12, 6, "s"),
    row("🟣 Storage", 50),
    ts("PV Usage %", [('kubelet_volume_stats_used_bytes/kubelet_volume_stats_capacity_bytes*100', '{{persistentvolumeclaim}}')], 0, 51, 24, 6, "percent"),
]

infra = {
    "annotations": {"list": []}, "editable": True, "gnetId": None, "graphTooltip": 1,
    "links": [], "panels": infra_panels, "refresh": "30s", "schemaVersion": 38, "style": "dark",
    "tags": ["enterprise", "infrastructure"],
    "templating": {"list": []}, "time": {"from": "now-6h", "to": "now"}, "timepicker": {},
    "timezone": "browser", "title": "Infrastructure Overview - Enterprise (Enhanced)", "uid": "infrastructure-v2", "version": 1
}
cm = json.dumps(create_cm("grafana-dashboard-infrastructure-v2", "grafana-dashboard-infrastructure-v2.json", infra), indent=2)
with open(os.path.join(MONITORING, "grafana-dashboard-infra-v2-cm.yaml"), "w") as f:
    f.write(cm)
kapply(cm)

# ===================== CODE-SERVER DASHBOARD =====================
print("Building Code-Server Dashboard v2...")
cs_panels = [
    row("🟢 Overview", 0),
    stat("Total Pods", 'count(up{namespace="ai-platform",pod=~"code-server-.*"}==1)', 0, 1, 3),
    stat("Ready Pods", 'count(kube_pod_status_ready{namespace="ai-platform",pod=~"code-server-.*",condition="true"})', 3, 1, 3),
    stat("Restarts (24h)", 'sum(increase(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"}[24h]))', 6, 1, 3),
    stat("Avg CPU/Pod", 'avg(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m]))', 9, 1, 3, "cpus"),
    stat("Avg Mem/Pod", 'avg(container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"})', 12, 1, 3, "bytes"),
    stat("Total CPU", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m]))', 15, 1, 3, "cpus"),
    stat("Total Mem", 'sum(container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"})', 18, 1, 3, "bytes"),
    stat("Avg Restart/H", 'sum(increase(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"}[1h]))/count(kube_pod_info{namespace="ai-platform",pod=~"code-server-.*"})', 21, 1, 3, thresholds={"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 0.5}, {"color": "red", "value": 2}]}),
    ts("CPU Per Pod", [('rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', '{{pod}}')], 0, 4, 24, 7, "cpus"),
    ts("Memory Per Pod", [('container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"}', '{{pod}}')], 0, 11, 24, 7, "bytes"),
    row("🔵 Top Consumers", 18),
    ts("CPU Top 10", [('topk(10,rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m]))', '{{pod}}')], 0, 19, 12, 7, "cpus"),
    ts("Memory Top 10", [('topk(10,container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"})', '{{pod}}')], 12, 19, 12, 7, "bytes"),
    ts("Network RX Per Pod", [('rate(container_network_receive_bytes_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', '{{pod}}')], 0, 26, 12, 7, "Bps"),
    ts("Network TX Per Pod", [('rate(container_network_transmit_bytes_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', '{{pod}}')], 12, 26, 12, 7, "Bps"),
    row("🟣 Health & Stability", 33),
    ts("Restarts (5min)", [('sum(increase(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"}[5m]))by(pod)', '{{pod}}')], 0, 34, 12, 6, "short"),
    ts("Phase Distribution", [('sum(kube_pod_status_phase{namespace="ai-platform",pod=~"code-server-.*"})by(phase)', '{{phase}}')], 12, 34, 12, 6, "short"),
]

cs_dash = {
    "annotations": {"list": []}, "editable": True, "gnetId": None, "graphTooltip": 1,
    "links": [], "panels": cs_panels, "refresh": "30s", "schemaVersion": 38, "style": "dark",
    "tags": ["enterprise", "code-server"],
    "templating": {"list": []}, "time": {"from": "now-6h", "to": "now"}, "timepicker": {},
    "timezone": "browser", "title": "Code-Server IDE - Enterprise (Enhanced)", "uid": "codeserver-v2", "version": 1
}
cm2 = json.dumps(create_cm("grafana-dashboard-codeserver-v2", "grafana-dashboard-codeserver-v2.json", cs_dash), indent=2)
kapply(cm2)

# ===================== PROMETHEUS RULES =====================
print("Deploying enhanced PrometheusRules...")
rules = """apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: enterprise-alert-rules-v2
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  groups:
  - name: ollama-model-alerts
    rules:
    - alert: OllamaModelNotLoaded
      expr: ollama_model_available == 0
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Ollama model {{ $labels.model }} not available on {{ $labels.source }}"
    - alert: OllamaAPIUnhealthy
      expr: ollama_api_health == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Ollama API unhealthy on {{ $labels.source }}"
    - alert: OllamaHighAPILatency
      expr: rate(ollama_api_latency_seconds_sum[5m])/rate(ollama_api_latency_seconds_count[5m]) > 5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Ollama API latency > 5s on {{ $labels.source }}/{{ $labels.endpoint }}"
    - alert: OllamaHighErrorRate
      expr: rate(ollama_api_errors_total[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Ollama error rate: {{ $value }}/s on {{ $labels.source }}"
    - alert: OllamaHighMemory
      expr: container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}/container_spec_memory_limit_bytes{namespace="ai-platform",pod=~"ollama-.*"} > 0.9
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "Ollama pod {{ $labels.pod }} memory > 90%"
  - name: litellm-alerts
    rules:
    - alert: LitellmGatewayDown
      expr: litellm_health{endpoint="health"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Litellm gateway is down"
    - alert: LitellmHighErrorRate
      expr: rate(litellm_api_proxy_errors_total[5m]) > 0.2
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Litellm error rate: {{ $value }}/s on {{ $labels.endpoint }}"
  - name: dify-alerts
    rules:
    - alert: DifyAPIDown
      expr: dify_api_health{service="dify-api"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Dify API is down"
    - alert: DifyWebDown
      expr: dify_api_health{service="dify-web"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Dify Web is down"
    - alert: DifyHighPodRestarts
      expr: rate(kube_pod_container_status_restarts_total{namespace="dify"}[1h]) > 0.1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Dify pod {{ $labels.pod }} restarts frequently ({{ $value }}/h)"
  - name: exporter-alerts
    rules:
    - alert: ExporterDown
      expr: up{namespace="default",pod=~".*-prometheus-exporter-.*"} == 0
      for: 3m
      labels:
        severity: critical
      annotations:
        summary: "Metrics exporter {{ $labels.pod }} is down"
  - name: infrastructure-alerts
    rules:
    - alert: NodeHighCPU
      expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance) * 100) > 90
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Node {{ $labels.instance }} CPU > 90%"
    - alert: NodeHighMemory
      expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Node {{ $labels.instance }} memory > 90%"
    - alert: NodeHighDisk
      expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 85
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Node {{ $labels.instance }} disk > 85%"
    - alert: PVHighUsage
      expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.8
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "PV {{ $labels.persistentvolumeclaim }} usage > 80%"
    - alert: CodeServerPodDown
      expr: count(up{namespace="ai-platform",pod=~"code-server-.*"}==1) < 18
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Code-server pods below 18 ({{ $value }} running)"
    - alert: HighPodRestarts
      expr: rate(kube_pod_container_status_restarts_total[1h]) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Pod {{ $labels.pod }} restarting > 1/hour in {{ $labels.namespace }}"
"""
kapply(rules)

print("\nDone! Dashboards + Rules deployed.")
print("Access: http://10.167.2.175:30082")
print("Dashboards: LLM Services v2, Dify Platform v2, Infrastructure v2, Code-Server v2")