from django.db import transaction
from django.http import HttpRequest

from rastro.iam.errors import IncorrectCredentialsError
from rastro.iam.ports import Authenticator, SessionStore
from rastro.iam.values import Email, RawPassword


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
