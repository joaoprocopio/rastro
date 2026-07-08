import pytest

from rastro_shared_kernel.env import get_env, parse_booleanish, parse_csv


def test_get_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK", "mock")
    env = get_env("MOCK")

    assert env == "mock"


def test_get_env_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MOCK", raising=False)
    env = get_env("MOCK")

    assert env is None


def test_get_env_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MOCK", raising=False)
    env = get_env("MOCK", default="default_mock")

    assert env == "default_mock"


def test_get_env_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK", "1")
    env = get_env("MOCK", parser=int)

    assert env == 1


def test_get_env_default_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MOCK", raising=False)
    env = get_env("MOCK", default="1", parser=int)

    assert env == 1


def test_parse_csv() -> None:
    env = parse_csv("one, two,three ")

    assert env == ["one", "two", "three"]


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (" TRUE ", True),
        ("true", True),
        ("yes", True),
        ("1", True),
        ("false", False),
        ("no", False),
        ("0", False),
    ],
)
def test_parse_booleanish(raw_value: str, expected: bool) -> None:
    env = parse_booleanish(raw_value)

    assert env is expected


def test_parse_booleanish_invalid() -> None:
    with pytest.raises(TypeError):
        parse_booleanish("invalid")
