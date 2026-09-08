cd /home/jovyan/work/security-audit
cat > src/infrastructure/http.rs <<'RUST'
//! Actix-Web primary adapter: REST API exposing the audit application service.
//! Every blocking CRDB call is offloaded to the blocking thread-pool via
//! `web::block` so the actix worker runtime is never re-entered or stalled.
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
    pub service: Arc<AuditService>,
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
    let service = state.service.clone();
    let (target, auditor) = (body.target.clone(), body.auditor.clone());
    let session = web::block(move || service.create_audit(&target, &auditor))
        .await.map_err(|e| AuditError(DomainError::Validation(format!("block: {e}"))))??;
    Ok(HttpResponse::Created().json(session))
}

async fn list_audits(state: web::Data<Arc<AppState>>) -> Result<HttpResponse, AuditError> {
    let service = state.service.clone();
    let sessions = web::block(move || service.list_audits())
        .await.map_err(|e| AuditError(DomainError::Validation(format!("block: {e}"))))??;
    Ok(HttpResponse::Ok().json(sessions))
}

async fn run_scan(state: web::Data<Arc<AppState>>, path: web::Path<String>, body: web::Json<ScanRequest>) -> Result<HttpResponse, AuditError> {
    let service = state.service.clone();
    let id = path.into_inner();
    let fps = body.fingerprints.clone();
    let findings = web::block(move || service.run_scan(&id, &fps))
        .await.map_err(|e| AuditError(DomainError::Validation(format!("block: {e}"))))??;
    Ok(HttpResponse::Ok().json(findings))
}

async fn finalize_audit(state: web::Data<Arc<AppState>>, path: web::Path<String>) -> Result<HttpResponse, AuditError> {
    let service = state.service.clone();
    let id = path.into_inner();
    let session = web::block(move || service.finalize(&id))
        .await.map_err(|e| AuditError(DomainError::Validation(format!("block: {e}"))))??;
    Ok(HttpResponse::Ok().json(session))
}

async fn compliance_report(state: web::Data<Arc<AppState>>, path: web::Path<String>, body: web::Json<ComplianceRequest>) -> Result<HttpResponse, AuditError> {
    let service = state.service.clone();
    let id = path.into_inner();
    let sl = body.security_level;
    let report = web::block(move || service.compliance_report(&id, sl))
        .await.map_err(|e| AuditError(DomainError::Validation(format!("block: {e}"))))??;
    Ok(HttpResponse::Ok().json(report))
}

async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"status":"ok","service":"security-audit"}))
}

/// Map domain errors to HTTP responses.
impl actix_web::ResponseError for AuditError {
    fn error_response(&self) -> HttpResponse {
        match &self.0 {
            DomainError::NotFound(_) => HttpResponse::NotFound().json(serde_json::json!({"error": self.0.to_string()})),
            DomainError::Validation(_) => HttpResponse::BadRequest().json(serde_json::json!({"error": self.0.to_string()})),
            DomainError::InvalidState(_) => HttpResponse::Conflict().json(serde_json::json!({"error": self.0.to_string()})),
            DomainError::Policy(_) => HttpResponse::UnprocessableEntity().json(serde_json::json!({"error": self.0.to_string()})),
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
    let state = Arc::new(AppState { service: Arc::new(AuditService::new(repo)) });
    log::info!("security-audit HTTP server configured (scope /api/v1, web::block offloading)");
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
RUST
echo "http.rs v2: $(wc -l < src/infrastructure/http.rs) lines"
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -8
tail -3 /tmp/rust_build.log
