#!/bin/bash
# Deploy CRDB with runAsUser:0 to fix permission issue
set -e

echo "=== Delete old StatefulSets ==="
kubectl delete sts cockroachdb-a cockroachdb-b cockroachdb-c -n infra 2>&1 || true

echo ""
echo "=== Deploy Node A (master, port 26257, root user) ==="
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
      securityContext:
        runAsUser: 0
        runAsGroup: 0
        fsGroup: 0
      initContainers:
      - name: copy-binary
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
        command: ['sh', '-c', 'cp /host-cockroach/cockroach /cockroach-binary/cockroach && chmod +x /cockroach-binary/cockroach']
        volumeMounts:
        - name: cockroach-binary
          mountPath: /cockroach-binary
        - name: host-binary
          mountPath: /host-cockroach
          readOnly: true
      containers:
      - name: cockroachdb
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        command: ['/cockroach-binary/cockroach']
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
        - containerPort: 26259
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
        - name: cockroach-binary
          mountPath: /cockroach-binary
          readOnly: true
      volumes:
      - name: data
        hostPath:
          path: /home/crdb-data/a
          type: Directory
      - name: cockroach-binary
        emptyDir: {}
      - name: host-binary
        hostPath:
          path: /opt/cockroach
          type: Directory
EOF

echo "Node A deployed"

echo ""
echo "=== Deploy Node B (master, port 26267, root user) ==="
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
      securityContext:
        runAsUser: 0
        runAsGroup: 0
        fsGroup: 0
      initContainers:
      - name: copy-binary
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
        command: ['sh', '-c', 'cp /host-cockroach/cockroach /cockroach-binary/cockroach && chmod +x /cockroach-binary/cockroach']
        volumeMounts:
        - name: cockroach-binary
          mountPath: /cockroach-binary
        - name: host-binary
          mountPath: /host-cockroach
          readOnly: true
      containers:
      - name: cockroachdb
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        command: ['/cockroach-binary/cockroach']
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
        - containerPort: 26269
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
        - name: cockroach-binary
          mountPath: /cockroach-binary
          readOnly: true
      volumes:
      - name: data
        hostPath:
          path: /home/crdb-data/b
          type: Directory
      - name: cockroach-binary
        emptyDir: {}
      - name: host-binary
        hostPath:
          path: /opt/cockroach
          type: Directory
EOF

echo "Node B deployed"

echo ""
echo "=== Deploy Node C (worker1, port 26257, root user) ==="
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
      securityContext:
        runAsUser: 0
        runAsGroup: 0
        fsGroup: 0
      initContainers:
      - name: copy-binary
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
        command: ['sh', '-c', 'cp /host-cockroach/cockroach /cockroach-binary/cockroach && chmod +x /cockroach-binary/cockroach']
        volumeMounts:
        - name: cockroach-binary
          mountPath: /cockroach-binary
        - name: host-binary
          mountPath: /host-cockroach
          readOnly: true
      containers:
      - name: cockroachdb
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        command: ['/cockroach-binary/cockroach']
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
        - containerPort: 8086
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
        - name: cockroach-binary
          mountPath: /cockroach-binary
          readOnly: true
      volumes:
      - name: data
        hostPath:
          path: /home/crdb-data/c
          type: DirectoryOrCreate
      - name: cockroach-binary
        emptyDir: {}
      - name: host-binary
        hostPath:
          path: /opt/cockroach
          type: Directory
EOF

echo "Node C deployed"

echo ""
echo "=== Wait 30s for pods ==="
sleep 30
kubectl get pods -n infra -o wide

echo ""
echo "=== Pod logs ==="
kubectl logs cockroachdb-a-0 -n infra -c cockroachdb 2>&1 | tail -10

echo ""
echo "=== Check CRDB cluster ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach node ls --insecure --host=localhost:26257 2>&1 | head -10

echo ""
echo "=== Check databases ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach sql --insecure --host=localhost:26257 --execute="SHOW DATABASES" 2>&1 | head -20
