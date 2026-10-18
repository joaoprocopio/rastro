from django.http import HttpRequest

from rastro.iam.errors import NotAuthenticatedError
from rastro.iam.models import Identity
from rastro.iam.ports import SessionStore


def identity_get_current(
    *, request: HttpRequest, session_store: SessionStore
) -> Identity:
    identity = session_store.current(request=request)
    if identity is None:
        raise NotAuthenticatedError()
    return identity
