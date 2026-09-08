import sys, json

d = json.load(sys.stdin)

# Print all fields
for k, v in sorted(d.items()):
    if isinstance(v, str) and len(v) > 200:
        print(f"  {k}: {v[:200]}...")
    else:
        print(f"  {k}: {v}")
