#!/bin/sh
echo "=== prod controller head (request mapping) ==="
sed -n '1,55p' /home/jovyan/work/mes-system/production-service/src/main/java/com/mes/production/controller/ProductionController.java | grep -E "RequestMapping|class|GetMapping|PostMapping"
echo "=== cache-common: redis config ==="
find /home/jovyan/work/mes-system/cache-common/src -name "*.java" | head -20
echo "=== prod.log InvalidDefinition context ==="
grep -B1 -A3 "InvalidDefinitionException" /tmp/prod.log | head -15
