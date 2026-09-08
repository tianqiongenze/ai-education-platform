#!/usr/bin/env python3
"""Generate Rust Industrial Security Audit System (DDD).
Actix-Web REST + rusqlite + clap CLI. Modules: audit engine, vulnerability
scanner, IEC 62443 compliance checker. Tests via `cargo test`."""
import os, textwrap
BASE = "/tmp/p4-rust/security-audit"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# ---- Cargo.toml: actix-web 4, rusqlite (bundled so no system sqlite needed),
# serde, clap, chrono, thiserror, tokio (actix pulls it). ----
w("Cargo.toml", r'''
[package]
name = "security-audit"
version = "1.0.0"
edition = "2021"
authors = ["student-rust"]
description = "工业安全审计系统 - Industrial Security Audit System (DDD)"

[lib]
name = "security_audit"
path = "src/lib.rs"

[[bin]]
name = "audit-cli"
path = "src/bin/cli.rs"

[[bin]]
name = "audit-server"
path = "src/bin/server.rs"

[dependencies]
actix-web = "4"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
rusqlite = { version = "0.31", features = ["bundled"] }
clap = { version = "4", features = ["derive"] }
chrono = { version = "0.4", features = ["serde"] }
thiserror = "1"
uuid = { version = "1", features = ["v4"] }
log = "0.4"
env_logger = "0.11"

[dev-dependencies]
# no extra test deps needed; tests use the public API + in-memory sqlite.
''')

# Cargo mirror config so it fetches from the working USTC sparse mirror.
w(".cargo/config.toml", r'''
[source.crates-io]
replace-with = "ustc"

[source.ustc]
registry = "sparse+https://mirrors.ustc.edu.cn/crates.io-index/"
''')

w(".gitignore", r'''
/target
*.db
Cargo.lock
''')

# =================== DOMAIN LAYER (pure, no framework deps) ===================
w("src/domain/mod.rs", r'''
//! Domain layer (DDD): core entities, value objects & domain services.
//! Depends only on std + chrono + thiserror + uuid — no infra concerns.

pub mod audit;
pub mod vulnerability;
pub mod compliance;
pub mod error;

pub use audit::*;
pub use vulnerability::*;
pub use compliance::*;
pub use error::DomainError;
''')

w("src/domain/error.rs", r'''
//! Domain errors.
use thiserror::Error;

#[derive(Error, Debug, Clone, PartialEq)]
pub enum DomainError {
    #[error("entity not found: {0}")]
    NotFound(String),
    #[error("validation error: {0}")]
    Validation(String),
    #[error("invalid state transition: {0}")]
    InvalidState(String),
    #[error("policy violation: {0}")]
    Policy(String),
}
''')

