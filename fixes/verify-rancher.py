import requests
requests.packages.urllib3.disable_warnings()
r = requests.post('https://localhost/v3-public/localProviders/local?action=login',
    json={'username':'admin','password':'Rancher@2026'}, verify=False)
print('Status:', r.status_code, '- SUCCESS' if r.status_code == 201 else '- FAILED')