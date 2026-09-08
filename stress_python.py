import requests, time, concurrent.futures, statistics, json, sys

BASE = 'http://localhost:8000'
results = {}

def hit_get(path):
    try:
        r = requests.get(f'{BASE}{path}', timeout=30)
        return r.status_code, r.elapsed.total_seconds()
    except Exception:
        return 0, 0.0

def hit_post(path, payload):
    try:
        r = requests.post(f'{BASE}{path}', json=payload, timeout=30)
        return r.status_code, r.elapsed.total_seconds()
    except Exception:
        return 0, 0.0

def tele(i):
    return {'device_id': f'dev-{i%50:03d}', 'metric': 'temperature', 'value': 60 + (i % 30)}

def run(name, fn, n, workers):
    fn(0)  # warmup
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        out = list(ex.map(fn, range(n)))
    elapsed = time.time() - start
    ok = sum(1 for s, _ in out if s in (200, 201))
    lat = sorted(t for s, t in out if s in (200, 201)) or [0]
    r = {
        'total': n, 'success': ok, 'error_rate': round(100*(n-ok)/n, 2),
        'rps': round(n/elapsed, 1),
        'p50_ms': round(statistics.median(lat)*1000, 1),
        'p95_ms': round(lat[int(len(lat)*0.95)]*1000, 1),
        'p99_ms': round(lat[int(len(lat)*0.99)]*1000, 1),
        'avg_ms': round(sum(lat)/len(lat)*1000, 1),
        'elapsed_s': round(elapsed, 1),
    }
    results[name] = r
    print(f'{name}:', json.dumps(r), flush=True)

# Health check first
try:
    h = requests.get(f'{BASE}/api/v1/health', timeout=5)
    print(f'Health: {h.status_code} {h.text[:100]}')
    if h.status_code != 200:
        sys.exit(1)
except Exception as e:
    print(f'Health check failed: {e}')
    sys.exit(1)

# 1. Read-heavy: analytics with required query params (L1 cache expected)
run('analytics_read_c1000',
    lambda i: hit_get(f'/api/v1/analytics?device_id=dev-{i%50:03d}&metric=temperature&window=60'),
    1000, 100)

# 2. Write-heavy: telemetry ingest (DB write to CRDB via WRITE engine)
run('telemetry_write_c500',
    lambda i: hit_post('/api/v1/telemetry', tele(i)),
    500, 50)

# 3. Status read (single device, cache)
run('status_read_c500',
    lambda i: hit_get('/api/v1/status/dev-001'),
    500, 50)

# 4. Mixed workload: 70% read / 30% write, 1000 ops, 100 workers
def mixed(i):
    if i % 10 < 7:
        return hit_get(f'/api/v1/analytics?device_id=dev-{i%50:03d}&metric=temperature&window=60')
    return hit_post('/api/v1/telemetry', tele(i))
run('mixed_70_30_c1000', mixed, 1000, 100)

# Cache stats after load
try:
    cs = requests.get(f'{BASE}/api/v1/cache-stats', timeout=5).json()
    print('cache_stats:', json.dumps(cs))
    results['cache_stats_final'] = cs
except Exception as e:
    print('cache_stats failed:', e)

# Spike test: 200 concurrent burst
run('spike_c200_500req',
    lambda i: hit_get(f'/api/v1/analytics?device_id=dev-{i%50:03d}&metric=temperature&window=60'),
    500, 200)

with open('/tmp/python_stress_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('SAVED /tmp/python_stress_results.json')
