import base64, hashlib, os

# Check the existing hash
existing_password = "ZWY1ZTAzMThmZTA3OGEyOWNmZTRiNGIxMjQ4YWFkYTk0NTlhOTIyY2ZlMjMyMzFiNGNiN2QyZWZiNmJlNTRhOA=="
existing_salt = "6gmfcmGAXsQ0jTQMjm/c4g=="

# Decode
pw_bytes = base64.b64decode(existing_password)
salt_bytes = base64.b64decode(existing_salt)

print(f"Password bytes length: {len(pw_bytes)}")
print(f"Salt bytes length: {len(salt_bytes)}")
print(f"Password hex: {pw_bytes.hex()}")
print(f"Salt hex: {salt_bytes.hex()}")

# Try different hashing methods
# Method 1: sha256(password + salt)
test_pw = "difyai123456"
h1 = hashlib.sha256(test_pw.encode() + salt_bytes).digest()
print(f"\nsha256(pw+salt): {base64.b64encode(h1).decode()}")
print(f"Match: {base64.b64encode(h1).decode() == existing_password}")

# Method 2: sha256(salt + password)
h2 = hashlib.sha256(salt_bytes + test_pw.encode()).digest()
print(f"sha256(salt+pw): {base64.b64encode(h2).decode()}")
print(f"Match: {base64.b64encode(h2).decode() == existing_password}")

# Method 3: double sha256
h3 = hashlib.sha256(hashlib.sha256(test_pw.encode() + salt_bytes).digest()).digest()
print(f"double sha256: {base64.b64encode(h3).decode()}")
print(f"Match: {base64.b64encode(h3).decode() == existing_password}")

# Method 4: pbkdf2
import hashlib
h4 = hashlib.pbkdf2_hmac('sha256', test_pw.encode(), salt_bytes, 100000)
print(f"pbkdf2: {base64.b64encode(h4).decode()}")
print(f"Match: {base64.b64encode(h4).decode() == existing_password}")

# Method 5: Try with the password_salt as the password
h5 = hashlib.sha256(salt_bytes + salt_bytes).digest()
print(f"\nsha256(salt+salt): {base64.b64encode(h5).decode()}")
print(f"Match: {base64.b64encode(h5).decode() == existing_password}")

# Method 6: The password field might be encrypted, not hashed
# Try AES decrypt with SECRET_KEY
print("\n--- Trying AES decrypt ---")
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
secret = b"REDACTED_KEY"
key = secret[:32]
try:
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = unpad(cipher.decrypt(pw_bytes), 16)
    print(f"Decrypted: {decrypted.decode()}")
except Exception as e:
    print(f"AES decrypt failed: {e}")