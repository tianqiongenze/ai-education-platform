#!/c/Python314/python
"""Verify all 4 dashboards have real data by querying a representative
Prometheus query from each panel of each dashboard via the Grafana API."""
import sys, json
sys.path.insert(0, "D:/dify-install")
import dashboard_lib
from pquery import query, extract

GRAFANA = dashboard_lib.GRAFANA
USER = dashboard_lib.USER
PASS = dashboard_lib.PASS

# Representative queries per dashboard (one or two per panel section)
CHECKS = {
    "Dify Platform": [
        ("Dify API Version", "max(dify_api_info) by (version)"),
        ("API Pods Ready", 'sum(kube_pod_status_phase{namespace="dify",phase="Running",pod=~"dify-api-.*"})'),
        ("Evicted Pods", 'sum(kube_pod_status_phase{namespace="dify",phase="Failed"})'),
        ("API Request Rate", 'sum(rate(dify_exporter_latency_sec_count{exported_service="api"}[5m]))'),
        ("API P95 latency", 'histogram_quantile(0.95, sum by (le) (rate(dify_exporter_latency_sec_bucket{exported_service="api"}[5m])))'),
        ("API Errors", 'sum(rate(dify_exporter_errors_total{exported_service="api"}[5m]))'),
        ("API Health Check", 'health_check_up{exported_endpoint="dify-api"}'),
        ("Pod CPU", 'sum(rate(container_cpu_usage_seconds_total{namespace="dify",pod=~"dify-.*"}[5m])) by (pod)'),
        ("Pod Memory", 'sum(container_memory_working_set_bytes{namespace="dify",pod=~"dify-.*"}) by (pod)'),
        ("Pod Restarts", 'sum by (pod) (kube_pod_container_status_restarts_total{namespace="dify"})'),
        ("CPU requests", 'sum(kube_pod_container_resource_requests{namespace="dify",resource="cpu",unit="core"})'),
        ("PostgreSQL Up", "pg_up"),
        ("Redis Up", "redis_up"),
        ("Redis clients", "redis_connected_clients"),
        ("Redis DB keys", "sum(redis_db_keys)"),
        ("Redis mem used", "redis_memory_used_bytes"),
        ("Redis mem %", "redis_memory_used_bytes / redis_memory_max_bytes * 100"),
        ("Redis keys by db", "redis_db_keys"),
        ("Redis cmd rate", 'sum(rate(redis_commands_total[5m])) by (cmd)'),
        ("Redis hit/miss", 'sum(rate(redis_keyspace_hits_total[5m]))'),
        ("PVC storage", "sum(kube_persistentvolumeclaim_resource_requests_storage_bytes) by (namespace) / 1073741824"),
    ],
    "Infrastructure": [
        ("Nodes Total", "count(kube_node_info)"),
        ("Nodes Ready", 'count(kube_node_status_condition{condition="Ready",status="true"})'),
        ("CPU capacity", 'sum(kube_node_status_capacity{resource="cpu",unit="core"})'),
        ("Memory GB", 'sum(kube_node_status_capacity{resource="memory",unit="byte"})/1073741824'),
        ("Pods Running", "count(kube_pod_info)"),
        ("Node CPU %", '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'),
        ("Node Mem %", '100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))'),
        ("Node Disk %", '100 * (1 - (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}))'),
        ("Disk read rate", "rate(node_disk_read_bytes_total[5m])"),
        ("Disk write rate", "rate(node_disk_written_bytes_total[5m])"),
        ("Network RX", 'sum by (instance) (rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br-.*|cni.*|flannel.*|calico.*|tunl.*"}[5m]))'),
        ("Node load", "node_load1"),
        ("CPU by ns", 'sum by (namespace) (rate(container_cpu_usage_seconds_total{namespace!=""}[5m]))'),
        ("Mem by ns", 'sum by (namespace) (container_memory_working_set_bytes{namespace!=""}) / 1073741824'),
        ("Pod count by ns", 'count by (namespace) (kube_pod_info)'),
        ("Restarts by ns", 'sum by (namespace) (rate(kube_pod_container_status_restarts_total[5m]))'),
        ("PVC storage by ns", 'sum by (namespace) (kube_persistentvolumeclaim_resource_requests_storage_bytes) / 1073741824'),
        ("PVC details", "kube_persistentvolumeclaim_resource_requests_storage_bytes"),
        ("Node free space", 'node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / 1073741824'),
        ("Pods by phase", 'count by (phase) (kube_pod_status_phase)'),
    ],
    "AI Model / LLM": [
        ("Ollama worker up", 'ollama_api_health{source="worker"}'),
        ("Models loaded", 'count(ollama_model_loaded{source="worker"}==1)'),
        ("API errors rate", "sum(rate(ollama_api_errors_total[1h]))"),
        ("Ollama tags", "sum(ollama_api_tags_total)"),
        ("Models loaded ts", "ollama_model_loaded"),
        ("Model sizes", 'ollama_model_size_bytes{source="worker"} / 1073741824'),
        ("Model memory", 'ollama_model_memory_bytes{source="worker"} / 1073741824'),
        ("Ollama P95", 'histogram_quantile(0.95, sum by (le, exported_endpoint) (rate(ollama_api_latency_seconds_bucket[5m])))'),
        ("Ollama errors", 'sum by (exported_endpoint, source) (rate(ollama_api_errors_total[5m]))'),
        ("Ollama CPU", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"ollama-.*"}[5m])) by (pod)'),
        ("Ollama mem", 'avg(container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}) / 1073741824'),
        ("Litellm pod", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"litellm-.*"})'),
        ("Gateway readiness", 'litellm_gateway_up{exported_endpoint="/health/readiness"}'),
        ("Models available", "litellm_models_available"),
        ("Active keys", "litellm_active_keys"),
        ("Litellm P95", 'histogram_quantile(0.95, sum by (le, exported_endpoint) (rate(litellm_check_sec_bucket[5m])))'),
        ("Litellm errors", 'sum by (exported_endpoint) (rate(litellm_check_errors_total[5m]))'),
        ("Litellm req rate", 'sum by (exported_endpoint) (rate(litellm_check_sec_count[5m]))'),
        ("Litellm CPU", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"litellm-.*"}[5m])) by (pod)'),
        ("Open-webui health", 'health_check_up{exported_endpoint="open-webui"}'),
        ("Health resp time", 'health_check_response_time_ms{exported_endpoint=~"open-webui.*|ollama-master"}'),
        ("Embed proxy CPU", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"embed-proxy-.*"}[5m])) by (pod)'),
        ("Exporters", 'count(up{job="ollama-exporter-python"}==1)'),
    ],
    "Code-Server / JupyterHub": [
        ("Code-server pod", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"code-server-.*"})'),
        ("Jupyterlab pod", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"jupyterlab-.*"})'),
        ("Code-server PVC", 'kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace="ai-platform",persistentvolumeclaim="code-server-data"} / 1073741824'),
        ("Code-server restarts", 'sum(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"})'),
        ("Code-server CPU", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])) by (pod)'),
        ("Code-server mem", 'container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"}'),
        ("Code-server CPU req", 'sum(kube_pod_container_resource_requests{namespace="ai-platform",pod=~"code-server-.*",resource="cpu",unit="core"})'),
        ("Jupyterhub pods", "count(kube_pod_info{namespace=\"jupyterhub\"})"),
        ("Active sessions", 'count(kube_pod_info{namespace="jupyterhub",pod=~"jupyter-student.*"})'),
        ("Hub pod up", 'sum(kube_pod_status_phase{namespace="jupyterhub",phase="Running",pod=~"jupyterhub-.*"})'),
        ("Jupyterhub CPU", 'sum(rate(container_cpu_usage_seconds_total{namespace="jupyterhub"}[5m])) by (pod)'),
        ("Jupyterhub mem", 'container_memory_working_set_bytes{namespace="jupyterhub"}'),
        ("Notebook CPU req", 'sum(kube_pod_container_resource_requests{namespace="jupyterhub",pod=~"jupyter-student.*",resource="cpu",unit="core"})'),
        ("Notebook mem req", 'sum(kube_pod_container_resource_requests{namespace="jupyterhub",pod=~"jupyter-student.*",resource="memory",unit="byte"})'),
        ("PVC storage", 'kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace=~"jupyterhub|ai-platform"} / 1073741824'),
        ("Restarts", 'sum by (namespace, pod) (kube_pod_container_status_restarts_total{namespace=~"ai-platform|jupyterhub"})'),
        ("Pod phase", 'count by (namespace, phase) (kube_pod_status_phase{namespace=~"ai-platform|jupyterhub"})'),
    ],
}

