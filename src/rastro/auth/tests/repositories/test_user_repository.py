import pytest

from rastro.auth.domain.aggregates import User
from rastro.auth.domain.errors import EmailInUseError
from rastro.auth.domain.ports import UserRepository
from rastro.auth.domain.value_objects import DisplayName, Email, HashedPassword
from rastro.common.domain.value_objects import Id


async def test_get_by_id_and_get_by_email_read_back_every_field_that_add_wrote(
    users: UserRepository, read_users: UserRepository, ana: User
) -> None:

    await users.add(ana)

    assert await read_users.get_by_id(ana.id) == ana
    assert await read_users.get_by_email(ana.email) == ana


async def test_get_by_id_and_get_by_email_answer_none_for_an_unknown_user(
    users: UserRepository,
) -> None:
    assert await users.get_by_id(Id(1)) is None
    assert await users.get_by_email(Email("nobody@x.com")) is None


async def test_two_next_id_calls_return_two_different_ids(
    users: UserRepository,
) -> None:
    first, second = await users.next_id(), await users.next_id()

    assert isinstance(first, Id)
    assert first != second


async def test_a_second_add_with_the_same_email_raises_email_in_use(
    users: UserRepository, ana: User
) -> None:
    await users.add(ana)
    other = User(
        id=await users.next_id(),
        email=Email("ana@x.com"),
        display_name=DisplayName("Other"),
        hashed_password=HashedPassword("fake$other"),
    )

    with pytest.raises(EmailInUseError):
        await users.add(other)


async def test_an_update_to_the_email_of_another_user_raises_email_in_use(
    users: UserRepository, ana: User
) -> None:
    await users.add(ana)
    other = User(
        id=await users.next_id(),
        email=Email("other@x.com"),
        display_name=DisplayName("Other"),
        hashed_password=HashedPassword("fake$other"),
    )
    await users.add(other)
    other.email = Email("ana@x.com")

    with pytest.raises(EmailInUseError):
        await users.update(other)


async def test_update_writes_every_field_of_the_user(
    users: UserRepository, read_users: UserRepository, ana: User
) -> None:
    await users.add(ana)
    ana.email = Email("ana@y.com")
    ana.display_name = DisplayName("Ana L.")
    ana.hashed_password = HashedPassword("fake$rehashed")

    await users.update(ana)

    assert await read_users.get_by_id(ana.id) == ana


async def test_update_of_a_missing_user_raises_lookup_error_and_adds_no_user(
    users: UserRepository, read_users: UserRepository, ana: User
) -> None:

    with pytest.raises(LookupError, match=f"with the id {ana.id.root}\\."):
        await users.update(ana)

    assert await read_users.get_by_id(ana.id) is None
    assert await read_users.get_by_email(ana.email) is None


async def test_a_field_assigned_with_no_update_keeps_its_stored_value(
    users: UserRepository, read_users: UserRepository, ana: User
) -> None:
    await users.add(ana)
    ana.display_name = DisplayName("Added")
    read = await read_users.get_by_id(ana.id)
    assert read is not None
    read.display_name = DisplayName("Read")

    stored = await read_users.get_by_id(ana.id)

    assert stored is not None
    assert stored.display_name == DisplayName("Ana")
