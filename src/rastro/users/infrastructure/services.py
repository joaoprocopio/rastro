from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpRequest

from rastro.users.domain.entities import User
from rastro.users.domain.services import (
    PasswordHashingService,
    SessionService,
)
from rastro.users.domain.value_objects import HashedPassword, RawPassword
from rastro.users.infrastructure.mappers import (
    DjangoToDomainUserMapper,
    DomainToDjangoUserMapper,
)


class DjangoSessionService(SessionService):
    def __init__(self, request: HttpRequest) -> None:
        self.request = request

    def login(self, user: User) -> None:
        login(self.request, DomainToDjangoUserMapper.map(user))

    def logout(self) -> None:
        logout(self.request)

    def logged_user(self) -> User | None:
        if self.request.user.pk is None:
            return None

        return DjangoToDomainUserMapper.map(self.request.user)


class DjangoPasswordHashingService(PasswordHashingService):
    def hash(self, raw_password: RawPassword) -> HashedPassword:
        return HashedPassword(make_password(raw_password.value))

    def verify(
        self, raw_password: RawPassword, hashed_password: HashedPassword
    ) -> bool:
        return check_password(raw_password.value, hashed_password.value)
