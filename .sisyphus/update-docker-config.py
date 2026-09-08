import json
cfg = json.load(open("/etc/docker/daemon.json"))
cfg["data-root"] = "/home/docker-data"
json.dump(cfg, open("/etc/docker/daemon.json", "w"), indent=2)
print("Updated daemon.json:")
print(json.dumps(cfg, indent=2))
