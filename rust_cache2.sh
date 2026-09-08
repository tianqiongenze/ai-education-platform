cd /home/jovyan/work/security-audit
echo "=== 3. cached repository wrapper + stats endpoint + audit_service cache hooks ==="
python3 - <<'PY'
# 3a. wrap CrdbAuditRepository with TwoLevelCache in server bin
p = 'src/bin/server.rs'
src = '''//! audit-server: Actix-Web REST API backed by CockroachDB (security_audit DB)
//! with a two-level cache (L1 in-process 30s + L2 Redis 300s).
use security_audit::infrastructure::http::run_server;
use security_audit::domain::error::DomainError;
use security_audit::infrastructure::repository::AuditRepository;
use security_audit::domain::audit::{AuditSession, Finding};
use std::sync::{Arc, Mutex};

/// Lazily-initializing wrapper so the blocking CRDB connection is opened
/// outside the actix runtime on first request (web::block handles offload).
pub struct LazyCrdbRepo {
    inner: Mutex<Option<Arc<security_audit::infrastructure::crdb_repository::CrdbAuditRepository>>>,
    cache: Arc<security_audit::infrastructure::cache::TwoLevelCache>,
}

impl LazyCrdbRepo {
    pub fn new() -> Self {
        Self { inner: Mutex::new(None),
               cache: Arc::new(security_audit::infrastructure::cache::TwoLevelCache::new()) }
    }
    fn repo(&self) -> Result<Arc<security_audit::infrastructure::crdb_repository::CrdbAuditRepository>, DomainError> {
        let mut guard = self.inner.lock().unwrap();
        if guard.is_none() {
            *guard = Some(Arc::new(security_audit::infrastructure::crdb_repository::CrdbAuditRepository::open()?));
        }
        Ok(guard.as_ref().unwrap().clone())
    }
    pub fn cache(&self) -> Arc<security_audit::infrastructure::cache::TwoLevelCache> { self.cache.clone() }
}

impl AuditRepository for LazyCrdbRepo {
    fn save_session(&self, s: &AuditSession) -> Result<(), DomainError> {
        let r = self.repo()?.save_session(s);
        // write-through: refresh the per-session and list caches
        if r.is_ok() {
            if let Ok(json) = serde_json::to_string(s) {
                self.cache.put(&format!("session:{}", s.id), &json);
            }
            self.cache.invalidate("list:all");
        }
        r
    }
    fn get_session(&self, id: &str) -> Option<AuditSession> {
        // L1/L2
        if let Some(json) = self.cache.get(&format!("session:{id}")) {
            if let Ok(s) = serde_json::from_str::<AuditSession>(&json) {
                if s.id == id { return Some(s); }
            }
        }
        // CRDB + fill cache
        let s = self.repo().ok()?.get_session(id)?;
        if let Ok(json) = serde_json::to_string(&s) {
            self.cache.put(&format!("session:{id}"), &json);
        }
        Some(s)
    }
    fn list_sessions(&self) -> Result<Vec<AuditSession>, DomainError> {
        if let Some(json) = self.cache.get("list:all") {
            if let Ok(v) = serde_json::from_str::<Vec<AuditSession>>(&json) {
                return Ok(v);
            }
        }
        let v = self.repo()?.list_sessions()?;
        if let Ok(json) = serde_json::to_string(&v) {
            self.cache.put("list:all", &json);
        }
        Ok(v)
    }
    fn save_finding(&self, sid: &str, f: &Finding) -> Result<(), DomainError> {
        let r = self.repo()?.save_finding(sid, f);
        if r.is_ok() {
            self.cache.invalidate(&format!("session:{sid}"));
            self.cache.invalidate("list:all");
        }
        r
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    let repo = Box::new(LazyCrdbRepo::new());
    log::info!("starting security-audit server on :8080 (CRDB + L1/L2 cache backend)");
    run_server(repo, "0.0.0.0:8080").await
}
'''
open(p, 'w').write(src)
print('server.rs: cache-wrapped repository')

# 3b. expose cache stats: AppState gains cache handle; /api/v1/cache/stats route
p = 'src/infrastructure/http.rs'
src = open(p).read()
old = '''pub struct AppState {
    pub service: Arc<AuditService>,
}'''
new = '''pub struct AppState {
    pub service: Arc<AuditService>,
    #[allow(dead_code)]
    pub cache_stats: std::sync::Arc<dyn Fn() -> String + Send + Sync>,
}'''
assert old in src; src = src.replace(old, new)

old = '''            .route("/health", web::get().to(health)),'''
new = '''            .route("/health", web::get().to(health))
            .route("/cache/stats", web::get().to(cache_stats)),'''
assert old in src; src = src.replace(old, new)

old = '''async fn health() -> HttpResponse {'''
new = '''async fn cache_stats(state: web::Data<Arc<AppState>>) -> HttpResponse {
    HttpResponse::Ok().body((state.cache_stats)())
}

async fn health() -> HttpResponse {'''
assert old in src; src = src.replace(old, new, 1)

old = '''    let state = Arc::new(AppState { service: Arc::new(AuditService::new(repo)) });'''
new = '''    let cache = repo.cache_handle();
    let state = Arc::new(AppState {
        service: Arc::new(AuditService::new(repo)),
        cache_stats: cache,
    });'''
assert old in src; src = src.replace(old, new)
open(p, 'w').write(src)
print('http.rs: /api/v1/cache/stats added')

# 3c. trait gains cache_handle default (no-op) so AuditService stays unchanged
p = 'src/infrastructure/repository.rs'
src = open(p).read()
if 'cache_handle' not in src:
    src += '''
/// Optional cache introspection for the HTTP layer (default: no stats).
pub trait CacheStatsProvider {
    fn cache_handle(&self) -> std::sync::Arc<dyn Fn() -> String + Send + Sync> {
        std::sync::Arc::new(|| "{}".to_string())
    }
}
'''
    open(p, 'w').write(src)
    print('repository.rs: CacheStatsProvider trait appended')
PY
echo "=== 3d. impl CacheStatsProvider for LazyCrdbRepo ==="
python3 - <<'PY'
p = 'src/bin/server.rs'
src = open(p).read()
if 'CacheStatsProvider' not in src:
    src = src.replace(
        'use security_audit::infrastructure::repository::AuditRepository;',
        'use security_audit::infrastructure::repository::{AuditRepository, CacheStatsProvider};')
    src += '''
impl CacheStatsProvider for LazyCrdbRepo {
    fn cache_handle(&self) -> std::sync::Arc<dyn Fn() -> String + Send + Sync> {
        let cache = self.cache.clone();
        std::sync::Arc::new(move || cache.stats())
    }
}
'''
    open(p, 'w').write(src)
    print('LazyCrdbRepo: CacheStatsProvider impl added')
PY
touch /tmp/rust_cache_step2_done