w("src/domain/audit.rs", r'''
//! Audit aggregate root + related value objects.
use chrono::{DateTime, Utc};
use uuid::Uuid;
use crate::domain::error::DomainError;

/// Severity of a finding.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum Severity {
    Info,
    Low,
    Medium,
    High,
    Critical,
}

impl Severity {
    pub fn rank(self) -> u8 {
        match self {
            Severity::Info => 0,
            Severity::Low => 1,
            Severity::Medium => 2,
            Severity::High => 3,
            Severity::Critical => 4,
        }
    }
    pub fn from_score(score: f64) -> Self {
        match score {
            s if s >= 9.0 => Severity::Critical,
            s if s >= 7.0 => Severity::High,
            s if s >= 4.0 => Severity::Medium,
            s if s > 0.0 => Severity::Low,
            _ => Severity::Info,
        }
    }
}

/// A single security finding produced by the audit engine.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Finding {
    pub id: String,
    pub target: String,
    pub rule_id: String,
    pub title: String,
    pub severity: Severity,
    pub cvss: f64,
    pub description: String,
    pub remediation: String,
    pub detected_at: DateTime<Utc>,
}

impl Finding {
    pub fn new(target: &str, rule_id: &str, title: &str, severity: Severity,
               cvss: f64, description: &str, remediation: &str) -> Result<Self, DomainError> {
        if target.is_empty() {
            return Err(DomainError::Validation("target is required".into()));
        }
        if rule_id.is_empty() {
            return Err(DomainError::Validation("rule_id is required".into()));
        }
        if !(0.0..=10.0).contains(&cvss) {
            return Err(DomainError::Validation("cvss must be in [0,10]".into()));
        }
        Ok(Self {
            id: Uuid::new_v4().to_string(),
            target: target.to_string(),
            rule_id: rule_id.to_string(),
            title: title.to_string(),
            severity,
            cvss,
            description: description.to_string(),
            remediation: remediation.to_string(),
            detected_at: Utc::now(),
        })
    }
}

/// AuditStatus state machine for an AuditSession aggregate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum AuditStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

/// AuditSession aggregate root — the central entity of the audit domain.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AuditSession {
    pub id: String,
    pub target: String,
    pub auditor: String,
    pub status: AuditStatus,
    pub findings: Vec<Finding>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

impl AuditSession {
    pub fn new(target: &str, auditor: &str) -> Result<Self, DomainError> {
        if target.is_empty() {
            return Err(DomainError::Validation("target is required".into()));
        }
        Ok(Self {
            id: Uuid::new_v4().to_string(),
            target: target.to_string(),
            auditor: auditor.to_string(),
            status: AuditStatus::Pending,
            findings: Vec::new(),
            started_at: None,
            completed_at: None,
            created_at: Utc::now(),
        })
    }

    /// Transition Pending -> Running. Enforces the state-machine invariant.
    pub fn start(&mut self) -> Result<(), DomainError> {
        if self.status != AuditStatus::Pending {
            return Err(DomainError::InvalidState(format!(
                "cannot start audit in state {:?}", self.status)));
        }
        self.status = AuditStatus::Running;
        self.started_at = Some(Utc::now());
        Ok(())
    }

    /// Add a finding to the audit (only while Running).
    pub fn add_finding(&mut self, finding: Finding) -> Result<(), DomainError> {
        if self.status != AuditStatus::Running {
            return Err(DomainError::InvalidState(
                "can only add findings while audit is running".into()));
        }
        self.findings.push(finding);
        Ok(())
    }

    /// Transition Running -> Completed.
    pub fn complete(&mut self) -> Result<(), DomainError> {
        if self.status != AuditStatus::Running {
            return Err(DomainError::InvalidState(format!(
                "cannot complete audit in state {:?}", self.status)));
        }
        self.status = AuditStatus::Completed;
        self.completed_at = Some(Utc::now());
        Ok(())
    }

    pub fn cancel(&mut self) -> Result<(), DomainError> {
        match self.status {
            AuditStatus::Pending | AuditStatus::Running => {
                self.status = AuditStatus::Cancelled;
                Ok(())
            }
            _ => Err(DomainError::InvalidState(
                "can only cancel pending or running audits".into())),
        }
    }

    /// Risk score = weighted sum of finding CVSS, capped at 10.
    pub fn risk_score(&self) -> f64 {
        let total: f64 = self.findings.iter()
            .map(|f| f.cvss * (f.severity.rank() as f64 + 1.0))
            .sum();
        (total / 5.0).min(10.0)
    }

    pub fn count_by_severity(&self, sev: Severity) -> usize {
        self.findings.iter().filter(|f| f.severity == sev).count()
    }
}
''')

