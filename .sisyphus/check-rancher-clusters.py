import sys, json
d = json.load(sys.stdin)
for c in d["data"]:
    name = c["name"]
    state = c["state"]
    transitioning = c["transitioning"]
    agent = "connected" if c.get("agentConnected", False) else "disconnected"
    print("%s: %s (transitioning=%s, agent=%s)" % (name, state, transitioning, agent))
