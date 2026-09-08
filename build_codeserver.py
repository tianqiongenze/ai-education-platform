#!/c/Python314/python
"""Code-Server / JupyterHub Dashboard - REAL verified metrics.
Fixes the broken code-server Enterprise dashboard which referenced non-existent
code_server_* metrics and wrong namespace. Uses real container metrics from
ai-platform (code-server, jupyterlab) and jupyterhub (jupyter-student*, jupyterhub) namespaces.
"""
import sys
sys.path.insert(0, "D:/dify-install")
from dashboard_lib import *
import json

P = [
    # ===== ROW: Code-Server (ai-platform) =====
    row("Code-Server (namespace: ai-platform)", {"h":1,"w":24,"x":0,"y":0}),

    stat("Code-Server Pod", [("", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"code-server-.*"})')],
         {"h":3,"w":6,"x":0,"y":1}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("JupyterLab Pod", [("", 'sum(kube_pod_status_phase{namespace="ai-platform",phase="Running",pod=~"jupyterlab-.*"})')],
         {"h":3,"w":6,"x":6,"y":1}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Code-Server PVC (GB)", [("", 'kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace="ai-platform",persistentvolumeclaim="code-server-data"} / 1073741824')],
         {"h":3,"w":6,"x":12,"y":1}, unit="deckbytes", decimals=0),
    stat("Code-Server Restarts", [("", 'sum(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"})')],
         {"h":3,"w":6,"x":18,"y":1}, unit="none"),

    ts("Code-Server CPU (cores)", [
        ("{{pod}}", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])) by (pod)'),
    ], {"h":8,"w":12,"x":0,"y":4}, unit="cores", decimals=2),

    ts("Code-Server Memory (bytes)", [
        ("{{pod}}", 'container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"}'),
    ], {"h":8,"w":12,"x":12,"y":4}, unit="bytes", decimals=0),

    ts("Code-Server CPU vs Request/Limit (cores)", [
        ("used", 'sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m]))'),
        ("request", 'sum(kube_pod_container_resource_requests{namespace="ai-platform",pod=~"code-server-.*",resource="cpu",unit="core"})'),
        ("limit", 'sum(kube_pod_container_resource_limits{namespace="ai-platform",pod=~"code-server-.*",resource="cpu",unit="core"})'),
    ], {"h":8,"w":12,"x":0,"y":12}, unit="cores", decimals=2),

    ts("Code-Server Memory vs Request/Limit (bytes)", [
        ("used", 'sum(container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"})'),
        ("request", 'sum(kube_pod_container_resource_requests{namespace="ai-platform",pod=~"code-server-.*",resource="memory",unit="byte"})'),
        ("limit", 'sum(kube_pod_container_resource_limits{namespace="ai-platform",pod=~"code-server-.*",resource="memory",unit="byte"})'),
    ], {"h":8,"w":12,"x":12,"y":12}, unit="bytes", decimals=0),

    # ===== ROW: JupyterHub =====
    row("JupyterHub (namespace: jupyterhub)", {"h":1,"w":24,"x":0,"y":20}),

    stat("JupyterHub Pods", [("", 'count(kube_pod_info{namespace="jupyterhub"})')],
         {"h":3,"w":6,"x":0,"y":21}, unit="none"),
    stat("Active User Sessions", [("", 'count(kube_pod_info{namespace="jupyterhub",pod=~"jupyter-student.*"})')],
         {"h":3,"w":6,"x":6,"y":21}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Hub Pod Up", [("", 'sum(kube_pod_status_phase{namespace="jupyterhub",phase="Running",pod=~"jupyterhub-.*"})')],
         {"h":3,"w":6,"x":12,"y":21}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":1}]}),
    stat("Total Restarts", [("", 'sum(kube_pod_container_status_restarts_total{namespace="jupyterhub"})')],
         {"h":3,"w":6,"x":18,"y":21}, unit="none"),

    ts("JupyterHub Pod CPU (cores, per pod)", [
        ("{{pod}}", 'sum(rate(container_cpu_usage_seconds_total{namespace="jupyterhub"}[5m])) by (pod)'),
    ], {"h":8,"w":12,"x":0,"y":24}, unit="cores", decimals=2),

    ts("JupyterHub Pod Memory (bytes, per pod)", [
        ("{{pod}}", 'container_memory_working_set_bytes{namespace="jupyterhub"}'),
    ], {"h":8,"w":12,"x":12,"y":24}, unit="bytes", decimals=0),

    ts("User Notebook CPU vs Request (cores, per pod)", [
        ("used {{pod}}", 'sum(rate(container_cpu_usage_seconds_total{namespace="jupyterhub",pod=~"jupyter-student.*"}[5m])) by (pod)'),
        ("request", 'sum(kube_pod_container_resource_requests{namespace="jupyterhub",pod=~"jupyter-student.*",resource="cpu",unit="core"})'),
    ], {"h":8,"w":12,"x":0,"y":32}, unit="cores", decimals=2),

    ts("User Notebook Memory vs Request (bytes)", [
        ("used {{pod}}", 'container_memory_working_set_bytes{namespace="jupyterhub",pod=~"jupyter-student.*"}'),
        ("request", 'sum(kube_pod_container_resource_requests{namespace="jupyterhub",pod=~"jupyter-student.*",resource="memory",unit="byte"})'),
    ], {"h":8,"w":12,"x":12,"y":32}, unit="bytes", decimals=0),

    # ===== ROW: Storage per user =====
    row("Storage Usage (per user / per pod)", {"h":1,"w":24,"x":0,"y":40}),

    bar("PVC Requested Storage (GB, jupyterhub + ai-platform)", [
        ("{{namespace}} {{persistentvolumeclaim}}", 'kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace=~"jupyterhub|ai-platform"} / 1073741824'),
    ], {"h":8,"w":12,"x":0,"y":41}, unit="deckbytes", decimals=1),

    tbl("PVC Details (jupyterhub + ai-platform)",
        'kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace=~"jupyterhub|ai-platform"}',
        {"h":8,"w":12,"x":12,"y":41}, unit="bytes"),

    # ===== ROW: Pod Status Table =====
    row("Pod Status Overview", {"h":1,"w":24,"x":0,"y":49}),

    tbl("All Pods (ai-platform + jupyterhub)",
        'kube_pod_info{namespace=~"ai-platform|jupyterhub"}',
        {"h":8,"w":12,"x":0,"y":50}, unit="short"),

    ts("Pod Restarts (ai-platform + jupyterhub)", [
        ("{{namespace}} {{pod}}", 'sum by (namespace, pod) (kube_pod_container_status_restarts_total{namespace=~"ai-platform|jupyterhub"})'),
    ], {"h":8,"w":12,"x":12,"y":50}, unit="none", decimals=0),

    ts("Pod Phase Count (ai-platform + jupyterhub)", [
        ("{{namespace}} {{phase}}", 'count by (namespace, phase) (kube_pod_status_phase{namespace=~"ai-platform|jupyterhub"})'),
    ], {"h":8,"w":24,"x":0,"y":58}, unit="none", decimals=0),
]

dash = {"panels": P, "description": "Code-Server + JupyterHub monitoring with REAL container metrics. Fixed broken code_server_* metrics and wrong namespace. Covers ai-platform (code-server, jupyterlab) and jupyterhub (student notebooks) namespaces."}
# code-server dashboard lives in ai-platform namespace with extra labels
res = push(dash, "code-server-enterprise", "code-server Enterprise", ["enterprise","code-server","jupyterhub","ai-platform"],
           namespace="ai-platform", cm_name="code-server-grafana-dashboard", cm_key="code-server-dashboard.json",
           extra_labels={"app.kubernetes.io/component":"monitoring","app.kubernetes.io/name":"code-server"})
print(json.dumps(res, indent=2))
