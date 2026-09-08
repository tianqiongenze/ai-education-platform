#!/bin/sh
tail -40 /tmp/prod.log | grep -E "Caused by|Error|ERROR|Exception" | head -12
echo "=== CRDB connectivity from pod ==="
which psql
psql "postgresql://root@10.167.2.175:26257/mes_system?sslmode=disable" -c "SELECT 1;" 2>&1 | head -5
echo "=== crdb db list ==="
psql "postgresql://root@10.167.2.175:26257/defaultdb?sslmode=disable" -c "SHOW DATABASES;" 2>&1 | head -10
