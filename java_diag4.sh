#!/bin/sh
echo "=== inv.log exception type ==="
grep -E "^[a-zA-Z].*Exception|Caused by" /tmp/inv.log 2>/dev/null | sort | uniq -c | sort -rn | head -8
echo "=== gateway routes for equipment ==="
grep -B2 -A8 "equipment" /home/jovyan/work/mes-system/gateway-service/src/main/resources/application.yml | head -30
echo "=== equipment controller mapping ==="
grep -rn "Mapping" /home/jovyan/work/mes-system/equipment-service/src/main/java --include="*.java" | grep -i "class\|GetMapping\|RequestMapping" | head -12
echo "=== production orders direct 8081 OK, gateway 500? replicate ==="
curl -s --max-time 5 "http://localhost:8080/api/v1/production/orders" -o /dev/null -w "%{http_code}\n"
curl -s --max-time 5 "http://localhost:8081/api/v1/production/orders" -o /dev/null -w "direct8081: %{http_code}\n"
