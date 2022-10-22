## -- IMPORTING -- ##

import base64

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto import Random

## -- VARIABLES -- ##

BLOCK_SIZE = 16

## -- FUNCTIONS -- ##


def pad(s: str) -> str:
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)


def unpad(s: bytes) -> str:
    return s[: -ord(s[len(s) - 1 :])].decode()


def get_private_key(password: str) -> bytes:
    salt = b"salt moment"
    kdf = PBKDF2(password=password, salt=salt, dkLen=64)

    return kdf[:32]


def encrypt(string: str, password: str) -> bytes:
    key = get_private_key(password)
    string = pad(string)

    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)

    return base64.b64encode(iv + cipher.encrypt(string.encode()))


def decrypt(encrypted_string: str, password: str) -> str:
    key = get_private_key(password)
    encrypted_string = base64.b64decode(encrypted_string)

    iv = encrypted_string[:16]
    cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)

    return unpad(cipher.decrypt(encrypted_string[16:]))
