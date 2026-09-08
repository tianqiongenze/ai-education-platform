cd /home/jovyan/work/security-audit
sed -i 's|pub trait AuditRepository: CacheStatsProvider: Send + Sync {|pub trait AuditRepository: CacheStatsProvider + Send + Sync {|' src/infrastructure/repository.rs
grep -n "pub trait AuditRepository" src/infrastructure/repository.rs
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -6
tail -2 /tmp/rust_build.log
