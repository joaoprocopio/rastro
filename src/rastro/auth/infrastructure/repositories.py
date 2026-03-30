from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from rastro.auth.domain.entities import User
from rastro.auth.domain.repository import UserRepository
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    Username,
)
from rastro.auth.infrastructure.mappers import DjangoToDomainUserMapper
from rastro_base.entity import Id

if TYPE_CHECKING:
    from django.contrib.auth.models import User as DjangoUser
else:
    DjangoUser = get_user_model()


class DjangoUserRepository(UserRepository):
    def create(
        self, username: Username, email: Email, hashed_password: HashedPassword
    ) -> User:
        django_user = DjangoUser.objects.create(  # type: ignore
            username=username.value,
            email=email.value,
            password=hashed_password.value,
        )
        django_user.save()

        return DjangoToDomainUserMapper.map(django_user)

    def save(self, user: User) -> None:
        django_user, _ = DjangoUser.objects.update_or_create(  # type: ignore
            pk=user.id.value,
            defaults={
                "username": user.username.value,
                "email": user.email.value,
                "password": user.hashed_password,
                "is_active": user.is_active,
            },
        )

    def get_by_id(self, id: Id) -> User | None:
        try:
            django_user = DjangoUser.objects.get(pk=id.value)  # type: ignore

            return DjangoToDomainUserMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> User | None:
        try:
            django_user = DjangoUser.objects.get(email=email.value)  # type: ignore

            return DjangoToDomainUserMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: Username) -> User | None:
        try:
            django_user = DjangoUser.objects.get(username=username.value)  # type: ignore

            return DjangoToDomainUserMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None
