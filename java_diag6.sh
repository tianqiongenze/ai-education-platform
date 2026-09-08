#!/bin/sh
echo "=== quality inspections body ==="
curl -s --max-time 5 "http://localhost:8082/api/v1/quality/inspections" | head -c 200; echo
echo "=== production cache metrics ==="
curl -s --max-time 5 "http://localhost:8081/api/v1/production/metrics/cache" | head -c 300; echo
echo "=== equipment 500 body ==="
curl -s --max-time 5 "http://localhost:8083/api/v1/equipment" | head -c 200; echo
echo "=== equipment log tail ==="
ls /tmp/*.log; tail -30 /tmp/equip.log 2>/dev/null | grep -E "Exception|Caused|at com.mes" | head -10
