#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
pkill -f "production-service" || true
sleep 2
export MES_DB_URL="jdbc:postgresql://10.167.2.175:26257/mes_system?sslmode=disable"
export MES_DB_USER="root"
export MES_DB_PASSWORD=""
export SPRING_FLYWAY_ENABLED="false"
export SPRING_JPA_DATABASE_PLATFORM="org.hibernate.dialect.PostgreSQLDialect"
export SPRING_JPA_HIBERNATE_DDL_AUTO="update"
export SPRING_DATASOURCE_HIKARI_CONNECTION_TIMEOUT="30000"
nohup java -jar production-service/target/production-service-1.0.0.jar > /tmp/prod.log 2>&1 &
echo "relaunched with PostgreSQLDialect"
sleep 45
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8081/actuator/health 2>/dev/null || echo 000)
echo "prod health: $code"
grep -E "Started Production|ERROR" /tmp/prod.log | head -3