total_ok = 0
total_fail = 0
for dash_name, checks in CHECKS.items():
    print("\n========== %s ==========" % dash_name)
    for label, expr in checks:
        d = query(expr)
        if "error" in d:
            print("  FAIL  %-28s ERROR: %s" % (label, str(d["error"])[:50]))
            total_fail += 1
            continue
        rows = extract(d)
        # Determine if there is real data (non-empty)
        has_data = len(rows) > 0
        # show a sample value
        sample = ""
        if rows:
            lbl, val = rows[0]
            # show first non-trivial
            for l, v in rows:
                if v not in (None, "", "0", 0):
                    sample = "%s=%s" % (l.get("pod") or l.get("namespace") or l.get("instance") or l.get("model") or l.get("exported_endpoint") or l.get("job") or "value", v)
                    break
            if not sample:
                lbl, val = rows[0]
                sample = "value=%s" % val
        status = "OK   " if has_data else "EMPTY"
        if has_data:
            total_ok += 1
        else:
            total_fail += 1
        print("  %s %-28s series=%-3d %s" % (status, label, len(rows), sample[:50]))

print("\n========== SUMMARY ==========")
print("Panels with data: %d" % total_ok)
print("Panels empty:     %d" % total_fail)
print("Total checked:    %d" % (total_ok + total_fail))
