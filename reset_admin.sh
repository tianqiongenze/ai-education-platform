#!/bin/bash
# Reset admin password in Dify
# Dify uses Flask-Security / werkzeug for password hashing
# We need to generate a new password hash and update the database

# First, let's check the password hash format
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "SELECT email, password_hash FROM accounts WHERE email='myuwei@126.com';"

echo "---"
echo "Now resetting password..."
# Generate a new password hash using Python in the dify-api pod
NEW_HASH=$(kubectl exec -n dify deploy/dify-api -- python3 -c "
from werkzeug.security import generate_password_hash
print(generate_password_hash('admin123'))
" 2>/dev/null)

echo "New hash: $NEW_HASH"

# Update the password in the database
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "UPDATE accounts SET password_hash='$NEW_HASH' WHERE email='myuwei@126.com';"

echo "Password reset to: admin123"