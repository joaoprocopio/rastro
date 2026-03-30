from django.contrib.auth.models import User as DjangoUser

from rastro.base.entity import Id
from rastro.users.domain.entities import User
from rastro.users.domain.repository import UserRepository
from rastro.users.domain.value_objects import (
    Email,
    RawPassword,
    Username,
)
from rastro.users.infrastructure.mappers import DjangoUserToDomainMapper


class DjangoUserRepository(UserRepository):
    def create(
        self, username: Username, email: Email, raw_password: RawPassword
    ) -> User:
        django_user = DjangoUser.objects.create_user(  # type: ignore
            username=username.value,
            email=email.value,
            password=raw_password.value,
        )

        return DjangoUserToDomainMapper.map(django_user)

    def get_by_id(self, id: Id) -> User | None:
        try:
            django_user = DjangoUser.objects.get(pk=id.value)  # type: ignore

            return DjangoUserToDomainMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> User | None:
        try:
            django_user = DjangoUser.objects.get(email=email.value)  # type: ignore

            return DjangoUserToDomainMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: Username) -> User | None:
        try:
            django_user = DjangoUser.objects.get(username=username.value)  # type: ignore

            return DjangoUserToDomainMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None
