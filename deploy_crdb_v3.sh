#!/bin/bash
# Fix CRDB: reduce memory settings + add /dev/shm emptyDir
set -e

echo "=== Delete old StatefulSets ==="
kubectl delete sts cockroachdb-a cockroachdb-b cockroachdb-c -n infra 2>&1 || true

echo ""
echo "=== Deploy with reduced memory + /dev/shm ==="

# Node A - reduced cache to 1GiB, max-sql-memory to 1GiB
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
        - --cache=512MiB
        - --max-sql-memory=512MiB
        ports:
        - containerPort: 26257
        - containerPort: 26259
        resources:
          limits:
            cpu: "4"
            memory: "3Gi"
          requests:
            cpu: "1"
            memory: "1Gi"
        volumeMounts:
        - name: data
          mountPath: /cockroach/cockroach-data
        - name: cockroach-binary
          mountPath: /cockroach-binary
          readOnly: true
        - name: shm
          mountPath: /dev/shm
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
      - name: shm
        emptyDir:
          medium: Memory
          sizeLimit: 1Gi
EOF

echo "Node A deployed (reduced memory)"

# Node B - same settings
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
        - --cache=512MiB
        - --max-sql-memory=512MiB
        ports:
        - containerPort: 26267
        - containerPort: 26269
        resources:
          limits:
            cpu: "4"
            memory: "3Gi"
          requests:
            cpu: "1"
            memory: "1Gi"
        volumeMounts:
        - name: data
          mountPath: /cockroach/cockroach-data
        - name: cockroach-binary
          mountPath: /cockroach-binary
          readOnly: true
        - name: shm
          mountPath: /dev/shm
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
      - name: shm
        emptyDir:
          medium: Memory
          sizeLimit: 1Gi
EOF

echo "Node B deployed (reduced memory)"

# Node C
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
        - --cache=512MiB
        - --max-sql-memory=512MiB
        ports:
        - containerPort: 26257
        - containerPort: 8086
        resources:
          limits:
            cpu: "4"
            memory: "3Gi"
          requests:
            cpu: "1"
            memory: "1Gi"
        volumeMounts:
        - name: data
          mountPath: /cockroach/cockroach-data
        - name: cockroach-binary
          mountPath: /cockroach-binary
          readOnly: true
        - name: shm
          mountPath: /dev/shm
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
      - name: shm
        emptyDir:
          medium: Memory
          sizeLimit: 1Gi
EOF

echo "Node C deployed (reduced memory)"

echo ""
echo "=== Wait 45s for pods ==="
sleep 45
kubectl get pods -n infra -o wide

echo ""
echo "=== Pod logs ==="
kubectl logs cockroachdb-a-0 -n infra -c cockroachdb 2>&1 | tail -10

echo ""
echo "=== Check cluster ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach node ls --insecure --host=localhost:26257 2>&1 | head -10

echo ""
echo "=== Check databases ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach sql --insecure --host=localhost:26257 --execute="SHOW DATABASES" 2>&1 | head -20
