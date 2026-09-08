#!/usr/bin/env python3
"""Stress test for security-audit (Rust/actix-web) on :8080.
Scenarios: create, list, finalize-chain, mixed, spike."""
import threading, urllib.request, urllib.error, json, time, random, sys

B = "http://127.0.0.1:8080/api/v1"
results = {}

def request(method, path, body=None):
    url = B + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data: req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception:
        return 0, b""

class Runner(threading.Thread):
    def __init__(self, scenario, dur, stop):
        super().__init__(daemon=True)
        self.scenario, self.dur, self.stop = scenario, dur, stop
        self.lat = []; self.ok = 0; self.total = 0

    def run(self):
        end = time.time() + self.dur
        while time.time() < end and not self.stop.is_set():
            t0 = time.time()
            code = 0
            if self.scenario == "create":
                code, _ = request("POST", "/audits", {"target": f"stress-target-{random.randint(1,100)}", "auditor": "stress"})
            elif self.scenario == "list":
                code, _ = request("GET", "/audits")
            elif self.scenario == "fullchain":
                c, b = request("POST", "/audits", {"target": f"fc-{random.randint(1,1000)}", "auditor": "stress"})
                if c == 201:
                    sid = json.loads(b)["id"]
                    c2, _ = request("POST", f"/audits/{sid}/scan", {"fingerprints": ["hmi-default-creds", "modbus-plaintext"]})
                    c3, _ = request("POST", f"/audits/{sid}/finalize")
                    code = 200 if (c2 == 200 and c3 == 200) else 500
                else:
                    code = 500
            elif self.scenario == "listheavy":
                for _ in range(3):
                    code, _ = request("GET", "/audits")
            dt = (time.time() - t0) * 1000
            self.lat.append(dt); self.total += 1
            if 200 <= code < 400: self.ok += 1

def bench(name, scenario, dur, nthreads):
    stop = threading.Event()
    runners = [Runner(scenario, dur, stop) for _ in range(nthreads)]
    for r in runners: r.start()
    time.sleep(dur + 1)
    stop.set()
    lat = []; ok = 0; total = 0
    for r in runners:
        lat.extend(r.lat); ok += r.ok; total += r.total
    lat.sort()
    n = len(lat) or 1
    stats = {
        "scenario": name,
        "rps": round(total / dur, 1),
        "p50_ms": round(lat[n // 2], 1) if lat else 0,
        "p95_ms": round(lat[int(n * 0.95)], 1) if lat else 0,
        "p99_ms": round(lat[int(n * 0.99)], 1) if lat else 0,
        "avg_ms": round(sum(lat) / n, 1) if lat else 0,
        "success_pct": round(100.0 * ok / total, 2) if total else 0,
        "total": total,
    }
    results[name] = stats
    print(json.dumps(stats))

print("=== Rust security-audit stress test ===")
bench("create", "create", 30, 16)
bench("list", "list", 30, 24)
bench("fullchain", "fullchain", 30, 16)
bench("mixed", "mixed", 30, 16)
# spike: 64 threads for 10s
bench("spike", "create", 10, 64)

with open("/tmp/stress_rust.json", "w") as f:
    json.dump(results, f, indent=2)
print("SAVED /tmp/stress_rust.json")
