import io
from collections.abc import Iterator

import pytest
from django.core.management import CommandError, call_command

from rastro.iam.models import Identity
from rastro.iam.values import DisplayName, Email


class Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


def create_superuser_interactively(
    monkeypatch: pytest.MonkeyPatch,
    *,
    answers: list[str],
    passwords: list[str],
) -> tuple[list[str], io.StringIO]:
    prompts: list[str] = []
    answer: Iterator[str] = iter(answers)
    password: Iterator[str] = iter(passwords)

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(answer)

    def fake_getpass(prompt: str = "Password: ") -> str:
        prompts.append(prompt)
        return next(password)

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("getpass.getpass", fake_getpass)
    stderr = io.StringIO()
    call_command(
        "createsuperuser",
        interactive=True,
        stdin=Tty(),
        stdout=io.StringIO(),
        stderr=stderr,
    )
    return prompts, stderr


def create_superuser_without_input(
    monkeypatch: pytest.MonkeyPatch, *, email: str, display_name: str, password: str
) -> None:
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", password)
    call_command(
        "createsuperuser",
        interactive=False,
        email=email,
        display_name=display_name,
        verbosity=0,
    )


@pytest.mark.django_db
def test_it_asks_for_the_email_the_display_name_and_the_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts, _ = create_superuser_interactively(
        monkeypatch,
        answers=[" Root@X.com ", "Root"],
        passwords=["supersecret", "supersecret"],
    )

    assert prompts == ["Email: ", "Display name: ", "Password: ", "Password (again): "]
    identity = Identity.objects.get()
    assert identity.email == Email("root@x.com")
    assert identity.display_name == DisplayName("Root")
    assert identity.check_password("supersecret")
    assert identity.is_staff is True
    assert identity.is_superuser is True


@pytest.mark.django_db
def test_it_rejects_an_invalid_email_and_asks_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts, stderr = create_superuser_interactively(
        monkeypatch,
        answers=["not-an-email", "root@x.com", "Root"],
        passwords=["supersecret", "supersecret"],
    )

    assert prompts[:2] == ["Email: ", "Email: "]
    assert "request.invalid_format" in stderr.getvalue()
    assert Identity.objects.get().email == Email("root@x.com")


@pytest.mark.django_db
def test_it_rejects_a_password_shorter_than_8_characters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(CommandError, match="request.too_short"):
        create_superuser_interactively(
            monkeypatch,
            answers=["root@x.com", "Root"],
            passwords=["short", "short"],
        )

    assert not Identity.objects.exists()


@pytest.mark.django_db
def test_it_creates_the_administrator_without_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_superuser_without_input(
        monkeypatch, email="root@x.com", display_name="Root", password="supersecret"
    )

    identity = Identity.objects.get()
    assert identity.check_password("supersecret")
    assert identity.is_staff is True
    assert identity.is_superuser is True


@pytest.mark.django_db
def test_it_rejects_a_short_password_without_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(CommandError, match="request.too_short"):
        create_superuser_without_input(
            monkeypatch, email="root@x.com", display_name="Root", password="short"
        )

    assert not Identity.objects.exists()


@pytest.mark.django_db
def test_it_rejects_a_missing_password_without_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)

    with pytest.raises(CommandError, match="request.too_short"):
        call_command(
            "createsuperuser",
            interactive=False,
            email="root@x.com",
            display_name="Root",
            verbosity=0,
        )

    assert not Identity.objects.exists()
