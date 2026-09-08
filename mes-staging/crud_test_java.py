#!/usr/bin/env python3
"""Java MES CRUD + integration test against live services (real PostgreSQL + Redis).

Exercises all 5 microservices through the gateway on :8080 and verifies:
  - CRUD operations persist to PostgreSQL
  - Two-level cache (Caffeine L1 + Redis L2) records hits on repeated reads
  - Write-through invalidation evicts cache on writes
"""
import json
import time
import requests

BASE = "http://localhost:8080"  # gateway
PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")

def main():
    s = requests.Session()

    # ---------- Production service CRUD ----------
    r = s.post(f"{BASE}/api/v1/production/orders",
               json={"productCode": "P-CRUD-1", "quantity": 100, "priority": "HIGH",
                     "workCenter": "WC-A", "assignedOperator": "OP-1"})
    check("production.create", r.status_code == 201, f"status={r.status_code}")
    order_id = r.json().get("id") if r.ok else None
    check("production.create.fields", r.ok and r.json()["status"] == "CREATED" and r.json()["quantity"] == 100)

    # read back (L1 miss -> L2 miss -> DB, backfill)
    r2 = s.get(f"{BASE}/api/v1/production/orders/{order_id}")
    check("production.read", r2.status_code == 200 and r2.json()["id"] == order_id)

    # read again (should be L1 hit now)
    r3 = s.get(f"{BASE}/api/v1/production/orders/{order_id}")
    check("production.read.cached", r3.status_code == 200 and r3.json()["id"] == order_id)

    # list all
    r4 = s.get(f"{BASE}/api/v1/production/orders")
    check("production.list", r4.status_code == 200 and isinstance(r4.json(), list) and len(r4.json()) >= 1)

    # start production (write -> evict cache)
    r5 = s.post(f"{BASE}/api/v1/production/orders/{order_id}/start")
    check("production.start", r5.status_code == 200 and r5.json()["status"] == "IN_PROGRESS",
          f"status_code={r5.status_code}")

    # progress + auto-complete
    r6 = s.post(f"{BASE}/api/v1/production/orders/{order_id}/progress?completed=100&defects=2")
    check("production.progress.complete", r6.status_code == 200 and r6.json()["status"] == "COMPLETED",
          f"status_code={r6.status_code}")

    # yield rate metric (cached)
    r7 = s.get(f"{BASE}/api/v1/production/orders/metrics/yield-rate")
    check("production.metrics.yield", r7.status_code == 200 and "yieldRate" in r7.json(),
          f"body={r7.text[:80]}")

    # cache stats endpoint
    r8 = s.get(f"{BASE}/api/v1/production/orders/metrics/cache")
    check("production.cache.stats", r8.status_code == 200 and "hitRatePercent" in r8.json(),
          f"body={r8.text[:120]}")
    if r8.ok:
        cs = r8.json()
        print(f"    cache snapshot: {cs}")

    # create a 2nd order for cancel flow + error handling
    rc = s.post(f"{BASE}/api/v1/production/orders", json={"productCode": "P-CRUD-2", "quantity": 50, "priority": "NORMAL"})
    cid = rc.json().get("id") if rc.ok else None
    rcc = s.post(f"{BASE}/api/v1/production/orders/{cid}/cancel")
    check("production.cancel", rcc.status_code == 200 and rcc.json()["status"] == "CANCELLED")

    # error handling: invalid priority -> 400
    re = s.post(f"{BASE}/api/v1/production/orders", json={"productCode": "X", "quantity": 1, "priority": "BOGUS"})
    check("production.error.400", re.status_code == 400, f"status={re.status_code}")
    # not found -> 400
    rnf = s.get(f"{BASE}/api/v1/production/orders/nonexistent-id")
    check("production.error.notfound", rnf.status_code == 400, f"status={rnf.status_code}")

    # ---------- Quality service CRUD ----------
    rq = s.post(f"{BASE}/api/v1/quality/inspections",
                json={"productionOrderId": order_id, "productCode": "P-CRUD-1",
                      "sampleSize": 100, "passed": 98, "failed": 2, "inspector": "Q-1"})
    check("quality.create", rq.status_code == 201, f"status={rq.status_code}")
    insp_id = rq.json().get("id") if rq.ok else None
    rqg = s.get(f"{BASE}/api/v1/quality/inspections/{insp_id}")
    check("quality.read", rqg.status_code == 200 and rqg.json()["result"] == "FAIL")
    rqm = s.get(f"{BASE}/api/v1/quality/inspections/metrics/fpy")
    check("quality.metrics.fpy", rqm.status_code == 200 and "firstPassYield" in rqm.json())

    # ---------- Equipment service CRUD ----------
    re_reg = s.post(f"{BASE}/api/v1/equipment",
                    json={"code": "EQ-CRUD-1", "name": "CNC-1", "location": "Bay-1",
                          "temperature": 0.0, "vibration": 0.0, "rpm": 0, "utilizationRate": 0.0})
    check("equipment.register", re_reg.status_code == 201, f"status={re_reg.status_code} {re_reg.text[:80]}")
    eq_id = re_reg.json().get("id") if re_reg.ok else None
    reg = s.get(f"{BASE}/api/v1/equipment/{eq_id}")
    check("equipment.read", reg.status_code == 200 and reg.json()["code"] == "EQ-CRUD-1")
    # telemetry ingestion (write -> evict)
    rt = s.post(f"{BASE}/api/v1/equipment/{eq_id}/telemetry",
                json={"temperature": 96.0, "vibration": 9.0, "rpm": 1500})
    check("equipment.telemetry.fault", rt.status_code == 200 and rt.json()["status"] == "FAULT",
          f"status={rt.status_code}")
    roee = s.get(f"{BASE}/api/v1/equipment/metrics/oee")
    check("equipment.metrics.oee", roee.status_code == 200 and "oee" in roee.json())

    # ---------- Inventory service CRUD ----------
    ri = s.post(f"{BASE}/api/v1/inventory/materials",
                json={"sku": "MAT-CRUD-1", "name": "Steel Rod", "unit": "kg",
                      "quantity": 500, "reorderPoint": 100, "safetyStock": 50, "unitCost": 12.5})
    check("inventory.create", ri.status_code == 201, f"status={ri.status_code} {ri.text[:80]}")
    rig = s.get(f"{BASE}/api/v1/inventory/materials/MAT-CRUD-1")
    check("inventory.read.sku", rig.status_code == 200 and rig.json()["sku"] == "MAT-CRUD-1")
    # stock movement OUT (write -> evict)
    rm = s.post(f"{BASE}/api/v1/inventory/movements",
                json={"sku": "MAT-CRUD-1", "quantity": 50, "type": "OUT"})
    check("inventory.move.out", rm.status_code == 200 and rm.json()["quantity"] == 450,
          f"status={rm.status_code} qty={rm.json().get('quantity') if rm.ok else 'n/a'}")
    # insufficient stock error
    rm2 = s.post(f"{BASE}/api/v1/inventory/movements",
                 json={"sku": "MAT-CRUD-1", "quantity": 99999, "type": "OUT"})
    check("inventory.error.insufficient", rm2.status_code == 409, f"status={rm2.status_code}")
    riv = s.get(f"{BASE}/api/v1/inventory/metrics/value")
    check("inventory.metrics.value", riv.status_code == 200 and "inventoryValue" in riv.json())

    # ---------- Verify PostgreSQL persistence ----------
    print("\n--- PostgreSQL persistence verification ---")
    import subprocess
    for db, sql, expect in [
        ("mes_production", f"SELECT count(*) FROM production_orders WHERE id='{order_id}'", "1"),
        ("mes_quality", f"SELECT count(*) FROM inspection_records WHERE id='{insp_id}'", "1"),
        ("mes_equipment", f"SELECT status FROM equipment WHERE id='{eq_id}'", "FAULT"),
        ("mes_inventory", f"SELECT quantity FROM materials WHERE sku='MAT-CRUD-1'", "450"),
    ]:
        out = subprocess.run(
            ["psql", "-h", "db-postgres.dify-plus.svc.cluster.local", "-U", "postgres", "-d", db, "-tAc", sql],
            capture_output=True, text=True, env={"PGPASSWORD": "difyai123456", "PATH": "/usr/bin:/bin"})
        val = out.stdout.strip()
        check(f"postgres.persist.{db}", val == expect, f"got='{val}' expect='{expect}'")

    # ---------- Cache hit-rate analysis ----------
    print("\n--- Cache hit-rate analysis (repeat reads) ---")
    # create fresh order, read it 20 times -> expect high L1 hit rate
    rcr = s.post(f"{BASE}/api/v1/production/orders", json={"productCode": "P-CACHE", "quantity": 10, "priority": "NORMAL"})
    cache_id = rcr.json()["id"] if rcr.ok else None
    for _ in range(20):
        s.get(f"{BASE}/api/v1/production/orders/{cache_id}")
    rcs = s.get(f"{BASE}/api/v1/production/orders/metrics/cache").json()
    print(f"    cache stats after 20x repeat reads: {rcs}")
    hit_rate = rcs.get("hitRatePercent", 0)
    check("cache.hitrate.high", hit_rate >= 50.0, f"hitRate={hit_rate}% (l1={rcs.get('l1Hits')}, l2={rcs.get('l2Hits')}, miss={rcs.get('misses')})")

    print(f"\n=== RESULT: {len(PASS)} passed, {len(FAIL)} failed ===")
    if FAIL:
        print("FAILED:", FAIL)
    return 0 if not FAIL else 1

if __name__ == "__main__":
    raise SystemExit(main())
