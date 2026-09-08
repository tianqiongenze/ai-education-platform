#!/bin/bash
set -e

# Login
echo "=== Logging into Rancher ==="
LOGIN=$(curl -k -s "https://localhost/v3-public/localProviders/local?action=login" \
  -H "Content-Type: application/json" \
  -d @/tmp/rancher-login.json)
echo "Login response received"

TOKEN=$(echo "$LOGIN" | sed 's/.*"token":"\([^"]*\)".*/\1/')
echo "Token: ${TOKEN:0:20}..."

# List current clusters
echo ""
echo "=== Current Clusters ==="
curl -k -s -H "Authorization: Bearer $TOKEN" "https://localhost/v3/clusters" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
for c in data:
    print(f\"  - {c['name']} (id={c['id']}, state={c.get('state','N/A')}, driver={c.get('driver','N/A')})\")
"

# Create cluster import
echo ""
echo "=== Creating Import Cluster ==="
IMPORT_CLUSTER=$(curl -k -s -X POST "https://localhost/v3/cluster" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "cluster",
    "name": "k8s-prod",
    "description": "Production K8S cluster on CentOS 7",
    "dockerRootDir": "/var/lib/docker",
    "enableClusterAlerting": false,
    "enableClusterMonitoring": false,
    "localClusterAuthEndpoint": {"enabled": false}
  }')

echo "Import cluster creation response:"
echo "$IMPORT_CLUSTER" | python3 -m json.tool 2>/dev/null || echo "$IMPORT_CLUSTER"

CLUSTER_ID=$(echo "$IMPORT_CLUSTER" | sed 's/.*"id":"\([^"]*\)".*/\1/')
echo "Cluster ID: $CLUSTER_ID"

# Generate cluster registration token
echo ""
echo "=== Generating Registration Token ==="
REG_TOKEN=$(curl -k -s -X POST "https://localhost/v3/clusterregistrationtoken" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"clusterRegistrationToken\",
    \"clusterId\": \"$CLUSTER_ID\"
  }")

echo "Registration token response:"
echo "$REG_TOKEN" | python3 -m json.tool 2>/dev/null || echo "$REG_TOKEN"

# Get the manifest URL (insecure command)
echo ""
echo "=== Getting Import Command ==="
MANIFEST_URL=$(echo "$REG_TOKEN" | sed 's/.*"insecureCommand":"\([^"]*\)".*/\1/')
echo "Manifest URL: $MANIFEST_URL"

# Download and save the manifest
echo ""
echo "=== Downloading Import Manifest ==="
curl -k -s -H "Authorization: Bearer $TOKEN" "$MANIFEST_URL" > /tmp/rancher-import.yaml

echo "Manifest saved to /tmp/rancher-import.yaml"
echo "First 50 lines:"
head -50 /tmp/rancher-import.yaml