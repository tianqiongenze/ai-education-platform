cd /home/jovyan/work/security-audit
pkill -f audit-server 2>/dev/null; sleep 1
export AUDIT_CRDB_URL="postgresql://root@10.167.2.175:26257/security_audit?sslmode=disable"
nohup target/release/audit-server > /tmp/rust-server.log 2>&1 &
sleep 3
echo "=== process ==="
pgrep -fa audit-server || echo "NOT RUNNING"
echo "=== log ==="
cat /tmp/rust-server.log
echo "=== health ==="
curl -s -m 5 http://127.0.0.1:8080/health || echo "HEALTH_FAIL"
echo ""
