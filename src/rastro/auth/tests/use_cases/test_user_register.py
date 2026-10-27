import pytest

from rastro.auth.application.dtos import UserRegisterInput
from rastro.auth.application.use_cases import user_register
from rastro.auth.domain.aggregates import User
from rastro.auth.domain.errors import EmailInUseError
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    RawPassword,
)
from rastro.auth.tests.fakes import FakePasswordHasher, FakeUserRepository


async def test_it_stores_a_new_user_with_the_next_id_and_the_hash(
    users: FakeUserRepository, ana: User, password_hasher: FakePasswordHasher
) -> None:
    await user_register(
        UserRegisterInput(
            email=Email("ada@x.com"),
            display_name=DisplayName("Ada"),
            password=RawPassword("supersecret"),
        ),
        users=users,
        password_hasher=password_hasher,
    )

    assert users.users == {
        1: ana,
        2: User(
            id=2,
            email=Email("ada@x.com"),
            display_name=DisplayName("Ada"),
            hashed_password=HashedPassword("fake$supersecret"),
        ),
    }


async def test_it_raises_email_in_use_for_an_email_that_a_user_holds(
    users: FakeUserRepository, ana: User, password_hasher: FakePasswordHasher
) -> None:
    with pytest.raises(EmailInUseError):
        await user_register(
            UserRegisterInput(
                email=Email("Ana@X.com"),
                display_name=DisplayName("Other Ana"),
                password=RawPassword("supersecret"),
            ),
            users=users,
            password_hasher=password_hasher,
        )

    assert users.users == {1: ana}