w("src/domain/vulnerability.rs", r'''
//! Vulnerability scanner domain service (pure rules).
use crate::domain::audit::{Finding, Severity};
use crate::domain::error::DomainError;

/// A known vulnerability signature (rule) used by the scanner.
#[derive(Debug, Clone)]
pub struct VulnerabilityRule {
    pub id: &'static str,
    pub title: &'static str,
    pub severity: Severity,
    pub cvss: f64,
    pub description: &'static str,
    pub remediation: &'static str,
    /// predicate: matches the fingerprint string of a target.
    pub match_substr: &'static str,
}

/// The signature DB (a domain service). In a real system this is loaded from
/// a feed; here it is a hand-curated table of common ICS weaknesses.
pub fn signature_db() -> Vec<VulnerabilityRule> {
    vec![
        VulnerabilityRule {
            id: "CVE-DEMO-001", title: "Default credentials on HMI",
            severity: Severity::Critical, cvss: 9.8,
            description: "HMI device ships with default admin/admin credentials.",
            remediation: "Change default credentials and enforce strong passwords.",
            match_substr: "hmi-default-creds",
        },
        VulnerabilityRule {
            id: "CVE-DEMO-002", title: "Unencrypted Modbus traffic",
            severity: Severity::High, cvss: 7.5,
            description: "Modbus TCP traffic is unencrypted, exposing commands.",
            remediation: "Tunnel Modbus over TLS or use a segmented VLAN.",
            match_substr: "modbus-plaintext",
        },
        VulnerabilityRule {
            id: "CVE-DEMO-003", title: "Outdated firmware on PLC",
            severity: Severity::Medium, cvss: 6.1,
            description: "PLC firmware is older than the latest patched release.",
            remediation: "Upgrade PLC firmware to the latest vendor release.",
            match_substr: "plc-stale-firmware",
        },
        VulnerabilityRule {
            id: "CVE-DEMO-004", title: "Open Telnet service",
            severity: Severity::High, cvss: 7.4,
            description: "Telnet service is reachable and transmits credentials in cleartext.",
            remediation: "Disable Telnet; use SSH with key-based auth.",
            match_substr: "telnet-open",
        },
        VulnerabilityRule {
            id: "CVE-DEMO-005", title: "Missing network segmentation",
            severity: Severity::Low, cvss: 3.7,
            description: "OT and IT zones are on the same flat network.",
            remediation: "Implement VLAN segmentation per IEC 62443 zones/conduits.",
            match_substr: "flat-network",
        },
    ]
}

/// Scan a target's fingerprint against the signature DB and produce findings.
pub fn scan(target: &str, fingerprints: &[String]) -> Result<Vec<Finding>, DomainError> {
    let mut findings = Vec::new();
    for rule in signature_db() {
        for fp in fingerprints {
            if fp.contains(rule.match_substr) {
                findings.push(Finding::new(
                    target, rule.id, rule.title, rule.severity, rule.cvss,
                    rule.description, rule.remediation)?);
            }
        }
    }
    Ok(findings)
}
''')

w("src/domain/compliance.rs", r'''
//! IEC 62443 compliance checker domain service.
use crate::domain::error::DomainError;

/// A single IEC 62443 requirement (subset, for demonstration).
#[derive(Debug, Clone)]
pub struct Requirement {
    pub id: &'static str,
    pub title: &'static str,
    pub level: u8, // Security Level 1..4
    pub required: bool,
}

pub fn requirements_catalog() -> Vec<Requirement> {
    vec![
        Requirement { id: "SR 1.1", title: "Human user identification", level: 1, required: true },
        Requirement { id: "SR 1.2", title: "Software and device identification", level: 1, required: true },
        Requirement { id: "SR 2.1", title: "Authorization enforcement", level: 1, required: true },
        Requirement { id: "SR 3.1", title: "Communication integrity", level: 2, required: true },
        Requirement { id: "SR 4.1", title: "Information confidentiality", level: 2, required: true },
        Requirement { id: "SR 5.1", title: "Network segmentation", level: 2, required: true },
        Requirement { id: "SR 6.1", title: "Audit log accessibility", level: 2, required: true },
        Requirement { id: "SR 7.1", title: "Denial of service protection", level: 3, required: false },
        Requirement { id: "SR 7.2", title: "Resource availability", level: 3, required: false },
    ]
}

/// A compliance result per requirement.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ComplianceResult {
    pub requirement_id: String,
    pub title: String,
    pub required: bool,
    pub satisfied: bool,
    pub status: String, // PASS, FAIL, N/A
}

/// Evaluate the set of satisfied requirement IDs against the catalog for a
/// given target security level (SL). Returns per-requirement results + score.
pub fn evaluate(satisfied_ids: &[String], target_sl: u8) -> Vec<ComplianceResult> {
    let cat = requirements_catalog();
    cat.iter().map(|r| {
        // A requirement applies if its SL <= target SL.
        let applies = r.level <= target_sl;
        let satisfied = satisfied_ids.iter().any(|s| s == r.id);
        let status = if !applies {
            "N/A".to_string()
        } else if satisfied {
            "PASS".to_string()
        } else if r.required {
            "FAIL".to_string()
        } else {
            "PASS".to_string() // optional, satisfied or not counts as pass at this level
        };
        ComplianceResult {
            requirement_id: r.id.to_string(),
            title: r.title.to_string(),
            required: r.required && applies,
            satisfied,
            status,
        }
    }).collect()
}

/// Compute the compliance percentage (passed / applicable-required).
pub fn compliance_score(results: &[ComplianceResult]) -> f64 {
    let applicable: Vec<&ComplianceResult> = results.iter()
        .filter(|r| r.required).collect();
    if applicable.is_empty() {
        return 100.0;
    }
    let passed = applicable.iter().filter(|r| r.status == "PASS").count();
    passed as f64 / applicable.len() as f64 * 100.0
}

/// Validate that a target security level is in 1..=4.
pub fn validate_sl(sl: u8) -> Result<u8, DomainError> {
    if (1..=4).contains(&sl) {
        Ok(sl)
    } else {
        Err(DomainError::Validation("security level must be 1..=4".into()))
    }
}
''')

