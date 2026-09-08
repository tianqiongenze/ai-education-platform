#!/bin/sh
# Cleanup v2: run psql INSIDE the rust pod (has psql client), clean stress rows
psql -h 10.167.2.175 -p 26257 -U root -d security_audit <<'SQL'
DELETE FROM findings WHERE session_id IN (SELECT id FROM audit_sessions WHERE auditor = 'stress');
DELETE FROM audit_sessions WHERE auditor = 'stress';
SQL
echo "=== 3-node consistency after cleanup ==="
for N in "10.167.2.175 26257" "10.167.2.175 26267" "10.167.2.176 26257"; do
  set -- $N
  echo -n "$1:$2 -> "
  S=$(psql -h $1 -p $2 -U root -d security_audit -t -c "SELECT count(*) FROM audit_sessions;" | tr -d ' \n')
  F=$(psql -h $1 -p $2 -U root -d security_audit -t -c "SELECT count(*) FROM findings;" | tr -d ' \n')
  echo "sessions=$S findings=$F"
done
