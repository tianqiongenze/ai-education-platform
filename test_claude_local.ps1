$env:ANTHROPIC_API_KEY="sk-ai-platform-master"
$env:ANTHROPIC_BASE_URL="http://10.167.2.175:30083"
$env:CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="1"
$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"

Write-Output "=== Testing Claude Code with local models ==="
Write-Output "Base URL: $env:ANTHROPIC_BASE_URL"
Write-Output ""

$models = @(
    "qwen2.5:7b",
    "qwen2.5:14b", 
    "qwen2.5:32b",
    "qwen2.5:72b",
    "deepseek-r1:14b",
    "deepseek-r1:32b",
    "qwen2.5-coder:14b"
)

foreach ($model in $models) {
    Write-Output "--- Testing model: $model ---"
    try {
        $result = claude --print --model $model "Say hello in one short sentence." --bare --no-session-persistence 2>&1
        Write-Output "Result: $result"
    } catch {
        Write-Output "Error: $_"
    }
    Write-Output ""
}

Write-Output "=== Test complete ==="