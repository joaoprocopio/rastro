from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.http import HttpRequest

from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.domain.services import PasswordHashingService, SessionService
from rastro.iam.values import HashedPassword, RawPassword
from rastro.iam.shared.mappers import DehydrateIdentityMapper


class DjangoSessionService(SessionService):
    def __init__(self, request: HttpRequest) -> None:
        self.request = request

    def start(self, identity: IdentityAggregate) -> None:
        auth.login(self.request, DehydrateIdentityMapper.map(identity))


class DjangoPasswordHashingService(PasswordHashingService):
    def hash(self, raw_password: RawPassword) -> HashedPassword:
        return HashedPassword(make_password(raw_password.value))
