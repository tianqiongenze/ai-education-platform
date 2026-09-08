cd /home/jovyan/work/security-audit
python3 - <<'PY'
p = 'src/application/audit_service.rs'
src = open(p).read()
# Map findings onto the FULL catalog requirement set (all 9 SRs),
# not just the 5 we guessed. Critical/High -> access-control FR1/FR2 gaps,
# Medium -> integrity/confidentiality/segmentation FR3/4/5, Low -> FR6/7.
old = """        let mut gaps: Vec<String> = Vec::new();
        let mut crit_or_high = 0usize;
        let mut medium = 0usize;
        let mut low = 0usize;
        for f in &session.findings {
            match f.severity {
                Severity::Critical | Severity::High => { crit_or_high += 1; gaps.push("SR 1.1".into()); gaps.push("SR 1.2".into()); }
                Severity::Medium => { medium += 1; gaps.push("SR 3.1".into()); }
                Severity::Low => { low += 1; gaps.push("SR 7.1".into()); }
                Severity::Info => {}
            }
        }
        let unique: std::collections::HashSet<String> = gaps.into_iter().collect();
        let all: Vec<String> = vec![
            "SR 1.1".into(), "SR 1.2".into(), "SR 3.1".into(), "SR 3.2".into(), "SR 7.1".into(),
        ];
        let satisfied: Vec<String> = all.into_iter().filter(|r| !unique.contains(r)).collect();"""
new = """        let mut crit_or_high = 0usize;
        let mut medium = 0usize;
        let mut low = 0usize;
        // Full catalog: a requirement is satisfied unless findings in its
        // severity band exist (evidence-based gap model for the demo rules).
        let all: Vec<&str> = requirements_catalog().iter().map(|r| r.id).collect();
        let mut gaps: Vec<String> = Vec::new();
        for f in &session.findings {
            match f.severity {
                Severity::Critical | Severity::High => {
                    crit_or_high += 1;
                    for id in ["SR 1.1", "SR 1.2", "SR 2.1"] { gaps.push(id.into()); }
                }
                Severity::Medium => {
                    medium += 1;
                    for id in ["SR 3.1", "SR 4.1", "SR 5.1"] { gaps.push(id.into()); }
                }
                Severity::Low => {
                    low += 1;
                    for id in ["SR 6.1", "SR 7.1", "SR 7.2"] { gaps.push(id.into()); }
                }
                Severity::Info => {}
            }
        }
        let unique: std::collections::HashSet<String> = gaps.into_iter().collect();
        let satisfied: Vec<String> = all.into_iter()
            .map(String::from)
            .filter(|r| !unique.contains(r))
            .collect();"""
assert old in src, 'gap block not found'
src = src.replace(old, new)
old2 = """use crate::domain::compliance::{evaluate, validate_sl, compliance_score, ComplianceResult};"""
new2 = """use crate::domain::compliance::{evaluate, validate_sl, compliance_score, requirements_catalog, ComplianceResult};"""
assert old2 in src
src = src.replace(old2, new2)
open(p, 'w').write(src)
print('compliance gap mapping patched (full 9-SR catalog)')
PY
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -6
tail -2 /tmp/rust_build.log
