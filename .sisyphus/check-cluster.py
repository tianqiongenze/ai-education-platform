import sys, json, ssl, urllib.request

token = "token-5vvlk:p7mnx7jjcnh8hm6n8mfdfkd5l4vhfc4n9fzht8kjxkfl24d2dc6dd9"

req = urllib.request.Request("https://localhost/v3/clusters")
req.add_header("Authorization", "Bearer " + token)
resp = urllib.request.urlopen(req, context=ssl._create_unverified_context())
data = json.load(resp)

for c in data['data']:
    print("  Cluster: " + c['name'])
    print("    ID: " + c['id'])
    print("    State: " + c.get('state', 'N/A'))
    print("    Transitioning: " + c.get('transitioning', 'N/A'))
    msg = c.get('transitioningMessage', '') or ''
    print("    Message: " + msg[:200])
    print("    Nodes: " + str(c.get('nodeCount', 0)))
    print("    Driver: " + c.get('driver', 'N/A'))
    version = c.get('version', {}) or {}
    print("    Version: " + version.get('gitVersion', 'N/A'))
    print()
