import enum

import pytest

from rastro.codes import ErrorCode


def test_codes_are_str_valued() -> None:
    assert ErrorCode.AUTH_CONTA_NAO_ENCONTRADA == "AUTH_CONTA_NAO_ENCONTRADA"
    assert isinstance(ErrorCode.AUTH_CONTA_NAO_ENCONTRADA, str)


def test_every_value_matches_its_name() -> None:
    for code in ErrorCode:
        assert code.value == code.name


def test_catalog_values_are_unique() -> None:
    values = [code.value for code in ErrorCode]

    assert len(values) == len(set(values))


def test_unique_decorator_rejects_duplicate_values() -> None:
    # documents the guarantee `@enum.unique` gives the catalog: a duplicate
    # value is a definition-time error, not a silent alias.
    with pytest.raises(ValueError):

        @enum.unique
        class _Dup(enum.StrEnum):
            ONE = "SAME"
            TWO = "SAME"
