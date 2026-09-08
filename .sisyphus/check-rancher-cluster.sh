#!/bin/bash
echo "=== cattle-system pods ==="
kubectl get pods -n cattle-system -o wide 2>&1
echo ""
echo "=== cattle-cluster-agent logs ==="
kubectl logs -n cattle-system deployment/cattle-cluster-agent --tail=10 2>&1
echo ""
echo "=== Rancher cluster status ==="
curl -sk "https://127.0.0.1/v3/clusters/c-jxn7d" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'name' in d:
    print('Cluster: %s, State: %s, Transitioning: %s' % (d.get('name'), d.get('state'), d.get('transitioning')))
    if d.get('conditions'):
        for c in d.get('conditions', []):
            if c.get('type') == 'Connected':
                print('Connected: %s, Message: %s' % (c.get('status'), c.get('message', '')))
else:
    print('Error: %s' % d)
"
