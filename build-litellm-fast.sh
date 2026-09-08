#!/bin/bash
set -e
echo "[$(date)] Starting litellm fast build with Tsinghua mirror..."
docker build -f litellm-fast.Dockerfile \
  -t ai-platform/litellm:custom \
  --no-cache \
  . 2>&1 | tee /root/litellm-fast-build.log
echo "[$(date)] Build complete!"
echo "[$(date)] Verifying websockets..."
docker run --rm ai-platform/litellm:custom python3 -c "import websockets; print('websockets OK:', websockets.__version__)"
echo "[$(date)] Image size:"
docker images ai-platform/litellm:custom --format '{{.Size}}'
