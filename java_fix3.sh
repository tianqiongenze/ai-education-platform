#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
echo "=== does new jar embed jsr310? ==="
unzip -l production-service/target/production-service-1.0.0.jar | grep -c "jsr310" || echo 0
echo "=== check inside BOOT-INF/lib ==="
unzip -l production-service/target/production-service-1.0.0.jar | grep "jackson" | head -8
