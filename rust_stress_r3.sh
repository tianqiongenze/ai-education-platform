#!/bin/sh
# Round 3 stress on cache-enabled build; capture cache stats before/after
cd /tmp
echo "=== stats BEFORE stress ==="
curl -s -m 5 http://127.0.0.1:8080/api/v1/cache/stats; echo
echo "=== running stress_rust.py (round 3, cache-enabled) ==="
python3 /tmp/stress_rust.py
echo "=== stats AFTER stress ==="
curl -s -m 5 http://127.0.0.1:8080/api/v1/cache/stats; echo
echo "=== redis key count (audit:cache:*) ==="
redis-cli -h redis.dify-plus.svc.cluster.local -a difyai123456 -n 5 --no-auth-warning KEYS 'audit:cache:*' | wc -l
