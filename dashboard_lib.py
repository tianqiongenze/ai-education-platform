#!/c/Python314/python
"""Build and push Grafana dashboards for the Dify/K8s platform.
All queries verified against the live Prometheus instance.

Dashboards are provisioned via the grafana sidecar from ConfigMaps, so they
cannot be saved through the Grafana HTTP API ("Cannot save provisioned dashboard").
Instead we update the ConfigMap directly via SSH + kubectl, then restart the
sidecar to pick up changes.
"""
import json, urllib.request, urllib.error, base64, sys, subprocess, tempfile, os

GRAFANA = "http://10.167.2.175:30082"
USER = "admin"
PASS = "uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb"
PROM_DS = {"uid": "prometheus", "type": "prometheus"}
SSH_HOST = "root@10.167.2.175"

# ----------------- panel helpers -----------------
def ts(title, exprs, grid, unit="short", span_label=None, decimals=None, legend=None):
    """timeseries panel. exprs = [(legend, expr), ...]"""
    targets = []
    for i, (lg, e) in enumerate(exprs):
        targets.append({
            "refId": chr(65+i), "expr": e, "legendFormat": lg or "{{instance}}",
            "datasource": PROM_DS, "editorMode": "code", "range": True
        })
    p = {
        "type": "timeseries", "title": title, "gridPos": grid,
        "datasource": PROM_DS, "targets": targets,
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"legend": {"displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}},
    }
    if decimals is not None:
        p["fieldConfig"]["defaults"]["decimals"] = decimals
    return p

def stat(title, exprs, grid, unit="short", decimals=None, thresholds=None, color_mode="background", reduceLast=True):
    """stat panel. exprs = [(name, expr), ...]"""
    targets = []
    for i, (lg, e) in enumerate(exprs):
        targets.append({"refId": chr(65+i), "expr": e, "legendFormat": lg,
                        "datasource": PROM_DS, "editorMode": "code", "instant": True})
    m = "last" if reduceLast else "first"
    p = {
        "type": "stat", "title": title, "gridPos": grid,
        "datasource": PROM_DS, "targets": targets,
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"colorMode": color_mode, "graphMode": "area", "justifyMode": "auto",
                    "reduceOptions": {"calcs": [m], "fields": "", "values": False},
                    "orientation": "auto", "textMode": "auto"},
    }
    if decimals is not None:
        p["fieldConfig"]["defaults"]["decimals"] = decimals
    if thresholds:
        p["fieldConfig"]["defaults"]["thresholds"] = thresholds
    return p

def gauge(title, expr, grid, unit="short", decimals=None, thresholds=None, max=None):
    """gauge panel."""
    p = {
        "type": "gauge", "title": title, "gridPos": grid,
        "datasource": PROM_DS,
        "targets": [{"refId": "A", "expr": expr, "legendFormat": "{{instance}}",
                     "datasource": PROM_DS, "editorMode": "code", "instant": True}],
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"showThresholdLabels": False, "showThresholdMarkers": True},
    }
    if decimals is not None: p["fieldConfig"]["defaults"]["decimals"] = decimals
    if thresholds: p["fieldConfig"]["defaults"]["thresholds"] = thresholds
    if max: p["fieldConfig"]["defaults"]["max"] = max
    return p

def bar(title, exprs, grid, unit="short", decimals=None):
    """bar gauge panel."""
    targets = []
    for i, (lg, e) in enumerate(exprs):
        targets.append({"refId": chr(65+i), "expr": e, "legendFormat": lg,
                        "datasource": PROM_DS, "editorMode": "code", "instant": True})
    p = {
        "type": "bargauge", "title": title, "gridPos": grid,
        "datasource": PROM_DS, "targets": targets,
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"displayMode": "gradient", "orientation": "horizontal",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}},
    }
    if decimals is not None: p["fieldConfig"]["defaults"]["decimals"] = decimals
    return p

def tbl(title, expr, grid, unit="short", hidden_cols=None):
    """table panel."""
    p = {
        "type": "table", "title": title, "gridPos": grid,
        "datasource": PROM_DS,
        "targets": [{"refId": "A", "expr": expr, "legendFormat": "",
                     "datasource": PROM_DS, "editorMode": "code", "instant": True, "format": "table"}],
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"showHeader": True},
    }
    return p

