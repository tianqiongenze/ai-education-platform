#!/bin/sh
# Test qwen2.5-coder FIM (fill-in-the-middle) completion latency
echo "=== LOADAVG ==="
cat /proc/loadavg
echo ""
echo "=== OLLAMA PS ==="
ollama ps 2>&1
echo ""
echo "=== FIM TEST: generate (non-stream) ==="
# qwen2.5-coder supports FIM via the /api/generate endpoint with raw prompt
# Using the FIM template format: <|fim_begin|>prefix<|fim_hole|>suffix<|fim_end|>
START=$(date +%s%N)
curl -s --max-time 30 http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "<|fim_begin|>def fibonacci(n):\n    if n <= 1:\n        return n\n    return<|fim_hole|>\n\n# Test\nprint(fibonacci(10))<|fim_end|>",
  "raw": true,
  "stream": false,
  "options": {"num_predict": 32, "temperature": 0.2, "stop": ["\n\n"]}
}' 2>&1
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo ""
echo "ELAPSED_MS=$ELAPSED"
echo ""
echo "=== FIM TEST 2: simpler ==="
START2=$(date +%s%N)
curl -s --max-time 30 http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "<|fim_begin|>import pandas as pd\n\ndef load_csv(path):\n    df = pd.read_csv(path)\n    return df.<|fim_hole|>\n\ndf = load_csv("data.csv")<|fim_end|>",
  "raw": true,
  "stream": false,
  "options": {"num_predict": 24, "temperature": 0.2, "stop": ["\n"]}
}' 2>&1
END2=$(date +%s%N)
ELAPSED2=$(( (END2 - START2) / 1000000 ))
echo ""
echo "ELAPSED_MS2=$ELAPSED2"
echo ""
echo "=== LOADAVG AFTER ==="
cat /proc/loadavg
