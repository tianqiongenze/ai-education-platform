import json, urllib.request

def get(path):
    try:
        with urllib.request.urlopen("http://localhost:8000" + path, timeout=10) as r:
            body = r.read().decode()[:400]
            return r.status, body
    except Exception as e:
        code = getattr(e, "code", None)
        try:
            body = e.read().decode()[:400]
        except Exception:
            body = str(e)
        return code, body

status, body = get("/api/v1/analytics?window=60")
print("ANALYTICS", status, body)
print()
try:
    with urllib.request.urlopen("http://localhost:8000/openapi.json", timeout=10) as r:
        d = json.load(r)
        for p, v in d["paths"].items():
            for m in v:
                print("ROUTE", m.upper(), p)
except Exception as e:
    print("OPENAPI FAIL", e)
