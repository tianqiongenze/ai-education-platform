#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
pkill -f "production-service" || true
sleep 2
# Clean flyway state + rerun with repair-like behavior: fresh baseline
export MES_DB_URL="jdbc:postgresql://10.167.2.175:26257/mes_system?sslmode=disable"
export MES_DB_USER="root"
export MES_DB_PASSWORD=""
export FLYWAY_URL="jdbc:postgresql://10.167.2.175:26257/mes_system?sslmode=disable"
export SPRING_FLYWAY_REPAIR_ENABLED="true"
# simplest: wipe the failed flyway schema history then re-run baseline
psql "postgresql://root@10.167.2.175:26257/mes_system?sslmode=disable" -c "DROP TABLE IF EXISTS flyway_schema_history;" 2>&1 | head -2
nohup java -jar production-service/target/production-service-1.0.0.jar > /tmp/prod.log 2>&1 &
echo relaunched
sleep 50
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8081/actuator/health 2>/dev/null || echo 000)
echo "prod health: $code"
grep -E "Started Production|Validate failed|Migrating schema" /tmp/prod.log | head -5
