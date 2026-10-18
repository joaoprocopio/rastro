from django.db import IntegrityError, transaction
from django.http import HttpRequest

from rastro.iam.errors import EmailInUseError, IncorrectCredentialsError
from rastro.iam.models import Identity
from rastro.iam.ports import Authenticator, PasswordHasher, SessionStore
from rastro.iam.values import DisplayName, Email, RawPassword


@transaction.atomic
def identity_register(
    *,
    email: Email,
    display_name: DisplayName,
    password: RawPassword,
    password_hasher: PasswordHasher,
) -> None:
    _identity_create(
        email=email,
        display_name=display_name,
        password=password,
        password_hasher=password_hasher,
        is_staff=False,
        is_superuser=False,
    )


@transaction.atomic
def identity_register_superuser(
    *,
    email: Email,
    display_name: DisplayName,
    password: RawPassword,
    password_hasher: PasswordHasher,
) -> None:
    _identity_create(
        email=email,
        display_name=display_name,
        password=password,
        password_hasher=password_hasher,
        is_staff=True,
        is_superuser=True,
    )


def _identity_create(
    *,
    email: Email,
    display_name: DisplayName,
    password: RawPassword,
    password_hasher: PasswordHasher,
    is_staff: bool,
    is_superuser: bool,
) -> None:
    if Identity.objects.filter(email=email).exists():
        raise EmailInUseError()
    try:
        Identity.objects.create(
            email=email,
            display_name=display_name,
            password=password_hasher(password=password).value,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
    except IntegrityError as error:
        raise EmailInUseError() from error


@transaction.atomic
def session_start(
    *,
    request: HttpRequest,
    email: Email,
    password: RawPassword,
    authenticator: Authenticator,
    session_store: SessionStore,
) -> None:
    identity = authenticator(request=request, email=email, password=password)
    if identity is None:
        raise IncorrectCredentialsError()
    session_store.start(request=request, identity=identity)


@transaction.atomic
def session_end(*, request: HttpRequest, session_store: SessionStore) -> None:
    session_store.end(request=request)
