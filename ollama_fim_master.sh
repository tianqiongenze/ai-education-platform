#!/bin/bash
# Test qwen2.5-coder FIM latency from master via ollama-worker NodePort
OLLAMA="http://10.167.2.175:30086"

echo "=== LOADAVG on master ==="
uptime

echo ""
echo "=== FIM TEST 1: fibonacci ==="
START=$(date +%s%N)
RESP=$(curl -s --max-time 60 "$OLLAMA/api/generate" -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "<|fim_begin|>def fibonacci(n):\n    if n <= 1:\n        return n\n    return<|fim_hole|>\n\n# Test\nprint(fibonacci(10))<|fim_end|>",
  "raw": true,
  "stream": false,
  "options": {"num_predict": 32, "temperature": 0.2, "stop": ["\n\n"]}
}')
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo "Response: $(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','').strip())" 2>/dev/null || echo "$RESP" | head -c 300)"
echo "ELAPSED_MS=$ELAPSED"
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'eval_count={d.get(\"eval_count\",\"?\")} eval_duration={d.get(\"eval_duration\",0)/1e9:.2f}s')" 2>/dev/null

echo ""
echo "=== FIM TEST 2: pandas ==="
START2=$(date +%s%N)
RESP2=$(curl -s --max-time 60 "$OLLAMA/api/generate" -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "<|fim_begin|>import pandas as pd\n\ndef load_csv(path):\n    df = pd.read_csv(path)\n    return df.<|fim_hole|>\n\ndf = load_csv(\"data.csv\")<|fim_end|>",
  "raw": true,
  "stream": false,
  "options": {"num_predict": 24, "temperature": 0.2, "stop": ["\n"]}
}')
END2=$(date +%s%N)
ELAPSED2=$(( (END2 - START2) / 1000000 ))
echo "Response: $(echo "$RESP2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','').strip())" 2>/dev/null || echo "$RESP2" | head -c 300)"
echo "ELAPSED_MS2=$ELAPSED2"

echo ""
echo "=== FIM TEST 3: very short (10 tokens) ==="
START3=$(date +%s%N)
RESP3=$(curl -s --max-time 60 "$OLLAMA/api/generate" -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "<|fim_begin|>def calc(x, y):\n    result = x +<|fim_hole|>\n    return result<|fim_end|>",
  "raw": true,
  "stream": false,
  "options": {"num_predict": 8, "temperature": 0.1, "stop": ["\n"]}
}')
END3=$(date +%s%N)
ELAPSED3=$(( (END3 - START3) / 1000000 ))
echo "Response: $(echo "$RESP3" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','').strip())" 2>/dev/null || echo "$RESP3" | head -c 300)"
echo "ELAPSED_MS3=$ELAPSED3"
