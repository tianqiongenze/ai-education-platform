#!/bin/sh
echo "=== prod cache metrics probe ==="
curl -s --max-time 5 "http://localhost:8081/api/v1/production/metrics/cache" | head -c 200; echo
grep -rn "metrics/cache" /home/jovyan/work/mes-system/production-service/src/main/java --include="*.java" | head -3
echo "=== quality inspections method ==="
sed -n '20,35p' /home/jovyan/work/mes-system/quality-service/src/main/java/com/mes/quality/controller/QualityController.java
echo "=== prod 500 in equip? check equip.log for LocalDateTime ==="
grep -c "LocalDateTime" /tmp/equip.log 2>/dev/null
grep -c "InvalidDefinitionException" /tmp/equip.log /tmp/prod.log /tmp/quality.log /tmp/gateway.log 2>/dev/null
