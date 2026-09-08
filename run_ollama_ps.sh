#!/bin/sh
ssh -o StrictHostKeyChecking=no root@10.167.2.175 "kubectl cp /tmp/ollama_ps.sh ai-platform/ollama-worker-58b7886cdd-2zqzw:/tmp/ollama_ps.sh"
ssh -o StrictHostKeyChecking=no root@10.167.2.175 "kubectl exec -n ai-platform ollama-worker-58b7886cdd-2zqzw -- sh /tmp/ollama_ps.sh"
