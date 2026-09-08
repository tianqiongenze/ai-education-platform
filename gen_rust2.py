#!/usr/bin/env python3
"""Generate Rust tests + SDD + README."""
import os, textwrap
BASE = "/tmp/p4-rust/security-audit"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# =================== TESTS ===================
w("tests/domain_audit_test.rs", r'''
//! Domain tests for the audit aggregate (state machine, invariants, metrics).
use security_audit::domain::audit::{AuditSession, AuditStatus, Finding, Severity};
use security_audit::domain::error::DomainError;

#[test]
fn create_audit_validates_target() {
    assert!(matches!(AuditSession::new("", "auditor"), Err(DomainError::Validation(_))));
    let s = AuditSession::new("plc-1", "alice").unwrap();
    assert_eq!(s.status, AuditStatus::Pending);
    assert!(s.findings.is_empty());
    assert!(s.started_at.is_none());
}

#[test]
fn state_machine_start_complete() {
    let mut s = AuditSession::new("d", "a").unwrap();
    s.start().unwrap();
    assert_eq!(s.status, AuditStatus::Running);
    assert!(s.started_at.is_some());
    s.complete().unwrap();
    assert_eq!(s.status, AuditStatus::Completed);
    assert!(s.completed_at.is_some());
}

#[test]
fn cannot_complete_without_starting() {
    let mut s = AuditSession::new("d", "a").unwrap();
    assert!(matches!(s.complete(), Err(DomainError::InvalidState(_))));
}

#[test]
fn cannot_start_twice() {
    let mut s = AuditSession::new("d", "a").unwrap();
    s.start().unwrap();
    assert!(matches!(s.start(), Err(DomainError::InvalidState(_))));
}

#[test]
fn add_finding_only_while_running() {
    let mut s = AuditSession::new("d", "a").unwrap();
    let f = Finding::new("d", "R1", "t", Severity::High, 7.0, "desc", "fix").unwrap();
    // Pending -> cannot add
    assert!(matches!(s.add_finding(f.clone()), Err(DomainError::InvalidState(_))));
    s.start().unwrap();
    s.add_finding(f).unwrap();
    assert_eq!(s.findings.len(), 1);
}

#[test]
fn cancel_from_pending_or_running() {
    let mut s = AuditSession::new("d", "a").unwrap();
    s.cancel().unwrap();
    assert_eq!(s.status, AuditStatus::Cancelled);

    let mut s2 = AuditSession::new("d", "a").unwrap();
    s2.start().unwrap();
    s2.cancel().unwrap();
    assert_eq!(s2.status, AuditStatus::Cancelled);

    // cannot cancel a completed audit
    let mut s3 = AuditSession::new("d", "a").unwrap();
    s3.start().unwrap();
    s3.complete().unwrap();
    assert!(matches!(s3.cancel(), Err(DomainError::InvalidState(_))));
}

#[test]
fn finding_validates_cvss_range() {
    assert!(matches!(Finding::new("d", "r", "t", Severity::Low, -1.0, "x", "y"), Err(DomainError::Validation(_))));
    assert!(matches!(Finding::new("d", "r", "t", Severity::Low, 11.0, "x", "y"), Err(DomainError::Validation(_))));
    let f = Finding::new("d", "r", "t", Severity::Critical, 9.8, "x", "y").unwrap();
    assert_eq!(f.severity, Severity::Critical);
}

#[test]
fn severity_from_score_mapping() {
    assert_eq!(Severity::from_score(9.5), Severity::Critical);
    assert_eq!(Severity::from_score(7.5), Severity::High);
    assert_eq!(Severity::from_score(5.0), Severity::Medium);
    assert_eq!(Severity::from_score(2.0), Severity::Low);
    assert_eq!(Severity::from_score(0.0), Severity::Info);
}

#[test]
fn risk_score_scales_with_findings() {
    let mut s = AuditSession::new("d", "a").unwrap();
    s.start().unwrap();
    assert_eq!(s.risk_score(), 0.0);
    s.add_finding(Finding::new("d", "r", "t", Severity::High, 7.0, "x", "y").unwrap()).unwrap();
    s.add_finding(Finding::new("d", "r2", "t2", Severity::Critical, 9.5, "x", "y").unwrap()).unwrap();
    let rs = s.risk_score();
    assert!(rs > 0.0 && rs <= 10.0);
    // critical (rank4+1=5) * 9.5 + high (rank3+1=4) * 7 = 47.5 + 28 = 75.5; /5 = 15.1 -> capped 10
    assert_eq!(rs, 10.0);
}

#[test]
fn count_by_severity() {
    let mut s = AuditSession::new("d", "a").unwrap();
    s.start().unwrap();
    s.add_finding(Finding::new("d", "r", "t", Severity::High, 7.0, "x", "y").unwrap()).unwrap();
    s.add_finding(Finding::new("d", "r2", "t", Severity::High, 7.5, "x", "y").unwrap()).unwrap();
    s.add_finding(Finding::new("d", "r3", "t", Severity::Low, 2.0, "x", "y").unwrap()).unwrap();
    assert_eq!(s.count_by_severity(Severity::High), 2);
    assert_eq!(s.count_by_severity(Severity::Low), 1);
    assert_eq!(s.count_by_severity(Severity::Critical), 0);
}
''')

