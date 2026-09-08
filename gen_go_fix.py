#!/usr/bin/env python3
"""Fix Go project: remove gRPC/grpc deps (air-gapped), fix http package name."""
import os, textwrap
BASE = "/tmp/p3-go/industrial-gateway"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# ---- go.mod: drop grpc/grpc, drop genproto. Keep gin + prometheus. ----
# We regenerate go.sum via go mod download for only the needed deps.
w("go.mod", r'''
module industrial-gateway

go 1.21

require (
	github.com/gin-gonic/gin v1.10.0
	github.com/prometheus/client_golang v1.19.1
)
''')

# Remove the stale go.sum so go recomputes it from scratch for our reduced dep set.
sum_path = os.path.join(BASE, "go.sum")
if os.path.exists(sum_path):
    os.remove(sum_path)
    print("removed stale go.sum")

# ---- FIX: http package name. router.go currently 'package httpadapter'.
# Rename to 'package http' (matching directory). Tests already 'package http'.
router_path = os.path.join(BASE, "internal/adapter/http/router.go")
with open(router_path) as f:
    src = f.read()
src = src.replace("package httpadapter", "package http", 1)
# Also update the comment that says grpcadapter import is fine
with open(router_path, "w") as f:
    f.write(src)
print("router.go -> package http")

# ---- FIX main.go: it imports grpcadapter, which imports usecase only (no grpc pkg).
# That import is fine (the grpc package itself isn't imported). Keep as-is.
# But we must ensure grpc/service.go doesn't import google.golang.org/grpc.
grpc_path = os.path.join(BASE, "internal/adapter/grpc/service.go")
with open(grpc_path) as f:
    gsrc = f.read()
# It already only imports context, errors, fmt, time, domain, usecase. Good.
assert "google.golang.org/grpc" not in gsrc, "grpc import still present!"
print("grpc/service.go confirmed grpc-free")

# ---- FIX: metrics package name. The dir is internal/adapter/metrics but
# package is 'metrics' — fine. Confirm.
met_path = os.path.join(BASE, "internal/adapter/metrics/metrics.go")
with open(met_path) as f:
    msrc = f.read()
assert "package metrics" in msrc
print("metrics package ok")

print("go fixes applied: reduced go.mod, package http, grpc-free")
