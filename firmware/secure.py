# secure.py — node-side authenticated encryption (AES-128-CBC + HMAC-SHA256),
# producing a Fernet-compatible token that server/secure.py decrypts.
# MicroPython built-ins only. Key derives from config.SECRET_PASSPHRASE.

import os
import time
import json
import struct
import hashlib
import ubinascii
from ucryptolib import aes
import config

_KEY = hashlib.sha256(config.SECRET_PASSPHRASE).digest()
_SIGN_KEY = _KEY[:16]
_ENC_KEY = _KEY[16:]
_MODE_CBC = 2


def _hmac_sha256(key, msg):
    block = 64
    if len(key) > block:
        key = hashlib.sha256(key).digest()
    key = key + b"\x00" * (block - len(key))
    o_pad = bytes((b ^ 0x5c) for b in key)
    i_pad = bytes((b ^ 0x36) for b in key)
    return hashlib.sha256(o_pad + hashlib.sha256(i_pad + msg).digest()).digest()


def _pkcs7(data):
    pad = 16 - (len(data) % 16)
    return data + bytes([pad]) * pad


def _b64url(raw):
    return ubinascii.b2a_base64(raw).rstrip(b"\n").replace(b"+", b"-").replace(b"/", b"_")


def encrypt_reading(reading):
    iv = os.urandom(16)
    ct = aes(_ENC_KEY, _MODE_CBC, iv).encrypt(_pkcs7(json.dumps(reading).encode("utf-8")))
    body = b"\x80" + struct.pack(">Q", int(time.time())) + iv + ct
    return _b64url(body + _hmac_sha256(_SIGN_KEY, body)).decode("ascii")