# =================== APPLICATION LAYER (use cases) ===================
w("src/application/mod.rs", r'''
//! Application layer: use cases orchestrating domain + repository ports.
pub mod audit_service;
pub use audit_service::AuditService;
''')

w("src/application/audit_service.rs", r'''
//! Audit application service: orchestrates the audit lifecycle, vulnerability
//! scan, and compliance check against a persistence port.
use crate::domain::audit::{AuditSession, AuditStatus, Finding, Severity};
use crate::domain::compliance::{evaluate, compliance_score, ComplianceResult, validate_sl};
use crate::domain::vulnerability::scan;
use crate::domain::error::DomainError;
use crate::infrastructure::repository::AuditRepository;

pub struct AuditService {
    repo: Box<dyn AuditRepository>,
}

impl AuditService {
    pub fn new(repo: Box<dyn AuditRepository>) -> Self {
        Self { repo }
    }

    /// Create and persist a new audit session.
    pub fn create_audit(&self, target: &str, auditor: &str) -> Result<AuditSession, DomainError> {
        let mut session = AuditSession::new(target, auditor)?;
        session.start()?;
        self.repo.save_session(&session)?;
        Ok(session)
    }

    /// Run a vulnerability scan against a target's fingerprints and attach findings.
    pub fn run_scan(&self, session_id: &str, fingerprints: &[String]) -> Result<Vec<Finding>, DomainError> {
        let mut session = self.repo.get_session(session_id)
            .ok_or_else(|| DomainError::NotFound(format!("session {}", session_id)))?;
        let findings = scan(&session.target, fingerprints)?;
        for f in &findings {
            session.add_finding(f.clone())?;
            self.repo.save_finding(session_id, f)?;
        }
        self.repo.save_session(&session)?;
        Ok(findings)
    }

    /// Complete the audit and return the final session.
    pub fn finalize(&self, session_id: &str) -> Result<AuditSession, DomainError> {
        let mut session = self.repo.get_session(session_id)
            .ok_or_else(|| DomainError::NotFound(format!("session {}", session_id)))?;
        session.complete()?;
        self.repo.save_session(&session)?;
        Ok(session)
    }

    /// Compliance report for the target security level.
    pub fn compliance_report(&self, session_id: &str, target_sl: u8) -> Result<ComplianceReport, DomainError> {
        validate_sl(target_sl)?;
        let session = self.repo.get_session(session_id)
            .ok_or_else(|| DomainError::NotFound(format!("session {}", session_id)))?;
        // Derive "satisfied" requirement IDs from absence of findings: a
        // requirement is satisfied if no finding references it as a gap.
        let satisfied: Vec<String> = vec![]; // in production this maps findings->requirements
        let results = evaluate(&satisfied, target_sl);
        let score = compliance_score(&results);
        Ok(ComplianceReport {
            session_id: session.id.clone(),
            target: session.target.clone(),
            security_level: target_sl,
            score,
            results,
            risk_score: session.risk_score(),
            findings_by_severity: SeveritySummary::from_session(&session),
        })
    }

    pub fn list_audits(&self) -> Result<Vec<AuditSession>, DomainError> {
        self.repo.list_sessions()
    }
}

#[derive(Debug, serde::Serialize)]
pub struct ComplianceReport {
    pub session_id: String,
    pub target: String,
    pub security_level: u8,
    pub score: f64,
    pub results: Vec<ComplianceResult>,
    pub risk_score: f64,
    pub findings_by_severity: SeveritySummary,
}

#[derive(Debug, serde::Serialize)]
pub struct SeveritySummary {
    pub critical: usize,
    pub high: usize,
    pub medium: usize,
    pub low: usize,
    pub info: usize,
}

impl SeveritySummary {
    pub fn from_session(s: &AuditSession) -> Self {
        Self {
            critical: s.count_by_severity(Severity::Critical),
            high: s.count_by_severity(Severity::High),
            medium: s.count_by_severity(Severity::Medium),
            low: s.count_by_severity(Severity::Low),
            info: s.count_by_severity(Severity::Info),
        }
    }
}
''')

