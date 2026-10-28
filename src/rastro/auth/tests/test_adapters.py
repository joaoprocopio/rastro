import argon2
from pydantic import SecretStr

from rastro.auth.domain.ports import PasswordCheck
from rastro.auth.domain.value_objects import HashedPassword, RawPassword
from rastro.auth.infrastructure.adapters import Argon2PasswordHasher

PASSWORD = RawPassword(SecretStr("password"))


def test_argon2_accepts_the_password_of_a_current_hash() -> None:
    hasher = Argon2PasswordHasher()

    check = hasher.verify(password=PASSWORD, hashed=hasher.hash(password=PASSWORD))

    assert check == PasswordCheck(is_correct=True, new_hash=None)


def test_argon2_rejects_a_wrong_password() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash(password=RawPassword(SecretStr("otherpassword")))

    assert hasher.verify(password=PASSWORD, hashed=hashed) == PasswordCheck(
        is_correct=False, new_hash=None
    )


def test_argon2_rejects_any_password_with_no_hash() -> None:
    assert Argon2PasswordHasher().verify(
        password=PASSWORD, hashed=None
    ) == PasswordCheck(is_correct=False, new_hash=None)


def test_argon2_returns_a_current_hash_for_an_outdated_one() -> None:
    hasher = Argon2PasswordHasher()
    outdated = HashedPassword(
        argon2.PasswordHasher(time_cost=1).hash(PASSWORD.root.get_secret_value())
    )

    check = hasher.verify(password=PASSWORD, hashed=outdated)

    assert check.is_correct
    assert check.new_hash is not None
    assert hasher.verify(password=PASSWORD, hashed=check.new_hash) == PasswordCheck(
        is_correct=True, new_hash=None
    )
