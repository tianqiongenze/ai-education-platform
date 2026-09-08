import base64, binascii, hashlib

# Existing password from DB
existing_pw_b64 = "ZWY1ZTAzMThmZTA3OGEyOWNmZTRiNGIxMjQ4YWFkYTk0NTlhOTIyY2ZlMjMyMzFiNGNiN2QyZWZiNmJlNTRhOA=="
existing_salt_b64 = "6gmfcmGAXsQ0jTQMjm/c4g=="

# Decode
pw_bytes = base64.b64decode(existing_pw_b64)
salt_bytes = base64.b64decode(existing_salt_b64)

print(f"Password bytes ({len(pw_bytes)}): {pw_bytes[:40]}")
print(f"Salt bytes ({len(salt_bytes)}): {salt_bytes.hex()}")

# The password field is 64 bytes - this is hex-encoded (128 hex chars = 64 bytes)
# Let's decode as hex
try:
    pw_hex = pw_bytes.decode('ascii')
    print(f"\nPassword as hex string: {pw_hex}")
    print(f"Hex string length: {len(pw_hex)}")
    
    # Now this hex string is the pbkdf2 output
    pw_hash = binascii.unhexlify(pw_hex)
    print(f"Actual hash bytes: {pw_hash.hex()}")
    print(f"Hash length: {len(pw_hash)} bytes")
    
    # Try to verify with known passwords
    for test_pw in ["difyai123456", "admin123", "Admin123!", "password", "123456", "admin"]:
        dk = hashlib.pbkdf2_hmac('sha256', test_pw.encode('utf-8'), salt_bytes, 10000)
        if dk == pw_hash:
            print(f"\n*** FOUND PASSWORD: {test_pw} ***")
            break
        else:
            print(f"  {test_pw}: no match")
except Exception as e:
    print(f"Error: {e}")
    # Maybe it's not hex
    print(f"Raw bytes: {pw_bytes.hex()}")