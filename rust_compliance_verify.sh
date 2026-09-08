cd /home/jovyan/work/security-audit
B=http://127.0.0.1:8080/api/v1
echo "===== clean-target compliance (no findings -> expect high score) ====="
R=$(curl -s -m 15 -X POST $B/audits -H "Content-Type: application/json" -d '{"target":"clean-plc-8","auditor":"qa"}')
SID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "  clean session=$SID"
# finalize WITHOUT scanning -> zero findings
curl -s -m 20 -X POST $B/audits/$SID/finalize > /dev/null
R=$(curl -s -m 20 -X POST $B/audits/$SID/compliance -H "Content-Type: application/json" -d '{"security_level":2}')
echo "$R" | python3 -c '
import sys,json
d=json.load(sys.stdin)
print("  clean-target score:",d["score"])
print("  results:",[(r["requirement_id"],r["status"]) for r in d["results"]])
pass_count=sum(1 for r in d["results"] if r["status"]=="PASS")
print("  PASS count:",pass_count,"/",len(d["results"]))
'
echo "===== vulnerable-target compliance (5 findings -> expect low score) ====="
R=$(curl -s -m 15 -X POST $B/audits -H "Content-Type: application/json" -d '{"target":"hmi-panel-7","auditor":"qa"}')
SID2=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s -m 30 -X POST $B/audits/$SID2/scan -H "Content-Type: application/json" \
  -d '{"fingerprints":["hmi-default-creds","modbus-plaintext","plc-stale-firmware","telnet-open","flat-network"]}' > /dev/null
curl -s -m 20 -X POST $B/audits/$SID2/finalize > /dev/null
R=$(curl -s -m 20 -X POST $B/audits/$SID2/compliance -H "Content-Type: application/json" -d '{"security_level":2}')
echo "$R" | python3 -c '
import sys,json
d=json.load(sys.stdin)
print("  vulnerable-target score:",d["score"])
print("  gap_counts:",d.get("gap_counts"))
print("  severity_summary:",d["findings_by_severity"])
fail_count=sum(1 for r in d["results"] if r["status"]=="FAIL")
print("  FAIL count:",fail_count,"/",len(d["results"]))
'
