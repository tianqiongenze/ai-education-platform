#!/c/Python314/python
"""Dify Platform Dashboard - uses REAL verified metrics.
Namespaces: dify (app), dify-plus (DB/redis/weaviate)
"""
import sys
sys.path.insert(0, "D:/dify-install")
from dashboard_lib import *
import json

P = [
    # ===== ROW 1: Dify Core Services Overview =====
    row("Dify Core Services (namespace: dify)", {"h":1,"w":24,"x":0,"y":0}),

    stat("Dify API Version", [("", "max(dify_api_info) by (version)")],
         {"h":3,"w":4,"x":0,"y":1}, unit="none", reduceLast=True),
    stat("API Pods Ready", [("", "sum(kube_pod_status_phase{namespace=\"dify\",phase=\"Running\",pod=~\"dify-api-.*\"})")],
         {"h":3,"w":4,"x":4,"y":1}, unit="none", thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Web Pods Ready", [("", "sum(kube_pod_status_phase{namespace=\"dify\",phase=\"Running\",pod=~\"dify-web-.*\"})")],
         {"h":3,"w":4,"x":8,"y":1}, unit="none"),
    stat("Worker Pods Running", [("", "sum(kube_pod_status_phase{namespace=\"dify\",phase=\"Running\",pod=~\"dify-worker-.*\"})")],
         {"h":3,"w":4,"x":12,"y":1}, unit="none"),
    stat("Plugin Daemon", [("", "sum(kube_pod_status_phase{namespace=\"dify\",phase=\"Running\",pod=~\"dify-plugin-daemon-.*\"})")],
         {"h":3,"w":4,"x":16,"y":1}, unit="none"),
    stat("Sandbox Pods", [("", "sum(kube_pod_status_phase{namespace=\"dify\",phase=\"Running\",pod=~\"dify-sandbox-.*\"})")],
         {"h":3,"w":4,"x":20,"y":1}, unit="none"),

    stat("Dify API Health", [("", "dify_exporter_up{exported_service=\"api\"}")],
         {"h":3,"w":4,"x":0,"y":4}, unit="none", color_mode="background",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Dify Web Health", [("", "dify_exporter_up{exported_service=\"web\"}")],
         {"h":3,"w":4,"x":4,"y":4}, unit="none", color_mode="background",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Worker Pods Total (all states)", [("", "count(kube_pod_info{namespace=\"dify\",pod=~\"dify-worker-.*\"})")],
         {"h":3,"w":4,"x":8,"y":4}, unit="none"),
    stat("Evicted Pods (dify)", [("", "sum(kube_pod_status_phase{namespace=\"dify\",phase=\"Failed\"})")],
         {"h":3,"w":4,"x":12,"y":4}, unit="none", color_mode="background",
         thresholds={"mode":"absolute","steps":[{"color":"green","value":None},{"color":"orange","value":1},{"color":"red","value":10}]}),
    stat("API Health Check (HTTP)", [("", "health_check_up{exported_endpoint=\"dify-api\"}")],
         {"h":3,"w":4,"x":16,"y":4}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Web Health Check (HTTP)", [("", "health_check_up{exported_endpoint=\"dify-web\"}")],
         {"h":3,"w":4,"x":20,"y":4}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),

    # ===== ROW: API Request Rate & Latency =====
    row("API Request Rate & Latency", {"h":1,"w":24,"x":0,"y":7}),

    ts("API Request Rate (req/s)", [
        ("API", "sum(rate(dify_exporter_latency_sec_count{exported_service=\"api\"}[5m]))"),
        ("Web", "sum(rate(dify_exporter_latency_sec_count{exported_service=\"web\"}[5m]))"),
    ], {"h":7,"w":12,"x":0,"y":8}, unit="reqps", decimals=2),

    ts("API Response Time P50/P95/P99 (s)", [
        ("P50 api", "histogram_quantile(0.50, sum by (le) (rate(dify_exporter_latency_sec_bucket{exported_service=\"api\"}[5m])))"),
        ("P95 api", "histogram_quantile(0.95, sum by (le) (rate(dify_exporter_latency_sec_bucket{exported_service=\"api\"}[5m])))"),
        ("P99 api", "histogram_quantile(0.99, sum by (le) (rate(dify_exporter_latency_sec_bucket{exported_service=\"api\"}[5m])))"),
        ("P50 web", "histogram_quantile(0.50, sum by (le) (rate(dify_exporter_latency_sec_bucket{exported_service=\"web\"}[5m])))"),
        ("P95 web", "histogram_quantile(0.95, sum by (le) (rate(dify_exporter_latency_sec_bucket{exported_service=\"web\"}[5m])))"),
    ], {"h":7,"w":12,"x":12,"y":8}, unit="s", decimals=3),

    ts("API & Web Error Rate (errors/s)", [
        ("API", "sum(rate(dify_exporter_errors_total{exported_service=\"api\"}[5m]))"),
        ("Web", "sum(rate(dify_exporter_errors_total{exported_service=\"web\"}[5m]))"),
    ], {"h":7,"w":12,"x":0,"y":15}, unit="ops", decimals=3),

    ts("API Health Check Latency (ms)", [
        ("{{exported_endpoint}}", "health_check_response_time_ms{exported_endpoint=~\"dify-api|dify-web\"}"),
    ], {"h":7,"w":12,"x":12,"y":15}, unit="ms", decimals=1),

    # ===== ROW: Pod Resource Usage =====
    row("Dify Pod CPU & Memory (by pod)", {"h":1,"w":24,"x":0,"y":22}),

    ts("Dify API/Worker/Plugin CPU (cores)", [
        ("{{pod}}", "sum(rate(container_cpu_usage_seconds_total{namespace=\"dify\",pod=~\"dify-.*\",container!=\"\"}[5m])) by (pod)"),
    ], {"h":8,"w":12,"x":0,"y":23}, unit="cores", decimals=2),

    ts("Dify API/Worker/Plugin Memory (bytes)", [
        ("{{pod}}", "sum(container_memory_working_set_bytes{namespace=\"dify\",pod=~\"dify-.*\"}) by (pod)"),
    ], {"h":8,"w":12,"x":12,"y":23}, unit="bytes", decimals=0),

    ts("Dify Pod Restarts (total, top pods)", [
        ("{{pod}}", "sum by (pod) (kube_pod_container_status_restarts_total{namespace=\"dify\"})"),
    ], {"h":8,"w":12,"x":0,"y":31}, unit="none", decimals=0),

    ts("Dify Pod CPU vs Requests/Limits (cores)", [
        ("CPU used", "sum(rate(container_cpu_usage_seconds_total{namespace=\"dify\",pod=~\"dify-.*\"}[5m]))"),
        ("CPU request", "sum(kube_pod_container_resource_requests{namespace=\"dify\",resource=\"cpu\",unit=\"core\"})"),
        ("CPU limit", "sum(kube_pod_container_resource_limits{namespace=\"dify\",resource=\"cpu\",unit=\"core\"})"),
    ], {"h":8,"w":12,"x":12,"y":31}, unit="cores", decimals=2),

    # ===== ROW: Dify Infrastructure (dify-plus) =====
    row("Dify Infrastructure (namespace: dify-plus: PostgreSQL / Redis / Weaviate)", {"h":1,"w":24,"x":0,"y":39}),

    stat("PostgreSQL Up", [("", "pg_up")],
         {"h":3,"w":4,"x":0,"y":40}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Redis Up", [("", "redis_up")],
         {"h":3,"w":4,"x":4,"y":40}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Redis Connected Clients", [("", "redis_connected_clients")],
         {"h":3,"w":4,"x":8,"y":40}, unit="none"),
    stat("Redis DB Keys", [("", "sum(redis_db_keys)")],
         {"h":3,"w":4,"x":12,"y":40}, unit="none"),
    stat("Weaviate Pods", [("", "sum(kube_pod_status_phase{namespace=\"dify-plus\",phase=\"Running\",pod=~\"weaviate-.*\"})")],
         {"h":3,"w":4,"x":16,"y":40}, unit="none"),
    stat("PgBouncer Pods", [("", "sum(kube_pod_status_phase{namespace=\"dify-plus\",phase=\"Running\",pod=~\"pgbouncer-.*\"})")],
         {"h":3,"w":4,"x":20,"y":40}, unit="none"),

    ts("Redis Memory Usage (used vs max)", [
        ("used", "redis_memory_used_bytes"),
        ("max", "redis_memory_max_bytes"),
        ("peak", "redis_memory_used_peak_bytes"),
    ], {"h":8,"w":12,"x":0,"y":43}, unit="bytes", decimals=0),

    ts("Redis Memory Usage %", [
        ("{{instance}}", "redis_memory_used_bytes / redis_memory_max_bytes * 100"),
    ], {"h":8,"w":12,"x":12,"y":43}, unit="percent", decimals=1),

    ts("Redis Keys by DB", [
        ("{{db}}", "redis_db_keys"),
    ], {"h":8,"w":12,"x":0,"y":51}, unit="none", decimals=0),

    ts("Redis Commands Rate (top commands)", [
        ("{{cmd}}", "sum(rate(redis_commands_total[5m])) by (cmd)"),
    ], {"h":8,"w":12,"x":12,"y":51}, unit="ops", decimals=2),

    ts("Redis Keyspace Hit/Miss Rate", [
        ("hits", "sum(rate(redis_keyspace_hits_total[5m]))"),
        ("misses", "sum(rate(redis_keyspace_misses_total[5m]))"),
    ], {"h":8,"w":12,"x":0,"y":59}, unit="ops", decimals=2),

    ts("Dify-Plus Infra CPU & Memory (by pod)", [
        ("CPU {{pod}}", "sum(rate(container_cpu_usage_seconds_total{namespace=\"dify-plus\"}[5m])) by (pod)"),
    ], {"h":8,"w":12,"x":12,"y":59}, unit="cores", decimals=2),

    # ===== ROW: PVC Storage =====
    row("Storage & PVC Usage", {"h":1,"w":24,"x":0,"y":67}),

    bar("PVC Requested Storage by Namespace (GB)", [
        ("{{namespace}}", "sum(kube_persistentvolumeclaim_resource_requests_storage_bytes) by (namespace) / 1073741824"),
    ], {"h":8,"w":24,"x":0,"y":68}, unit="deckbytes", decimals=1),

    tbl("PVC Details (dify / dify-plus)", "kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace=~\"dify|dify-plus\"}",
        {"h":8,"w":24,"x":0,"y":76}, unit="bytes"),
]

dash = {"panels": P, "description": "Dify Platform monitoring - real data from dify/dify-plus namespaces, dify-exporter, redis/postgres exporters and health checks."}
res = push(dash, "dify-platform-v2", "Dify Platform - Enterprise (Enhanced)", ["enterprise","ai-platform","dify","llm"],
           namespace="monitoring", cm_name="grafana-dashboard-dify-platform-v2", cm_key="grafana-dashboard-dify-platform-v2.json")
print(json.dumps(res, indent=2))
