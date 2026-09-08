#!/c/Python314/python
"""AI Model / LLM Services Dashboard - REAL verified metrics.
Fixes the broken llm-services-v2 dashboard which referenced non-existent
litellm_api_proxy_* metrics. Uses real litellm_check_*, litellm_gateway_up,
ollama_* metrics from the python exporters.
"""
import sys
sys.path.insert(0, "D:/dify-install")
from dashboard_lib import *
import json

P = [
    # ===== ROW: Ollama Runtime Engine =====
    row("Ollama Runtime Engine (per-model metrics)", {"h":1,"w":24,"x":0,"y":0}),

    stat("Ollama Worker Up", [("", 'ollama_api_health{source="worker"}')],
         {"h":3,"w":4,"x":0,"y":1}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Ollama Master Up", [("", 'ollama_api_health{source="master"}')],
         {"h":3,"w":4,"x":4,"y":1}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Models Loaded (worker)", [("", 'count(ollama_model_loaded{source="worker"}==1)')],
         {"h":3,"w":4,"x":8,"y":1}, unit="none"),
    stat("API Errors Rate (1h)", [("", 'sum(rate(ollama_api_errors_total[1h]))')],
         {"h":3,"w":4,"x":12,"y":1}, unit="ops", decimals=3),
    stat("Ollama Worker Pod", [("", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"ollama-.*"})')],
         {"h":3,"w":4,"x":16,"y":1}, unit="none"),
    stat("API Tags Calls", [("", 'sum(ollama_api_tags_total)')],
         {"h":3,"w":4,"x":20,"y":1}, unit="none"),

    ts("Ollama Models Loaded (per model)", [
        ("{{model}} ({{source}})", 'ollama_model_loaded'),
    ], {"h":8,"w":12,"x":0,"y":4}, unit="none", decimals=0),

    bar("Ollama Model Sizes (GB, per model)", [
        ("{{model}}", 'ollama_model_size_bytes{source="worker"} / 1073741824'),
    ], {"h":8,"w":12,"x":12,"y":4}, unit="deckbytes", decimals=2),

    ts("Per-Model Memory Usage (GB)", [
        ("{{model}}", 'ollama_model_memory_bytes{source="worker"} / 1073741824'),
    ], {"h":8,"w":12,"x":0,"y":12}, unit="deckbytes", decimals=2),

    ts("Ollama API Latency P50/P95/P99 (s, per endpoint)", [
        ("P50 {{exported_endpoint}}", 'histogram_quantile(0.50, sum by (le, exported_endpoint) (rate(ollama_api_latency_seconds_bucket[5m])))'),
        ("P95 {{exported_endpoint}}", 'histogram_quantile(0.95, sum by (le, exported_endpoint) (rate(ollama_api_latency_seconds_bucket[5m])))'),
        ("P99 {{exported_endpoint}}", 'histogram_quantile(0.99, sum by (le, exported_endpoint) (rate(ollama_api_latency_seconds_bucket[5m])))'),
    ], {"h":8,"w":12,"x":12,"y":12}, unit="s", decimals=3),

    ts("Ollama API Errors Rate (per endpoint)", [
        ("{{exported_endpoint}} {{source}}", 'sum by (exported_endpoint, source) (rate(ollama_api_errors_total[5m]))'),
    ], {"h":8,"w":12,"x":0,"y":20}, unit="ops", decimals=3),

    ts("Ollama API Tags Calls Rate", [
        ("{{source}}", 'sum by (source) (rate(ollama_api_tags_total[5m]))'),
    ], {"h":8,"w":12,"x":12,"y":20}, unit="ops", decimals=3),

    ts("Ollama Worker CPU (cores)", [
        ("{{pod}}", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"ollama-.*"}[5m])) by (pod)'),
    ], {"h":8,"w":12,"x":0,"y":28}, unit="cores", decimals=2),

    gauge("Ollama Worker Memory (GB)", 'avg(container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}) / 1073741824',
          {"h":8,"w":12,"x":12,"y":28}, unit="deckbytes", decimals=1, max=128,
          thresholds={"mode":"absolute","steps":[{"color":"green","value":None},{"color":"yellow","value":100},{"color":"red","value":120}]}),

    # ===== ROW: LiteLLM AI Gateway =====
    row("LiteLLM AI Gateway", {"h":1,"w":24,"x":0,"y":36}),

    stat("LiteLLM Pod", [("", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"litellm-.*"})')],
         {"h":3,"w":4,"x":0,"y":37}, unit="none"),
    stat("Gateway Readiness", [("", 'litellm_gateway_up{exported_endpoint="/health/readiness"}')],
         {"h":3,"w":4,"x":4,"y":37}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Gateway Liveliness", [("", 'litellm_gateway_up{exported_endpoint="/health/liveliness"}')],
         {"h":3,"w":4,"x":8,"y":37}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Gateway Health (/health)", [("", 'litellm_gateway_up{exported_endpoint="/health"}')],
         {"h":3,"w":4,"x":12,"y":37}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Models Available", [("", 'litellm_models_available')],
         {"h":3,"w":4,"x":16,"y":37}, unit="none"),
    stat("Active Keys", [("", 'litellm_active_keys')],
         {"h":3,"w":4,"x":20,"y":37}, unit="none"),

    ts("LiteLLM Gateway Health Status (per endpoint)", [
        ("{{exported_endpoint}}", 'litellm_gateway_up'),
    ], {"h":8,"w":12,"x":0,"y":40}, unit="none", decimals=0),

    ts("LiteLLM Gateway Latency P50/P95/P99 (s)", [
        ("P50 {{exported_endpoint}}", 'histogram_quantile(0.50, sum by (le, exported_endpoint) (rate(litellm_check_sec_bucket[5m])))'),
        ("P95 {{exported_endpoint}}", 'histogram_quantile(0.95, sum by (le, exported_endpoint) (rate(litellm_check_sec_bucket[5m])))'),
        ("P99 {{exported_endpoint}}", 'histogram_quantile(0.99, sum by (le, exported_endpoint) (rate(litellm_check_sec_bucket[5m])))'),
    ], {"h":8,"w":12,"x":12,"y":40}, unit="s", decimals=3),

    ts("LiteLLM Check Errors Rate (per endpoint)", [
        ("{{exported_endpoint}}", 'sum by (exported_endpoint) (rate(litellm_check_errors_total[5m]))'),
    ], {"h":8,"w":12,"x":0,"y":48}, unit="ops", decimals=3),

    ts("LiteLLM Check Request Rate (per endpoint)", [
        ("{{exported_endpoint}}", 'sum by (exported_endpoint) (rate(litellm_check_sec_count[5m]))'),
    ], {"h":8,"w":12,"x":12,"y":48}, unit="reqps", decimals=2),

    ts("LiteLLM CPU (cores)", [
        ("{{pod}}", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"litellm-.*"}[5m])) by (pod)'),
    ], {"h":8,"w":12,"x":0,"y":56}, unit="cores", decimals=2),

    ts("LiteLLM Memory (bytes)", [
        ("{{pod}}", 'container_memory_working_set_bytes{namespace="ai-platform",pod=~"litellm-.*"}'),
    ], {"h":8,"w":12,"x":12,"y":56}, unit="bytes", decimals=0),

    # ===== ROW: Embed Proxy & Open-WebUI =====
    row("Embed Proxy & Frontend Health", {"h":1,"w":24,"x":0,"y":64}),

    stat("Embed Proxy Pod", [("", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"embed-proxy-.*"})')],
         {"h":3,"w":6,"x":0,"y":65}, unit="none"),
    stat("Open-WebUI Health", [("", 'health_check_up{exported_endpoint="open-webui"}')],
         {"h":3,"w":6,"x":6,"y":65}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Ollama Master Health", [("", 'health_check_up{exported_endpoint="ollama-master"}')],
         {"h":3,"w":6,"x":12,"y":65}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Open-WebUI /health", [("", 'health_check_up{exported_endpoint="open-webui-health"}')],
         {"h":3,"w":6,"x":18,"y":65}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),

    ts("Frontend Health Check Status (HTTP code)", [
        ("{{exported_endpoint}}", 'health_check_status_code{exported_endpoint=~"open-webui.*|ollama-master"}'),
    ], {"h":8,"w":12,"x":0,"y":68}, unit="none", decimals=0),

    ts("Frontend Health Check Response Time (ms)", [
        ("{{exported_endpoint}}", 'health_check_response_time_ms{exported_endpoint=~"open-webui.*|ollama-master"}'),
    ], {"h":8,"w":12,"x":12,"y":68}, unit="ms", decimals=1),

    ts("Embed Proxy CPU (cores)", [
        ("{{pod}}", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"embed-proxy-.*"}[5m])) by (pod)'),
    ], {"h":8,"w":12,"x":0,"y":76}, unit="cores", decimals=2),

    ts("Embed Proxy Memory (bytes)", [
        ("{{pod}}", 'container_memory_working_set_bytes{namespace="ai-platform",pod=~"embed-proxy-.*"}'),
    ], {"h":8,"w":12,"x":12,"y":76}, unit="bytes", decimals=0),

    # ===== ROW: Exporter Health =====
    row("Metric Exporters Health", {"h":1,"w":24,"x":0,"y":84}),

    stat("Ollama Exporter", [("", 'count(up{job="ollama-exporter-python"}==1)')],
         {"h":3,"w":8,"x":0,"y":85}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("LiteLLM Exporter", [("", 'count(up{job="litellm-exporter-python"}==1)')],
         {"h":3,"w":8,"x":8,"y":85}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Dify Exporter", [("", 'count(up{job="dify-exporter-python"}==1)')],
         {"h":3,"w":8,"x":16,"y":85}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
]

dash = {"panels": P, "description": "AI Model / LLM Services monitoring with REAL ollama + litellm exporter metrics. Fixed broken litellm_api_proxy_* queries."}
res = push(dash, "llm-services-v2", "LLM Services - Enterprise (Enhanced)", ["enterprise","ai-platform","llm","ollama"],
           namespace="monitoring", cm_name="grafana-dashboard-llm-services-v2", cm_key="grafana-dashboard-llm-services-v2.json")
print(json.dumps(res, indent=2))
