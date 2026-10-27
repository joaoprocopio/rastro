import pytest

from rastro.auth.domain.ports import Clock, PasswordHasher
from rastro.auth.presentation import dependencies


@pytest.fixture
def password_hasher() -> PasswordHasher:
    # The app hashes with argon2, so the User of a view test holds an argon2 hash.
    return dependencies.password_hasher()


@pytest.fixture
def clock() -> Clock:
    # The view tests compare expires_at with the wall clock.
    return dependencies.clock()
