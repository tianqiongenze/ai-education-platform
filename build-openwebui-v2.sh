#!/bin/bash
set -e

echo "========================================"
echo "Building open-webui custom image (v2 - simplified)"
echo "Time: $(date)"
echo "========================================"

cd /root

# Verify base image exists
echo "Using base image:"
docker images | grep open-webui | grep main

# Build custom image with simplified Dockerfile
echo ""
echo "Building ai-platform/open-webui:fixed6..."
docker build -f open-webui-fix7.Dockerfile -t ai-platform/open-webui:fixed6 .

echo ""
echo "Build exit code: $?"
echo "========================================"
echo "Image info:"
docker images ai-platform/open-webui:fixed6 --format '{{.ID}} {{.Size}} {{.CreatedAt}}'

echo ""
echo "Build completed!"
echo "Time: $(date)"
