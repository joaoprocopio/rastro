from typing import Optional

from django.contrib import auth
from django.contrib.auth.hashers import make_password, verify_password
from django.http import HttpRequest

from rastro.conta.domain.aggregates import Conta
from rastro.conta.domain.services import (
    PasswordHashingService,
    PasswordVerification,
    SessionService,
)
from rastro.conta.domain.value_objects import HashedPassword, RawPassword
from rastro.conta.shared.mappers import DehydrateContaMapper, HydrateContaMapper


class DjangoSessionService(SessionService):
    def __init__(self, request: HttpRequest) -> None:
        self.request = request

    def login(self, conta: Conta) -> None:
        auth.login(self.request, DehydrateContaMapper.map(conta))

    def logout(self) -> None:
        auth.logout(self.request)

    def logged_conta(self) -> Optional[Conta]:
        user = auth.get_user(self.request)

        if user.pk is None:
            return None

        return HydrateContaMapper.map(user)


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