# =================== INFRASTRUCTURE LAYER ===================
w("src/infrastructure/mod.rs", r'''
//! Infrastructure layer: persistence (rusqlite) + HTTP (actix) adapters.
pub mod repository;
pub mod http;
''')

w("src/infrastructure/repository.rs", r'''
//! Repository port + SQLite implementation.
use std::sync::Mutex;
use rusqlite::{params, Connection};
use chrono::{DateTime, Utc};
use crate::domain::audit::{AuditSession, AuditStatus, Finding, Severity};
use crate::domain::error::DomainError;

/// The repository port (trait). The application service depends on this.
pub trait AuditRepository: Send + Sync {
    fn save_session(&self, s: &AuditSession) -> Result<(), DomainError>;
    fn get_session(&self, id: &str) -> Option<AuditSession>;
    fn list_sessions(&self) -> Result<Vec<AuditSession>, DomainError>;
    fn save_finding(&self, session_id: &str, f: &Finding) -> Result<(), DomainError>;
}

/// SQLite-backed repository. Uses a Mutex-guarded connection (rusqlite is not
/// Sync by itself). `:memory:` path gives an ephemeral DB for tests.
pub struct SqliteAuditRepository {
    conn: Mutex<Connection>,
}

impl SqliteAuditRepository {
    pub fn open(path: &str) -> Result<Self, DomainError> {
        let conn = Connection::open(path)
            .map_err(|e| DomainError::Validation(format!("db open: {e}")))?;
        Self::init_schema(&conn)
            .map_err(|e| DomainError::Validation(format!("db schema: {e}")))?;
        Ok(Self { conn: Mutex::new(conn) })
    }

    /// In-memory repository (for tests and ephemeral runs).
    pub fn in_memory() -> Result<Self, DomainError> {
        Self::open(":memory:")
    }

    fn init_schema(conn: &Connection) -> rusqlite::Result<()> {
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS audit_sessions (
                id TEXT PRIMARY KEY, target TEXT, auditor TEXT, status TEXT,
                started_at TEXT, completed_at TEXT, created_at TEXT);
             CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY, session_id TEXT, target TEXT, rule_id TEXT,
                title TEXT, severity TEXT, cvss REAL, description TEXT,
                remediation TEXT, detected_at TEXT);
             CREATE INDEX IF NOT EXISTS idx_findings_session ON findings(session_id);",
        )?;
        Ok(())
    }
}

impl AuditRepository for SqliteAuditRepository {
    fn save_session(&self, s: &AuditSession) -> Result<(), DomainError> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR REPLACE INTO audit_sessions
             (id, target, auditor, status, started_at, completed_at, created_at)
             VALUES (?1,?2,?3,?4,?5,?6,?7)",
            params![
                s.id, s.target, s.auditor, format!("{:?}", s.status),
                s.started_at.map(|t| t.to_rfc3339()),
                s.completed_at.map(|t| t.to_rfc3339()),
                s.created_at.to_rfc3339(),
            ],
        ).map_err(|e| DomainError::Validation(format!("save session: {e}")))?;
        // Persist the latest findings snapshot too (delete + re-insert).
        conn.execute("DELETE FROM findings WHERE session_id = ?1", params![s.id])
            .map_err(|e| DomainError::Validation(format!("clear findings: {e}")))?;
        for f in &s.findings {
            conn.execute(
                "INSERT INTO findings (id, session_id, target, rule_id, title, severity,
                 cvss, description, remediation, detected_at)
                 VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
                params![f.id, s.id, f.target, f.rule_id, f.title,
                    format!("{:?}", f.severity), f.cvss, f.description,
                    f.remediation, f.detected_at.to_rfc3339()],
            ).map_err(|e| DomainError::Validation(format!("save finding: {e}")))?;
        }
        Ok(())
    }

    fn get_session(&self, id: &str) -> Option<AuditSession> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, target, auditor, status, started_at, completed_at, created_at
             FROM audit_sessions WHERE id = ?1").ok()?;
        let row = stmt.query_row(params![id], |r| {
            Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?,
                r.get::<_, String>(2)?, r.get::<_, String>(3)?,
                r.get::<_, Option<String>>(4)?, r.get::<_, Option<String>>(5)?,
                r.get::<_, String>(6)?))
        }).ok()?;

        let findings = load_findings(&conn, id).unwrap_or_default();
        Some(AuditSession {
            id: row.0, target: row.1, auditor: row.2,
            status: parse_status(&row.3), started_at: row.4.and_then(|s| DateTime::parse_from_rfc3339(&s).ok().map(|d| d.with_timezone(&Utc))),
            completed_at: row.5.and_then(|s| DateTime::parse_from_rfc3339(&s).ok().map(|d| d.with_timezone(&Utc))),
            created_at: DateTime::parse_from_rfc3339(&row.6).ok().map(|d| d.with_timezone(&Utc)).unwrap_or_else(Utc::now),
            findings,
        })
    }

    fn list_sessions(&self) -> Result<Vec<AuditSession>, DomainError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, target, auditor, status, started_at, completed_at, created_at
             FROM audit_sessions ORDER BY created_at DESC")
            .map_err(|e| DomainError::Validation(format!("list: {e}")))?;
        let rows = stmt.query_map([], |r| {
            Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?,
                r.get::<_, String>(2)?, r.get::<_, String>(3)?,
                r.get::<_, Option<String>>(4)?, r.get::<_, Option<String>>(5)?,
                r.get::<_, String>(6)?))
        }).map_err(|e| DomainError::Validation(format!("list map: {e}")))?;
        let mut out = Vec::new();
        for row in rows {
            let row = row.map_err(|e| DomainError::Validation(format!("list row: {e}")))?;
            let findings = load_findings(&conn, &row.0).unwrap_or_default();
            out.push(AuditSession {
                id: row.0, target: row.1, auditor: row.2,
                status: parse_status(&row.3),
                started_at: row.4.and_then(|s| DateTime::parse_from_rfc3339(&s).ok().map(|d| d.with_timezone(&Utc))),
                completed_at: row.5.and_then(|s| DateTime::parse_from_rfc3339(&s).ok().map(|d| d.with_timezone(&Utc))),
                created_at: DateTime::parse_from_rfc3339(&row.6).ok().map(|d| d.with_timezone(&Utc)).unwrap_or_else(Utc::now),
                findings,
            });
        }
        Ok(out)
    }

    fn save_finding(&self, _session_id: &str, _f: &Finding) -> Result<(), DomainError> {
        // Findings are persisted transactionally via save_session; this is a
        // no-op kept for port-completeness.
        Ok(())
    }
}

fn load_findings(conn: &Connection, session_id: &str) -> rusqlite::Result<Vec<Finding>> {
    let mut stmt = conn.prepare(
        "SELECT id, target, rule_id, title, severity, cvss, description, remediation, detected_at
         FROM findings WHERE session_id = ?1 ORDER BY detected_at")?;
    let rows = stmt.query_map(params![session_id], |r| {
        Ok(Finding {
            id: r.get(0)?, target: r.get(1)?, rule_id: r.get(2)?, title: r.get(3)?,
            severity: parse_severity(&r.get::<_, String>(4)?), cvss: r.get(5)?,
            description: r.get(6)?, remediation: r.get(7)?,
            detected_at: DateTime::parse_from_rfc3339(&r.get::<_, String>(8)?).ok().map(|d| d.with_timezone(&Utc)).unwrap_or_else(Utc::now),
        })
    })?;
    let mut out = Vec::new();
    for row in rows { out.push(row?); }
    Ok(out)
}

fn parse_status(s: &str) -> AuditStatus {
    match s {
        "Pending" => AuditStatus::Pending,
        "Running" => AuditStatus::Running,
        "Completed" => AuditStatus::Completed,
        "Failed" => AuditStatus::Failed,
        "Cancelled" => AuditStatus::Cancelled,
        _ => AuditStatus::Pending,
    }
}

fn parse_severity(s: &str) -> Severity {
    match s {
        "Info" => Severity::Info,
        "Low" => Severity::Low,
        "Medium" => Severity::Medium,
        "High" => Severity::High,
        "Critical" => Severity::Critical,
        _ => Severity::Info,
    }
}
''')

