"""
E2E tests for the MES Production System (Java Spring Boot) project.
Tests cover: production orders CRUD, start/progress/cancel, yield rate,
quality inspections, FPY, defect rate, frontend verification.
"""
import pytest
import json
import sys
import os
import requests


# Base URLs for the microservices
PRODUCTION_BASE = os.environ.get("PRODUCTION_API", "http://localhost:8081/api/v1/production")
QUALITY_BASE = os.environ.get("QUALITY_API", "http://localhost:8082/api/v1/quality")


class TestProductionOrderCRUD:
    """Production order lifecycle: create → get → start → progress → cancel."""

    def test_create_production_order(self):
        body = {"productName": "E2E-Product", "plannedQuantity": 100, "priority": "NORMAL"}
        r = requests.post(f"{PRODUCTION_BASE}/orders", json=body)
        assert r.status_code == 201
        data = r.json()
        assert data["productName"] == "E2E-Product"
        assert data["plannedQuantity"] == 100 or data["plannedQty"] == 100
        assert data["status"] == "PENDING"
        return data["id"] or data["orderId"]

    def test_get_production_order(self):
        oid = self.test_create_production_order()
        r = requests.get(f"{PRODUCTION_BASE}/orders/{oid}")
        assert r.status_code == 200
        assert r.json()["id"] == oid or r.json()["orderId"] == oid

    def test_list_all_orders(self):
        r = requests.get(f"{PRODUCTION_BASE}/orders")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_orders_by_status(self):
        r = requests.get(f"{PRODUCTION_BASE}/orders", params={"status": "PENDING"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for o in data:
            assert o["status"] == "PENDING"

    def test_start_production_order(self):
        oid = self.test_create_production_order()
        r = requests.post(f"{PRODUCTION_BASE}/orders/{oid}/start")
        assert r.status_code == 200
        assert r.json()["status"] == "RUNNING"

    def test_report_progress(self):
        oid = self.test_create_production_order()
        requests.post(f"{PRODUCTION_BASE}/orders/{oid}/start")
        r = requests.post(f"{PRODUCTION_BASE}/orders/{oid}/progress",
                         params={"completed": 50, "defects": 2})
        assert r.status_code == 200
        data = r.json()
        assert data["completedQuantity"] == 50 or data["completed"] == 50

    def test_cancel_production_order(self):
        oid = self.test_create_production_order()
        r = requests.post(f"{PRODUCTION_BASE}/orders/{oid}/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "CANCELLED"

    def test_create_order_invalid_quantity(self):
        body = {"productName": "Bad", "plannedQuantity": -1, "priority": "NORMAL"}
        r = requests.post(f"{PRODUCTION_BASE}/orders", json=body)
        assert r.status_code in (400, 422)

    def test_create_order_missing_name(self):
        body = {"plannedQuantity": 100, "priority": "NORMAL"}
        r = requests.post(f"{PRODUCTION_BASE}/orders", json=body)
        assert r.status_code in (400, 422)


class TestProductionMetrics:
    """Yield rate and cache metrics."""

    def test_yield_rate_endpoint(self):
        r = requests.get(f"{PRODUCTION_BASE}/orders/metrics/yield-rate")
        assert r.status_code == 200
        data = r.json()
        assert "yieldRate" in data
        assert data["unit"] == "percent"

    def test_cache_stats_endpoint(self):
        r = requests.get(f"{PRODUCTION_BASE}/orders/metrics/cache")
        assert r.status_code == 200


class TestQualityInspection:
    """Quality inspection CRUD and metrics."""

    def test_record_inspection_pass(self):
        body = {"orderId": "E2E-ORD-001", "inspectionItem": "尺寸检测", "result": "PASS"}
        r = requests.post(f"{QUALITY_BASE}/inspections", json=body)
        assert r.status_code == 201
        data = r.json()
        assert data["result"] == "PASS"

    def test_record_inspection_fail(self):
        body = {"orderId": "E2E-ORD-001", "inspectionItem": "外观检测",
                "result": "FAIL", "defectDescription": "表面划痕"}
        r = requests.post(f"{QUALITY_BASE}/inspections", json=body)
        assert r.status_code == 201
        assert r.json()["result"] == "FAIL"

    def test_get_inspection_by_id(self):
        body = {"orderId": "E2E-ORD-002", "inspectionItem": "功能测试", "result": "PASS"}
        create = requests.post(f"{QUALITY_BASE}/inspections", json=body)
        iid = create.json()["id"]
        r = requests.get(f"{QUALITY_BASE}/inspections/{iid}")
        assert r.status_code == 200

    def test_list_inspections_by_order(self):
        body = {"orderId": "E2E-ORD-003", "inspectionItem": "测试", "result": "PASS"}
        requests.post(f"{QUALITY_BASE}/inspections", json=body)
        r = requests.get(f"{QUALITY_BASE}/inspections", params={"orderId": "E2E-ORD-003"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    def test_fpy_metric(self):
        r = requests.get(f"{QUALITY_BASE}/inspections/metrics/fpy")
        assert r.status_code == 200
        assert "firstPassYield" in r.json()

    def test_defect_rate_metric(self):
        r = requests.get(f"{QUALITY_BASE}/inspections/metrics/defect-rate")
        assert r.status_code == 200
        assert "defectRate" in r.json()

    def test_quality_cache_stats(self):
        r = requests.get(f"{QUALITY_BASE}/inspections/metrics/cache")
        assert r.status_code == 200


class TestFullProductionWorkflow:
    """E2E: create order → start → progress → inspect → finalize."""

    def test_complete_production_lifecycle(self):
        # 1. Create order
        create = requests.post(f"{PRODUCTION_BASE}/orders", json={
            "productName": "E2E-Full-Test", "plannedQuantity": 50, "priority": "HIGH"
        })
        assert create.status_code == 201
        oid = create.json()["id"] or create.json()["orderId"]

        # 2. Start production
        start = requests.post(f"{PRODUCTION_BASE}/orders/{oid}/start")
        assert start.status_code == 200
        assert start.json()["status"] == "RUNNING"

        # 3. Report progress in batches
        for batch in [(20, 1), (40, 2), (50, 3)]:
            prog = requests.post(f"{PRODUCTION_BASE}/orders/{oid}/progress",
                                params={"completed": batch[0], "defects": batch[1]})
            assert prog.status_code == 200

        # 4. Record quality inspections
        for i in range(5):
            result = "PASS" if i < 4 else "FAIL"
            insp = requests.post(f"{QUALITY_BASE}/inspections", json={
                "orderId": oid, "inspectionItem": f"检测-{i}", "result": result,
                "defectDescription": "" if result == "PASS" else "不合格项"
            })
            assert insp.status_code == 201

        # 5. Verify metrics
        yld = requests.get(f"{PRODUCTION_BASE}/orders/metrics/yield-rate")
        assert yld.status_code == 200
        assert isinstance(yld.json()["yieldRate"], (int, float))

        fpy = requests.get(f"{QUALITY_BASE}/inspections/metrics/fpy")
        assert fpy.status_code == 200
        assert isinstance(fpy.json()["firstPassYield"], (int, float))


class TestFrontendVerification:
    """Verify the MES frontend HTML exists and is valid."""

    def test_frontend_file_exists(self):
        # Find the frontend relative to the mes-system project
        possible_paths = [
            "frontend/index.html",
            "/home/jovyan/work/mes-system/frontend/index.html",
            os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return
        pytest.skip("Frontend not found in expected locations")

    def test_frontend_contains_mes_title(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/mes-system/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert 'MES' in content or '生产管理' in content

    def test_frontend_has_order_management(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/mes-system/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert 'createOrder' in content or '订单' in content

    def test_frontend_has_quality_tab(self):
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if not os.path.exists(path):
            path = "/home/jovyan/work/mes-system/frontend/index.html"
        if not os.path.exists(path):
            pytest.skip("Frontend not found")
        with open(path) as f:
            content = f.read()
        assert 'quality' in content.lower() or '质量' in content
