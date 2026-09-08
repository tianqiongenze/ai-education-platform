#!/bin/bash
set -e

echo "========================================"
echo "Building open-webui custom image"
echo "Time: $(date)"
echo "========================================"

cd /root

# Check if base image is available (from DaoCloud mirror or ghcr.io)
BASE_EXISTS=false
docker images ghcr.m.daocloud.io/open-webui/open-webui --format '{{.ID}}' 2>/dev/null | grep -q . && BASE_EXISTS=true
docker images ghcr.io/open-webui/open-webui --format '{{.ID}}' 2>/dev/null | grep -q . && BASE_EXISTS=true

if [ "$BASE_EXISTS" = false ]; then
    echo "ERROR: No open-webui base image found!"
    docker images | grep open-webui
    exit 1
fi

echo "Using base image from:"
docker images | grep open-webui

# Tag the mirror image as ghcr.io so the Dockerfile works
if docker images ghcr.m.daocloud.io/open-webui/open-webui --format '{{.ID}}' 2>/dev/null | grep -q .; then
    echo "Tagging mirror image as ghcr.io..."
    IMAGE_ID=$(docker images ghcr.m.daocloud.io/open-webui/open-webui -q)
    docker tag $IMAGE_ID ghcr.io/open-webui/open-webui:main 2>/dev/null || true
fi

# Build custom image
echo ""
echo "Building open-webui:fixed6..."
docker build -f open-webui-fix6.Dockerfile -t ai-platform/open-webui:fixed6 . 2>&1 | tee /root/openwebui-build.log

echo ""
echo "Build exit code: $?"
echo "========================================"
echo "Image info:"
docker images ai-platform/open-webui:fixed6 --format '{{.ID}} {{.Size}} {{.CreatedAt}}'

echo ""
echo "Build completed!"
echo "Time: $(date)"
