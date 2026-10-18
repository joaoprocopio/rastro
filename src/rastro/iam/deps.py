from rastro.iam.adapters import (
    DjangoSessionStore,
    django_authenticate,
    django_make_password,
)
from rastro.iam.ports import Authenticator, PasswordHasher, SessionStore

AUTHENTICATE: Authenticator = django_authenticate
SESSION_STORE: SessionStore = DjangoSessionStore()
PASSWORD_HASHER: PasswordHasher = django_make_password
