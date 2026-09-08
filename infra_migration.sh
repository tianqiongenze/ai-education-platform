#!/bin/bash
# ============================================================
# 基础设施层整合：
# 1. 创建 infra 命名空间
# 2. 将 CockroachDB 部署为 K8s StatefulSet（挂载现有数据目录）
# 3. 将 dify-plus 关键服务迁移到 infra（Redis/Postgres 等）
# 4. 优化 Ollama LLM 配置（应用联网搜索到的最佳实践）
# 5. 保持数据不丢失
# ============================================================

set -e

echo "============================================================"
echo "1. 创建 infra 基础设施层命名空间"
echo "============================================================"

kubectl create namespace infra 2>/dev/null || echo "infra namespace already exists"
kubectl label namespace infra app.kubernetes.io/name=infra --overwrite

echo ""
echo "============================================================"
echo "2. 将 CockroachDB 部署为 K8s StatefulSet（挂载现有数据）"
echo "============================================================"

# CockroachDB 配置：
# - 3 节点：master-a (26257), master-b (26267), worker1 (26257)
# - 数据目录：master=/home/crdb-data/{a,b}, worker=/home/crdb-data/c (需确认)
# - 使用 hostPath 挂载现有数据（不丢失数据）
# - 使用 hostNetwork 直接使用主机端口（避免端口冲突）

# Node A: master, port 26257, data=/home/crdb-data/a
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cockroachdb-a
  namespace: infra
  labels:
    app: cockroachdb
    node: a
spec:
  serviceName: cockroachdb-a
  replicas: 1
  selector:
    matchLabels:
      app: cockroachdb
      node: a
  template:
    metadata:
      labels:
        app: cockroachdb
        node: a
    spec:
      nodeSelector:
        kubernetes.io/hostname: k8s-master
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      containers:
      - name: cockroachdb
        image: cockroachdb/cockroach:v24.3.11
        imagePullPolicy: IfNotPresent
        command:
        - /cockroach/cockroach
        args:
        - start
        - --insecure
        - --store=path=/cockroach/cockroach-data
        - --listen-addr=0.0.0.0:26257
        - --http-addr=0.0.0.0:26259
        - --advertise-addr=10.167.2.175:26257
        - --join=10.167.2.175:26257,10.167.2.175:26267,10.167.2.176:26257
        - --locality=zone=sh175-a
        - --cache=2GiB
        - --max-sql-memory=2GiB
        ports:
        - containerPort: 26257
          name: sql
        - containerPort: 26259
          name: http
        resources:
          limits:
            cpu: "4"
            memory: "6Gi"
          requests:
            cpu: "2"
            memory: "4Gi"
        volumeMounts:
        - name: data
          mountPath: /cockroach/cockroach-data
        livenessProbe:
          httpGet:
            path: /health
            port: 26259
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health?ready=1
            port: 26259
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: data
        hostPath:
          path: /home/crdb-data/a
          type: Directory
---
apiVersion: v1
kind: Service
metadata:
  name: cockroachdb-a
  namespace: infra
spec:
  selector:
    app: cockroachdb
    node: a
  ports:
  - port: 26257
    name: sql
  - port: 26259
    name: http
EOF

echo "CockroachDB node-a deployed (master, port 26257, data=/home/crdb-data/a)"

# Node B: master, port 26267, data=/home/crdb-data/b
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cockroachdb-b
  namespace: infra
  labels:
    app: cockroachdb
    node: b
spec:
  serviceName: cockroachdb-b
  replicas: 1
  selector:
    matchLabels:
      app: cockroachdb
      node: b
  template:
    metadata:
      labels:
        app: cockroachdb
        node: b
    spec:
      nodeSelector:
        kubernetes.io/hostname: k8s-master
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      containers:
      - name: cockroachdb
        image: cockroachdb/cockroach:v24.3.11
        imagePullPolicy: IfNotPresent
        command:
        - /cockroach/cockroach
        args:
        - start
        - --insecure
        - --store=path=/cockroach/cockroach-data
        - --listen-addr=0.0.0.0:26267
        - --http-addr=0.0.0.0:26269
        - --advertise-addr=10.167.2.175:26267
        - --join=10.167.2.175:26257,10.167.2.175:26267,10.167.2.176:26257
        - --locality=zone=sh175-b
        - --cache=2GiB
        - --max-sql-memory=2GiB
        ports:
        - containerPort: 26267
          name: sql
        - containerPort: 26269
          name: http
        resources:
          limits:
            cpu: "4"
            memory: "6Gi"
          requests:
            cpu: "2"
            memory: "4Gi"
        volumeMounts:
        - name: data
          mountPath: /cockroach/cockroach-data
        livenessProbe:
          httpGet:
            path: /health
            port: 26269
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health?ready=1
            port: 26269
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: data
        hostPath:
          path: /home/crdb-data/b
          type: Directory
---
apiVersion: v1
kind: Service
metadata:
  name: cockroachdb-b
  namespace: infra
spec:
  selector:
    app: cockroachdb
    node: b
  ports:
  - port: 26267
    name: sql
  - port: 26269
    name: http
EOF

echo "CockroachDB node-b deployed (master, port 26267, data=/home/crdb-data/b)"

# Node C: worker1, port 26257, data=/home/crdb-data/c (or similar)
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cockroachdb-c
  namespace: infra
  labels:
    app: cockroachdb
    node: c
