from rastro.iam.adapters import DjangoSessionStore, django_authenticate
from rastro.iam.ports import Authenticator, SessionStore

AUTHENTICATE: Authenticator = django_authenticate
SESSION_STORE: SessionStore = DjangoSessionStore()
