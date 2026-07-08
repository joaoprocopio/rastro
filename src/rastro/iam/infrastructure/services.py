from typing import Optional

from django.contrib import auth
from django.contrib.auth.hashers import make_password, verify_password
from django.http import HttpRequest

from rastro.iam.domain.aggregates import IdentityAggregate
from rastro.iam.domain.services import (
    PasswordHashingService,
    PasswordVerification,
    SessionService,
)
from rastro.iam.domain.value_objects import HashedPassword, RawPassword
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


class DjangoPasswordHashingService(PasswordHashingService):
    def hash(self, raw_password: RawPassword) -> HashedPassword:
        return HashedPassword(make_password(raw_password.root))

    def verify(
        self, raw_password: RawPassword, hashed_password: HashedPassword
    ) -> PasswordVerification:
        is_correct, must_upgrade = verify_password(
            raw_password.root, hashed_password.root
        )

        return PasswordVerification(is_correct=is_correct, must_upgrade=must_upgrade)
