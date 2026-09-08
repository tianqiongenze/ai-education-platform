#!/bin/bash
echo "============================================================"
echo "            RIGOROUS FINAL VERIFICATION"
echo "============================================================"

PASS=0
FAIL=0

check() {
  local desc="$1"
  local cmd="$2"
  echo -n "CHECK: $desc ... "
  if eval "$cmd" > /dev/null 2>&1; then
    echo "PASS"
    PASS=$((PASS + 1))
  else
    echo "FAIL"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "--- 1. KUBERNETES NODES ---"
check "Both nodes Ready" "kubectl get nodes 2>&1 | grep -v NAME | grep -v NotReady | wc -l | grep -q 2"

echo ""
echo "--- 2. SYSTEM PODS ---"
check "etcd running" "kubectl get pod -n kube-system etcd-k8s-master 2>&1 | grep -q Running"
check "kube-apiserver running" "kubectl get pod -n kube-system kube-apiserver-k8s-master 2>&1 | grep -q Running"
check "kube-controller-manager running" "kubectl get pod -n kube-system kube-controller-manager-k8s-master 2>&1 | grep -q Running"
check "kube-scheduler running" "kubectl get pod -n kube-system kube-scheduler-k8s-master 2>&1 | grep -q Running"
check "coredns running" "kubectl get pods -n kube-system -l k8s-app=kube-dns 2>&1 | grep Running | wc -l | grep -q 2"
check "calico-node running (both)" "kubectl get pods -n kube-system -l k8s-app=calico-node 2>&1 | grep Running | wc -l | grep -q 2"
check "calico-kube-controllers running" "kubectl get pods -n kube-system -l k8s-app=calico-kube-controllers 2>&1 | grep -q Running"
check "metrics-server running" "kubectl get pods -n kube-system -l k8s-app=metrics-server 2>&1 | grep -q Running"
check "kube-proxy running (both)" "kubectl get pods -n kube-system -l k8s-app=kube-proxy 2>&1 | grep Running | wc -l | grep -q 2"

echo ""
echo "--- 3. RANCHER & AGENT ---"
check "Rancher container ping" "curl -sk http://127.0.0.1/ping 2>&1 | grep -q pong"
check "cattle-cluster-agent running" "kubectl get pod -n cattle-system 2>&1 | grep cattle-cluster-agent | grep -q Running"

echo ""
echo "--- 4. APPLICATION PODS ---"
check "Dify API running" "kubectl get pods -n dify -l app=dify-api 2>&1 | grep Running | wc -l | grep -q 3"
check "Dify Web running" "kubectl get pods -n dify -l app=dify-web 2>&1 | grep Running | wc -l | grep -q 3"
check "Dify Worker running" "kubectl get pods -n dify -l app=dify-worker 2>&1 | grep Running | wc -l | grep -q 3"
check "ingress-nginx running" "kubectl get pods -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx 2>&1 | grep Running | grep -q 1"
check "grafana running" "kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana 2>&1 | grep -q Running"
check "alertmanager running" "kubectl get pods -n monitoring -l app.kubernetes.io/name=alertmanager 2>&1 | grep -q Running"
check "loki-stack running" "kubectl get pods -n monitoring -l app=loki-stack 2>&1 | grep -q Running"
check "postgres running" "kubectl get pods -n dify-plus -l app=db-postgres 2>&1 | grep -q Running"
check "redis running" "kubectl get pods -n dify-plus -l app=redis 2>&1 | grep -q Running"
check "weaviate running" "kubectl get pods -n dify-plus -l app=weaviate 2>&1 | grep -q Running"

echo ""
echo "--- 5. PVC STATUS ---"
check "All PVCs Bound" "kubectl get pvc -A 2>&1 | grep -v NAME | grep -v Bound | wc -l | grep -q 0"

echo ""
echo "--- 6. DOCKER CONFIGURATION ---"
check "Master Docker root = /home/docker-data" "docker info --format '{{.DockerRootDir}}' 2>&1 | grep -q '/home/docker-data'"

echo ""
echo "--- 7. LOCAL-PATH PROVISIONER ---"
check "local-path symlink exists" "ls -la /opt/local-path-provisioner 2>&1 | grep -q '-> /home/k8s-local-path'"
check "local-path pod running" "kubectl get pods -n local-path-storage 2>&1 | grep -q Running"

echo ""
echo "--- 8. ZERO BAD PODS ---"
bad=$(kubectl get pods -A 2>/dev/null | grep -vE 'Running|Completed' | grep -v NAMESPACE | wc -l)
check "Zero non-Running, non-Completed pods" "[ $bad -eq 0 ]"

echo ""
echo "============================================================"
echo "RESULTS: $PASS passed, $FAIL failed"
echo "============================================================"
