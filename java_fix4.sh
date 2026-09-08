#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
pkill -f "production-service" || true
sleep 2
export MES_DB_URL="jdbc:postgresql://10.167.2.175:26257/mes_system?sslmode=disable"
export MES_DB_USER="root"
export MES_DB_PASSWORD=""
export SPRING_FLYWAY_ENABLED="false"
nohup java -jar production-service/target/production-service-1.0.0.jar > /tmp/prod.log 2>&1 &
echo "production relaunched with flyway disabled"
sleep 40
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8081/actuator/health 2>/dev/null || echo 000)
echo "prod health: $code"
tail -5 /tmp/prod.log