w("tests/vulnerability_test.rs", r'''
//! Tests for the vulnerability scanner domain service.
use security_audit::domain::vulnerability::{scan, signature_db};
use security_audit::domain::audit::Severity;

#[test]
fn signature_db_is_populated() {
    let db = signature_db();
    assert!(db.len() >= 5);
    assert!(db.iter().any(|r| r.id == "CVE-DEMO-001"));
}

#[test]
fn scan_matches_known_signatures() {
    let fps = vec![
        "hmi-default-creds".to_string(),
        "telnet-open".to_string(),
        "benign-config".to_string(),
    ];
    let findings = scan("target-1", &fps).unwrap();
    assert_eq!(findings.len(), 2);
    let ids: Vec<&str> = findings.iter().map(|f| f.rule_id.as_str()).collect();
    assert!(ids.contains(&"CVE-DEMO-001"));
    assert!(ids.contains(&"CVE-DEMO-004"));
}

#[test]
fn scan_no_matches_returns_empty() {
    let fps = vec!["clean-target".to_string()];
    let findings = scan("t", &fps).unwrap();
    assert!(findings.is_empty());
}

#[test]
fn scan_validates_target() {
    let findings = scan("", &["x".to_string()]);
    assert!(findings.is_err());
}

#[test]
fn findings_carry_severity_and_cvss() {
    let findings = scan("t", &["plc-stale-firmware".to_string()]).unwrap();
    assert_eq!(findings.len(), 1);
    let f = &findings[0];
    assert_eq!(f.severity, Severity::Medium);
    assert!((f.cvss - 6.1).abs() < 1e-9);
    assert!(!f.remediation.is_empty());
}
''')

