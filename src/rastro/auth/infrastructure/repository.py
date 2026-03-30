from django.contrib.auth import get_user_model

from rastro.auth.domain.entities import User
from rastro.auth.domain.repository import UserRepository
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    Username,
)
from rastro.auth.infrastructure.mappers import DjangoToDomainUserMapper
from rastro.base.entity import Id

DjangoUser = get_user_model()


class DjangoUserRepository(UserRepository):
    def create(
        self, username: Username, email: Email, hashed_password: HashedPassword
    ) -> User:
        django_user = DjangoUser.objects.create(
            username=username.value,
            email=email.value,
            password=hashed_password.value,
        )
        django_user.save()

        return DjangoToDomainUserMapper.map(django_user)

    def get_by_id(self, id: Id) -> User | None:
        try:
            django_user = DjangoUser.objects.get(pk=id.value)

            return DjangoToDomainUserMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> User | None:
        try:
            django_user = DjangoUser.objects.get(email=email.value)

            return DjangoToDomainUserMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: Username) -> User | None:
        try:
            django_user = DjangoUser.objects.get(username=username.value)

            return DjangoToDomainUserMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None
