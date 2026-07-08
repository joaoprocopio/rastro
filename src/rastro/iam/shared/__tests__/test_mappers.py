from rastro.iam.domain.value_objects import DisplayName, Email, HashedPassword
from rastro.iam.models import IdentityModel
from rastro.iam.shared.mappers import (
    DehydrateIdentityMapper,
    HydrateIdentityMapper,
    OutputIdentityMapper,
    PresentIdentityMapper,
)


def test_hydrate_identity(identity: IdentityModel) -> None:
    hydrated_identity = HydrateIdentityMapper.map(identity)

    assert hydrated_identity.display_name == DisplayName(identity.display_name)
    assert hydrated_identity.email == Email(identity.email)
    assert hydrated_identity.password == HashedPassword(identity.password)
    assert hydrated_identity.date_joined == identity.date_joined
    assert hydrated_identity.last_login == identity.last_login
    assert hydrated_identity.is_active == identity.is_active
    assert hydrated_identity.is_staff == identity.is_staff
    assert hydrated_identity.is_superuser == identity.is_superuser


def test_dehydrate_identity(identity: IdentityModel) -> None:
    dehydrated_identity = DehydrateIdentityMapper.map(
        HydrateIdentityMapper.map(identity)
    )

    assert dehydrated_identity.email == identity.email
    assert dehydrated_identity.display_name == identity.display_name
    assert dehydrated_identity.password == identity.password
    assert dehydrated_identity.date_joined == identity.date_joined
    assert dehydrated_identity.last_login == identity.last_login
    assert dehydrated_identity.is_active == identity.is_active
    assert dehydrated_identity.is_staff == identity.is_staff
    assert dehydrated_identity.is_superuser == identity.is_superuser


def test_present_identity_from_domain(identity: IdentityModel) -> None:
    public_identity = PresentIdentityMapper.map(HydrateIdentityMapper.map(identity))

    assert public_identity.email == Email(identity.email)
    assert public_identity.display_name == DisplayName(identity.display_name)


def test_present_identity_from_output(identity: IdentityModel) -> None:
    public_identity = PresentIdentityMapper.map(
        OutputIdentityMapper.map(HydrateIdentityMapper.map(identity))
    )

    assert public_identity.email == Email(identity.email)
    assert public_identity.display_name == DisplayName(identity.display_name)


def test_output_identity(identity: IdentityModel) -> None:
    output_identity = OutputIdentityMapper.map(HydrateIdentityMapper.map(identity))

    assert output_identity.email == Email(identity.email)
    assert output_identity.display_name == DisplayName(identity.display_name)
    assert output_identity.date_joined == identity.date_joined
    assert output_identity.last_login == identity.last_login
    assert output_identity.is_active == identity.is_active
    assert output_identity.is_staff == identity.is_staff
    assert output_identity.is_superuser == identity.is_superuser
