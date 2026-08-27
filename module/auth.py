import hashlib
import os
import hmac

def generate_salt() -> str:
    return os.urandom(16).hex()

def hash_password(password: str, salt:str) -> str:
    password_bytes = password.encode("utf-8")
    salt_bytes = bytes.fromhex(salt)
    hashed = hashlib.pbkdf2_hmac("sha256", password_bytes, salt_bytes, 100000)
    return hashed.hex()

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    password_hash = hash_password(password, salt)
    return hmac.compare_digest(password_hash, expected_hash)