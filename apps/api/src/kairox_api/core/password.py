import hashlib

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_argon2 = PasswordHasher()
_ARGON2_PREFIX = "$argon2id$"


def hash_password(password: str) -> str:
    return _argon2.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    if hashed.startswith(_ARGON2_PREFIX):
        try:
            return _argon2.verify(hashed, plain)
        except VerifyMismatchError:
            return False
    # bcrypt path: legacy migration only — new passwords always use argon2id
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
