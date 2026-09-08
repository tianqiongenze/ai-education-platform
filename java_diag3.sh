#!/bin/sh
echo "=== gateway api test (current PG datasource) ==="
curl -s --max-time 5 http://localhost:8080/api/v1/production/orders | head -c 300; echo
curl -s --max-time 5 http://localhost:8080/api/v1/equipment/list | head -c 300; echo
echo "=== equipment direct 8083 ==="
curl -s --max-time 5 http://localhost:8083/api/v1/equipment/list | head -c 200; echo
curl -s --max-time 5 http://localhost:8083/api/equipment 2>/dev/null | head -c 200; echo
echo "=== prod svc 8081 root probe ==="
curl -s --max-time 5 http://localhost:8081/api/v1/production/orders | head -c 300; echo
echo "=== inventory start error head ==="
grep -m2 -B2 "Error\|APPLICATION FAILED" /tmp/inv.log 2>/dev/null | head -20
