from abc import ABC, abstractmethod

from django.contrib.auth.models import User as DjangoUser

from rastro.users.entities import User
from rastro.users.mappers import DjangoUserToEntityMapper


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> User: ...

    @abstractmethod
    def verify_password(self, user: User, password: str) -> bool: ...


class DjangoUserRepository(UserRepository):
    def get_by_id(self, id: int) -> User | None:
        try:
            django_user = DjangoUser.objects.get(pk=id)  # type: ignore[misc]

            return DjangoUserToEntityMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> User | None:
        try:
            django_user = DjangoUser.objects.get(email=email)  # type: ignore[misc]

            return DjangoUserToEntityMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> User | None:
        try:
            django_user = DjangoUser.objects.get(username=username)  # type: ignore[misc]

            return DjangoUserToEntityMapper.map(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def save(self, user: User) -> User:
        if user.id is None:
            django_user = DjangoUser.objects.create_user(  # type: ignore[misc]
                username=user.username.value,
                email=user.email.value,
                password=user.password.value,
            )

            return DjangoUserToEntityMapper.map(django_user)

        django_user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore[misc]

        django_user.username = user.username.value
        django_user.email = user.email.value
        django_user.password = user.password.value

        django_user.save()
        django_user.check_password

        return DjangoUserToEntityMapper.map(django_user)

    def verify_password(self, user: User, password: str) -> bool:
        try:
            django_user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore

            return django_user.check_password(password)
        except DjangoUser.DoesNotExist:
            return False
