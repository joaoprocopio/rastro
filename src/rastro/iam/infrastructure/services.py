from typing import Optional

from django.contrib import auth
from django.http import HttpRequest

from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.domain.services import SessionService
from rastro.iam.shared.mappers import DehydrateIdentityMapper, HydrateIdentityMapper


class DjangoSessionService(SessionService):
    def __init__(self, request: HttpRequest) -> None:
        self.request = request

    def start(self, identity: IdentityAggregate) -> None:
        auth.login(self.request, DehydrateIdentityMapper.map(identity))

    def end(self) -> None:
        auth.logout(self.request)

    def current_identity(self) -> Optional[IdentityAggregate]:
        user = auth.get_user(self.request)

        if user.pk is None:
            return None

        return HydrateIdentityMapper.map(user)