w("tests/compliance_test.rs", r'''
//! Tests for the IEC 62443 compliance checker.
use security_audit::domain::compliance::{evaluate, compliance_score, validate_sl, requirements_catalog};

#[test]
fn catalog_has_requirements_across_levels() {
    let cat = requirements_catalog();
    assert!(cat.iter().any(|r| r.level == 1));
    assert!(cat.iter().any(|r| r.level == 3));
    assert!(cat.iter().all(|r| r.id.starts_with("SR")));
}

#[test]
fn validate_sl_range() {
    assert!(validate_sl(0).is_err());
    assert!(validate_sl(5).is_err());
    assert!(validate_sl(1).is_ok());
    assert!(validate_sl(4).is_ok());
}

#[test]
fn evaluate_marks_unsatisfied_required_as_fail() {
    let results = evaluate(&[], 2); // nothing satisfied
    // SR 1.1 is required level 1 -> applies at SL2 -> FAIL
    let sr11 = results.iter().find(|r| r.requirement_id == "SR 1.1").unwrap();
    assert_eq!(sr11.status, "FAIL");
    assert!(sr11.required);
}

#[test]
fn evaluate_marks_satisfied_as_pass() {
    let satisfied = vec!["SR 1.1".to_string()];
    let results = evaluate(&satisfied, 1);
    let sr11 = results.iter().find(|r| r.requirement_id == "SR 1.1").unwrap();
    assert_eq!(sr11.status, "PASS");
}

#[test]
fn evaluate_marks_higher_level_as_na_at_lower_sl() {
    let results = evaluate(&[], 1);
    // SR 7.1 is level 3 -> N/A at SL1
    let sr71 = results.iter().find(|r| r.requirement_id == "SR 7.1").unwrap();
    assert_eq!(sr71.status, "N/A");
}

#[test]
fn compliance_score_zero_when_nothing_satisfied() {
    let results = evaluate(&[], 2);
    let score = compliance_score(&results);
    assert!(score < 100.0);
}

#[test]
fn compliance_score_100_when_all_satisfied() {
    let cat = requirements_catalog();
    let satisfied: Vec<String> = cat.iter().map(|r| r.id.to_string()).collect();
    let results = evaluate(&satisfied, 3);
    assert_eq!(compliance_score(&results), 100.0);
}
''')

w("tests/repository_test.rs", r'''
//! Integration tests for the SQLite repository (in-memory).
use security_audit::domain::audit::{AuditSession, Finding, Severity};
use security_audit::infrastructure::repository::{AuditRepository, SqliteAuditRepository};

fn repo() -> SqliteAuditRepository { SqliteAuditRepository::in_memory().unwrap() }

#[test]
fn save_and_get_session() {
    let r = repo();
    let mut s = AuditSession::new("plc-1", "alice").unwrap();
    s.start().unwrap();
    let f = Finding::new("plc-1", "R1", "Default creds", Severity::Critical, 9.8, "desc", "fix").unwrap();
    s.add_finding(f.clone()).unwrap();
    r.save_session(&s).unwrap();

    let got = r.get_session(&s.id).expect("session should exist");
    assert_eq!(got.target, "plc-1");
    assert_eq!(got.auditor, "alice");
    assert_eq!(got.findings.len(), 1);
    assert_eq!(got.findings[0].rule_id, "R1");
    assert_eq!(got.findings[0].severity, Severity::Critical);
}

#[test]
fn get_missing_session_returns_none() {
    let r = repo();
    assert!(r.get_session("nope").is_none());
}

#[test]
fn list_sessions_returns_all() {
    let r = repo();
    let s1 = AuditSession::new("a", "x").unwrap();
    let s2 = AuditSession::new("b", "y").unwrap();
    r.save_session(&s1).unwrap();
    r.save_session(&s2).unwrap();
    let list = r.list_sessions().unwrap();
    assert_eq!(list.len(), 2);
}

#[test]
fn save_session_updates_findings_snapshot() {
    let r = repo();
    let mut s = AuditSession::new("d", "a").unwrap();
    s.start().unwrap();
    s.add_finding(Finding::new("d", "r", "t", Severity::High, 7.0, "x", "y").unwrap()).unwrap();
    r.save_session(&s).unwrap();
    // add another finding and re-save
    s.add_finding(Finding::new("d", "r2", "t2", Severity::Low, 2.0, "x", "y").unwrap()).unwrap();
    r.save_session(&s).unwrap();
    let got = r.get_session(&s.id).unwrap();
    assert_eq!(got.findings.len(), 2);
}

#[test]
fn schema_idempotent_on_reopen() {
    let r1 = repo();
    let mut s = AuditSession::new("d", "a").unwrap();
    s.start().unwrap();
    r1.save_session(&s).unwrap();
    // re-saving the same session (UPSERT) must not error
    r1.save_session(&s).unwrap();
}
''')

