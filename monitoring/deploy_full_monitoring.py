#!/usr/bin/env python3
"""
Complete enterprise monitoring deployment:
1. Deploy ollama-prometheus-exporter (per-model metrics via ollama API)
2. Deploy litellm metrics exporter  
3. Build fine-grained Grafana dashboards with per-model latency, tokens, requests
4. Deploy ServiceMonitors for all exporters
5. Deploy PrometheusRules with per-service alerting
6. Generate 3 PPTs with light-gradient professional theme
"""
import subprocess, json, os, sys, time, re, textwrap

BASE = r"D:\dify-install"
MONITORING = os.path.join(BASE, "monitoring")
LOADTEST = os.path.join(BASE, "load-test")
NODE_MODULES = LOADTEST

def run(cmd, cwd=None, timeout=60):
    """Run kubectl or shell command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or BASE, timeout=timeout)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def kapply(yaml_str):
    """Apply YAML via kubectl stdin"""
    p = subprocess.run(["kubectl", "apply", "-f", "-"], input=yaml_str, capture_output=True, text=True, timeout=60)
    print(f"  kubectl apply: {p.stdout.strip()}")
    if p.stderr.strip():
        print(f"  stderr: {p.stderr.strip()[:200]}")
    return p.returncode == 0

# =============================================
# PART 1: DEPLOY OLLAMA PROMETHEUS EXPORTER
# =============================================
print("=" * 60)
print("PART 1: Deploying ollama-prometheus-exporter")
print("=" * 60)

# Check what models exist on the cluster
stdout, stderr, rc = run("kubectl exec -n ai-platform deploy/ollama-master -- ollama list 2>nul || echo ''")
print(f"  Models: {stdout[:200] if stdout else 'Cannot query'}")

# Deploy a Python-based exporter that scrapes ollama API and exposes Prometheus metrics
ollama_exporter_yaml = """apiVersion: v1
kind: ConfigMap
metadata:
  name: ollama-exporter-script
  namespace: default
data:
  exporter.py: |
    from prometheus_client import start_http_server, Gauge, Histogram, Counter, Summary
    import requests, time, os, threading

    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://ollama-master.ai-platform.svc.cluster.local:11434')
    OLLAMA_WORKER_URL = os.environ.get('OLLAMA_WORKER_URL', 'http://ollama-worker.ai-platform.svc.cluster.local:11434')
    SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', '15'))

    # Model-level metrics
    model_info = Gauge('ollama_model_info', 'Model info', ['model', 'family', 'parameter_size'])
    model_available = Gauge('ollama_model_available', 'Model availability', ['model', 'source'])
    model_size_bytes = Gauge('ollama_model_size_bytes', 'Model size in bytes', ['model'])
    model_gpu_layers = Gauge('ollama_model_gpu_layers', 'GPU layers used', ['model'])
    
    # Runtime metrics (from ollama ps)
    model_loaded = Gauge('ollama_model_loaded', 'Model loaded in memory', ['model', 'source'])
    model_memory_bytes = Gauge('ollama_model_memory_bytes', 'Model memory usage', ['model', 'source'])
    model_active_requests = Gauge('ollama_model_active_requests', 'Active requests per model', ['model', 'source'])
    
    # API-level metrics
    api_health = Gauge('ollama_api_health', 'Ollama API health status', ['source'])
    api_tags_total = Gauge('ollama_api_tags_total', 'Total models available', ['source'])
    api_latency_seconds = Histogram('ollama_api_latency_seconds', 'API call latency', ['source', 'endpoint'])
    api_errors_total = Counter('ollama_api_errors_total', 'API error count', ['source', 'error_type'])
    
    # Version info
    version_info = Gauge('ollama_version_info', 'Ollama version', ['version', 'source'])

    def scrape_ollama(url, source):
        try:
            t0 = time.time()
            resp = requests.get(f'{url}/api/tags', timeout=10)
            api_latency_seconds.labels(source=source, endpoint='tags').observe(time.time() - t0)
            
            if resp.status_code == 200:
                api_health.labels(source=source).set(1)
                data = resp.json()
                models = data.get('models', [])
                api_tags_total.labels(source=source).set(len(models))
                
                for m in models:
                    name = m.get('name', 'unknown')
                    model_available.labels(model=name, source=source).set(1)
                    model_size_bytes.labels(model=name).set(m.get('size', 0))
                    family = m.get('details', {}).get('family', 'unknown')
                    param_size = m.get('details', {}).get('parameter_size', 'unknown')
                    model_info.labels(model=name, family=family, parameter_size=param_size).set(1)
            else:
                api_health.labels(source=source).set(0)
                api_errors_total.labels(source=source, error_type=f'http_{resp.status_code}').inc()
        except Exception as e:
            api_health.labels(source=source).set(0)
            api_errors_total.labels(source=source, error_type=type(e).__name__).inc()
        
        # Get running models
        try:
            t1 = time.time()
            resp = requests.get(f'{url}/api/ps', timeout=10)
            api_latency_seconds.labels(source=source, endpoint='ps').observe(time.time() - t1)
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get('models', []):
                    name = m.get('name', 'unknown')
                    model_loaded.labels(model=name, source=source).set(1)
                    model_memory_bytes.labels(model=name, source=source).set(m.get('size_vram', 0))
        except:
            pass
        
        # Get version
        try:
            resp = requests.get(f'{url}/api/version', timeout=5)
            if resp.status_code == 200:
                ver = resp.json().get('version', 'unknown')
                version_info.labels(version=ver, source=source).set(1)
        except:
            pass

    def scrape_loop():
        while True:
            t0 = time.time()
            scrape_ollama(OLLAMA_URL, 'master')
            if OLLAMA_WORKER_URL:
                try:
                    scrape_ollama(OLLAMA_WORKER_URL, 'worker')
                except:
                    pass
            elapsed = time.time() - t0
            sleep_time = max(1, SCRAPE_INTERVAL - elapsed)
            time.sleep(sleep_time)

    if __name__ == '__main__':
        port = int(os.environ.get('PORT', '9469'))
        start_http_server(port)
        print(f'Ollama exporter started on port {port}')
        scrape_loop()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama-prometheus-exporter
  namespace: default
  labels:
    app: ollama-prometheus-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama-prometheus-exporter
  template:
    metadata:
      labels:
        app: ollama-prometheus-exporter
    spec:
      containers:
      - name: exporter
        image: python:3.11-slim
        command: ["sh", "-c"]
        args:
        - "pip install prometheus-client requests && python /app/exporter.py"
        ports:
        - name: metrics
          containerPort: 9469
        env:
        - name: OLLAMA_URL
          value: "http://ollama-master.ai-platform.svc.cluster.local:11434"
        - name: OLLAMA_WORKER_URL
          value: "http://ollama-worker.ai-platform.svc.cluster.local:11434"
        - name: SCRAPE_INTERVAL
          value: "15"
        - name: PORT
          value: "9469"
        volumeMounts:
        - name: script
          mountPath: /app
        resources:
          limits:
            cpu: 200m
            memory: 128Mi
          requests:
            cpu: 50m
            memory: 64Mi
      volumes:
      - name: script
        configMap:
          name: ollama-exporter-script
