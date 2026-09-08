#!/c/Python314/python
"""Infrastructure Overview Dashboard - REAL verified metrics.
Replaces broken queries (nginx_ingress_*, kubelet_volume_stats_*) with working ones.
"""
import sys
sys.path.insert(0, "D:/dify-install")
from dashboard_lib import *
import json

P = [
    # ===== ROW: Cluster Overview =====
    row("Cluster Overview", {"h":1,"w":24,"x":0,"y":0}),

    stat("Nodes Total", [("", "count(kube_node_info)")], {"h":3,"w":3,"x":0,"y":1}, unit="none"),
    stat("Nodes Ready", [("", 'count(kube_node_status_condition{condition="Ready",status="true"})')],
         {"h":3,"w":3,"x":3,"y":1}, unit="none",
         thresholds={"mode":"absolute","steps":[{"color":"red","value":None},{"color":"green","value":2}]}),
    stat("CPU Cores (capacity)", [("", 'sum(kube_node_status_capacity{resource="cpu",unit="core"})')],
         {"h":3,"w":3,"x":6,"y":1}, unit="cores", decimals=0),
    stat("Memory (GB)", [("", 'sum(kube_node_status_capacity{resource="memory",unit="byte"})/1073741824')],
         {"h":3,"w":3,"x":9,"y":1}, unit="deckbytes", decimals=0),
    stat("Pods Running", [("", 'count(kube_pod_info)')], {"h":3,"w":3,"x":12,"y":1}, unit="none"),
    stat("Namespaces", [("", 'count(kube_namespace_created)')], {"h":3,"w":3,"x":15,"y":1}, unit="none"),
    stat("PVs", [("", 'count(kube_persistentvolume_info)')], {"h":3,"w":3,"x":18,"y":1}, unit="none"),
    stat("Services", [("", 'count(kube_service_info)')], {"h":3,"w":3,"x":21,"y":1}, unit="none"),

    # ===== ROW: Node Resource Usage (real per-node) =====
    row("Node CPU / Memory / Disk / Network (per node, real data)", {"h":1,"w":24,"x":0,"y":4}),

    ts("Node CPU Usage % (per node)", [
        ("{{instance}}", '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'),
    ], {"h":8,"w":12,"x":0,"y":5}, unit="percent", decimals=1),

    ts("Node Memory Usage % (per node)", [
        ("{{instance}}", '100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))'),
    ], {"h":8,"w":12,"x":12,"y":5}, unit="percent", decimals=1),

    ts("Node Memory Used vs Total (GB)", [
        ("used {{instance}}", '(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1073741824'),
        ("total {{instance}}", 'node_memory_MemTotal_bytes / 1073741824'),
    ], {"h":8,"w":12,"x":0,"y":13}, unit="deckbytes", decimals=1),

    ts("Node Disk Usage % (root filesystem)", [
        ("{{instance}}", '100 * (1 - (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}))'),
    ], {"h":8,"w":12,"x":12,"y":13}, unit="percent", decimals=1),

    ts("Node Disk I/O - Read/Write Rate (bytes/s)", [
        ("read {{instance}} {{device}}", 'rate(node_disk_read_bytes_total[5m])'),
        ("write {{instance}} {{device}}", 'rate(node_disk_written_bytes_total[5m])'),
    ], {"h":8,"w":12,"x":0,"y":21}, unit="Bps", decimals=0),

    ts("Node Network Traffic RX/TX (bytes/s, physical)", [
        ("RX {{instance}}", 'sum by (instance) (rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br-.*|cni.*|flannel.*|calico.*|tunl.*"}[5m]))'),
        ("TX {{instance}}", 'sum by (instance) (rate(node_network_transmit_bytes_total{device!~"lo|veth.*|docker.*|br-.*|cni.*|flannel.*|calico.*|tunl.*"}[5m]))'),
    ], {"h":8,"w":12,"x":12,"y":21}, unit="Bps", decimals=0),

    ts("Node Load Average (1/5/15 min)", [
        ("load1 {{instance}}", 'node_load1'),
        ("load5 {{instance}}", 'node_load5'),
        ("load15 {{instance}}", 'node_load15'),
    ], {"h":8,"w":12,"x":0,"y":29}, unit="short", decimals=2),

    ts("Node CPU Cores Used (per node)", [
        ("{{instance}}", 'sum by (instance) (rate(node_cpu_seconds_total{mode!="idle"}[5m]))'),
    ], {"h":8,"w":12,"x":12,"y":29}, unit="cores", decimals=2),

    # ===== ROW: Namespace Resources =====
    row("Namespace Resource Breakdown", {"h":1,"w":24,"x":0,"y":37}),

    ts("CPU Usage by Namespace (cores)", [
        ("{{namespace}}", 'sum by (namespace) (rate(container_cpu_usage_seconds_total{namespace!=""}[5m]))'),
    ], {"h":8,"w":12,"x":0,"y":38}, unit="cores", decimals=2),

    ts("Memory Usage by Namespace (GB)", [
        ("{{namespace}}", 'sum by (namespace) (container_memory_working_set_bytes{namespace!=""}) / 1073741824'),
    ], {"h":8,"w":12,"x":12,"y":38}, unit="deckbytes", decimals=2),

    bar("Pod Count by Namespace", [
        ("{{namespace}}", 'count by (namespace) (kube_pod_info)'),
    ], {"h":8,"w":12,"x":0,"y":46}, unit="none", decimals=0),

    ts("Pod Restarts Rate by Namespace (restarts/s)", [
        ("{{namespace}}", 'sum by (namespace) (rate(kube_pod_container_status_restarts_total[5m]))'),
    ], {"h":8,"w":12,"x":12,"y":46}, unit="ops", decimals=3),

    # ===== ROW: Storage & PVC =====
    row("Storage & Persistent Volumes", {"h":1,"w":24,"x":0,"y":54}),

    bar("PVC Requested Storage by Namespace (GB)", [
        ("{{namespace}}", 'sum by (namespace) (kube_persistentvolumeclaim_resource_requests_storage_bytes) / 1073741824'),
    ], {"h":8,"w":12,"x":0,"y":55}, unit="deckbytes", decimals=1),

    tbl("PVC Details (all namespaces)",
        'kube_persistentvolumeclaim_resource_requests_storage_bytes',
        {"h":8,"w":12,"x":12,"y":55}, unit="bytes"),

    ts("Node Filesystem Free Space (GB, root)", [
        ("{{instance}}", 'node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / 1073741824'),
        ("total {{instance}}", 'node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / 1073741824'),
    ], {"h":8,"w":24,"x":0,"y":63}, unit="deckbytes", decimals=1),

    # ===== ROW: Node Status Table =====
    row("Node Status & Pod Phase Summary", {"h":1,"w":24,"x":0,"y":71}),

    tbl("Node Status (Ready/CPU/Memory capacity)",
        'kube_node_status_capacity{resource=~"cpu|memory"}',
        {"h":8,"w":12,"x":0,"y":72}, unit="short"),

    bar("Pods by Phase (all namespaces)", [
        ("{{phase}}", 'count by (phase) (kube_pod_status_phase)'),
    ], {"h":8,"w":12,"x":12,"y":72}, unit="none", decimals=0),
]

dash = {"panels": P, "description": "Infrastructure overview with REAL node-exporter + kube-state-metrics data. Fixed broken ingress/volume queries."}
res = push(dash, "infrastructure-v2", "Infrastructure Overview - Enterprise (Enhanced)", ["enterprise","infrastructure","k8s"],
           namespace="monitoring", cm_name="grafana-dashboard-infrastructure-v2", cm_key="grafana-dashboard-infrastructure-v2.json")
print(json.dumps(res, indent=2))