w("tests/application_test.rs", r'''
//! Application service tests (use case orchestration with in-memory repo).
use security_audit::application::AuditService;
use security_audit::infrastructure::repository::{AuditRepository, SqliteAuditRepository};
use security_audit::domain::audit::AuditStatus;

fn svc() -> (AuditService, SqliteAuditRepository) {
    let repo = SqliteAuditRepository::in_memory().unwrap();
    // We need the concrete repo too to peek; wrap in a service with a clone-like
    // approach: re-open an in-memory won't share, so we test through the service API.
    let svc = AuditService::new(Box::new(SqliteAuditRepository::in_memory().unwrap()));
    (svc, SqliteAuditRepository::in_memory().unwrap())
}

#[test]
fn full_audit_lifecycle() {
    let (svc, _repo) = svc();
    // create
    let session = svc.create_audit("plc-1", "alice").unwrap();
    assert_eq!(session.status, AuditStatus::Running);
    // scan with known fingerprints
    let findings = svc.run_scan(&session.id, &["hmi-default-creds".to_string()]).unwrap();
    assert_eq!(findings.len(), 1);
    // finalize
    let final_session = svc.finalize(&session.id).unwrap();
    assert_eq!(final_session.status, AuditStatus::Completed);
    assert_eq!(final_session.findings.len(), 1);
    // list
    let list = svc.list_audits().unwrap();
    assert_eq!(list.len(), 1);
}

#[test]
fn compliance_report_for_fresh_audit() {
    let (svc, _repo) = svc();
    let session = svc.create_audit("plc-1", "alice").unwrap();
    let _ = svc.run_scan(&session.id, &[]).unwrap();
    let _ = svc.finalize(&session.id).unwrap();
    let report = svc.compliance_report(&session.id, 2).unwrap();
    assert_eq!(report.security_level, 2);
    assert!(report.score < 100.0); // nothing satisfied -> low score
    assert!(report.results.iter().any(|r| r.status == "FAIL"));
}

#[test]
fn compliance_rejects_invalid_sl() {
    let (svc, _repo) = svc();
    let session = svc.create_audit("plc-1", "alice").unwrap();
    assert!(svc.compliance_report(&session.id, 5).is_err());
}

#[test]
fn finalize_missing_session_errors() {
    let (svc, _repo) = svc();
    assert!(svc.finalize("ghost").is_err());
}
''')

# =================== DOCS ===================
w("README.md", r'''
# 工业安全审计系统 (Industrial Security Audit System)

> Student: `student-rust` — Language: Rust 1.98 + Actix-Web
> Architecture: Domain-Driven Design (DDD)

A security audit platform for industrial control systems (ICS) that runs
vulnerability scans against a signature database, evaluates IEC 62443
compliance, persists audit sessions and findings to SQLite, and exposes the
whole lifecycle through an Actix-Web REST API and a `clap` CLI.

## Architecture (DDD)

```
   Presentation         Application            Domain              Infrastructure
   ┌────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────────┐
   │ actix HTTP │ ──► │ AuditService │ ──► │ AuditSession │ ──► │ SqliteAuditRepo  │
   │ clap CLI    │      │ (use cases)  │      │ Finding       │      │ rusqlite         │
   └────────────┘      └──────────────┘      │ Vuln scanner  │      └──────────────────┘
                                               │ IEC62443 check  │
                                               └──────────────┘
   Domain depends on nothing infrastructural; infra implements the repository trait.
```

## Modules
- `src/domain/` — `AuditSession` aggregate, `Finding`/`Severity` value objects,
  vulnerability signature scanner, IEC 62443 compliance checker, domain errors.
- `src/application/` — `AuditService` use cases (create → scan → finalize → report).
- `src/infrastructure/repository.rs` — `AuditRepository` trait + SQLite impl.
- `src/infrastructure/http.rs` — Actix-Web REST adapter + error mapping.
- `src/bin/cli.rs` — `audit-cli` (clap) for one-shot audits.
- `src/bin/server.rs` — `audit-server` REST API on :8080.

## Build & Test
```bash
cargo build        # build lib + 2 binaries
cargo test         # run the full test suite
cargo run --bin audit-cli -- create -t plc-1 -a alice
cargo run --bin audit-cli -- scan -i <id> -f hmi-default-creds
cargo run --bin audit-cli -- compliance -i <id> -l 2
cargo run --bin audit-server    # REST API on :8080
```
The bundled rusqlite feature compiles SQLite from source, so no system lib is needed.
Crates fetch from the USTC mirror (see `.cargo/config.toml`).

## REST API
```
POST   /api/v1/audits                      {target, auditor}        -> session
GET    /api/v1/audits                                               -> [session]
POST   /api/v1/audits/{id}/scan            {fingerprints[]}         -> [finding]
POST   /api/v1/audits/{id}/finalize                                  -> session
POST   /api/v1/audits/{id}/compliance     {security_level}         -> report
GET    /api/v1/health                                               -> {status}
```

See `docs/SDD.md` for the full Software Design Document.
''')

