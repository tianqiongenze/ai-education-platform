#!/bin/bash
set -e

echo "========================================"
echo "Installing Continue.dev extension on code-server"
echo "Time: $(date)"
echo "========================================"

VSIX_FILE="/root/continue.vsix"

if [ ! -f "$VSIX_FILE" ]; then
    echo "ERROR: VSIX file not found at $VSIX_FILE"
    exit 1
fi

FILE_SIZE=$(stat -c%s "$VSIX_FILE" 2>/dev/null || stat -f%z "$VSIX_FILE" 2>/dev/null)
echo "VSIX file size: $FILE_SIZE bytes"

if [ "$FILE_SIZE" -lt 50000000 ]; then
    echo "WARNING: File seems incomplete (< 50MB). The download may still be in progress."
    echo "Current size: $FILE_SIZE bytes"
    echo "Full VSIX is typically 80-100 MB"
fi

# Get pod name
POD_NAME=$(kubectl get pods -n ai-platform -l app=code-server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    echo "ERROR: No code-server pod found"
    kubectl get pods -n ai-platform -l app=code-server
    exit 1
fi

echo "Using pod: $POD_NAME"

# Copy VSIX to pod
echo "Copying VSIX to pod..."
kubectl cp "$VSIX_FILE" "ai-platform/$POD_NAME:/tmp/continue.vsix" 2>&1

# Install extension
echo "Installing extension..."
kubectl exec -n ai-platform "$POD_NAME" -- code-server --install-extension /tmp/continue.vsix 2>&1

echo ""
echo "Verifying installation..."
kubectl exec -n ai-platform "$POD_NAME" -- code-server --list-extensions | grep -i continue || echo "Extension not found in list"

echo ""
echo "========================================"
echo "Continue.dev installation completed!"
echo "Time: $(date)"
