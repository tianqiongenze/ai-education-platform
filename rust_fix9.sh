cd /home/jovyan/work/security-audit
python3 - <<'PY'
p = 'src/infrastructure/repository.rs'
src = open(p).read()
# Remove the leftover garbage from the truncated replacement
old = '''/// Optional cache introspection for the HTTP layer (default: no stats).
/// A supertrait of AuditRepository so `Box<dyn AuditRepository>` exposes it.
/// Optional cache introspection for the HTTP layer (default: no stats).
/// A supertrait of AuditRepository so `Box<dyn AuditRepository>` exposes it.
pub trait CacheStatsProvider {
    fn cache_handle(&self) -> std::sync::Arc<dyn Fn() -> String + Send + Sync> {
        std::sync::Arc::new(|| "{}".to_string())
    }
}

/// Blanket impl: repositories without their own cache report empty stats.
impl<T: Send + Sync> CacheStatsProvider for T {}
".to_string())
    }
}

pub trait AuditRepository'''
new = '''/// Optional cache introspection for the HTTP layer (default: no stats).
/// A supertrait of AuditRepository so `Box<dyn AuditRepository>` exposes it.
pub trait CacheStatsProvider {
    fn cache_handle(&self) -> std::sync::Arc<dyn Fn() -> String + Send + Sync> {
        std::sync::Arc::new(|| "{}".to_string())
    }
}

/// Blanket impl: repositories without their own cache report empty stats.
impl<T: Send + Sync> CacheStatsProvider for T {}

pub trait AuditRepository'''
assert old in src, 'garbage block not found'
src = src.replace(old, new)
open(p, 'w').write(src)
print('repository.rs garbage cleaned')
PY
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -6
tail -2 /tmp/rust_build.log
