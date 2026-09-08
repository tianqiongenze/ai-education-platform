#!/bin/bash
# Generate proper Dify password hash using the EXACT same algorithm as Dify's password.py
NEW_PASSWORD="difyai123456"

# Use the dify-api pod to generate the hash
RESULT=$(kubectl exec -n dify deploy/dify-api -- python3 -c "
import hashlib, binascii, base64, os

password = '$NEW_PASSWORD'
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
# hash_password returns hexlify(dk) which is bytes
password_hex = binascii.hexlify(dk)  # This is bytes
# The stored password is base64 of the hex bytes
password_b64 = base64.b64encode(password_hex).decode()
salt_b64 = base64.b64encode(salt).decode()
print(f'{password_b64}|{salt_b64}')
" 2>/dev/null)

PASSWORD_B64=$(echo "$RESULT" | cut -d'|' -f1)
SALT_B64=$(echo "$RESULT" | cut -d'|' -f2)

echo "Password base64: $PASSWORD_B64"
echo "Salt base64: $SALT_B64"

# Update the database
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "UPDATE accounts SET password='$PASSWORD_B64', password_salt='$SALT_B64' WHERE email='myuwei@126.com';"

echo "Password set to: $NEW_PASSWORD"

# Verify by trying to login
echo "---"
echo "Testing login..."
python3 -c "
import urllib.request, json, base64

email = 'myuwei@126.com'
password = '$NEW_PASSWORD'
encoded = base64.b64encode(password.encode()).decode()

data = json.dumps({'email': email, 'password': encoded}).encode()
req = urllib.request.Request(
    'http://10.167.2.176:30501/console/api/login',
    data=data,
    headers={'Content-Type': 'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print('Login SUCCESS!')
    print(f'Token: {result.get(\"access_token\", \"\")[:60]}...')
except urllib.error.HTTPError as e:
    print(f'Failed: {e.code} - {e.read().decode()[:200]}')
"