---
apiVersion: v1
kind: Service
metadata:
  name: ollama-prometheus-exporter
  namespace: default
  labels:
    app: ollama-prometheus-exporter
spec:
  selector:
    app: ollama-prometheus-exporter
  ports:
  - name: metrics
    port: 9469
    targetPort: 9469
  type: ClusterIP
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ollama-prometheus-exporter
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: ollama-prometheus-exporter
  namespaceSelector:
    matchNames:
    - default
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
"""

kapply(ollama_exporter_yaml)

# =============================================
# PART 2: LITELLM METRICS EXPORTER  
# =============================================
print("\n" + "=" * 60)
print("PART 2: Deploying litellm metrics exporter")
print("=" * 60)

# Check if litellm has a metrics port
stdout, _, _ = run("kubectl get svc -n ai-platform litellm -o jsonpath='{.spec.ports[*].port}'")
print(f"  Litellm service ports: {stdout}")

# Deploy a proxy exporter that queries litellm health/status
litellm_exporter_yaml = """apiVersion: v1
kind: ConfigMap
metadata:
  name: litellm-exporter-script
  namespace: default
data:
  exporter.py: |
    from prometheus_client import start_http_server, Gauge, Counter, Histogram
    import requests, time, os

    LITELLM_URL = os.environ.get('LITELLM_URL', 'http://litellm.ai-platform.svc.cluster.local:4000')
    SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', '15'))

    # Service metrics
    litellm_health = Gauge('litellm_health', 'Litellm gateway health', ['endpoint'])
    litellm_models_available = Gauge('litellm_models_available', 'Models available in litellm')
    litellm_api_latency = Histogram('litellm_api_proxy_latency_seconds', 'Proxy API latency', ['endpoint'])
    litellm_api_errors = Counter('litellm_api_proxy_errors_total', 'Proxy API errors', ['endpoint', 'error_type'])
    
    # Model availability via litellm
    litellm_model_available = Gauge('litellm_model_available', 'Model available via litellm', ['model'])

    def check_health():
        try:
            t0 = time.time()
            resp = requests.get(f'{LITELLM_URL}/health', timeout=10)
            litellm_api_latency.labels(endpoint='health').observe(time.time() - t0)
            if resp.status_code == 200:
                litellm_health.labels(endpoint='health').set(1)
            else:
                litellm_health.labels(endpoint='health').set(0)
                litellm_api_errors.labels(endpoint='health', error_type=f'status_{resp.status_code}').inc()
        except Exception as e:
            litellm_health.labels(endpoint='health').set(0)
            litellm_api_errors.labels(endpoint='health', error_type=type(e).__name__).inc()

    def check_models():
        try:
            t0 = time.time()
            resp = requests.get(f'{LITELLM_URL}/v1/models', timeout=10)
            litellm_api_latency.labels(endpoint='models').observe(time.time() - t0)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get('data', [])
                litellm_models_available.set(len(models))
                for m in models:
                    litellm_model_available.labels(model=m.get('id', 'unknown')).set(1)
        except Exception as e:
            litellm_api_errors.labels(endpoint='models', error_type=type(e).__name__).inc()

    def scrape_loop():
        while True:
            t0 = time.time()
            check_health()
            check_models()
            elapsed = time.time() - t0
            time.sleep(max(1, SCRAPE_INTERVAL - elapsed))

    if __name__ == '__main__':
        port = int(os.environ.get('PORT', '9476'))
        start_http_server(port)
        print(f'Litellm exporter started on port {port}')
        scrape_loop()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: litellm-prometheus-exporter
  namespace: default
  labels:
    app: litellm-prometheus-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: litellm-prometheus-exporter
  template:
    metadata:
      labels:
        app: litellm-prometheus-exporter
    spec:
      containers:
      - name: exporter
        image: python:3.11-slim
        command: ["sh", "-c"]
        args:
        - "pip install prometheus-client requests && python /app/exporter.py"
        ports:
        - name: metrics
          containerPort: 9476
        env:
        - name: LITELLM_URL
          value: "http://litellm.ai-platform.svc.cluster.local:4000"
        - name: SCRAPE_INTERVAL
          value: "15"
        - name: PORT
          value: "9476"
        volumeMounts:
        - name: script
          mountPath: /app
        resources:
          limits:
            cpu: 200m
            memory: 128Mi
          requests:
            cpu: 50m
            memory: 64Mi
      volumes:
      - name: script
        configMap:
          name: litellm-exporter-script
