#!/usr/bin/env python3
"""Generate and deploy Grafana dashboards for all enterprise services."""
import json, subprocess, os

BASE = os.path.dirname(os.path.abspath(__file__))

def make_stat(title, expr, gridPos, thresholds=None):
    if thresholds is None:
        thresholds = {"mode": "absolute", "steps": [
            {"color": "red", "value": None}, {"color": "green", "value": 0}]}
    return {
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [],
            "thresholds": thresholds, "unit": "none"}},
        "gridPos": gridPos, "id": 0,
        "options": {"colorMode": "background", "graphMode": "area", "justifyMode": "auto",
            "orientation": "auto", "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto"},
        "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "stat"
    }

def make_timeseries(title, expr, gridPos, unit="short", legend="{{pod}}"):
    return {
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"},
            "custom": {"drawStyle": "line", "fillOpacity": 10, "lineWidth": 2,
                "showPoints": "never", "spanNulls": False, "stacking": {"mode": "none", "group": "A"}},
            "unit": unit}, "overrides": []},
        "gridPos": gridPos, "id": 0,
        "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "last"]},
            "tooltip": {"mode": "multi"}},
        "targets": [{"expr": expr, "legendFormat": legend, "refId": "A"}],
        "title": title, "type": "timeseries"
    }

def make_gauge(title, expr, gridPos, unit="percent", max_val=100):
    return {
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {"defaults": {"color": {"mode": "thresholds"},
            "thresholds": {"mode": "absolute", "steps": [
                {"color": "green", "value": None}, {"color": "yellow", "value": 70},
                {"color": "red", "value": 85}]},
            "unit": unit, "min": 0, "max": max_val}},
        "gridPos": gridPos, "id": 0,
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "showThresholdLabels": True, "showThresholdMarkers": True},
        "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "gauge"
    }

def make_row(title, gridPos):
    return {"collapsed": False, "datasource": {"type": "prometheus", "uid": "prometheus"},
        "gridPos": gridPos, "id": 0, "panels": [], "title": title, "type": "row"}

def make_table(title, expr, gridPos):
    return {
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {"defaults": {"custom": {"align": "auto"}}},
        "gridPos": gridPos, "id": 0,
        "options": {"showHeader": True},
        "targets": [{"expr": expr, "format": "table", "refId": "A"}],
        "title": title, "type": "table"
    }

def build_dashboard(title, uid, panels):
    pid = 1
    for p in panels:
        p["id"] = pid
        pid += 1
    return {
        "annotations": {"list": []}, "editable": True, "gnetId": None,
        "graphTooltip": 1, "id": None, "links": [], "panels": panels,
        "refresh": "30s", "schemaVersion": 38, "style": "dark",
        "tags": ["enterprise", "ai-platform"], "templating": {"list": []},
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {}, "timezone": "browser",
        "title": title, "uid": uid, "version": 1
    }

# ===== DASHBOARD 1: LLM Services =====
llm_panels = [
    make_row("Ollama Runtime Engine", {"h": 1, "w": 24, "x": 0, "y": 0}),
    make_stat("Ollama Master", 'count(up{namespace="ai-platform",pod=~"ollama-master-.*"}==1)', {"h": 3, "w": 6, "x": 0, "y": 1}),
    make_stat("Ollama Worker", 'count(up{namespace="ai-platform",pod=~"ollama-worker-.*"}==1)', {"h": 3, "w": 6, "x": 6, "y": 1}),
    make_gauge("Ollama Memory %", 'avg(container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}/container_spec_memory_limit_bytes{namespace="ai-platform",pod=~"ollama-.*"})*100', {"h": 6, "w": 6, "x": 12, "y": 1}),
    make_timeseries("Ollama CPU Usage", 'rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"ollama-.*"}[5m])', {"h": 6, "w": 6, "x": 18, "y": 1}, "cpus"),
    make_timeseries("Ollama Memory Usage", 'container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}', {"h": 6, "w": 12, "x": 0, "y": 7}, "bytes"),

    make_row("Litellm Gateway", {"h": 1, "w": 24, "x": 0, "y": 13}),
    make_stat("Litellm Pods", 'count(up{namespace="ai-platform",pod=~"litellm-.*"}==1)', {"h": 3, "w": 4, "x": 0, "y": 14}),
    make_stat("Litellm 5xx Rate %", 'sum(rate(http_requests_total{namespace="ai-platform",status=~"5.."}[5m]))/sum(rate(http_requests_total{namespace="ai-platform"}[5m]))*100', {"h": 3, "w": 4, "x": 4, "y": 14}, {"mode":"absolute","steps":[{"color":"green","value":None},{"color":"yellow","value":1},{"color":"red","value":5}]}),
    make_gauge("Litellm Error %", 'sum(rate(http_requests_total{namespace="ai-platform",status=~"5.."}[5m]))/sum(rate(http_requests_total{namespace="ai-platform"}[5m]))*100', {"h": 6, "w": 4, "x": 8, "y": 14}, "percent", 20),
    make_timeseries("Litellm Request Rate", 'sum(rate(http_requests_total{namespace="ai-platform"}[5m]))', {"h": 6, "w": 6, "x": 12, "y": 14}, "reqps"),
    make_timeseries("Litellm Error Rate", 'sum(rate(http_requests_total{namespace="ai-platform",status=~"5.."}[5m]))', {"h": 6, "w": 6, "x": 18, "y": 14}, "reqps"),
    make_timeseries("Litellm Latency P95", 'histogram_quantile(0.95,sum(rate(http_request_duration_seconds_bucket{namespace="ai-platform"}[5m]))by(le))', {"h": 6, "w": 12, "x": 0, "y": 20}, "s"),

    make_row("Open-WebUI", {"h": 1, "w": 24, "x": 0, "y": 26}),
    make_stat("Open-WebUI Status", 'count(up{namespace="ai-platform",pod=~"open-webui-.*"}==1)', {"h": 3, "w": 6, "x": 0, "y": 27}),
    make_timeseries("Open-WebUI Request Rate", 'sum(rate(http_requests_total{namespace="ai-platform",pod=~"open-webui-.*"}[5m]))', {"h": 6, "w": 9, "x": 6, "y": 27}, "reqps"),
    make_timeseries("Open-WebUI CPU", 'rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"open-webui-.*"}[5m])', {"h": 6, "w": 9, "x": 15, "y": 27}, "cpus"),
]

