#!/c/Python314/python
"""Query Prometheus via Grafana ds/query API and print results simply."""
import sys, json, urllib.request, urllib.error, base64

GRAFANA = "http://10.167.2.175:30082"   # master node NodePort (restored after calico-node fix)
USER = "admin"
PASS = "uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb"

def query(expr, instant=True, minutes_range=360):
    body = {
        "queries":[{"refId":"A","datasource":{"uid":"prometheus","type":"prometheus"},
                    "expr":expr,"instant":instant,"range":not instant}],
        "from":"now-%dm"%minutes_range,"to":"now"
    }
    req = urllib.request.Request(GRAFANA+"/api/ds/query",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json",
                 "Authorization":"Basic "+base64.b64encode((USER+":"+PASS).encode()).decode()},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": "HTTP "+str(e.code), "body": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}

def extract(d):
    """Return list of (labels_dict, value) for instant query.
    Frame structure:
      schema.fields = [{name:'Time',...},{name:'up', labels:{...},...}]
      data.values = [[ts],[val]]   parallel arrays for one series
    Multiple frames = multiple series.
    """
    out = []
    frames = d.get("results",{}).get("A",{}).get("frames",[])
    for f in frames:
        schema_fields = f.get("schema",{}).get("fields",[])
        # find value field (the one that is not Time)
        labels = {}
        val_name = None
        for fld in schema_fields:
            nm = fld.get("name")
            if nm == "Time":
                continue
            val_name = nm
            labels = fld.get("labels",{}) or {}
            break
        data_vals = f.get("data",{}).get("values",[])
        # data_vals is like [[ts1,ts2,...],[v1,v2,...]]  or [[ts],[v]]
        if len(data_vals) >= 2:
            values_list = data_vals[1]
            # take last value (most recent)
            if values_list:
                v = values_list[-1]
                out.append((dict(labels), v))
    return out

def extract_range(d):
    """Return list of (labels_dict, [ (ts,val), ... ]) for range query."""
    out = []
    frames = d.get("results",{}).get("A",{}).get("frames",[])
    for f in frames:
        schema_fields = f.get("schema",{}).get("fields",[])
        labels = {}
        for fld in schema_fields:
            nm = fld.get("name")
            if nm != "Time":
                labels = fld.get("labels",{}) or {}
                break
        data_vals = f.get("data",{}).get("values",[])
        if len(data_vals) >= 2:
            ts_list = data_vals[0]
            v_list = data_vals[1]
            pts = list(zip(ts_list, v_list))
            out.append((dict(labels), pts))
    return out

if __name__ == "__main__":
    expr = sys.argv[1] if len(sys.argv)>1 else "up"
    mode = sys.argv[2] if len(sys.argv)>2 else "instant"
    d = query(expr, instant=(mode=="instant"))
    if "error" in d:
        print("ERROR:", d["error"]); print(d.get("body","")); sys.exit(1)
    rows = extract(d) if mode=="instant" else extract_range(d)
    print(f"Query: {expr}")
    print(f"Results: {len(rows)} series")
    from collections import defaultdict
    by_job = defaultdict(list)
    for labels,val in rows:
        by_job[labels.get("job","?")].append((labels,val))
    for job in sorted(by_job):
        print(f"  job={job} ({len(by_job[job])} series)")
        for labels,val in by_job[job][:6]:
            inst = labels.get("instance","")
            extra = {k:v for k,v in labels.items() if k not in ("job","instance","__name__","endpoint","metrics_path")}
            print(f"     inst={inst:32} val={val} {extra}")
