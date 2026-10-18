from typing import Protocol

from rastro.iam.values import HashedPassword, RawPassword


class PasswordHasher(Protocol):
    def __call__(self, *, password: RawPassword) -> HashedPassword: ...
