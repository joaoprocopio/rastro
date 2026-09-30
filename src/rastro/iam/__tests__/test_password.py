from argon2 import PasswordHasher

from rastro.iam import password


def test_hash_is_argon2id_with_the_owasp_parameters() -> None:
    password_hash = password.hash_password("correct horse")

    assert password_hash.startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_verify_accepts_the_right_password() -> None:
    password_hash = password.hash_password("correct horse")

    assert password.verify_password(password_hash, "correct horse")


def test_verify_rejects_a_wrong_password() -> None:
    password_hash = password.hash_password("correct horse")

    assert not password.verify_password(password_hash, "battery staple")


def test_verify_rejects_a_hash_that_is_not_argon2() -> None:
    assert not password.verify_password("pbkdf2_sha256$1$salt$hash", "anything")


def test_needs_rehash_flags_other_parameters() -> None:
    outdated = PasswordHasher(time_cost=1, memory_cost=8 * 1024).hash("pw")

    assert password.needs_rehash(outdated)
    assert not password.needs_rehash(password.hash_password("pw"))