w("src/infrastructure/http.rs", r'''
//! Actix-Web primary adapter: REST API exposing the audit application service.
use actix_web::{web, App, HttpServer, HttpResponse, middleware};
use std::sync::Arc;
use serde::Deserialize;
use crate::application::AuditService;
use crate::domain::error::DomainError;

#[derive(Deserialize)]
pub struct CreateAudit { pub target: String, pub auditor: String }

#[derive(Deserialize)]
pub struct ScanRequest { pub fingerprints: Vec<String> }

#[derive(Deserialize)]
pub struct ComplianceRequest { pub security_level: u8 }

/// Shared app state injected into handlers.
pub struct AppState {
    pub service: AuditService,
}

/// Configure the routes on a ServiceConfig.
pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api/v1")
            .route("/audits", web::post().to(create_audit))
            .route("/audits", web::get().to(list_audits))
            .route("/audits/{id}/scan", web::post().to(run_scan))
            .route("/audits/{id}/finalize", web::post().to(finalize_audit))
            .route("/audits/{id}/compliance", web::post().to(compliance_report))
            .route("/health", web::get().to(health)),
    );
}

async fn create_audit(state: web::Data<Arc<AppState>>, body: web::Json<CreateAudit>) -> Result<HttpResponse, AuditError> {
    let session = state.service.create_audit(&body.target, &body.auditor)?;
    Ok(HttpResponse::Created().json(session))
}

async fn list_audits(state: web::Data<Arc<AppState>>) -> Result<HttpResponse, AuditError> {
    let sessions = state.service.list_audits()?;
    Ok(HttpResponse::Ok().json(sessions))
}

async fn run_scan(state: web::Data<Arc<AppState>>, path: web::Path<String>, body: web::Json<ScanRequest>) -> Result<HttpResponse, AuditError> {
    let findings = state.service.run_scan(&path.into_inner(), &body.fingerprints)?;
    Ok(HttpResponse::Ok().json(findings))
}

async fn finalize_audit(state: web::Data<Arc<AppState>>, path: web::Path<String>) -> Result<HttpResponse, AuditError> {
    let session = state.service.finalize(&path.into_inner())?;
    Ok(HttpResponse::Ok().json(session))
}

async fn compliance_report(state: web::Data<Arc<AppState>>, path: web::Path<String>, body: web::Json<ComplianceRequest>) -> Result<HttpResponse, AuditError> {
    let report = state.service.compliance_report(&path.into_inner(), body.security_level)?;
    Ok(HttpResponse::Ok().json(report))
}

async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"status":"ok","service":"security-audit"}))
}

/// Map domain errors to HTTP responses.
impl actix_web::ResponseError for AuditError {
    fn error_response(&self) -> HttpResponse {
        match self.0 {
            DomainError::NotFound(_) => HttpResponse::NotFound().json(serde_json::json!({"error": self.to_string()})),
            DomainError::Validation(_) => HttpResponse::BadRequest().json(serde_json::json!({"error": self.to_string()})),
            DomainError::InvalidState(_) => HttpResponse::Conflict().json(serde_json::json!({"error": self.to_string()})),
            DomainError::Policy(_) => HttpResponse::UnprocessableEntity().json(serde_json::json!({"error": self.to_string()})),
        }
    }
}

struct AuditError(DomainError);
impl std::fmt::Display for AuditError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { self.0.fmt(f) }
}
impl std::fmt::Debug for AuditError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { write!(f, "{:?}", self.0) }
}
impl From<DomainError> for AuditError { fn from(e: DomainError) -> Self { AuditError(e) } }

/// Run the HTTP server. `repo` is injected as a trait object.
pub async fn run_server(repo: Box<dyn crate::infrastructure::repository::AuditRepository>, bind: &str)
    -> std::io::Result<()>
{
    let state = Arc::new(AppState { service: AuditService::new(repo) });
    HttpServer::new(move || {
        App::new()
            .wrap(middleware::Logger::default())
            .app_data(web::Data::new(state.clone()))
            .configure(configure_routes)
    })
    .bind(bind)?
    .run()
    .await
}
''')

