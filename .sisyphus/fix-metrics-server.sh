#!/bin/bash
echo "Fixing metrics-server image..."
kubectl set image deployment -n kube-system metrics-server metrics-server=m.daocloud.io/registry.k8s.io/metrics-server/metrics-server:v0.6.4 2>&1
echo "Waiting for rollout..."
kubectl rollout status deployment -n kube-system metrics-server 2>&1
echo "New pod:"
kubectl get pods -n kube-system -l k8s-app=metrics-server -o wide 2>&1
