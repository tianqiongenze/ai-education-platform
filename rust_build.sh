cd /home/jovyan/work/security-audit
export CARGO_HOME=/home/jovyan/.cargo
export PATH=$CARGO_HOME/bin:$PATH
sed -i 's|^postgres = "0.19"|postgres = { version = "0.19", features = ["with-chrono-0_4"] }|' Cargo.toml
grep -n "^postgres" Cargo.toml
pkill -f audit-server 2>/dev/null; sleep 1
cargo build --release --bin audit-server > /tmp/rust_build.log 2>&1
echo "BUILD_RC=$?"
tail -5 /tmp/rust_build.log