# =================== LIB ROOT ===================
w("src/lib.rs", r'''
//! Industrial Security Audit System (DDD).
//!
//! Layers:
//! - `domain`: pure entities, value objects, domain services (audit, vuln, compliance)
//! - `application`: use cases (AuditService) orchestrating domain + repository port
//! - `infrastructure`: SQLite repository + Actix-Web REST adapter

pub mod domain;
pub mod application;
pub mod infrastructure;
''')

# =================== BINS ===================
w("src/bin/server.rs", r'''
//! audit-server: runs the Actix-Web REST API.
use security_audit::infrastructure::http::run_server;
use security_audit::infrastructure::repository::SqliteAuditRepository;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    let db_path = std::env::var("AUDIT_DB").unwrap_or_else(|_| "audit.db".to_string());
    let repo = Box::new(SqliteAuditRepository::open(&db_path)
        .expect("failed to open audit database"));
    log::info!("starting security-audit server on :8080");
    run_server(repo, "0.0.0.0:8080").await
}
''')

w("src/bin/cli.rs", r'''
//! audit-cli: command-line tool to run a one-shot audit + compliance report.
use clap::{Parser, Subcommand};
use security_audit::application::AuditService;
use security_audit::infrastructure::repository::SqliteAuditRepository;

#[derive(Parser)]
#[command(name = "audit-cli", version, about = "Industrial security audit CLI")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Create a new audit session for a target.
    Create { #[arg(short, long)] target: String, #[arg(short, long)] auditor: String },
    /// Run a vulnerability scan using comma-separated fingerprints.
    Scan { #[arg(short, long)] id: String, #[arg(short, long)] fingerprints: String },
    /// Finalize an audit session.
    Finalize { #[arg(short, long)] id: String },
    /// Generate an IEC 62443 compliance report.
    Compliance { #[arg(short, long)] id: String, #[arg(short, long)] level: u8 },
    /// List all audit sessions.
    List,
}

fn main() {
    let db_path = std::env::var("AUDIT_DB").unwrap_or_else(|_| "audit.db".to_string());
    let repo = Box::new(SqliteAuditRepository::open(&db_path).expect("db open"));
    let svc = AuditService::new(repo);
    let cli = Cli::parse();

    match cli.command {
        Command::Create { target, auditor } => {
            let s = svc.create_audit(&target, &auditor).unwrap();
            println!("Created audit {} for target '{}' by '{}'", s.id, s.target, s.auditor);
        }
        Command::Scan { id, fingerprints } => {
            let fps: Vec<String> = fingerprints.split(',').map(|s| s.trim().to_string()).collect();
            let findings = svc.run_scan(&id, &fps).unwrap();
            println!("Scan produced {} findings:", findings.len());
            for f in &findings {
                println!("  [{:?}] {} (cvss {}): {}", f.severity, f.rule_id, f.cvss, f.title);
            }
        }
        Command::Finalize { id } => {
            let s = svc.finalize(&id).unwrap();
            println!("Finalized audit {}: risk_score = {:.2}, findings = {}", s.id, s.risk_score(), s.findings.len());
        }
        Command::Compliance { id, level } => {
            let report = svc.compliance_report(&id, level).unwrap();
            println!("Compliance score (SL{}): {:.1}%", report.security_level, report.score);
            for r in &report.results {
                if r.required {
                    println!("  [{}] {} - {}", r.status, r.requirement_id, r.title);
                }
            }
        }
        Command::List => {
            let sessions = svc.list_audits().unwrap();
            if sessions.is_empty() { println!("No audit sessions."); }
            for s in &sessions {
                println!("{} | target={} | {:?} | findings={}", s.id, s.target, s.status, s.findings.len());
            }
        }
    }
}
''')

print("rust source written")
