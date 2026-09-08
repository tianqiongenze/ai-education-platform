#!/bin/bash
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c "SELECT id, email, name, last_login_at FROM accounts ORDER BY created_at LIMIT 5;"