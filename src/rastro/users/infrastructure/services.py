from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User as DjangoUser
from django.http import HttpRequest

from rastro.base.entity import Id
from rastro.users.domain.services import (
    PasswordHashingService,
    SessionService,
)
from rastro.users.domain.value_objects import HashedPassword, RawPassword


class DjangoPasswordHashingService(PasswordHashingService):
    def hash(self, raw_password: RawPassword) -> HashedPassword:
        return HashedPassword(make_password(raw_password.value))

    def verify(
        self, raw_password: RawPassword, hashed_password: HashedPassword
    ) -> bool:
        return check_password(raw_password.value, hashed_password.value)


class DjangoSessionService(SessionService):
    def login(self, request: HttpRequest, user_id: Id) -> None:
        django_user = DjangoUser.objects.get(pk=user_id.value)  # type: ignore
        login(request, django_user)

    def logout(self, request: HttpRequest) -> None:
        logout(request)

    def access_current_user_id(self, request: HttpRequest) -> Id | None:
        pk = request.user.pk

        if pk is not None:
            return Id(int(pk))

        return None
