# secure.py — server-side authenticated encryption (Fernet: AES-128-CBC + HMAC-SHA256).
# Readings travel and rest as ciphertext; only this process decrypts. Tampered or
# forged tokens fail the HMAC check and decrypt to None.

import json
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from credentials import SECRET_PASSPHRASE

_KEY = base64.urlsafe_b64encode(hashlib.sha256(SECRET_PASSPHRASE).digest())
_fernet = Fernet(_KEY)


def encrypt_reading(reading):
    plaintext = json.dumps(reading, separators=(",", ":")).encode("utf-8")
    return _fernet.encrypt(plaintext).decode("ascii")


def decrypt_reading(token):
    if isinstance(token, str):
        token = token.encode("ascii")
    try:
        return json.loads(_fernet.decrypt(token))
    except (InvalidToken, ValueError, UnicodeDecodeError):
        return None
