#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
echo "=== production jar exists? ==="
ls -la production-service/target/*.jar 2>/dev/null || echo "NO JAR - need rebuild"
echo "=== check prod pom for cache-common dependency and jsr310 ==="
grep -A2 "cache-common\|jsr310\|jdk8" production-service/pom.xml | head -20
echo "=== check running prod uses old jar (mtime) ==="
stat -c "%y %n" production-service/target/production-service-1.0.0.jar 2>/dev/null || true
ps aux | grep "production-service" | grep -v grep | awk '{print $9}'
