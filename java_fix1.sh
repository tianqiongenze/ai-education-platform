#!/bin/sh
set -e
cd /home/jovyan/work/mes-system
echo "=== rebuilding cache-common ==="
mvn -q -pl cache-common install -DskipTests -o 2>&1 | tail -3 || mvn -q -pl cache-common install -DskipTests 2>&1 | tail -5
echo "=== check spring.factories/auto-configuration imports ==="
find cache-common/src -name "spring.factories" -o -name "*.imports" | head -3
cat cache-common/src/main/resources/META-INF/spring/*.imports 2>/dev/null || cat cache-common/src/main/resources/META-INF/spring.factories 2>/dev/null || echo "NO AUTOCONFIG REGISTRATION FILE"
