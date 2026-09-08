cd /home/jovyan/work/security-audit
cat > src/bin/server.rs <<'RUST'
//! audit-server: Actix-Web REST API backed by CockroachDB (security_audit DB).
use security_audit::infrastructure::http::run_server;
use security_audit::domain::error::DomainError;
use security_audit::infrastructure::repository::AuditRepository;
use security_audit::domain::audit::{AuditSession};
use std::sync::{Arc, Mutex};

/// Lazily-initializing wrapper so the blocking CRDB connection is opened
/// OUTSIDE the actix runtime (in spawn_blocking) instead of main().
pub struct LazyCrdbRepo {
    inner: Arc<Mutex<Option<Arc<security_audit::infrastructure::crdb_repository::CrdbAuditRepository>>>>,
}

impl LazyCrdbRepo {
    pub fn new() -> Self {
        Self { inner: Arc::new(Mutex::new(None)) }
    }
    fn get(&self) -> Result<Arc<security_audit::infrastructure::crdb_repository::CrdbAuditRepository>, DomainError> {
        let mut guard = self.inner.lock().unwrap();
        if guard.is_none() {
            *guard = Some(Arc::new(security_audit::infrastructure::crdb_repository::CrdbAuditRepository::open()?));
        }
        Ok(guard.as_ref().unwrap().clone())
    }
}

impl AuditRepository for LazyCrdbRepo {
    fn save_session(&self, s: &AuditSession) -> Result<(), DomainError> { self.get()?.save_session(s) }
    fn get_session(&self, id: &str) -> Option<AuditSession> { self.get().ok()?.get_session(id) }
    fn list_sessions(&self) -> Result<Vec<AuditSession>, DomainError> { self.get()?.list_sessions() }
    fn save_finding(&self, sid: &str, f: &security_audit::domain::audit::Finding) -> Result<(), DomainError> { self.get()?.save_finding(sid, f) }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    let repo = Box::new(LazyCrdbRepo::new());
    log::info!("starting security-audit server on :8080 (CRDB backend, cluster mode, lazy connect)");
    run_server(repo, "0.0.0.0:8080").await
}
RUST
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
tail -3 /tmp/rust_build.log