# ===== DASHBOARD 2: Dify Platform =====
dify_panels = [
    make_row("Dify Core Services (dify namespace)", {"h": 1, "w": 24, "x": 0, "y": 0}),
    make_stat("Dify API Pods", 'count(up{namespace="dify",pod=~"dify-api-.*"}==1)', {"h": 3, "w": 4, "x": 0, "y": 1}),
    make_stat("Dify Web Pods", 'count(up{namespace="dify",pod=~"dify-web-.*"}==1)', {"h": 3, "w": 4, "x": 4, "y": 1}),
    make_stat("Dify Worker Pods", 'count(up{namespace="dify",pod=~"dify-worker-.*"}==1)', {"h": 3, "w": 4, "x": 8, "y": 1}),
    make_stat("Plugin Daemon", 'count(up{namespace="dify",pod=~"dify-plugin-daemon-.*"}==1)', {"h": 3, "w": 4, "x": 12, "y": 1}),
    make_stat("SMTP Debug", 'count(up{namespace="dify",pod=~"smtp-debug-.*"}==1)', {"h": 3, "w": 4, "x": 16, "y": 1}),
    make_timeseries("Dify API Request Rate", 'sum(rate(http_requests_total{namespace="dify",pod=~"dify-api-.*"}[5m]))', {"h": 6, "w": 8, "x": 0, "y": 4}, "reqps"),
    make_timeseries("Dify API Error Rate", 'sum(rate(http_requests_total{namespace="dify",pod=~"dify-api-.*",status=~"5.."}[5m]))', {"h": 6, "w": 8, "x": 8, "y": 4}, "reqps"),
    make_timeseries("Dify API Latency P95", 'histogram_quantile(0.95,sum(rate(http_request_duration_seconds_bucket{namespace="dify",pod=~"dify-api-.*"}[5m]))by(le))', {"h": 6, "w": 8, "x": 16, "y": 4}, "s"),
    make_timeseries("Dify CPU Usage", 'rate(container_cpu_usage_seconds_total{namespace="dify"}[5m])', {"h": 6, "w": 12, "x": 0, "y": 10}, "cpus"),
    make_timeseries("Dify Memory Usage", 'container_memory_working_set_bytes{namespace="dify"}', {"h": 6, "w": 12, "x": 12, "y": 10}, "bytes"),

    make_row("Dify Infrastructure (dify-plus namespace)", {"h": 1, "w": 24, "x": 0, "y": 16}),
    make_stat("PostgreSQL", 'count(up{namespace="dify-plus",pod=~"db-postgres-.*"}==1)', {"h": 3, "w": 4, "x": 0, "y": 17}),
    make_stat("Redis", 'count(up{namespace="dify-plus",pod=~"redis-.*"}==1)', {"h": 3, "w": 4, "x": 4, "y": 17}),
    make_stat("Weaviate", 'count(up{namespace="dify-plus",pod=~"weaviate-.*"}==1)', {"h": 3, "w": 4, "x": 8, "y": 17}),
    make_stat("Mail Server", 'count(up{namespace="dify-plus",pod=~"mail-server-.*"}==1)', {"h": 3, "w": 4, "x": 12, "y": 17}),
    make_timeseries("PostgreSQL Memory", 'container_memory_working_set_bytes{namespace="dify-plus",pod=~"db-postgres-.*"}', {"h": 6, "w": 8, "x": 0, "y": 20}, "bytes"),
    make_timeseries("Redis Memory", 'container_memory_working_set_bytes{namespace="dify-plus",pod=~"redis-.*"}', {"h": 6, "w": 8, "x": 8, "y": 20}, "bytes"),
    make_timeseries("Weaviate Memory", 'container_memory_working_set_bytes{namespace="dify-plus",pod=~"weaviate-.*"}', {"h": 6, "w": 8, "x": 16, "y": 20}, "bytes"),
]

