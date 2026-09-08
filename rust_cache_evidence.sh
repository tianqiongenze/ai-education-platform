#!/bin/sh
# Cache evidence: repeat reads to demonstrate L1/L2 hits and L2 fallback
B=http://127.0.0.1:8080/api/v1
echo "=== baseline stats ==="
curl -s -m 5 $B/cache/stats; echo
SID=$(curl -s -m 15 $B/audits | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["id"])')
echo "=== 5 repeated GET /audits/{id} on session $SID ==="
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "%{http_code} " -m 10 $B/audits/$SID
done
echo ""
echo "=== 3 repeated GET /audits (list) ==="
for i in 1 2 3; do
  curl -s -o /dev/null -w "%{http_code} " -m 10 $B/audits
done
echo ""
echo "=== stats after cached reads ==="
curl -s -m 5 $B/cache/stats; echo
echo "=== simulate L1 expiry proof: L2 hits counter increments when L1 (30s) misses ==="
echo "(L1 TTL=30s; wait would be needed for live demo — L2 hits shown in stress phase)"
