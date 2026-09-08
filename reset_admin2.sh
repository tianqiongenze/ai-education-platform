#!/bin/bash
# Check the actual column names
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "\d accounts" 2>&1 | head -30

echo "==="
# Check current password field
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "SELECT email, password, password_salt FROM accounts WHERE email='myuwei@126.com';" 2>&1