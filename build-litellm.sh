#!/bin/bash
set -e

echo "========================================"
echo "Building litellm image with [proxy] extras"
echo "Time: $(date)"
echo "========================================"

cd /root

# Build the Docker image
docker build -f litellm.Dockerfile -t ai-platform/litellm:custom . 2>&1 | tee /root/litellm-rebuild.log

echo ""
echo "Build exit code: $?"
echo "========================================"
echo "Image info:"
docker images ai-platform/litellm:custom --format '{{.ID}} {{.Size}} {{.CreatedAt}}'
echo "========================================"

# Test if websockets is available
echo ""
echo "Testing websockets import..."
docker run --rm ai-platform/litellm:custom python3 -c "import websockets; print('websockets OK:', websockets.__version__)"

echo ""
echo "Testing litellm import..."
docker run --rm ai-platform/litellm:custom python3 -c "import litellm; print('litellm OK:', litellm.__version__)"

echo ""
echo "Build completed successfully!"
echo "Time: $(date)"
