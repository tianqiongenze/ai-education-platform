#!/bin/sh
# Retest T5/T6 with correct fingerprint substrings from the signature DB
B=http://127.0.0.1:8080/api/v1
echo "===== T5' create + scan with known fingerprints ====="
R=$(curl -s -m 15 -X POST $B/audits -H "Content-Type: application/json" -d '{"target":"hmi-panel-7","auditor":"zhang-wei"}')
SID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "  session_id=$SID"
R=$(curl -s -m 30 -X POST $B/audits/$SID/scan -H "Content-Type: application/json" \
  -d '{"fingerprints":["hmi-default-creds","modbus-plaintext","plc-stale-firmware","telnet-open","flat-network"]}')
echo "$R" | head -c 500; echo
N=$(echo "$R" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))' 2>/dev/null)
echo "  findings_count=$N"

echo "===== T6' findings persisted? GET /audits/{id} ====="
R=$(curl -s -m 15 $B/audits/$SID)
echo "$R" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("findings:",len(d["findings"]),"status:",d["status"])' 2>/dev/null

echo "===== CRDB verify (findings table via psql) ====="
psql -h 10.167.2.175 -p 26257 -U root -d security_audit -c "SELECT rule_id,severity,cvss FROM findings WHERE session_id='$SID' ORDER BY cvss DESC;" 2>&1 | head -12
psql -h 10.167.2.175 -p 26257 -U root -d security_audit -c "SELECT count(*) AS total_findings FROM findings;" 2>&1

echo "===== finalize + compliance with real findings ====="
R=$(curl -s -m 20 -X POST $B/audits/$SID/finalize)
echo "$R" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("status:",d["status"],"| risk_score:",d.get("risk_score","n/a"))' 2>/dev/null
R=$(curl -s -m 20 -X POST $B/audits/$SID/compliance -H "Content-Type: application/json" -d '{"security_level":2}')
echo "$R" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("compliance score:",d["score"],"| severity summary:",d["findings_by_severity"])' 2>/dev/null

echo "===== three-node consistency ====="
for P in 26257 26267; do
  echo -n "  10.167.2.175:$P sessions="
  psql -h 10.167.2.175 -p $P -U root -d security_audit -t -c "SELECT count(*) FROM audit_sessions;" 2>/dev/null | tr -d ' \n'
  echo " findings=$(psql -h 10.167.2.175 -p $P -U root -d security_audit -t -c 'SELECT count(*) FROM findings;' 2>/dev/null | tr -d ' ')"
done
echo -n "  10.167.2.176:26257 sessions="
psql -h 10.167.2.176 -p 26257 -U root -d security_audit -t -c "SELECT count(*) FROM audit_sessions;" 2>/dev/null | tr -d ' \n'
echo " findings=$(psql -h 10.167.2.176 -p 26257 -U root -d security_audit -t -c 'SELECT count(*) FROM findings;' 2>/dev/null | tr -d ' ')"
