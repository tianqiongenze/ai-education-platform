#!/bin/bash
set -ex
python3 - <<'EOF'
import json, subprocess
def run(*a): return subprocess.run(a, capture_output=True, text=True)
d = json.loads(run("kubectl","-n","openedx","get","deploy","mfe","-o","json").stdout)
t = d["spec"]["template"]["spec"]
c = t["containers"][0]
c.setdefault("volumeMounts",[]).append({"name":"mfe-caddy","mountPath":"/etc/caddy/Caddyfile","subPath":"Caddyfile","readOnly":True})
t.setdefault("volumes",[]).append({"name":"mfe-caddy","configMap":{"name":"mfe-caddy"}})
open("/tmp/mfe-deploy-new.json","w").write(json.dumps(d))
print("patched json written")
EOF
kubectl -n openedx apply -f /tmp/mfe-deploy-new.json
kubectl -n openedx rollout status deploy/mfe --timeout=300s
sleep 5
kubectl exec -n openedx deploy/mfe -- sh -c 'for p in / /learning /authn /account /profile; do code=$(wget -S -q -O /dev/null http://localhost:80$p 2>&1 | head -1 | grep -o "200\|404\|30[0-9]"); echo "$p -> $code"; done'
echo MFEVOLFIXDONE
