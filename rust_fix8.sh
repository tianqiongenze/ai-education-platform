cd /home/jovyan/work/security-audit
python3 - <<'PY'
# Blanket impl: every Send+Sync type gets the default no-op cache stats.
p = 'src/infrastructure/repository.rs'
src = open(p).read()
provider = '''
/// Optional cache introspection for the HTTP layer (default: no stats).
/// A supertrait of AuditRepository so `Box<dyn AuditRepository>` exposes it.
pub trait CacheStatsProvider {
    fn cache_handle(&self) -> std::sync::Arc<dyn Fn() -> String + Send + Sync> {
        std::sync::Arc::new(|| "{}".to_string())
    }
}
'''
if 'impl<T: Send + Sync> CacheStatsProvider for T' not in src:
    blanket = '''
/// Blanket impl: repositories without their own cache report empty stats.
impl<T: Send + Sync> CacheStatsProvider for T {}
'''
    # remove per-type default body duplicates if any
    anchor = 'pub trait CacheStatsProvider'
    idx = src.index(anchor)
    end = src.index('}', src.index('fn cache_handle', idx)) + 1
    src = src[:idx] + provider.strip() + '\n' + blanket + src[end:]
    open(p, 'w').write(src)
    print('repository.rs: blanket impl added, trait body simplified')
else:
    print('already patched')
PY
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -6
grep -B2 -A8 "^error\[" /tmp/rust_build.log | head -30
tail -2 /tmp/rust_build.log
