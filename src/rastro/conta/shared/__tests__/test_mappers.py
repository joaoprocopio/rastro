from rastro.conta.domain.value_objects import DisplayName, Email, HashedPassword
from rastro.conta.models import Conta as ContaModel
from rastro.conta.shared.mappers import (
    DehydrateContaMapper,
    HydrateContaMapper,
    OutputContaMapper,
    PresentContaMapper,
)


def test_hydrate_conta(conta: ContaModel) -> None:
    hydrated_conta = HydrateContaMapper.map(conta)

    assert hydrated_conta.display_name == DisplayName(conta.display_name)
    assert hydrated_conta.email == Email(conta.email)
    assert hydrated_conta.password == HashedPassword(conta.password)
    assert hydrated_conta.date_joined == conta.date_joined
    assert hydrated_conta.last_login == conta.last_login
    assert hydrated_conta.is_active == conta.is_active
    assert hydrated_conta.is_staff == conta.is_staff
    assert hydrated_conta.is_superuser == conta.is_superuser


def test_dehydrate_conta(conta: ContaModel) -> None:
    dehydrated_conta = DehydrateContaMapper.map(HydrateContaMapper.map(conta))

    assert dehydrated_conta.email == conta.email
    assert dehydrated_conta.display_name == conta.display_name
    assert dehydrated_conta.password == conta.password
    assert dehydrated_conta.date_joined == conta.date_joined
    assert dehydrated_conta.last_login == conta.last_login
    assert dehydrated_conta.is_active == conta.is_active
    assert dehydrated_conta.is_staff == conta.is_staff
    assert dehydrated_conta.is_superuser == conta.is_superuser


def test_preset_conta_from_domain(conta: ContaModel) -> None:
    public_conta = PresentContaMapper.map(HydrateContaMapper.map(conta))

    assert public_conta.email == Email(conta.email)
    assert public_conta.display_name == DisplayName(conta.display_name)


def test_preset_conta_from_output(conta: ContaModel) -> None:
    public_conta = PresentContaMapper.map(
        OutputContaMapper.map(HydrateContaMapper.map(conta))
    )

    assert public_conta.email == Email(conta.email)
    assert public_conta.display_name == DisplayName(conta.display_name)


def test_output_conta(conta: ContaModel) -> None:
    output_conta = OutputContaMapper.map(HydrateContaMapper.map(conta))

    assert output_conta.email == Email(conta.email)
    assert output_conta.display_name == DisplayName(conta.display_name)
    assert output_conta.password == HashedPassword(conta.password)
    assert output_conta.date_joined == conta.date_joined
    assert output_conta.last_login == conta.last_login
    assert output_conta.is_active == conta.is_active
    assert output_conta.is_staff == conta.is_staff
    assert output_conta.is_superuser == conta.is_superuser
