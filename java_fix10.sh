#!/bin/sh
cd /home/jovyan/work/mes-system
echo "=== datasource router config class ==="
grep -rln "routing\|RoutingDataSource\|AbstractRoutingDataSource\|LazyConnectionDataSourceProxy" production-service/src/main/java | head -5
echo "=== show it ==="
find production-service/src/main/java -name "*.java" | xargs grep -ln "RoutingDataSource" | head -2 | while read f; do echo "--- $f"; cat "$f"; done | head -80
