cd /home/jovyan/work/security-audit
echo "=== 1. add redis dep ==="
grep -q '^redis' Cargo.toml || sed -i 's|^postgres = .*|&\nredis = "0.25"|' Cargo.toml
grep -n "^redis\|^postgres" Cargo.toml

echo "=== 2. create cache module (L1 in-process + L2 Redis, write-through) ==="
cat > src/infrastructure/cache.rs <<'RUST'
//! Two-level cache adapter:
//!   L1  in-process TTL map (hot path, 30 s)
//!   L2  Redis on the platform cluster (300 s) — redis.dify-plus.svc.cluster.local:6379
//!   L3  CockroachDB (source of truth)
//! Read path: L1 -> L2 -> repo; Write path: repo first, then fill L1+L2
//! (write-through); delete invalidates both levels.
use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, Instant};
use redis::Commands;

const L1_TTL: Duration = Duration::from_secs(30);
const L2_TTL: u64 = 300;

struct Entry {
    value: String,
    expires: Instant,
}

pub struct TwoLevelCache {
    l1: Mutex<HashMap<String, Entry>>,
    conn: Mutex<Option<redis::Client>>,
    pub l1_hits: std::sync::atomic::AtomicUsize,
    pub l2_hits: std::sync::atomic::AtomicUsize,
    pub misses: std::sync::atomic::AtomicUsize,
    pub l2_writes: std::sync::atomic::AtomicUsize,
}

fn redis_url() -> String {
    std::env::var("AUDIT_REDIS_URL").unwrap_or_else(|_| {
        "redis://:difyai123456@redis.dify-plus.svc.cluster.local:6379/5".into()
    })
}

impl TwoLevelCache {
    pub fn new() -> Self {
        let client = redis::Client::open(redis_url()).ok();
        // eager probe so connection errors surface at boot, but non-fatal
        if let Some(c) = &client {
            if let Ok(mut cc) = c.get_connection() {
                let _: Result<(), _> = cc.set::<_, _, ()>("audit:cache:boot", "ok");
            }
        }
        Self {
            l1: Mutex::new(HashMap::new()),
            conn: Mutex::new(client),
            l1_hits: std::sync::atomic::AtomicUsize::new(0),
            l2_hits: std::sync::atomic::AtomicUsize::new(0),
            misses: std::sync::atomic::AtomicUsize::new(0),
            l2_writes: std::sync::atomic::AtomicUsize::new(0),
        }
    }

    /// Read-through: L1 -> L2 -> None (caller falls back to CRDB and calls put).
    pub fn get(&self, key: &str) -> Option<String> {
        // L1
        if let Ok(map) = self.l1.lock() {
            if let Some(e) = map.get(key) {
                if e.expires > Instant::now() {
                    self.l1_hits.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                    return Some(e.value.clone());
                }
            }
        }
        // L2 (Redis)
        if let Ok(guard) = self.conn.lock() {
            if let Some(client) = guard.as_ref() {
                if let Ok(mut cc) = client.get_connection() {
                    let v: Result<Option<String>, _> = cc.get(format!("audit:cache:{key}"));
                    if let Ok(Some(val)) = v {
                        self.l2_hits.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                        if let Ok(mut map) = self.l1.lock() {
                            map.insert(key.to_string(),
                                Entry { value: val.clone(), expires: Instant::now() + L1_TTL });
                        }
                        return Some(val);
                    }
                }
            }
        }
        self.misses.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        None
    }

    /// Write-through: fill L1 + L2 after a CRDB write/read.
    pub fn put(&self, key: &str, value: &str) {
        if let Ok(mut map) = self.l1.lock() {
            map.insert(key.to_string(),
                Entry { value: value.to_string(), expires: Instant::now() + L1_TTL });
        }
        if let Ok(guard) = self.conn.lock() {
            if let Some(client) = guard.as_ref() {
                if let Ok(mut cc) = client.get_connection() {
                    let _: Result<(), _> = cc.set_ex(format!("audit:cache:{key}"), value, L2_TTL);
                    self.l2_writes.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                }
            }
        }
    }

    /// Invalidate both levels (called on writes).
    pub fn invalidate(&self, key: &str) {
        if let Ok(guard) = self.conn.lock() {
            if let Some(client) = guard.as_ref() {
                if let Ok(mut cc) = client.get_connection() {
                    let _: Result<(), _> = cc.del(format!("audit:cache:{key}"));
                }
            }
        }
        if let Ok(mut map) = self.l1.lock() {
            map.remove(key);
        }
    }

    pub fn stats(&self) -> String {
        format!(
            "{{\"l1_hits\":{},\"l2_hits\":{},\"misses\":{},\"l2_writes\":{}}}",
            self.l1_hits.load(std::sync::atomic::Ordering::Relaxed),
            self.l2_hits.load(std::sync::atomic::Ordering::Relaxed),
            self.misses.load(std::sync::atomic::Ordering::Relaxed),
            self.l2_writes.load(std::sync::atomic::Ordering::Relaxed))
    }
}
RUST
grep -q 'pub mod cache;' src/infrastructure/mod.rs || echo 'pub mod cache;' >> src/infrastructure/mod.rs
cat src/infrastructure/mod.rs
touch /tmp/rust_cache_step1_done
