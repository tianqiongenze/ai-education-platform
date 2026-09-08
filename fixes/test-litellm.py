import urllib.request
resp = urllib.request.urlopen('http://localhost:4000/health/readiness')
print(resp.read().decode())
resp2 = urllib.request.urlopen('http://localhost:4000/v1/models')
print(resp2.read().decode())