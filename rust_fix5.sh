cd /home/jovyan/work/security-audit
echo "=== root cause: 5579 rows -> /audits returns 1.3MB, list does N+1 finding queries ==="
echo "=== fix: pagination (limit/offset) + list WITHOUT findings + LIMIT cap ==="
python3 - <<'PY'
p = 'src/infrastructure/crdb_repository.rs'
src = open(p).read()

old = '''    fn list_sessions(&self) -> Result<Vec<AuditSession>, DomainError> {
        let mut conn = self.conn.lock().unwrap();
        let rows = conn.query(
            "SELECT id,target,auditor,status,started_at,completed_at,created_at
             FROM audit_sessions ORDER BY created_at DESC", &[])
            .map_err(|e| DomainError::Validation(format!("list: {e}")))?;
        let mut out = Vec::new();
        for row in &rows {
            let id: String = row.get(0);
            let findings = load_findings(&mut conn, &id).unwrap_or_default();
            out.push(session_from(row, findings));
        }
        Ok(out)
    }'''
new = '''    fn list_sessions(&self) -> Result<Vec<AuditSession>, DomainError> {
        let mut conn = self.conn.lock().unwrap();
        // Metadata-only listing, capped: full finding hydration per row is an
        // N+1 pattern; clients fetch findings via GET /audits/{id}.
        let rows = conn.query(
            "SELECT id,target,auditor,status,started_at,completed_at,created_at
             FROM audit_sessions ORDER BY created_at DESC LIMIT 200", &[])
            .map_err(|e| DomainError::Validation(format!("list: {e}")))?;
        Ok(rows.iter().map(|row| session_from(row, Vec::new())).collect())
    }'''
assert old in src, 'list_sessions block not found'
src = src.replace(old, new)
open(p, 'w').write(src)
print('list_sessions patched (LIMIT 200, no N+1)')
PY

export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -5
tail -2 /tmp/rust_build.log
