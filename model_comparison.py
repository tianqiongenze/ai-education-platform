#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-Model Comparison Test"""
import requests, json, time, socket, urllib3
urllib3.disable_warnings()

LITELLM = "http://10.167.2.176:30083"
LITELLM_KEY = "sk-ai-platform-master"

# Redis8 check
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(("10.167.2.175", 30095))
    s.close()
    print("Redis8 NodePort 30095: ACCESSIBLE")
except:
    print("Redis8 NodePort 30095: NOT ACCESSIBLE")

models = ["qwen2.5-coder:7b", "glm4:9b", "qwen3:4b", "qwen3:8b", "yi:6b", "llama3.1:8b"]
scenarios = [
    ("Industrial IoT", "What is Industrial Internet? Answer in one sentence."),
    ("PLC Programming", "What is a PLC? Answer in one sentence."),
    ("Python Coding", "Write a Python function to sort a list. Just the code."),
    ("Database", "What is a database transaction? Answer in one sentence."),
    ("Networking", "What is the difference between TCP and UDP? Answer briefly."),
    ("AI/ML", "What is overfitting in machine learning? Answer in one sentence."),
]

print("")
print("=" * 70)
print("Multi-Model Comparison")
print("=" * 70)
print("%-25s %-22s %6s %7s %s" % ("Model", "Scenario", "Time", "Tokens", "Status"))
print("-" * 70)

all_results = []
for model in models:
    for scenario, question in scenarios:
        try:
            start = time.time()
            r = requests.post(LITELLM + "/v1/chat/completions",
                headers={"Authorization": "Bearer " + LITELLM_KEY, "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": question}], "max_tokens": 100},
                timeout=180)
            elapsed = time.time() - start
            if r.status_code == 200:
                answer = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = r.json().get("usage", {}).get("total_tokens", 0)
                print("%-25s %-22s %5.1fs %7d PASS  %s" % (model, scenario, elapsed, tokens, answer[:40]))
                all_results.append({"model": model, "scenario": scenario, "time": elapsed, "tokens": tokens, "answer": answer[:80], "status": "PASS"})
            else:
                print("%-25s %-22s %5.1fs       FAIL(%d)" % (model, scenario, elapsed, r.status_code))
                all_results.append({"model": model, "scenario": scenario, "time": elapsed, "tokens": 0, "answer": "", "status": "FAIL"})
        except Exception as e:
            print("%-25s %-22s       ERR %s" % (model, scenario, str(e)[:30]))
            all_results.append({"model": model, "scenario": scenario, "time": 0, "tokens": 0, "answer": "", "status": "FAIL"})
    time.sleep(2)

# Embedding test
try:
    r = requests.post(LITELLM + "/v1/embeddings",
        headers={"Authorization": "Bearer " + LITELLM_KEY, "Content-Type": "application/json"},
        json={"model": "bge-m3", "input": "test"}, timeout=30)
    emb = r.json().get("data", [{}])[0].get("embedding", []) if r.status_code == 200 else []
    print("\nEmbedding bge-m3: dim=%d status=%d" % (len(emb), r.status_code))
except Exception as e:
    print("\nEmbedding: ERR %s" % str(e)[:50])

# Average by model
print("\n" + "=" * 70)
print("Average Response Time by Model")
print("=" * 70)
for model in models:
    model_tests = [r for r in all_results if r["model"] == model and r["status"] == "PASS"]
    if model_tests:
        avg_time = sum(r["time"] for r in model_tests) / len(model_tests)
        avg_tokens = sum(r["tokens"] for r in model_tests) / len(model_tests)
        print("  %-25s avg=%4.1fs  tokens=%4.0f  pass=%d/%d" % (model, avg_time, avg_tokens, len(model_tests), len(scenarios)))
    else:
        print("  %-25s ALL FAILED" % model)

# Best model per scenario
print("\n" + "=" * 70)
print("Best Model per Scenario (fastest)")
print("=" * 70)
for scenario, _ in scenarios:
    scenario_tests = [r for r in all_results if r["scenario"] == scenario and r["status"] == "PASS"]
    if scenario_tests:
        best = min(scenario_tests, key=lambda x: x["time"])
        print("  %-22s -> %-25s (%.1fs, %d tokens)" % (scenario, best["model"], best["time"], best["tokens"]))
    else:
        print("  %-22s -> ALL FAILED" % scenario)

print("\nDone. Total tests: %d, Passed: %d" % (len(all_results), sum(1 for r in all_results if r["status"] == "PASS")))
