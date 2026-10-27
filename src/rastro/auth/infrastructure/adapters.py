import secrets
from datetime import UTC, datetime

import argon2

from rastro.auth.domain.value_objects import HashedPassword, RawPassword


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = argon2.PasswordHasher()
        self._fixed_hash = HashedPassword.model_validate(
            self._hasher.hash(secrets.token_urlsafe())
        )

    @property
    def fixed_hash(self) -> HashedPassword:
        return self._fixed_hash

    def hash(self, *, password: RawPassword) -> HashedPassword:
        return HashedPassword.model_validate(self._hasher.hash(password.root))

    def verify(self, *, password: RawPassword, hashed: HashedPassword) -> bool:
        # Any other argon2 error means a corrupted hash, so it answers 500.
        try:
            return self._hasher.verify(hashed.root, password.root)
        except argon2.exceptions.VerifyMismatchError:
            return False

    def needs_rehash(self, *, hashed: HashedPassword) -> bool:
        return self._hasher.check_needs_rehash(hashed.root)


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