def row(title, grid, collapsed=False):
    return {"type": "row", "title": title, "gridPos": grid, "collapsed": collapsed,
            "panels": [] if collapsed else None}

def pie(title, expr, grid, unit="short"):
    p = {
        "type": "piechart", "title": title, "gridPos": grid,
        "datasource": PROM_DS,
        "targets": [{"refId": "A", "expr": expr, "legendFormat": "{{.name}}",
                     "datasource": PROM_DS, "editorMode": "code", "instant": True}],
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"displayLabels": ["name", "percent"], "pieType": "donut"},
    }
    return p

# ----------------- push helper -----------------
def _panel_ids(panels):
    """Assign sequential integer ids to all panels (rows included)."""
    for i, p in enumerate(panels, 1):
        p["id"] = i
    return panels

def push(dashboard, uid, title, tags, namespace="monitoring", cm_name=None, cm_key=None, folder_uid=None, extra_labels=None):
    """Push a dashboard by updating its provisioned ConfigMap via SSH + kubectl.

    namespace: namespace of the ConfigMap (monitoring for 3 dashboards, ai-platform for code-server)
    cm_name: ConfigMap name (defaults to grafana-dashboard-<uid>)
    cm_key: data key in the ConfigMap (defaults to <cm_name>.json)
    extra_labels: dict of additional labels to merge (e.g. app.kubernetes.io/name)
    """
    cm_name = cm_name or "grafana-dashboard-" + uid
    cm_key = cm_key or cm_name + ".json"
    # set top-level dashboard identity fields
    dashboard["uid"] = uid
    dashboard["title"] = title
    dashboard["tags"] = tags
    dashboard["timezone"] = "browser"
    dashboard["schemaVersion"] = 39
    dashboard["version"] = 0
    dashboard["refresh"] = "30s"
    dashboard.setdefault("time", {"from": "now-6h", "to": "now"})
    dashboard.setdefault("timepicker", [{"now": True, "refresh": ["5s","10s","30s","1m","5m","15m","30m","1h","2h","1d"]}])
    dashboard.setdefault("fiscalYearStartMonth", 0)
    dashboard.setdefault("graphTooltip", 1)
    dashboard.setdefault("editable", True)
    _panel_ids(dashboard.get("panels", []))

    # Write the dashboard JSON to a local temp file, base64-encode, and apply via SSH.
    js = json.dumps(dashboard, ensure_ascii=False, separators=(",", ":"))
    labels = {"grafana_dashboard": "1"}
    if extra_labels:
        labels.update(extra_labels)
    # Build a ConfigMap manifest and apply it. We pipe a base64-decoded JSON manifest
    # through kubectl apply to avoid shell-escaping issues with the embedded dashboard JSON.
    cm_manifest = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": cm_name,
            "namespace": namespace,
            "labels": labels,
        },
        "data": {cm_key: js},
    }
    manifest_json = json.dumps(cm_manifest)
    # Pipe the manifest JSON to kubectl over SSH stdin. This avoids all shell-escaping
    # issues. Use /usr/bin/kubectl explicitly (non-login ssh PATH may be minimal).
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
        "/usr/bin/kubectl apply -f -",
    ]
    try:
        out = subprocess.run(cmd, input=manifest_json.encode("utf-8"),
                             capture_output=True, timeout=60)
        stdout = out.stdout.decode("utf-8", "replace")
        stderr = out.stderr.decode("utf-8", "replace")
        result = stdout.strip() + ("\n" + stderr.strip() if stderr.strip() else "")
        ok = ("configured" in stdout or "created" in stdout or "unchanged" in stdout)
        return {"ok": ok, "output": result, "cm": cm_name, "ns": namespace, "key": cm_key, "len": len(js)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def reload_sidecar():
    """Restart the grafana dashboard sidecar so it reloads updated ConfigMaps.
    The sidecar (k8s-sidecar) reloads on a timer, but deleting the grafana pod's
    sidecar container triggers an immediate reload. Simplest: rollout restart grafana.
    """
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
           "/usr/bin/kubectl rollout restart deployment kube-prometheus-stack-grafana -n monitoring"]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=60)
        return out.stdout.decode("utf-8", "replace").strip()
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print("dashboard_lib module loaded")
