#!/bin/sh
echo "=== ports via ss ==="
ss -tlnp 2>/dev/null | grep -E ':(808[0-9]|8081)' || echo "no ss result"
echo "=== curl direct services ==="
for p in 8081 8082 8083 8084 8080; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:$p/actuator/health 2>/dev/null)
  echo "port $p /actuator/health -> $code"
done
echo "=== inventory log tail ==="
tail -5 /tmp/inv.log 2>/dev/null || echo "no /tmp/inv.log"
echo "=== crdb driver in m2 ==="
ls /home/jovyan/.m2/repository/org/postgresql/postgresql/ 2>/dev/null | head -3
