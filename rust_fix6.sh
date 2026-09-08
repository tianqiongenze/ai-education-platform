cd /home/jovyan/work/security-audit
python3 - <<'PY'
# cache_handle must exist on dyn AuditRepository: use a supertrait instead.
p = 'src/infrastructure/repository.rs'
src = open(p).read()
# remove the standalone trait appended earlier
old = '''
/// Optional cache introspection for the HTTP layer (default: no stats).
pub trait CacheStatsProvider {
    fn cache_handle(&self) -> std::sync::Arc<dyn Fn() -> String + Send + Sync> {
        std::sync::Arc::new(|| "{}".to_string())
    }
}
'''
assert old in src
src = src.replace(old, '')

# find the trait declaration and make CacheStatsProvider a supertrait with default
import re
m = re.search(r'pub trait AuditRepository([^}]*)\{', src)
assert m, 'AuditRepository trait not found'
decl_start = m.start()
decl_line_end = src.index('{', decl_start)
head = src[decl_start:decl_line_end]
if 'CacheStatsProvider' not in head:
    new_head = head.replace('pub trait AuditRepository', 'pub trait AuditRepository: CacheStatsProvider')
    src = src[:decl_start] + new_head + src[decl_line_end:]
# add the provider trait BEFORE AuditRepository
provider = '''
/// Optional cache introspection for the HTTP layer (default: no stats).
/// A supertrait of AuditRepository so `Box<dyn AuditRepository>` exposes it.
pub trait CacheStatsProvider {
    fn cache_handle(&self) -> std::sync::Arc<dyn Fn() -> String + Send + Sync> {
        std::sync::Arc::new(|| "{}".to_string())
    }
}
'''
anchor = 'pub trait AuditRepository'
idx = src.index(anchor)
src = src[:idx] + provider + '\n' + src[idx:]
open(p, 'w').write(src)
print('repository.rs: CacheStatsProvider is now supertrait of AuditRepository')

# server.rs: import only AuditRepository (supertrait comes along)
p = 'src/bin/server.rs'
src = open(p).read()
src = src.replace(
    'use security_audit::infrastructure::repository::{AuditRepository, CacheStatsProvider};',
    'use security_audit::infrastructure::repository::AuditRepository;')
open(p, 'w').write(src)
print('server.rs import fixed')

# http.rs: import the supertrait
p = 'src/infrastructure/http.rs'
src = open(p).read()
if 'use crate::infrastructure::repository::AuditRepository;' in src and 'CacheStatsProvider' not in src.split('pub struct AppState')[0]:
    src = src.replace(
        'use crate::infrastructure::repository::AuditRepository;',
        'use crate::infrastructure::repository::{AuditRepository, CacheStatsProvider};')
    open(p, 'w').write(src)
    print('http.rs import fixed')
else:
    print('http.rs import already ok or absent')
PY
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -6
tail -2 /tmp/rust_build.log
