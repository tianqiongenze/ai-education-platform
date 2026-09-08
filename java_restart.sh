#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
echo "=== stopping old services ==="
pkill -f "production-service" || true
pkill -f "quality-service" || true
pkill -f "equipment-service" || true
pkill -f "gateway-service" || true
sleep 3
echo "=== CRDB switch: MES_DB_URL env override to CRDB 26257 ==="
export MES_DB_URL="jdbc:postgresql://10.167.2.175:26257/mes_system?sslmode=disable"
export MES_DB_USER="root"
export MES_DB_PASSWORD=""
export REDIS_HOST="redis.dify-plus.svc.cluster.local"
nohup java -jar production-service/target/production-service-1.0.0.jar > /tmp/prod.log 2>&1 &
sleep 2
nohup java -jar quality-service/target/quality-service-1.0.0.jar > /tmp/quality.log 2>&1 &
sleep 2
nohup java -jar equipment-service/target/equipment-service-1.0.0.jar > /tmp/equip.log 2>&1 &
sleep 2
nohup java -jar inventory-service/target/inventory-service-1.0.0.jar > /tmp/inv.log 2>&1 &
sleep 2
nohup java -jar gateway-service/target/gateway-service-1.0.0.jar > /tmp/gateway.log 2>&1 &
echo "=== launched; wait for boot ==="
sleep 30
for p in 8081 8082 8083 8084 8080; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:$p/actuator/health)
  echo "port $p -> $code"
done
