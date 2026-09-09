#!/bin/bash
# Fix studio 404: add NodePort 31825 to all LMS/CMS URL settings
set -e
NS=openedx
PORT="31825"
DOMAIN="openedx.10.167.2.175.nip.io"
S_DOMAIN="studio.openedx.10.167.2.175.nip.io"
NEW_ROOT="https://${DOMAIN}:${PORT}"

CM_CONFIG=$(kubectl get cm -n $NS -o name | grep openedx-config | head -1)
CM_CMS_SET=$(kubectl get cm -n $NS -o name | grep openedx-settings-cms | head -1)
CM_LMS_SET=$(kubectl get cm -n $NS -o name | grep openedx-settings-lms | head -1)
echo "CMs: $CM_CONFIG $CM_CMS_SET $CM_LMS_SET"

mkdir -p /tmp/fix404 && cd /tmp/fix404

# --- 1. Patch openedx-config (lms.env.json / cms.env.json) ---
kubectl get $CM_CONFIG -n $NS -o jsonpath="{.data.lms\.env\.json}" > lms.env.json
kubectl get $CM_CONFIG -n $NS -o jsonpath="{.data.cms\.env\.json}" > cms.env.json
python3 - <<EOF
import json
for f in ("lms.env.json", "cms.env.json"):
    with open(f) as fh:
        d = json.load(fh)
    d["LMS_ROOT_URL"] = "${NEW_ROOT}"
    d["SITE_NAME"] = "${S_DOMAIN}:${PORT}" if f == "cms.env.json" else "${DOMAIN}:${PORT}"
    # add CSRF origins for both hosts with port
    origins = [o for o in d.get("CSRF_TRUSTED_ORIGINS", []) if "${PORT}" not in o]
    origins += [
        "https://${DOMAIN}:${PORT}",
        "https://${S_DOMAIN}:${PORT}",
    ]
    d["CSRF_TRUSTED_ORIGINS"] = sorted(set(origins))
    with open(f, "w") as fh:
        json.dump(d, fh)
    print(f, "patched:", d["LMS_ROOT_URL"], d["SITE_NAME"])
EOF
kubectl create configmap $(basename $CM_CONFIG) -n $NS \
  --from-file=lms.env.json=lms.env.json --from-file=cms.env.json=cms.env.json \
  --dry-run=client -o yaml | kubectl replace -f -
echo "config CM patched"

# --- 2. Patch settings overlays (production.py) ---
for pair in "$CM_CMS_SET:cms" "$CM_LMS_SET:lms"; do
  CM="${pair%%:*}"; KIND="${pair##*:}"
  kubectl get $CM -n $NS -o jsonpath="{.data['production\.py']}" > /tmp/fix404/$KIND-production.py || \
  kubectl get $CM -n $NS -o json > /tmp/fix404/$KIND.json
done

python3 - <<EOF
import subprocess, json, re

def patch_production(kind, cm_name):
    # fetch data keys
    raw = subprocess.check_output(
        ["kubectl", "get", "cm", cm_name, "-n", "openedx", "-o", "json"]).decode()
    data = json.loads(raw)["data"]
    newdata = {}
    for key, content in data.items():
        c = content
        # add :31825 to nip.io URLs that lack a port
        c = re.sub(r"(https?://(?:studio\.)?openedx\.10\.167\.2\.175\.nip\.io)(?!:\d)(/|\"|'|$)",
                   r"\1:31825\2", c)
        # force http scheme to https where URL points to our domain
        c = c.replace("http://openedx.10.167.2.175.nip.io:31825", "https://openedx.10.167.2.175.nip.io:31825")
        c = c.replace("http://studio.openedx.10.167.2.175.nip.io:31825", "https://studio.openedx.10.167.2.175.nip.io:31825")
        newdata[key] = c
        open("/tmp/fix404/%s-%s-patched" % (kind, key), "w").write(c)
    with open("/tmp/fix404/%s-cm.json" % kind, "w") as fh:
        json.dump({"apiVersion": "v1", "kind": "ConfigMap",
                   "metadata": {"name": cm_name, "namespace": "openedx"},
                   "data": newdata}, fh)

for kind in ("cms", "lms"):
    cm_name = subprocess.check_output(
        ["bash", "-c",
         "kubectl get cm -n openedx -o name | grep openedx-settings-%s | head -1" % kind]
    ).decode().strip().replace("configmap/", "")
    print("patching", kind, cm_name)
    patch_production(kind, cm_name)
EOF

kubectl replace -f /tmp/fix404/cms-cm.json
kubectl replace -f /tmp/fix404/lms-cm.json
echo "settings CMs patched"

# --- 3. Restart deployments ---
kubectl rollout restart deploy/lms deploy/cms -n $NS
echo "RESTART_TRIGGERED"
