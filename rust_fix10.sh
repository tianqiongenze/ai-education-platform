cd /home/jovyan/work/security-audit
python3 - <<'PY'
p = 'src/bin/server.rs'
src = open(p).read()
old = 'use security_audit::infrastructure::repository::AuditRepository;'
new = 'use security_audit::infrastructure::repository::{AuditRepository, CacheStatsProvider};'
if old in src and 'repository::{AuditRepository, CacheStatsProvider}' not in src:
    src = src.replace(old, new)
    open(p, 'w').write(src)
    print('server.rs import updated')
else:
    print('import already correct')
PY
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -6
tail -2 /tmp/rust_build.log
