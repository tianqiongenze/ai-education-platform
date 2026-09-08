#!/bin/sh
cd /home/jovyan/work/security-audit && export CARGO_HOME=/home/jovyan/.cargo
cargo test 2>&1 | grep -E 'test result' > /tmp/all_tests.txt
cat /tmp/all_tests.txt
python3 - <<'PY'
import re
p=f=0
for line in open('/tmp/all_tests.txt'):
    m=re.search(r'(\d+) passed; (\d+) failed', line)
    if m: p+=int(m.group(1)); f+=int(m.group(2))
print(f"TOTAL: {p} passed, {f} failed")
PY
