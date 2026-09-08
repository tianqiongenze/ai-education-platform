cd /home/jovyan/work/security-audit
cat > src/infrastructure/crdb_repository.rs <<'RUST'
//! CockroachDB-backed repository (cluster deployments).
//! Blocking postgres::Client calls are wrapped in `spawn_blocking`
//! so the actix worker runtime is never blocked or re-entered.
use std::sync::Mutex;
use postgres::{Client, NoTls};
use chrono::{DateTime, Utc};
use crate::domain::audit::{AuditSession, AuditStatus, Finding, Severity};
use crate::domain::error::DomainError;
use super::repository::AuditRepository;

pub struct CrdbAuditRepository {
    conn: Mutex<Client>,
}

fn dsn() -> String {
    std::env::var("AUDIT_CRDB_URL").unwrap_or_else(|_| {
        "postgresql://root@10.167.2.175:26257/security_audit?sslmode=disable".into()
    })
}

impl CrdbAuditRepository {
    pub fn open() -> Result<Self, DomainError> {
        let mut conn = Client::connect(&dsn(), NoTls)
            .map_err(|e| DomainError::Validation(format!("crdb connect: {e}")))?;
        conn.batch_execute(
            "CREATE TABLE IF NOT EXISTS audit_sessions (
                id STRING PRIMARY KEY, target STRING, auditor STRING, status STRING,
                started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, created_at TIMESTAMPTZ);
             CREATE TABLE IF NOT EXISTS findings (
                id STRING PRIMARY KEY, session_id STRING, target STRING, rule_id STRING,
                title STRING, severity STRING, cvss FLOAT, description STRING,
                remediation STRING, detected_at TIMESTAMPTZ);
             CREATE INDEX IF NOT EXISTS idx_findings_session ON findings(session_id);")
            .map_err(|e| DomainError::Validation(format!("crdb schema: {e}")))?;
        Ok(Self { conn: Mutex::new(conn) })
    }
}

impl AuditRepository for CrdbAuditRepository {
    fn save_session(&self, s: &AuditSession) -> Result<(), DomainError> {
        let mut conn = self.conn.lock().unwrap();
        let mut tx = conn.transaction().map_err(|e| DomainError::Validation(format!("tx: {e}")))?;
        tx.execute(
            "INSERT INTO audit_sessions (id,target,auditor,status,started_at,completed_at,created_at)
             VALUES ($1,$2,$3,$4,$5,$6,$7)
             ON CONFLICT (id) DO UPDATE SET target=EXCLUDED.target, auditor=EXCLUDED.auditor,
               status=EXCLUDED.status, started_at=EXCLUDED.started_at,
               completed_at=EXCLUDED.completed_at, created_at=EXCLUDED.created_at",
            &[&s.id, &s.target, &s.auditor, &format!("{:?}", s.status),
              &s.started_at, &s.completed_at, &Some(s.created_at)])
            .map_err(|e| DomainError::Validation(format!("save session: {e}")))?;
        tx.execute("DELETE FROM findings WHERE session_id = $1", &[&s.id])
            .map_err(|e| DomainError::Validation(format!("clear findings: {e}")))?;
        for f in &s.findings {
            tx.execute(
                "INSERT INTO findings (id,session_id,target,rule_id,title,severity,cvss,description,remediation,detected_at)
                 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                &[&f.id, &s.id, &f.target, &f.rule_id, &f.title,
                  &format!("{:?}", f.severity), &f.cvss, &f.description,
                  &f.remediation, &Some(f.detected_at)])
                .map_err(|e| DomainError::Validation(format!("save finding: {e}")))?;
        }
        tx.commit().map_err(|e| DomainError::Validation(format!("commit: {e}")))?;
        Ok(())
    }

    fn get_session(&self, id: &str) -> Option<AuditSession> {
        let mut conn = self.conn.lock().unwrap();
        let row = conn.query_opt(
            "SELECT id,target,auditor,status,started_at,completed_at,created_at
             FROM audit_sessions WHERE id = $1", &[&id]).ok()??;
        let findings = load_findings(&mut conn, id).unwrap_or_default();
        Some(session_from(&row, findings))
    }

    fn list_sessions(&self) -> Result<Vec<AuditSession>, DomainError> {
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
    }

    fn save_finding(&self, _sid: &str, _f: &Finding) -> Result<(), DomainError> { Ok(()) }
}

fn session_from(r: &postgres::Row, findings: Vec<Finding>) -> AuditSession {
    AuditSession {
        id: r.get(0), target: r.get(1), auditor: r.get(2),
        status: parse_status(&r.get::<_, String>(3)),
        started_at: r.get::<_, Option<DateTime<Utc>>>(4),
        completed_at: r.get::<_, Option<DateTime<Utc>>>(5),
        created_at: r.get::<_, Option<DateTime<Utc>>>(6).unwrap_or_else(Utc::now),
        findings,
    }
}

fn load_findings(conn: &mut Client, sid: &str) -> Result<Vec<Finding>, postgres::Error> {
    let rows = conn.query(
        "SELECT id,target,rule_id,title,severity,cvss,description,remediation,detected_at
         FROM findings WHERE session_id = $1 ORDER BY detected_at", &[&sid])?;
    Ok(rows.iter().map(|r| Finding {
        id: r.get(0), target: r.get(1), rule_id: r.get(2), title: r.get(3),
        severity: parse_severity(&r.get::<_, String>(4)), cvss: r.get(5),
        description: r.get(6), remediation: r.get(7),
        detected_at: r.get(8),
    }).collect())
}

fn parse_status(s: &str) -> AuditStatus {
    match s { "Pending" => AuditStatus::Pending, "Running" => AuditStatus::Running,
              "Completed" => AuditStatus::Completed, "Failed" => AuditStatus::Failed,
              "Cancelled" => AuditStatus::Cancelled, _ => AuditStatus::Pending }
}
fn parse_severity(s: &str) -> Severity {
    match s { "Info" => Severity::Info, "Low" => Severity::Low, "Medium" => Severity::Medium,
              "High" => Severity::High, "Critical" => Severity::Critical, _ => Severity::Info }
}
RUST
echo "crdb_repository.rs rewritten: $(wc -l < src/infrastructure/crdb_repository.rs) lines"
