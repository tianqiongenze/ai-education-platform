import sys, json, base64
d = json.load(sys.stdin)
for k, v in d.items():
    val = base64.b64decode(v).decode()
    print(f"{k}={val[:60]}")