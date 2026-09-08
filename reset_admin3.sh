#!/bin/bash
# Generate new password hash using Dify's own password hashing
NEW_PASSWORD="admin123"

# Use the dify-api pod to generate the hash
RESULT=$(kubectl exec -n dify deploy/dify-api -- python3 -c "
import base64, hashlib, os

password = '$NEW_PASSWORD'
salt = base64.b64encode(os.urandom(16)).decode()
# Dify uses: base64(sha256(password + salt))
combined = password + salt
hash_val = hashlib.sha256(combined.encode()).digest()
password_enc = base64.b64encode(hash_val).decode()
print(f'{password_enc}|{salt}')
" 2>/dev/null)

PASSWORD_ENC=$(echo "$RESULT" | cut -d'|' -f1)
SALT=$(echo "$RESULT" | cut -d'|' -f2)

echo "New password_enc: $PASSWORD_ENC"
echo "New salt: $SALT"

# Update the database
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "UPDATE accounts SET password='$PASSWORD_ENC', password_salt='$SALT' WHERE email='myuwei@126.com';"

echo "Password reset to: $NEW_PASSWORD"