#!/bin/sh
# Clean stress-generated rows from CRDB (auditor='stress') + flush cache keys
cat > /tmp/cleanup.sql <<'EOF'
DELETE FROM findings WHERE session_id IN (SELECT id FROM audit_sessions WHERE auditor = 'stress');
DELETE FROM audit_sessions WHERE auditor = 'stress';
EOF
echo "=== before cleanup (master write node) ==="
psql "postgresql://root@10.167.2.175:26257/security_audit?sslmode=disable" -t -c "SELECT count(*) FROM audit_sessions; SELECT count(*) FROM findings;"
psql "postgresql://root@10.167.2.175:26257/security_audit?sslmode=disable" -f /tmp/cleanup.sql
echo "=== after cleanup, 3-node consistency ==="
for N in 10.167.2.175:26257 10.167.2.175:26267 10.167.2.176:26257; do
  echo -n "$N: "
  psql "postgresql://root@$N/security_audit?sslmode=disable" -t -c "SELECT count(*) || ' sessions / ' || (SELECT count(*) FROM findings) || ' findings' FROM audit_sessions;"
done
echo "=== flush Redis cache keys ==="
redis-cli -h redis.dify-plus.svc.cluster.local -a difyai123456 -n 5 --no-auth-warning EVAL "local k = redis.call('keys','audit:cache:*') for i,v in ipairs(k) do redis.call('del',v) end return #k" 0
