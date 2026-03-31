from typing import Optional

from django.contrib import auth
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpRequest

from rastro.auth.domain.entities import User
from rastro.auth.domain.services import (
    PasswordHashingService,
    SessionService,
)
from rastro.auth.domain.value_objects import HashedPassword, RawPassword
from rastro.auth.infrastructure.mappers import (
    DjangoToDomainUserMapper,
    DomainToDjangoUserMapper,
)


class DjangoSessionService(SessionService):
    def __init__(self, request: HttpRequest) -> None:
        self.request = request

    def login(self, user: User) -> None:
        auth.login(self.request, DomainToDjangoUserMapper.map(user))

    def logout(self) -> None:
        auth.logout(self.request)

    def logged_user(self) -> Optional[User]:
        user = auth.get_user(self.request)

        if user.pk is None:
            return None

        return DjangoToDomainUserMapper.map(user)


class DjangoPasswordHashingService(PasswordHashingService):
    def hash(self, raw_password: RawPassword) -> HashedPassword:
        return HashedPassword(make_password(raw_password.value))

    def verify(
        self, raw_password: RawPassword, hashed_password: HashedPassword
    ) -> bool:
        return check_password(raw_password.value, hashed_password.value)
