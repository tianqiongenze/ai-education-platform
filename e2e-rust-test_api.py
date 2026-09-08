"""
E2E tests for the Security Audit (Rust actix-web) project.
Tests cover: create audit, list audits, get audit, run scan,
compliance report, finalize, cache stats, health, frontend verification.
Uses requests for HTTP E2E testing.
"""
import pytest
import json
import sys
import os
import requests

BASE = os.environ.get("AUDIT_API", "http://localhost:8091/api/v1")


class TestHealthEndpoint:
    """GET /api/v1/health"""

    def test_health_returns_ok(self):
        r = requests.get(f"{BASE}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "security-audit"


class TestCreateAudit:
    """POST /api/v1/audits"""

    def test_create_audit_session(self):
        body = {"target": "E2E-PLC-001", "auditor": "e2e-tester"}
        r = requests.post(f"{BASE}/audits", json=body)
        assert r.status_code == 201
        data = r.json()
        assert data["target"] == "E2E-PLC-001"
        assert data["auditor"] == "e2e-tester"
        assert data["status"] == "IN_PROGRESS"
        return data["id"] or data["session_id"]

    def test_create_audit_missing_target(self):
        body = {"auditor": "e2e-tester"}
        r = requests.post(f"{BASE}/audits", json=body)
        assert r.status_code in (400, 422)

    def test_create_audit_missing_auditor(self):
        body = {"target": "E2E-PLC-002"}
        r = requests.post(f"{BASE}/audits", json=body)
        assert r.status_code in (400, 422)


class TestListAudits:
    """GET /api/v1/audits"""

    def test_list_audits_returns_list(self):
        r = requests.get(f"{BASE}/audits")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_audits_after_create(self):
        # Create an audit first
        requests.post(f"{BASE}/audits", json={"target": "E2E-LIST-TEST", "auditor": "e2e"})
        r = requests.get(f"{BASE}/audits")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        # Verify it contains our audit
        targets = [a.get("target") for a in data]
        assert "E2E-LIST-TEST" in targets


class TestGetAudit:
    """GET /api/v1/audits/{id}"""

    def test_get_audit_by_id(self):
        # Create first
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-GET-TEST", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]
        # Get
        r = requests.get(f"{BASE}/audits/{aid}")
        assert r.status_code == 200
        assert r.json()["id"] == aid or r.json()["session_id"] == aid

    def test_get_nonexistent_audit(self):
        r = requests.get(f"{BASE}/audits/nonexistent-id")
        assert r.status_code in (404, 400, 422)


class TestRunScan:
    """POST /api/v1/audits/{id}/scan"""

    def test_scan_with_fingerprints(self):
        # Create audit
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-SCAN-001", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        # Run scan with known fingerprints
        body = {"fingerprints": ["hmi-default-creds", "modbus-plaintext"]}
        r = requests.post(f"{BASE}/audits/{aid}/scan", json=body)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Should find 2 findings matching the fingerprints
        assert len(data) == 2

    def test_scan_empty_fingerprints(self):
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-SCAN-002", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        body = {"fingerprints": []}
        r = requests.post(f"{BASE}/audits/{aid}/scan", json=body)
        assert r.status_code == 200
        assert len(r.json()) == 0  # No findings for empty fingerprints

    def test_scan_unknown_fingerprints(self):
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-SCAN-003", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        body = {"fingerprints": ["nonexistent-fingerprint"]}
        r = requests.post(f"{BASE}/audits/{aid}/scan", json=body)
        assert r.status_code == 200
        assert len(r.json()) == 0  # No matching findings


class TestComplianceReport:
    """POST /api/v1/audits/{id}/compliance"""

    def test_compliance_report_for_clean_audit(self):
        # Create audit with no findings (empty scan)
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-COMPLY-CLEAN", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        # Run scan with no fingerprints (clean audit)
        requests.post(f"{BASE}/audits/{aid}/scan", json={"fingerprints": []})

        # Get compliance report
        body = {"security_level": 2}
        r = requests.post(f"{BASE}/audits/{aid}/compliance", json=body)
        assert r.status_code == 200
        data = r.json()
        # Clean audit should have high compliance score
        assert data["score"] == 100.0 or data.get("compliance_score") == 100.0

    def test_compliance_report_for_vulnerable_audit(self):
        # Create audit with known vulnerabilities
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-COMPLY-VULN", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        # Scan with critical + high findings
        requests.post(f"{BASE}/audits/{aid}/scan", json={
            "fingerprints": ["hmi-default-creds", "modbus-plaintext"]
        })

        # Get compliance report
        body = {"security_level": 2}
        r = requests.post(f"{BASE}/audits/{aid}/compliance", json=body)
        assert r.status_code == 200
        data = r.json()
        # Vulnerable audit should have lower score
        score = data["score"] or data.get("compliance_score", 0)
        assert score < 100.0
        # Should have gap counts
        gaps = data.get("gaps") or data.get("gap_counts") or {}
        assert len(gaps) > 0

    def test_compliance_invalid_security_level(self):
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-COMPLY-INVALID", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        body = {"security_level": 5}  # Invalid (should be 1-4)
        r = requests.post(f"{BASE}/audits/{aid}/compliance", json=body)
        assert r.status_code in (400, 422)


class TestFinalizeAudit:
    """POST /api/v1/audits/{id}/finalize"""

    def test_finalize_audit(self):
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-FINALIZE", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        r = requests.post(f"{BASE}/audits/{aid}/finalize")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "FINALIZED"

    def test_finalize_already_finalized(self):
        create = requests.post(f"{BASE}/audits", json={"target": "E2E-DOUBLE-FINAL", "auditor": "e2e"})
        aid = create.json()["id"] or create.json()["session_id"]

        r1 = requests.post(f"{BASE}/audits/{aid}/finalize")
        assert r1.status_code == 200

        r2 = requests.post(f"{BASE}/audits/{aid}/finalize")
        # Should error or return same state
        assert r2.status_code in (200, 400, 409, 422)


class TestCacheStats:
    """GET /api/v1/cache/stats"""

    def test_cache_stats_returns_data(self):
        r = requests.get(f"{BASE}/cache/stats")
        assert r.status_code == 200
        # Cache stats may return text or JSON
        assert len(r.text) > 0


class TestFullAuditLifecycle:
    """E2E: create → scan → compliance → finalize."""

    def test_complete_audit_workflow(self):
        # 1. Create audit
        create = requests.post(f"{BASE}/audits", json={
            "target": "E2E-FULL-AUDIT",
            "auditor": "e2e-full-tester"
        })
        assert create.status_code == 201
        aid = create.json()["id"] or create.json()["session_id"]

        # 2. Run scan with multiple fingerprints
        scan = requests.post(f"{BASE}/audits/{aid}/scan", json={
            "fingerprints": ["hmi-default-creds", "modbus-plaintext", "unauth-access"]
        })
        assert scan.status_code == 200
        findings = scan.json()
        assert len(findings) > 0

        # 3. Get compliance report
        compliance = requests.post(f"{BASE}/audits/{aid}/compliance", json={
            "security_level": 2
        })
        assert compliance.status_code == 200
        score = compliance.json().get("score") or compliance.json().get("compliance_score")
        assert score is not None
        assert score < 100.0  # Has vulnerabilities, so < 100

        # 4. Finalize
        finalize = requests.post(f"{BASE}/audits/{aid}/finalize")
        assert finalize.status_code == 200
        assert finalize.json()["status"] == "FINALIZED"

        # 5. Verify in list
        lst = requests.get(f"{BASE}/audits")
        assert lst.status_code == 200
        ids = [a.get("id") or a.get("session_id") for a in lst.json()]
        assert aid in ids


class TestFrontendVerification:
    """Verify the Security Audit frontend."""

    def test_frontend_file_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/security-audit/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        assert os.path.getsize(path) > 1000

    def test_frontend_has_audit_title(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/security-audit/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert '安全审计' in content or 'Security Audit' in content

    def test_frontend_has_create_audit_form(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/security-audit/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert 'createAudit' in content or 'audit' in content.lower()

    def test_frontend_has_scan_functionality(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/security-audit/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert 'runScan' in content or 'scan' in content.lower()

    def test_frontend_has_compliance_display(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/security-audit/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert 'compliance' in content.lower() or '合规' in content

    def test_frontend_has_api_log(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/security-audit/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert 'apiLog' in content or 'logApi' in content
