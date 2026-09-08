#!/bin/bash
# Generate a proper Dify password hash using the Dify API's own encryption
# Dify uses: encrypt_password(password) which uses SECRET_KEY for AES encryption

kubectl exec -n dify deploy/dify-api -- python3 -c "
from core.helper import encrypter
import base64

# Generate encrypted password
password = 'admin123'
encrypted = encrypter.encrypt(password)
print(f'Encrypted: {encrypted}')

# Also generate salt
salt = encrypter.generate_salt()
print(f'Salt: {salt}')

# Generate the stored password format
stored = encrypter.encrypt_password(password, salt)
print(f'Stored: {stored}')
" 2>/dev/null