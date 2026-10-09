"""Password hashing built on Werkzeug's PBKDF2-SHA256.

Used by both services so a hash created by one is verifiable by the other.
Usess standard-library-backed PBKDF2 — no native crypto builds needed.
"""

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(plain: str) -> str:
    return generate_password_hash(plain, method="pbkdf2:sha256", salt_length=16)


def verify_password(plain: str, hashed: str) -> bool:
    return check_password_hash(hashed, plain)