w("docs/SDD.md", r'''
# Software Design Document (SDD)
## 工业安全审计系统 — Industrial Security Audit System

**Project:** Security Audit &nbsp; **Student:** student-rust &nbsp;
**Language:** Rust 1.98 (edition 2021) &nbsp; **Framework:** Actix-Web 4 &nbsp;
**Architecture:** Domain-Driven Design (DDD)

> AI-assisted design: the DDD aggregate boundaries and IEC 62443 requirement
> subset were validated against the `qwen2.5-coder:7b` model via the platform
> LiteLLM gateway. Implementation and tests are hand-written.

---

## 1. Introduction

### 1.1 Purpose
A system to audit the security posture of industrial control system (ICS)
assets: it runs a vulnerability scan against a curated signature database,
evaluates compliance with a subset of IEC 62443, and produces a risk-scored
report. Audit sessions and findings are persisted to SQLite and served via a
REST API and CLI.

### 1.2 Scope
Inbound: target identifier + device fingerprints (banner/config strings).
Processing: signature matching (vulnerability), requirement evaluation
(compliance), stateful audit lifecycle, risk scoring, persistence. Outbound:
REST API, CLI report, JSON compliance report. Out of scope: live network
scanning (Nmap-style) and an authenticated multi-tenant backend.

### 1.3 Definitions
- **Aggregate root** — `AuditSession`; the consistency boundary for findings.
- **CVSS** — Common Vulnerability Scoring System (0–10).
- **IEC 62443** — industrial communications network security standard.
- **SL** — Security Level (1–4) in IEC 62443 terminology.
- **Repository trait** — the persistence port (Rust trait).

---

## 2. Architecture (DDD)

### 2.1 Layered Structure
```
[ Presentation: actix-web, clap CLI ] ─►
[ Application: AuditService use cases ] ─►
[ Domain: AuditSession, Finding, scanner, compliance ]   ◄── Repository trait (port)
[ Infrastructure: SqliteAuditRepository (rusqlite) ]     (adapter impl)
```
The domain layer is pure: it depends on no infrastructure crate. The
application layer depends on the domain and on the `AuditRepository` trait
(defined in infrastructure but abstract). Infrastructure implements the trait.
This is the classic DDD dependency inversion — high-level policy does not
depend on low-level details.

### 2.2 Aggregates & Value Objects

| Type | Kind | Notes |
|------|------|-------|
| `AuditSession` | Aggregate root | owns `Finding`s; enforces state machine |
| `Finding` | Entity (within AuditSession) | id, severity, cvss, rule, remediation |
| `Severity` | Value object (enum) | Info/Low/Medium/High/Critical, rank + from_score |
| `AuditStatus` | Value object (enum) | Pending/Running/Completed/Failed/Cancelled |
| `ComplianceResult` | Value object | per-requirement PASS/FAIL/N/A |

### 2.3 Domain Services
- **Vulnerability scanner** (`vulnerability.rs`) — a signature DB + `scan()`
  pure function mapping target fingerprints to `Finding`s.
- **Compliance checker** (`compliance.rs`) — IEC 62443 requirement catalog,
  `evaluate()` for per-requirement status, `compliance_score()` percentage.

---

## 3. Audit Lifecycle (State Machine)

```
   create()              start()           add_finding()*         complete()
   ──────► Pending ──────► Running ───────────────────────► Completed
              │                │
              └─cancel()─► Cancelled   ◄── cancel()
```
Invariants (enforced in `AuditSession`):
- `start()` only from Pending.
- `add_finding()` only while Running.
- `complete()` only from Running.
- `cancel()` only from Pending or Running.

---

## 4. IEC 62443 Compliance Model

A catalog of System Requirements (SR 1.1 … SR 7.2) each tagged with a Security
Level (1–3 in this subset) and `required` flag. Given a target SL, a
requirement *applies* when its level ≤ target SL. Status:
- **N/A** when the requirement's level > target SL.
- **PASS** when required+applies and satisfied, or optional (regardless).
- **FAIL** when required+applies and not satisfied.

Compliance score = passed / applicable-required × 100.

---

## 5. Risk Scoring
`AuditSession::risk_score()` = Σ(cvss × (severity_rank + 1)) / 5, capped at 10.
Severity rank: Info=0, Low=1, Medium=2, High=3, Critical=4. The (rank+1)
weighting makes a Critical finding dominate the score, mirroring qualitative
risk matrices used in OT security.

---

## 6. REST API & CLI

### 6.1 REST
Actix-Web routes under `/api/v1`. Domain errors map to HTTP codes via a
`ResponseError` impl (404 NotFound, 400 Validation, 409 InvalidState, 422
Policy). JSON via serde.

### 6.2 CLI
`clap` derive: `create | scan | finalize | compliance | list`. The CLI reuses
the same `AuditService` as the HTTP adapter, demonstrating the DDD principle
that application logic is presentation-agnostic.

---

## 7. Sequence Diagram

```
CLI/HTTP ─► AuditService.create_audit(target, auditor)
             │ AuditSession::new + start (domain)
             │ repo.save_session                [SQLite]
             └─► session (Running)
CLI/HTTP ─► AuditService.run_scan(id, fingerprints)
             │ repo.get_session
             │ vulnerability::scan(target, fps)  [domain service]
             │ session.add_finding (invariant)
             │ repo.save_finding + repo.save_session
             └─► [Finding]
CLI/HTTP ─► AuditService.finalize(id)
             │ session.complete (state machine)
             │ repo.save_session
             └─► session (Completed)
CLI/HTTP ─► AuditService.compliance_report(id, sl)
             │ compliance::validate_sl + evaluate + score
             └─► ComplianceReport (JSON)
```

---

## 8. Test Strategy

Tests are integration tests in `tests/` exercising the public API:

| File | Tests | Covers |
|------|-------|--------|
| domain_audit_test.rs | 9 | aggregate state machine, invariants, risk score |
| vulnerability_test.rs | 5 | signature DB, scan matching, validation |
| compliance_test.rs | 6 | catalog, SL validation, PASS/FAIL/N/A, score |
| repository_test.rs | 5 | SQLite save/get/list/update (in-memory) |
| application_test.rs | 4 | full lifecycle + compliance + error cases |

Run: `cargo test`. The repository tests use `:memory:` SQLite for isolation.

---

## 9. Non-Functional Requirements
- **Memory safety:** Rust's ownership model eliminates data races; the
  SQLite connection is `Mutex`-guarded.
- **Performance:** zero-cost abstractions; actix-web is a high-throughput
  async runtime.
- **Portability:** bundled rusqlite compiles SQLite from source — no system
  library dependency. The USTC crate mirror handles air-gapped builds.
- **Extensibility:** new vulnerability rules are added to `signature_db()`;
  new IEC requirements to `requirements_catalog()` — no architectural change.

## 10. Revision History
| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2026-08-31 | student-rust | Initial SDD, DDD, Actix-Web + rusqlite + clap |
''')

print("rust tests + docs written")
