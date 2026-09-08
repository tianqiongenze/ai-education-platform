cd /home/jovyan/work/security-audit
python3 - <<'PY'
# Blanket impl conflicts with the specific impl for LazyCrdbRepo.
# Solution: drop the blanket impl; give the default ONLY via the trait,
# and impl the trait explicitly for Sqlite + Crdb repos (no-op).
p = 'src/infrastructure/repository.rs'
src = open(p).read()
old = '''/// Blanket impl: repositories without their own cache report empty stats.
impl<T: Send + Sync> CacheStatsProvider for T {}
'''
assert old in src
src = src.replace(old, '')
open(p, 'w').write(src)
print('blanket impl removed')
PY
cat >> src/infrastructure/repository.rs <<'RUST'

impl CacheStatsProvider for SqliteAuditRepository {}
RUST
cat >> src/infrastructure/crdb_repository.rs <<'RUST'

impl super::repository::CacheStatsProvider for CrdbAuditRepository {}
RUST
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -6
tail -2 /tmp/rust_build.log
