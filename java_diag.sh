#!/bin/sh
echo "=== JAVA PROCS ==="
ps aux | grep java | grep -v grep | head -8
echo "=== PORTS ==="
netstat -tln 2>/dev/null | grep -E '808[0-9]' || echo "no listening 808x"
echo "=== M2 jsr310 ==="
ls /home/jovyan/.m2/repository/com/fasterxml/jackson/datatype/jackson-datatype-jsr310/ 2>/dev/null || echo "no jsr310 in m2"
echo "=== PROD YML ==="
grep -A5 "datasource" /home/jovyan/work/mes-system/production-service/src/main/resources/application.yml | head -20
