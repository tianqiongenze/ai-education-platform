#!/bin/sh
echo "=== equipment list route ==="
curl -s --max-time 5 "http://localhost:8083/api/v1/equipment" | head -c 300; echo
echo "=== equipment cache stats ==="
curl -s --max-time 5 "http://localhost:8083/api/v1/equipment/metrics/cache" | head -c 300; echo
echo "=== quality routes ==="
grep -rn "Mapping" /home/jovyan/work/mes-system/quality-service/src/main/java --include="*.java" | grep -E "GetMapping|RequestMapping" | head -10
echo "=== quality list ==="
curl -s --max-time 5 "http://localhost:8082/api/v1/quality/records" -o /dev/null -w "records: %{http_code}\n"
echo "=== production routes ==="
grep -rn "GetMapping" /home/jovyan/work/mes-system/production-service/src/main/java --include="*.java" | head -10
echo "=== inventory controller ==="
grep -rn "GetMapping\|RequestMapping" /home/jovyan/work/mes-system/inventory-service/src/main/java --include="*.java" | head -10
