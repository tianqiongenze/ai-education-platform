cd /home/jovyan/work/security-audit
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
grep -E "^error" /tmp/rust_build.log | head -8
grep -B2 -A8 "^error\[" /tmp/rust_build.log | head -50
tail -2 /tmp/rust_build.log
