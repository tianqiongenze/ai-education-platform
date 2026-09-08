import sys, json
pvs = json.load(sys.stdin)
for pv in pvs.get("items", []):
    name = pv["metadata"]["name"]
    pvc = pv.get("spec", {}).get("claimRef", {}).get("name", "?")
    ns = pv.get("spec", {}).get("claimRef", {}).get("namespace", "?")
    node = "unknown"
    affinity = pv.get("spec", {}).get("nodeAffinity", {})
    reqs = affinity.get("required", {})
    terms = reqs.get("nodeSelectorTerms", [])
    for t in terms:
        for expr in t.get("matchExpressions", []):
            if expr.get("key") == "kubernetes.io/hostname":
                node = expr.get("values", ["?"])[0]
    path = "?"
    if pv.get("spec", {}).get("local", {}).get("path"):
        path = pv["spec"]["local"]["path"]
    print("%-35s %-30s %-15s %s" % (name, ns+"/"+pvc, node, path))
