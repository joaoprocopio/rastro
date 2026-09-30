"""Argon2id password hashing, with the parameters from the OWASP Password Storage Cheat Sheet."""

import logging
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

log = logging.getLogger(__name__)

# OWASP's minimum for Argon2id: 19 MiB of memory, 2 iterations, 1 degree of
# parallelism. The memory cost applies per hash, so 40 threads that hash at once
# hold about 760 MiB.
_hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1)

# Computed at import, so the first sign-in for an unknown email does not pay
# for one extra hash.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError:
        return False
    except InvalidHashError:
        log.error("Stored password hash is not a valid Argon2 hash.")
        return False


def needs_rehash(password_hash: str) -> bool:
    """Tell whether the hash uses other parameters than `_hasher`."""
    return _hasher.check_needs_rehash(password_hash)


def burn_verification(password: str) -> None:
    """Spend the time of one verification against a hash that never matches.

    A sign-in for an unknown email calls this, so it takes as long as a sign-in
    with a wrong password and the response time does not reveal which emails
    exist.
    """
    verify_password(_DUMMY_HASH, password)
