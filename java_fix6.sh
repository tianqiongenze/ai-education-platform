#!/bin/sh
psql "postgresql://root@10.167.2.175:26257/defaultdb?sslmode=disable" -c "SHOW DATABASES;" 2>&1 | grep -i mes
echo "=== tables in mes_system (if exists) ==="
psql "postgresql://root@10.167.2.175:26257/mes_system?sslmode=disable" -c "SHOW TABLES;" 2>&1 | head -15
