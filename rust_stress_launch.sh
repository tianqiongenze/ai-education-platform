cd /home/jovyan/work/security-audit
cat > /tmp/stress_mixed_patch.py <<'PY'
# quick patch: add "mixed" scenario branch to stress runner
p = '/tmp/stress_rust.py'
src = open(p).read()
old = '''            elif self.scenario == "listheavy":'''
new = '''            elif self.scenario == "mixed":
                pick = random.random()
                if pick < 0.4:
                    code, _ = request("POST", "/audits", {"target": f"mx-{random.randint(1,100)}", "auditor": "stress"})
                elif pick < 0.8:
                    code, _ = request("GET", "/audits")
                else:
                    c, b = request("POST", "/audits", {"target": f"mxc-{random.randint(1,100)}", "auditor": "stress"})
                    if c == 201:
                        sid = json.loads(b)["id"]
                        c2, _ = request("POST", f"/audits/{sid}/finalize")
                        code = 200 if c2 == 200 else 500
                    else:
                        code = 500
            elif self.scenario == "listheavy":'''
assert old in src
src = src.replace(old, new)
open(p, 'w').write(src)
print("mixed branch added")
PY
python3 /tmp/stress_mixed_patch.py
echo "=== launch stress in background ==="
nohup python3 /tmp/stress_rust.py > /tmp/stress_rust_out.txt 2>&1 &
echo "STRESS_STARTED pid=$!"