# ===== DASHBOARD 3: Infrastructure =====
infra_panels = [
    make_row("Ingress NGINX", {"h": 1, "w": 24, "x": 0, "y": 0}),
    make_stat("Ingress Controller", 'count(up{namespace="ingress-nginx",pod=~"ingress-nginx-controller-.*"}==1)', {"h": 3, "w": 4, "x": 0, "y": 1}),
    make_stat("Ingress 5xx Rate %", 'sum(rate(nginx_ingress_controller_requests{status=~"5.."}[5m]))/sum(rate(nginx_ingress_controller_requests[5m]))*100', {"h": 3, "w": 4, "x": 4, "y": 1}, {"mode":"absolute","steps":[{"color":"green","value":None},{"color":"yellow","value":1},{"color":"red","value":5}]}),
    make_stat("Ingress 4xx Rate %", 'sum(rate(nginx_ingress_controller_requests{status=~"4.."}[5m]))/sum(rate(nginx_ingress_controller_requests[5m]))*100', {"h": 3, "w": 4, "x": 8, "y": 1}, {"mode":"absolute","steps":[{"color":"green","value":None},{"color":"yellow","value":5},{"color":"red","value":15}]}),
    make_gauge("Ingress Error %", 'sum(rate(nginx_ingress_controller_requests{status=~"5.."}[5m]))/sum(rate(nginx_ingress_controller_requests[5m]))*100', {"h": 6, "w": 4, "x": 12, "y": 1}, "percent", 10),
    make_timeseries("Ingress Request Rate", 'sum(rate(nginx_ingress_controller_requests[5m]))', {"h": 6, "w": 8, "x": 16, "y": 1}, "reqps"),
    make_timeseries("Ingress P99 Latency", 'histogram_quantile(0.99,sum(rate(nginx_ingress_controller_request_duration_seconds_bucket[5m]))by(le))', {"h": 6, "w": 12, "x": 0, "y": 7}, "s"),
    make_timeseries("Ingress 4xx/5xx Errors", 'sum(rate(nginx_ingress_controller_requests{status=~"[45].."}[5m]))by(status)', {"h": 6, "w": 12, "x": 12, "y": 7}, "reqps", "{{status}}"),

    make_row("Nodes", {"h": 1, "w": 24, "x": 0, "y": 13}),
    make_stat("Node Count", 'count(kube_node_status_condition{condition="Ready",status="true"})', {"h": 3, "w": 4, "x": 0, "y": 14}),
    make_gauge("CPU Usage %", '100-avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))*100', {"h": 6, "w": 5, "x": 4, "y": 14}, "percent"),
    make_gauge("Memory Usage %", '(1-node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)*100', {"h": 6, "w": 5, "x": 9, "y": 14}, "percent"),
    make_gauge("Disk Usage %", '(1-node_filesystem_avail_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"})*100', {"h": 6, "w": 5, "x": 14, "y": 14}, "percent"),
    make_timeseries("Node CPU", '100-avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))*100', {"h": 6, "w": 12, "x": 0, "y": 20}, "percent", "{{instance}}"),
    make_timeseries("Node Memory", '(1-node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)*100', {"h": 6, "w": 12, "x": 12, "y": 20}, "percent", "{{instance}}"),

    make_row("Storage & Rancher", {"h": 1, "w": 24, "x": 0, "y": 26}),
    make_table("PVC Usage", 'kubelet_volume_stats_used_bytes/kubelet_volume_stats_capacity_bytes*100', {"h": 6, "w": 12, "x": 0, "y": 27}),
    make_stat("Rancher Agent", 'count(up{namespace="cattle-system",pod=~"cattle-cluster-agent-.*"}==1)', {"h": 3, "w": 6, "x": 12, "y": 27}),
    make_stat("Local Path Provisioner", 'count(up{namespace="local-path-storage"}==1)', {"h": 3, "w": 6, "x": 18, "y": 27}),
]

