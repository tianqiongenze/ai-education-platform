#!/bin/bash
set -e

echo "========================================"
echo "Redeploying litellm"
echo "Time: $(date)"
echo "========================================"

# Delete old pod to force restart with new image
kubectl delete pod -n ai-platform -l app=litellm

echo ""
echo "Waiting for new pod to start..."
sleep 5

# Watch pod status
kubectl get pods -n ai-platform -l app=litellm -w --timeout=120s &
WATCH_PID=$!

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod -n ai-platform -l app=litellm --timeout=180s 2>&1 || true
kill $WATCH_PID 2>/dev/null || true

echo ""
echo "========================================"
echo "Pod status:"
kubectl get pods -n ai-platform -l app=litellm
echo ""

# Check logs
POD_NAME=$(kubectl get pods -n ai-platform -l app=litellm -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$POD_NAME" ]; then
    echo "Pod logs:"
    kubectl logs -n ai-platform $POD_NAME --tail=20
fi

echo ""
echo "========================================"
echo "Testing litellm health endpoint..."
sleep 5
kubectl run test-litellm --rm -i --restart=Never --image=alpine:edge --command -- sh -c "apk add --no-cache curl >/dev/null 2>&1 && curl -s http://litellm:4000/health/liveliness" 2>&1 || true

echo ""
echo "Redeploy completed!"
echo "Time: $(date)"
