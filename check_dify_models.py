import urllib.request, json, base64, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
data = json.dumps({'email': 'myuwei@126.com', 'password': base64.b64encode('difyai123456'.encode()).decode()}).encode()
req = urllib.request.Request('http://localhost:5001/console/api/login', data=data, headers={'Content-Type': 'application/json'})
resp = opener.open(req)
token = json.load(resp).get('access_token', '')
csrf = None
for c in cj:
    if c.name == 'csrf_token':
        csrf = c.value
        break
h = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrf}
pid = 'langgenius/openai_api_compatible/openai_api_compatible'
req = urllib.request.Request('http://localhost:5001/console/api/workspaces/current/model-providers/' + pid + '/models', headers=h)
resp = opener.open(req)
data = json.load(resp)
print('Total models:', len(data.get('data', [])))
for m in data.get('data', []):
    print('  %-35s status=%-20s type=%s' % (m['model'], m.get('status','?'), m.get('model_type','?')))