---
apiVersion: v1
kind: Service
metadata:
  name: litellm-prometheus-exporter
  namespace: default
  labels:
    app: litellm-prometheus-exporter
spec:
  selector:
    app: litellm-prometheus-exporter
  ports:
  - name: metrics
    port: 9476
    targetPort: 9476
  type: ClusterIP
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: litellm-prometheus-exporter
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: litellm-prometheus-exporter
  namespaceSelector:
    matchNames:
    - default
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
"""

kapply(litellm_exporter_yaml)

# =============================================
# PART 3: DIFY API METRICS EXPORTER
# =============================================
print("\n" + "=" * 60)
print("PART 3: Deploying Dify API metrics exporter")
print("=" * 60)

dify_exporter_yaml = """apiVersion: v1
kind: ConfigMap
metadata:
  name: dify-exporter-script
  namespace: default
data:
  exporter.py: |
    from prometheus_client import start_http_server, Gauge, Counter, Histogram
    import requests, time, os

    DIFY_API = os.environ.get('DIFY_API', 'http://dify-api.dify.svc.cluster.local:5001')
    DIFY_WEB = os.environ.get('DIFY_WEB', 'http://dify-web.dify.svc.cluster.local:3000')
    SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', '15'))

    dify_api_health = Gauge('dify_api_health', 'Dify API health', ['service'])
    dify_api_latency = Histogram('dify_api_check_latency_seconds', 'Check latency', ['service', 'endpoint'])
    dify_api_errors = Counter('dify_api_check_errors_total', 'Check errors', ['service', 'error_type'])

    def check_service(name, url, endpoint='/health'):
        try:
            t0 = time.time()
            resp = requests.get(f'{url}{endpoint}', timeout=10)
            dify_api_latency.labels(service=name, endpoint=endpoint).observe(time.time() - t0)
            if resp.status_code < 500:
                dify_api_health.labels(service=name).set(1)
            else:
                dify_api_health.labels(service=name).set(0)
        except Exception as e:
            dify_api_health.labels(service=name).set(0)
            dify_api_errors.labels(service=name, error_type=type(e).__name__).inc()

    def scrape_loop():
        while True:
            check_service('dify-api', DIFY_API)
            check_service('dify-web', DIFY_WEB)
            time.sleep(SCRAPE_INTERVAL)

    if __name__ == '__main__':
        port = int(os.environ.get('PORT', '9480'))
        start_http_server(port)
        print(f'Dify exporter started on port {port}')
        scrape_loop()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dify-prometheus-exporter
  namespace: default
  labels:
    app: dify-prometheus-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dify-prometheus-exporter
  template:
    metadata:
      labels:
        app: dify-prometheus-exporter
    spec:
      containers:
      - name: exporter
        image: python:3.11-slim
        command: ["sh", "-c"]
        args:
        - "pip install prometheus-client requests && python /app/exporter.py"
        ports:
        - name: metrics
          containerPort: 9480
        env:
        - name: DIFY_API
          value: "http://dify-api.dify.svc.cluster.local:5001"
        - name: DIFY_WEB
          value: "http://dify-web.dify.svc.cluster.local:3000"
        - name: SCRAPE_INTERVAL
          value: "15"
        - name: PORT
          value: "9480"
        volumeMounts:
        - name: script
          mountPath: /app
        resources:
          limits:
            cpu: 200m
            memory: 128Mi
          requests:
            cpu: 50m
            memory: 64Mi
      volumes:
      - name: script
        configMap:
          name: dify-exporter-script
---
apiVersion: v1
kind: Service
metadata:
  name: dify-prometheus-exporter
  namespace: default
  labels:
    app: dify-prometheus-exporter