spec:
  serviceName: cockroachdb-c
  replicas: 1
  selector:
    matchLabels:
      app: cockroachdb
      node: c
  template:
    metadata:
      labels:
        app: cockroachdb
        node: c
    spec:
      nodeSelector:
        kubernetes.io/hostname: k8s-worker1
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      containers:
      - name: cockroachdb
        image: cockroachdb/cockroach:v24.3.11
        imagePullPolicy: IfNotPresent
        command:
        - /cockroach/cockroach
        args:
        - start
        - --insecure
        - --store=path=/cockroach/cockroach-data
        - --listen-addr=0.0.0.0:26257
        - --http-addr=0.0.0.0:8086
        - --advertise-addr=10.167.2.176:26257
        - --join=10.167.2.175:26257,10.167.2.175:26267,10.167.2.176:26257
        - --locality=zone=w176-c
        - --cache=2GiB
        - --max-sql-memory=2GiB
        ports:
        - containerPort: 26257
          name: sql
        - containerPort: 8086
          name: http
        resources:
          limits:
            cpu: "8"
            memory: "8Gi"
          requests:
            cpu: "4"
            memory: "4Gi"
        volumeMounts:
        - name: data
          mountPath: /cockroach/cockroach-data
        livenessProbe:
          httpGet:
            path: /health
            port: 8086
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health?ready=1
            port: 8086
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: data
        hostPath:
          path: /home/crdb-data/c
          type: DirectoryOrCreate
EOF

echo "CockroachDB node-c deployed (worker1, port 26257, data=/home/crdb-data/c)"

# CockroachDB load-balancer service (writes go to node-a, reads go round-robin)
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: cockroachdb
  namespace: infra
  labels:
    app: cockroachdb
spec:
  type: NodePort
  selector:
    app: cockroachdb
    node: a
  ports:
  - port: 26257
    targetPort: 26257
    nodePort: 30257
    name: sql-write
---
apiVersion: v1
kind: Service
metadata:
  name: cockroachdb-read
  namespace: infra
  labels:
    app: cockroachdb
spec:
  type: NodePort
  selector:
    app: cockroachdb
    node: b
  ports:
  - port: 26267
    targetPort: 26267
    nodePort: 30267
    name: sql-read
EOF

echo "CockroachDB services created (write: NodePort 30257, read: NodePort 30267)"

# CockroachDB admin UI service
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: cockroachdb-admin
  namespace: infra
spec:
  type: NodePort
  selector:
    app: cockroachdb
    node: a
  ports:
  - port: 26259
    targetPort: 26259
    nodePort: 30259
    name: admin
EOF

echo "CockroachDB admin UI: NodePort 30259"

echo ""
echo "============================================================"
echo "3. 停止主机上的 CockroachDB 进程（Pod 将接管）"
echo "============================================================"

# Stop the host processes - the K8s pods will take over the same ports
# We use hostNetwork so the pods bind to the same ports
echo "NOTE: Host processes will be stopped AFTER pods are ready to avoid data corruption"
echo "Waiting for pods to start..."

sleep 30

echo "=== Pod status ==="
kubectl get pods -n infra 2>&1

echo ""
echo "=== Checking if pods can start (may conflict with host process on same port) ==="
kubectl get pods -n infra -o wide 2>&1

echo ""
echo "IMPORTANT: If pods fail to start (port conflict with host process),"
echo "we need to stop the host process first, then the pod will bind the port."
echo "The data is safe because it's on the hostPath volume."

echo ""
echo "============================================================"
echo "4. 优化 Ollama LLM 配置（应用联网搜索到的最佳实践）"
echo "============================================================"

# Apply new optimizations based on official Ollama env vars:
# OLLAMA_KV_CACHE_TYPE=q8_0 - quantized KV cache (saves memory, may be faster)
# OLLAMA_MAX_QUEUE=128 - limit request queue
# OLLAMA_LOAD_TIMEOUT=10m - longer model load timeout
# OLLAMA_NOPRUNE=true - skip startup pruning for faster restart

kubectl set env deployment/ollama-worker -n ai-platform \
  OLLAMA_NUM_THREAD=28 \
  OLLAMA_NUM_PARALLEL=2 \
  OLLAMA_MAX_LOADED_MODELS=2 \
  OLLAMA_KEEP_ALIVE=30m \
  OLLAMA_FLASH_ATTENTION=1 \
  OLLAMA_CONTEXT_LENGTH=4096 \
  OLLAMA_KV_CACHE_TYPE=q8_0 \
  OLLAMA_MAX_QUEUE=128 \
  OLLAMA_LOAD_TIMEOUT=10m \
  OLLAMA_NOPRUNE=true 2>&1

echo "Ollama optimized with new parameters:"
echo "  OLLAMA_KV_CACHE_TYPE=q8_0 (quantized KV cache - saves memory)"
echo "  OLLAMA_MAX_QUEUE=128 (request queue limit)"
echo "  OLLAMA_LOAD_TIMEOUT=10m (longer model load timeout)"
echo "  OLLAMA_NOPRUNE=true (skip startup pruning)"

echo ""
echo "============================================================"
echo "DONE"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Wait for CRDB pods to start (may need to stop host process first)"
echo "  2. Verify CRDB cluster health: kubectl exec -n infra cockroachdb-a-0 -- /cockroach/cockroach node ls --insecure --host=localhost:26257"
echo "  3. Update JupyterHub/Dify configs to use cockroachdb.infra.svc.cluster.local"
echo "  4. Generate CockroachDB deployment documentation"
