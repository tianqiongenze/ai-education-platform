#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
pkill -f "production-service" || true
sleep 2
# Flyway bypass: explicit URL; ddl-auto update to create tables in CRDB
export MES_DB_URL="jdbc:postgresql://10.167.2.175:26257/mes_system?sslmode=disable"
export MES_DB_USER="root"
export MES_DB_PASSWORD=""
export FLYWAY_URL="jdbc:postgresql://10.167.2.175:26257/mes_system?sslmode=disable"
export SPRING_FLYWAY_ENABLED="true"
nohup java -jar production-service/target/production-service-1.0.0.jar > /tmp/prod.log 2>&1 &
echo relaunched
sleep 45
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8081/actuator/health 2>/dev/null || echo 000)
echo "prod health: $code"
grep -E "Started Production|APPLICATION FAILED|Error starting" /tmp/prod.log | head -3