# ===== DASHBOARD 4: Code-Server =====
cs_panels = [
    make_row("Overview", {"h": 1, "w": 24, "x": 0, "y": 0}),
    make_stat("Ready Pods", 'kube_deployment_status_replicas_ready{namespace="ai-platform",deployment="code-server"}', {"h": 3, "w": 4, "x": 0, "y": 1}),
    make_stat("Desired Pods", 'kube_deployment_spec_replicas{namespace="ai-platform",deployment="code-server"}', {"h": 3, "w": 4, "x": 4, "y": 1}),
    make_stat("Available Pods", 'kube_deployment_status_replicas_available{namespace="ai-platform",deployment="code-server"}', {"h": 3, "w": 4, "x": 8, "y": 1}),
    make_stat("Pod Restarts", 'sum(rate(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"}[15m]))', {"h": 3, "w": 4, "x": 12, "y": 1}, {"mode":"absolute","steps":[{"color":"green","value":None},{"color":"yellow","value":0.01},{"color":"red","value":0.1}]}),
    make_timeseries("Pod Count History", 'kube_deployment_status_replicas_ready{namespace="ai-platform",deployment="code-server"}', {"h": 6, "w": 12, "x": 0, "y": 4}, "short"),
    make_gauge("Pod Readiness %", 'kube_deployment_status_replicas_ready{namespace="ai-platform",deployment="code-server"}/kube_deployment_spec_replicas{namespace="ai-platform",deployment="code-server"}*100', {"h": 6, "w": 4, "x": 12, "y": 4}),

    make_row("Performance", {"h": 1, "w": 24, "x": 0, "y": 10}),
    make_timeseries("CPU Usage per Pod", 'rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', {"h": 6, "w": 12, "x": 0, "y": 11}, "cpus"),
    make_timeseries("Memory Usage per Pod", 'container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"}', {"h": 6, "w": 12, "x": 12, "y": 11}, "bytes"),
    make_gauge("Avg CPU %", 'avg(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])/container_spec_cpu_quota{namespace="ai-platform",pod=~"code-server-.*"}*container_spec_cpu_period{namespace="ai-platform",pod=~"code-server-.*"})*100', {"h": 6, "w": 6, "x": 0, "y": 17}),
    make_gauge("Avg Memory %", 'avg(container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"}/container_spec_memory_limit_bytes{namespace="ai-platform",pod=~"code-server-.*"})*100', {"h": 6, "w": 6, "x": 6, "y": 17}),
    make_timeseries("CPU Throttling", 'rate(container_cpu_cfs_throttled_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', {"h": 6, "w": 12, "x": 12, "y": 17}, "short"),

    make_row("Health", {"h": 1, "w": 24, "x": 0, "y": 23}),
    make_table("Pod Status", 'kube_pod_status_ready{namespace="ai-platform",pod=~"code-server-.*"}', {"h": 6, "w": 24, "x": 0, "y": 24}),
]

dashboards = [
    ("LLM Services - Enterprise Monitoring", "llm-services", llm_panels, "grafana-dashboard-llm.json"),
    ("Dify Platform - Enterprise Monitoring", "dify-platform", dify_panels, "grafana-dashboard-dify.json"),
    ("Infrastructure - Enterprise Monitoring", "infrastructure", infra_panels, "grafana-dashboard-infra.json"),
    ("Code-Server IDE - Enterprise Monitoring", "codeserver", cs_panels, "grafana-dashboard-codeserver.json"),
]

for title, uid, panels, filename in dashboards:
    dashboard = build_dashboard(title, uid, panels)
    filepath = os.path.join(BASE, filename)
    with open(filepath, "w") as f:
        json.dump(dashboard, f, indent=2)
    print(f"Created: {filename} ({len(panels)} panels)")

    # Deploy as ConfigMap
    cm_name = f"grafana-dashboard-{uid}"
    cm = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": cm_name,
            "namespace": "monitoring",
            "labels": {
                "grafana_dashboard": "1",
                "app": "kube-prometheus-stack-grafana"
            }
        },
        "data": {
            f"{cm_name}.json": json.dumps(dashboard)
        }
    }
    result = subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=json.dumps(cm), text=True, capture_output=True
    )
    print(f"  Deployed: {cm_name} -> {result.stdout.strip() or result.stderr.strip()}")

print("\nDone! All 4 dashboards created and deployed.")
print("Grafana: http://10.167.2.175:30082 (admin / prom-operator)")