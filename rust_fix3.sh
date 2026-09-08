cd /home/jovyan/work/security-audit
echo "=== fix 1: save_finding persists to CRDB findings table ==="
python3 - <<'PY'
import re
p = 'src/infrastructure/crdb_repository.rs'
src = open(p).read()
old = '''    fn save_finding(&self, _sid: &str, _f: &Finding) -> Result<(), DomainError> { Ok(()) }'''
new = '''    fn save_finding(&self, sid: &str, f: &Finding) -> Result<(), DomainError> {
        let mut conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO findings (id,session_id,target,rule_id,title,severity,cvss,description,remediation,detected_at)
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
             ON CONFLICT (id) DO NOTHING",
            &[&f.id, &sid, &f.target, &f.rule_id, &f.title,
              &format!("{:?}", f.severity), &f.cvss, &f.description,
              &f.remediation, &Some(f.detected_at)])
            .map_err(|e| DomainError::Validation(format!("save finding: {e}")))?;
        Ok(())
    }'''
assert old in src, 'save_finding stub not found'
src = src.replace(old, new)
open(p, 'w').write(src)
print('save_finding patched')
PY

echo "=== fix 2: add get_audit service method + route ==="
python3 - <<'PY'
p = 'src/application/audit_service.rs'
src = open(p).read()
anchor = '''    pub fn list_audits(&self) -> Result<Vec<AuditSession>, DomainError> {
        self.repo.list_sessions()
    }'''
add = anchor + '''

    /// Fetch a single audit session by id.
    pub fn get_audit(&self, session_id: &str) -> Result<AuditSession, DomainError> {
        self.repo.get_session(session_id)
            .ok_or_else(|| DomainError::NotFound(format!("session {}", session_id)))
    }'''
assert anchor in src, 'list_audits anchor not found'
src = src.replace(anchor, add)
open(p, 'w').write(src)
print('get_audit added to service')

p = 'src/infrastructure/http.rs'
src = open(p).read()
old = '''            .route("/audits", web::get().to(list_audits))'''
new = '''            .route("/audits", web::get().to(list_audits))
            .route("/audits/{id}", web::get().to(get_audit))'''
assert old in src
src = src.replace(old, new)
anchor = '''async fn run_scan('''
add = '''async fn get_audit(state: web::Data<Arc<AppState>>, path: web::Path<String>) -> Result<HttpResponse, AuditError> {
    let service = state.service.clone();
    let id = path.into_inner();
    let session = web::block(move || service.get_audit(&id))
        .await.map_err(|e| AuditError(DomainError::Validation(format!("block: {e}"))))??;
    Ok(HttpResponse::Ok().json(session))
}

async fn run_scan('''
assert anchor in src
src = src.replace(anchor, add, 1)
open(p, 'w').write(src)
print('get_audit route+handler added')
PY

echo "=== rebuild ==="
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -8
tail -2 /tmp/rust_build.log
