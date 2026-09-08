#!/bin/bash
# Generate proper Dify password using pbkdf2_hmac
NEW_PASSWORD="Admin123!"

# Use the dify-api pod to generate the hash using the exact same algorithm
RESULT=$(kubectl exec -n dify deploy/dify-api -- python3 -c "
import hashlib, binascii, base64, os

password = '$NEW_PASSWORD'
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
password_hex = binascii.hexlify(dk)
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

# Verify
echo "---"
echo "Verifying..."
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "SELECT email, password, password_salt FROM accounts WHERE email='myuwei@126.com';"