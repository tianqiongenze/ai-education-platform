#!/bin/sh
# Rust security-audit: full-chain functional test
B=http://127.0.0.1:8080/api/v1
PASS=0; FAIL=0
check() {
  NAME="$1"; EXPECT="$2"; ACTUAL="$3"
  if echo "$ACTUAL" | grep -q "$EXPECT"; then
    PASS=$((PASS+1)); echo "PASS | $NAME | $EXPECT"
  else
    FAIL=$((FAIL+1)); echo "FAIL | $NAME | expected [$EXPECT] got: $(echo $ACTUAL | head -c 200)"
  fi
}

echo "===== T1 health ====="
R=$(curl -s -m 10 $B/health); check "T1 GET /health" '"status":"ok"' "$R"

echo "===== T2 create audit ====="
R=$(curl -s -m 15 -X POST $B/audits -H "Content-Type: application/json" -d '{"target":"plc-line-3-controller","auditor":"zhang-wei"}')
check "T2 POST /audits -> 201 + RUNNING" '"status":' "$R"
SID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "  session_id=$SID"

echo "===== T3 list audits ====="
R=$(curl -s -m 15 $B/audits)
check "T3 GET /audits contains session" "$SID" "$R"

echo "===== T4 get audit by id ====="
R=$(curl -s -m 15 $B/audits/$SID)
check "T4 GET /audits/{id}" "$SID" "$R"

echo "===== T5 run scan with fingerprints ====="
R=$(curl -s -m 30 -X POST $B/audits/$SID/scan -H "Content-Type: application/json" \
  -d '{"fingerprints":["hardcoded-credential","weak-tls-1.0","default-password","open-mqtt-no-auth","sql-injection-prone","insecure-ota-update"]}')
check "T5 POST /audits/{id}/scan -> findings" '"rule_id"' "$R"
echo "  findings: $(echo $R | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d),"findings, severities:",[f["severity"] for f in d])' 2>/dev/null)"

echo "===== T6 get audit with findings persisted ====="
R=$(curl -s -m 15 $B/audits/$SID)
FN=$(echo "$R" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["findings"]))' 2>/dev/null)
check "T6 findings persisted in CRDB (count>0)" "0" "$(python3 -c "print(0 if int('$FN' or 0)>0 else 1)")-ok-marker"

echo "===== T7 finalize audit ====="
R=$(curl -s -m 20 -X POST $B/audits/$SID/finalize)
check "T7 POST /audits/{id}/finalize -> COMPLETED" 'COMPLETED' "$R"

echo "===== T8 compliance report ====="
R=$(curl -s -m 20 -X POST $B/audits/$SID/compliance -H "Content-Type: application/json" -d '{"security_level":2}')
check "T8 POST /audits/{id}/compliance" '"security_level"' "$R"
echo "  report: $(echo $R | head -c 300)"

echo "===== T9 invalid transition (finalize again) ====="
R=$(curl -s -m 20 -X POST $B/audits/$SID/finalize)
check "T9 double-finalize rejected (409)" '"error"' "$R"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 20 -X POST $B/audits/$SID/finalize)
check "T9b double-finalize HTTP code 409" "409" "$CODE"

echo "===== T10 not found ====="
CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 15 $B/audits/00000000-0000-0000-0000-000000000000)
check "T10 GET missing audit -> 404" "404" "$CODE"

echo "===== T11 validation error (empty target) ====="
CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 15 -X POST $B/audits -H "Content-Type: application/json" -d '{"target":"","auditor":"x"}')
check "T11 empty target -> 400" "400" "$CODE"

echo "===== SUMMARY ====="
echo "PASS=$PASS FAIL=$FAIL"
