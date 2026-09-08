import requests, json
requests.packages.urllib3.disable_warnings()

# Login with current password
r = requests.post('https://localhost/v3-public/localProviders/local?action=login',
    json={'username':'admin','password':'hExZh_vOpwI2l4vI295R'}, verify=False)
data = r.json()
token = data['token']
user_id = data['userId']
print(f"Logged in as user: {user_id}")

# Change password
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
r = requests.post(f'https://localhost/v3/users/{user_id}?action=setpassword',
    json={'newPassword': 'Rancher@2026'}, headers=headers, verify=False)
print(f"Password change: {r.status_code}")

# Verify new password
r2 = requests.post('https://localhost/v3-public/localProviders/local?action=login',
    json={'username':'admin','password':'Rancher@2026'}, verify=False)
print(f"Verify new password: {r2.status_code}")