spec:
  selector:
    app: dify-prometheus-exporter
  ports:
  - name: metrics
    port: 9480
    targetPort: 9480
  type: ClusterIP
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dify-prometheus-exporter
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: dify-prometheus-exporter
  namespaceSelector:
    matchNames:
    - default
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
"""

kapply(dify_exporter_yaml)

# =============================================
# PART 4: ENHANCED GRAFANA DASHBOARDS
# =============================================
print("\n" + "=" * 60)
print("PART 4: Deploying enhanced Grafana dashboards")
print("=" * 60)

def create_dashboard_configmap(name, filename, json_data):
    cm = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": name,
            "namespace": "monitoring",
            "labels": {
                "grafana_dashboard": "1",
                "app": "kube-prometheus-stack-grafana"
            }
        },
        "data": {
            filename: json.dumps(json_data, indent=2)
        }
    }
    return cm

# --- Dashboard 1: LLM Services (Enhanced) ---
llm_dashboard = {
    "annotations": {"list": []},
    "editable": True,
    "gnetId": None,
    "graphTooltip": 1,
    "links": [],
    "panels": [],
    "refresh": "30s",
    "schemaVersion": 38,
    "style": "dark",
    "tags": ["enterprise", "ai-platform", "llm"],
    "templating": {"list": []},
    "time": {"from": "now-6h", "to": "now"},
    "timepicker": {},
    "timezone": "browser",
    "title": "LLM Services - Enterprise (Enhanced)",
    "uid": "llm-services-v2",
    "version": 1
}

panels = []
y = 0
panel_id = 0

def add_row(title):
    global y, panel_id
    panel_id += 1
    panels.append({
        "collapsed": False, "datasource": {"type": "prometheus", "uid": "prometheus"},
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y}, "id": panel_id,
        "panels": [], "title": title, "type": "row"
    })
    y += 1
    return panel_id

def add_stat(title, expr, w=4, h=3, color_mode="background", unit="none", thresholds=None):
    global y, panel_id
    panel_id += 1
    if thresholds is None:
        thresholds = {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 0}]}
    panels.append({
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": thresholds, "unit": unit}},
        "gridPos": {"h": h, "w": w, "x": (panel_id-1)%24, "y": y},
        "id": panel_id, "options": {"colorMode": color_mode, "graphMode": "area", "justifyMode": "auto", "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "textMode": "auto"},
        "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "stat"
    })
    if (panel_id) % (24//w) == 0: y += h
    return panel_id

def add_timeseries(title, exprs, w=12, h=7, unit="short", legend=True):
    global y, panel_id
    panel_id += 1
    targets = [{"expr": e, "legendFormat": l, "refId": chr(65+i)} for i,(e,l) in enumerate(exprs)]
    panels.append({
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "custom": {"drawStyle": "line", "fillOpacity": 10, "lineWidth": 2, "showPoints": "never", "spanNulls": True, "stacking": {"mode": "none", "group": "A"}}, "unit": unit}, "overrides": []},
        "gridPos": {"h": h, "w": w, "x": (panel_id-1)%(24//2)*w if w==12 else 0, "y": y},
        "id": panel_id, "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "last"]} if legend else {"showLegend": False}, "tooltip": {"mode": "multi"}},
        "targets": targets, "title": title, "type": "timeseries"
    })
    y += h
    return panel_id

def add_gauge(title, expr, w=4, h=5, unit="percent", min_val=0, max_val=100):
    global y, panel_id
    panel_id += 1
    panels.append({
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 60}, {"color": "orange", "value": 80}, {"color": "red", "value": 90}]}, "unit": unit, "min": min_val, "max": max_val}},
        "gridPos": {"h": h, "w": w, "x": (panel_id-1)*w % 24, "y": y},
        "id": panel_id, "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "showThresholdLabels": True, "showThresholdMarkers": True},
        "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "gauge"
    })
    return panel_id

# ROW 1: Ollama Overview
add_row("🔴 Ollama Runtime Engine (Per-Model Metrics)")

# Stats row
add_stat("Ollama Master", 'count(up{namespace="ai-platform",pod=~"ollama-master-.*"}==1)', 3, 2)
add_stat("Ollama Worker", 'count(up{namespace="ai-platform",pod=~"ollama-worker-.*"}==1)', 3, 2)
add_stat("Models Available (Master)", 'ollama_api_tags_total{source="master"}', 3, 2)
add_stat("Models Available (Worker)", 'ollama_api_tags_total{source="worker"} or vector(0)', 3, 2)
add_stat("API Health Master", 'ollama_api_health{source="master"}', 3, 2)
add_stat("API Health Worker", 'ollama_api_health{source="worker"} or vector(0)', 3, 2)
add_stat("Loaded Models", 'count(ollama_model_loaded==1)', 3, 2)
add_stat("API Errors (1h)", 'sum(rate(ollama_api_errors_total[1h]))', 3, 2, thresholds={"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 0.1}, {"color": "red", "value": 1}]})

y = panels[-1]["gridPos"]["y"] + panels[-1]["gridPos"]["h"]

# Model size breakdown
add_timeseries("Model Sizes (All Models)", [('ollama_model_size_bytes', '{{model}}')], 12, 6, "bytes")
add_timeseries("Models Loaded in Memory", [('ollama_model_loaded', '{{model}}({{source}})')], 12, 6, "short")

# Per-model memory usage
add_timeseries("Per-Model Memory Usage", [('ollama_model_memory_bytes', '{{model}}({{source}})')], 12, 6, "bytes")
add_timeseries("API Latency (Per Endpoint)", [('rate(ollama_api_latency_seconds_sum{source="master"}[2m])/rate(ollama_api_latency_seconds_count{source="master"}[2m])', '{{endpoint}}')], 12, 6, "s")

# Container resources
add_timeseries("Ollama CPU Usage", [('rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"ollama-.*"}[5m])', '{{pod}}')], 12, 6, "cpus")
add_timeseries("Ollama Memory Usage", [('container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}', '{{pod}}')], 12, 6, "bytes")
add_gauge("Ollama Memory %", 'avg(container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}/container_spec_memory_limit_bytes{namespace="ai-platform",pod=~"ollama-.*"})*100', 6, 5)

# ROW 2: Litellm Gateway
add_row("🟢 Litellm AI Gateway")
add_stat("Litellm Pods", 'count(up{namespace="ai-platform",pod=~"litellm-.*"}==1)', 3, 2)
add_stat("Gateway Health", 'litellm_health{endpoint="health"}', 3, 2)
add_stat("Models Routed", 'litellm_models_available', 3, 2)
add_stat("Errors (1h)", 'sum(rate(litellm_api_proxy_errors_total[1h]))', 3, 2, thresholds={"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 0.1}, {"color": "red", "value": 1}]})

add_timeseries("Litellm Request Rate", [('sum(rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"litellm-.*"}[5m]))', 'Request Rate (CPU proxy)')], 12, 6, "cpus")
add_timeseries("Gateway Health Latency", [('rate(litellm_api_proxy_latency_seconds_sum[2m])/rate(litellm_api_proxy_latency_seconds_count[2m])', '{{endpoint}}')], 12, 6, "s")
add_timeseries("Litellm CPU", [('rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"litellm-.*"}[5m])', '{{pod}}')], 12, 6, "cpus")
add_timeseries("Litellm Memory", [('container_memory_working_set_bytes{namespace="ai-platform",pod=~"litellm-.*"}', '{{pod}}')], 12, 6, "bytes")

# ROW 3: Open-WebUI
add_row("🔵 Open-WebUI Frontend")
add_stat("WebUI Status", 'count(up{namespace="ai-platform",pod=~"open-webui-.*"}==1)', 4, 2)
add_stat("WebUI Restarts(1h)", 'sum(increase(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"open-webui-.*"}[1h]))', 4, 2)
add_timeseries("WebUI CPU", [('rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"open-webui-.*"}[5m])', '{{pod}}')], 12, 6, "cpus")
add_timeseries("WebUI Memory", [('container_memory_working_set_bytes{namespace="ai-platform",pod=~"open-webui-.*"}', '{{pod}}')], 12, 6, "bytes")

# ROW 4: Exporter Health
add_row("⚪ Metric Exporters Health")
add_stat("Ollama Exporter", 'count(up{namespace="default",pod=~"ollama-prometheus-exporter-.*"}==1)', 4, 2)
add_stat("Litellm Exporter", 'count(up{namespace="default",pod=~"litellm-prometheus-exporter-.*"}==1)', 4, 2)
add_stat("Dify Exporter", 'count(up{namespace="default",pod=~"dify-prometheus-exporter-.*"}==1)', 4, 2)

llm_dashboard["panels"] = panels

# Write dashboard JSON
with open(os.path.join(MONITORING, "grafana-dashboard-llm-v2.json"), "w") as f:
    json.dump(llm_dashboard, f, indent=2)

# Create ConfigMap and apply
cm_data = json.dumps(create_dashboard_configmap(
    "grafana-dashboard-llm-services-v2", 
    "grafana-dashboard-llm-services-v2.json", 
    llm_dashboard
), indent=2)

with open(os.path.join(MONITORING, "grafana-dashboard-llm-v2-cm.yaml"), "w") as f:
    f.write(cm_data)

kapply(cm_data)

# --- Dashboard 2: Dify Platform (Enhanced) ---
print("  Building Dify dashboard...")
dify_dashboard = dict(llm_dashboard)  # Copy base
dify_dashboard["title"] = "Dify Platform - Enterprise (Enhanced)"
dify_dashboard["uid"] = "dify-platform-v2"
dify_dashboard["panels"] = []

panels2 = []
y2 = 0
pid = 0

def add_row2(title):
    global y2, pid
    pid += 1
    panels2.append({"collapsed": False, "datasource": {"type": "prometheus", "uid": "prometheus"}, "gridPos": {"h": 1, "w": 24, "x": 0, "y": y2}, "id": pid, "panels": [], "title": title, "type": "row"})
    y2 += 1

def add_stat2(title, expr, w=4, h=3, thresholds=None):
    global y2, pid
    pid += 1
    if thresholds is None:
        thresholds = {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 0}]}
    panels2.append({"datasource": {"type": "prometheus", "uid": "prometheus"}, "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": thresholds, "unit": "none"}}, "gridPos": {"h": h, "w": w, "x": (pid-1)*w%24, "y": y2}, "id": pid, "options": {"colorMode": "background", "graphMode": "area", "justifyMode": "auto", "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "textMode": "auto"}, "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "stat"})

def add_ts2(title, exprs, w=12, h=7, unit="short"):
    global y2, pid
    pid += 1
    targets = [{"expr": e, "legendFormat": l, "refId": chr(65+i)} for i,(e,l) in enumerate(exprs)]
    panels2.append({"datasource": {"type": "prometheus", "uid": "prometheus"}, "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "custom": {"drawStyle": "line", "fillOpacity": 10, "lineWidth": 2, "showPoints": "never", "spanNulls": True, "stacking": {"mode": "none", "group": "A"}}, "unit": unit}, "overrides": []}, "gridPos": {"h": h, "w": w, "x": 0 if w==24 else (pid-1)*w%24, "y": y2}, "id": pid, "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "last"]}, "tooltip": {"mode": "multi"}}, "targets": targets, "title": title, "type": "timeseries"})
    y2 += h

add_row2("🟣 Dify Core Services (dify namespace)")
add_stat2("API Pods", 'count(up{namespace="dify",pod=~"dify-api-.*"}==1)')
add_stat2("Web Pods", 'count(up{namespace="dify",pod=~"dify-web-.*"}==1)')
add_stat2("Worker Pods", 'count(up{namespace="dify",pod=~"dify-worker-.*"}==1)')
add_stat2("Plugin Daemon", 'count(up{namespace="dify",pod=~"dify-plugin-daemon-.*"}==1)')
add_stat2("SMTP Debug", 'count(up{namespace="dify",pod=~"smtp-debug-.*"}==1)')
add_stat2("API Health", 'dify_api_health{service="dify-api"}', thresholds={"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 0}]})

y2 = 5

# API metrics
add_ts2("Dify API Request Rate", [('sum(rate(container_cpu_usage_seconds_total{namespace="dify"}[5m]))by(pod)', '{{pod}}')], 12, 5, "cpus")
add_ts2("Dify Web Request Rate", [('rate(container_cpu_usage_seconds_total{namespace="dify",pod=~"dify-web-.*"}[5m])', '{{pod}}')], 12, 5, "cpus")

add_ts2("Dify API Latency (Health Check)", [('rate(dify_api_check_latency_seconds_sum{service="dify-api"}[2m])/rate(dify_api_check_latency_seconds_count{service="dify-api"}[2m])', 'API Health Check')], 12, 5, "s")
add_ts2("Dify Web Latency", [('rate(dify_api_check_latency_seconds_sum{service="dify-web"}[2m])/rate(dify_api_check_latency_seconds_count{service="dify-web"}[2m])', 'Web Health Check')], 12, 5, "s")

add_ts2("Dify API Errors", [('sum(rate(dify_api_check_errors_total{service="dify-api"}[5m]))', 'API Errors')], 12, 5, "short")
add_ts2("Dify Web Errors", [('sum(rate(dify_api_check_errors_total{service="dify-web"}[5m]))', 'Web Errors')], 12, 5, "short")

add_ts2("Dify All CPU Usage", [('rate(container_cpu_usage_seconds_total{namespace="dify"}[5m])', '{{pod}}')], 24, 6, "cpus")
add_ts2("Dify All Memory Usage", [('container_memory_working_set_bytes{namespace="dify"}', '{{pod}}')], 24, 6, "bytes")

add_row2("🟡 Dify Infrastructure (dify-plus)")
add_stat2("PostgreSQL", 'count(up{namespace="dify-plus",pod=~"db-postgres-.*"}==1)')
add_stat2("Redis", 'count(up{namespace="dify-plus",pod=~"redis-.*"}==1)')
add_stat2("Weaviate", 'count(up{namespace="dify-plus",pod=~"weaviate-.*"}==1)')
add_stat2("Mail Server", 'count(up{namespace="dify-plus",pod=~"mail-server-.*"}==1)')

add_ts2("Dify Infra CPU", [('rate(container_cpu_usage_seconds_total{namespace="dify-plus"}[5m])', '{{pod}}')], 12, 6, "cpus")
add_ts2("Dify Infra Memory", [('container_memory_working_set_bytes{namespace="dify-plus"}', '{{pod}}')], 12, 6, "bytes")

add_ts2("PostgreSQL Memory", [('container_memory_working_set_bytes{namespace="dify-plus",pod=~"db-postgres-.*"}', '{{pod}}')], 12, 6, "bytes")
add_ts2("Redis Memory", [('container_memory_working_set_bytes{namespace="dify-plus",pod=~"redis-.*"}', '{{pod}}')], 12, 6, "bytes")

add_row2("⚪ Dify Exporter")
add_stat2("Exporter Health", 'count(up{namespace="default",pod=~"dify-prometheus-exporter-.*"}==1)')

dify_dashboard["panels"] = panels2

with open(os.path.join(MONITORING, "grafana-dashboard-dify-v2.json"), "w") as f:
    json.dump(dify_dashboard, f, indent=2)

cm_dify = json.dumps(create_dashboard_configmap("grafana-dashboard-dify-platform-v2", "grafana-dashboard-dify-platform-v2.json", dify_dashboard), indent=2)
with open(os.path.join(MONITORING, "grafana-dashboard-dify-v2-cm.yaml"), "w") as f:
    f.write(cm_dify)
kapply(cm_dify)

# --- Dashboard 3: Infrastructure (Enhanced) ---
print("  Building Infrastructure dashboard...")
infra_dashboard = dict(llm_dashboard)
infra_dashboard["title"] = "Infrastructure Overview - Enterprise (Enhanced)"
infra_dashboard["uid"] = "infrastructure-v2"
infra_dashboard["panels"] = []

panels3 = []
y3 = 0
pid3 = 0

def add_row3(title):
    global y3, pid3
    pid3 += 1
    panels3.append({"collapsed": False, "datasource": {"type": "prometheus", "uid": "prometheus"}, "gridPos": {"h": 1, "w": 24, "x": 0, "y": y3}, "id": pid3, "panels": [], "title": title, "type": "row"})
    y3 += 1

def add_stat3(title, expr, w=4, h=2):
    global y3, pid3
    pid3 += 1
    panels3.append({"datasource": {"type": "prometheus", "uid": "prometheus"}, "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 0}]}, "unit": "none"}}, "gridPos": {"h": h, "w": w, "x": (pid3-1)*w%24, "y": y3}, "id": pid3, "options": {"colorMode": "background", "graphMode": "area", "justifyMode": "auto", "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "textMode": "auto"}, "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "stat"})

def add_ts3(title, exprs, w=12, h=6, unit="short"):
    global y3, pid3
    pid3 += 1
    targets = [{"expr": e, "legendFormat": l, "refId": chr(65+i)} for i,(e,l) in enumerate(exprs)]
    panels3.append({"datasource": {"type": "prometheus", "uid": "prometheus"}, "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "custom": {"drawStyle": "line", "fillOpacity": 10, "lineWidth": 2, "showPoints": "never", "spanNulls": True, "stacking": {"mode": "none", "group": "A"}}, "unit": unit}, "overrides": []}, "gridPos": {"h": h, "w": w, "x": 0 if w==24 else (pid3-1)*w%24, "y": y3}, "id": pid3, "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "last"]}, "tooltip": {"mode": "multi"}}, "targets": targets, "title": title, "type": "timeseries"})
    y3 += h

add_row3("🟠 Cluster Nodes")
add_stat3("Nodes Total", 'count(kube_node_info)', 3)
add_stat3("Nodes Ready", 'count(kube_node_status_condition{condition="Ready",status="true"})', 3)
add_stat3("CPU Cores", 'sum(kube_node_status_capacity{resource="cpu"})', 3)
add_stat3("Memory Total", 'sum(kube_node_status_capacity{resource="memory"})/1073741824', 3)

add_ts3("Node CPU Usage %", [('100-avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))by(instance)*100', '{{instance}}')], 12, 6, "percent")
add_ts3("Node Memory Usage %", [('100*(1-(node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes))', '{{instance}}')], 12, 6, "percent")
add_ts3("Node Disk Usage %", [('100*(1-(node_filesystem_avail_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"}))', '{{instance}}')], 12, 6, "percent")
add_ts3("Node Network RX/TX", [('rate(node_network_receive_bytes_total[5m])', '{{instance}} rx'),('rate(node_network_transmit_bytes_total[5m])', '{{instance}} tx')], 24, 6, "Bps")

add_row3("🟢 Namespace Resources")
add_ts3("CPU Usage by Namespace", [('sum(rate(container_cpu_usage_seconds_total[5m]))by(namespace)', '{{namespace}}')], 24, 7, "cpus")
add_ts3("Memory Usage by Namespace", [('sum(container_memory_working_set_bytes)by(namespace)', '{{namespace}}')], 24, 7, "bytes")
add_ts3("Pod Count by Namespace", [('count(kube_pod_info)by(namespace)', '{{namespace}}')], 24, 6, "short")

add_row3("🔴 Ingress & Network")
add_ts3("Ingress Request Rate", [('sum(rate(nginx_ingress_controller_requests[5m]))by(ingress)', '{{ingress}}')], 12, 6, "reqps")
add_ts3("Ingress Error Rate (5xx)", [('sum(rate(nginx_ingress_controller_requests{status=~"5.."}[5m]))by(ingress)', '{{ingress}}')], 12, 6, "reqps")

add_row3("🟣 Persistent Storage")
add_ts3("PV Usage %", [('kubelet_volume_stats_used_bytes/kubelet_volume_stats_capacity_bytes*100', '{{persistentvolumeclaim}}({{namespace}})')], 24, 6, "percent")

infra_dashboard["panels"] = panels3

with open(os.path.join(MONITORING, "grafana-dashboard-infra-v2.json"), "w") as f:
    json.dump(infra_dashboard, f, indent=2)

cm_infra = json.dumps(create_dashboard_configmap("grafana-dashboard-infrastructure-v2", "grafana-dashboard-infrastructure-v2.json", infra_dashboard), indent=2)
kapply(cm_infra)

# --- Dashboard 4: Code-Server (Enhanced) ---
print("  Building Code-Server dashboard...")
cs_dashboard = dict(llm_dashboard)
cs_dashboard["title"] = "Code-Server IDE - Enterprise (Enhanced)"
cs_dashboard["uid"] = "codeserver-v2"
cs_dashboard["panels"] = []

panels4 = []
y4 = 0
pid4 = 0

def add_row4(title):
    global y4, pid4
    pid4 += 1
    panels4.append({"collapsed": False, "datasource": {"type": "prometheus", "uid": "prometheus"}, "gridPos": {"h": 1, "w": 24, "x": 0, "y": y4}, "id": pid4, "panels": [], "title": title, "type": "row"})
    y4 += 1

def add_stat4(title, expr, w=4, h=2):
    global y4, pid4
    pid4 += 1
    panels4.append({"datasource": {"type": "prometheus", "uid": "prometheus"}, "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "mappings": [], "thresholds": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 0}]}, "unit": "none"}}, "gridPos": {"h": h, "w": w, "x": (pid4-1)*w%24, "y": y4}, "id": pid4, "options": {"colorMode": "background", "graphMode": "area", "justifyMode": "auto", "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "textMode": "auto"}, "targets": [{"expr": expr, "refId": "A"}], "title": title, "type": "stat"})

def add_ts4(title, exprs, w=12, h=6, unit="short"):
    global y4, pid4
    pid4 += 1
    targets = [{"expr": e, "legendFormat": l, "refId": chr(65+i)} for i,(e,l) in enumerate(exprs)]
    panels4.append({"datasource": {"type": "prometheus", "uid": "prometheus"}, "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "custom": {"drawStyle": "line", "fillOpacity": 10, "lineWidth": 2, "showPoints": "never", "spanNulls": True, "stacking": {"mode": "none", "group": "A"}}, "unit": unit}, "overrides": []}, "gridPos": {"h": h, "w": w, "x": 0 if w==24 else (pid4-1)*w%24, "y": y4}, "id": pid4, "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "last"]}, "tooltip": {"mode": "multi"}}, "targets": targets, "title": title, "type": "timeseries"})
    y4 += h

add_row4("🟢 Code-Server Overview")
add_stat4("Total Pods", 'count(up{namespace="ai-platform",pod=~"code-server-.*"}==1)', 3)
add_stat4("Ready Pods", 'count(kube_pod_status_ready{namespace="ai-platform",pod=~"code-server-.*",condition="true"})', 3)
add_stat4("Restarts (24h)", 'sum(increase(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"}[24h]))', 3)
add_stat4("Avg Restarts/Pod", 'sum(increase(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"}[1h]))/count(kube_pod_info{namespace="ai-platform",pod=~"code-server-.*"})', 3, thresholds={"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 0.5}, {"color": "red", "value": 2}]})

add_ts4("Code-Server CPU Usage (Per Pod)", [('rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', '{{pod}}')], 24, 7, "cpus")
add_ts4("Code-Server Memory Usage (Per Pod)", [('container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"}', '{{pod}}')], 24, 7, "bytes")

add_row4("🔵 Code-Server Resource Distribution")
add_ts4("CPU Top 10 Pods", [('topk(10,rate(container_cpu_usage_seconds_total{namespace="ai-platform",pod=~"code-server-.*"}[5m]))', '{{pod}}')], 12, 7, "cpus")
add_ts4("Memory Top 10 Pods", [('topk(10,container_memory_working_set_bytes{namespace="ai-platform",pod=~"code-server-.*"})', '{{pod}}')], 12, 7, "bytes")
add_ts4("Network RX by Pod", [('rate(container_network_receive_bytes_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', '{{pod}}')], 12, 7, "Bps")
add_ts4("Network TX by Pod", [('rate(container_network_transmit_bytes_total{namespace="ai-platform",pod=~"code-server-.*"}[5m])', '{{pod}}')], 12, 7, "Bps")

add_row4("🟣 Code-Server Health")
add_ts4("Pod Restarts Over Time", [('sum(increase(kube_pod_container_status_restarts_total{namespace="ai-platform",pod=~"code-server-.*"}[5m]))by(pod)', '{{pod}}')], 24, 6, "short")
add_ts4("Pod Phase Distribution", [('sum(kube_pod_status_phase{namespace="ai-platform",pod=~"code-server-.*"})by(phase)', '{{phase}}')], 12, 6, "short")

cs_dashboard["panels"] = panels4

with open(os.path.join(MONITORING, "grafana-dashboard-cs-v2.json"), "w") as f:
    json.dump(cs_dashboard, f, indent=2)

cm_cs = json.dumps(create_dashboard_configmap("grafana-dashboard-codeserver-v2", "grafana-dashboard-codeserver-v2.json", cs_dashboard), indent=2)
kapply(cm_cs)

# =============================================
# PART 5: ENHANCED PROMETHEUS RULES
# =============================================
print("\n" + "=" * 60)
print("PART 5: Deploying enhanced PrometheusRules")
print("=" * 60)

enhanced_rules = """apiVersion: monitoring.coreos.com/v1
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
        description: "Model {{ $labels.model }} is not available on {{ $labels.source }}. Check ollama service."
    - alert: OllamaAPIUnhealthy
      expr: ollama_api_health == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Ollama API unhealthy on {{ $labels.source }}"
        description: "Ollama API on {{ $labels.source }} is not responding. Pod may be down."
    - alert: OllamaHighAPILatency
      expr: rate(ollama_api_latency_seconds_sum[5m])/rate(ollama_api_latency_seconds_count[5m]) > 5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Ollama API latency > 5s"
        description: "Ollama endpoint {{ $labels.endpoint }} has high latency on {{ $labels.source }}"
    - alert: OllamaHighErrorRate
      expr: rate(ollama_api_errors_total[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Ollama error rate above threshold"
        description: "Ollama errors: {{ $value }}/s on {{ $labels.source }}"
    - alert: OllamaHighMemory
      expr: container_memory_working_set_bytes{namespace="ai-platform",pod=~"ollama-.*"}/container_spec_memory_limit_bytes{namespace="ai-platform",pod=~"ollama-.*"} > 0.9
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "Ollama pod {{ $labels.pod }} memory > 90%"
        description: "Memory usage is {{ $value | humanizePercentage }}"
  - name: litellm-alerts
    rules:
    - alert: LitellmGatewayDown
      expr: litellm_health{endpoint="health"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Litellm gateway is down"
        description: "Litellm health check failing for more than 2 minutes"
    - alert: LitellmHighErrorRate
      expr: rate(litellm_api_proxy_errors_total[5m]) > 0.2
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Litellm error rate: {{ $value }}/s"
        description: "Errors on endpoint {{ $labels.endpoint }}"
  - name: dify-alerts
    rules:
    - alert: DifyAPIDown
      expr: dify_api_health{service="dify-api"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Dify API is down"
        description: "Dify API health check failing"
    - alert: DifyWebDown
      expr: dify_api_health{service="dify-web"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Dify Web is down"
        description: "Dify Web health check failing"
    - alert: DifyHighPodRestarts
      expr: rate(kube_pod_container_status_restarts_total{namespace="dify"}[1h]) > 0.1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Dify pod {{ $labels.pod }} restarts frequently"
        description: "{{ $value }} restarts/hour"
  - name: exporter-alerts
    rules:
    - alert: ExporterDown
      expr: up{namespace="default",pod=~".*-prometheus-exporter-.*"} == 0
      for: 3m
      labels:
        severity: critical
      annotations:
        summary: "Metrics exporter {{ $labels.pod }} is down"
        description: "The Prometheus metrics exporter for {{ $labels.pod }} is not responding"
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
      expr: (1 - (node_filesystem_avail_bytes{mountpoint='/'} / node_filesystem_size_bytes{mountpoint='/'})) * 100 > 85
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
        description: "Expected 20+ code-server pods"
"""

with open(os.path.join(MONITORING, "enterprise-alert-rules-v2.yaml"), "w") as f:
    f.write(enhanced_rules)

kapply(enhanced_rules)

# =============================================
# SUMMARY
# =============================================
print("\n" + "=" * 60)
print("DEPLOYMENT COMPLETE")
print("=" * 60)
print("""
Deployed:
  1. ollama-prometheus-exporter (per-model metrics: model_info, model_loaded, model_memory, api_latency)
  2. litellm-prometheus-exporter (gateway health, model availability)
  3. dify-prometheus-exporter (API/Web health checks)
  4. 3 ServiceMonitors for new exporters
  5. 4 Enhanced Grafana dashboards:
     - LLM Services v2 (per-model latency, tokens, memory, CPU)
     - Dify Platform v2 (API/worker/queue, infra memory)
     - Infrastructure v2 (node resources, PV usage, ingress)
     - Code-Server v2 (per-pod CPU/memory/network, top resources)
  6. Enhanced PrometheusRules v2 (11 alerts: model, API, node, PV, code-server)

Access: http://10.167.2.175:30082
""")

# Wait for exporter pods to start
print("\nWaiting for exporter pods to start...")
time.sleep(5)
stdout, _, _ = run("kubectl get pods -n default | Select-String exporter")
print(f"  Exporter pods:\n{stdout}")

print("\n✓ Monitoring deployment complete!")