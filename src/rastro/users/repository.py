from abc import ABC, abstractmethod

from django.contrib.auth.models import User as DjangoUser

from rastro.base.entities import Id
from rastro.users.entities import User
from rastro.users.value_objects import Email, Name, PasswordHash, Username


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> User: ...


class DjangoUserRepository(UserRepository):
    def get_by_id(self, id: int) -> User | None:
        try:
            user = DjangoUser.objects.get(pk=id)  # type: ignore[misc]
            return self._to_entity(user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> User | None:
        try:
            user = DjangoUser.objects.get(email=email)  # type: ignore[misc]
            return self._to_entity(user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> User | None:
        try:
            user = DjangoUser.objects.get(username=username)  # type: ignore[misc]
            return self._to_entity(user)
        except DjangoUser.DoesNotExist:
            return None

    def save(self, user: User) -> User:
        if user.id is None:
            user = DjangoUser.objects.create_user(  # type: ignore[misc]
                username=user.username.value,
                email=user.email.value,
                password=None,
                first_name=user.first_name.value,
                last_name=user.last_name.value,
            )
            user.password = user.password_hash.value
            user.save()
            return self._to_entity(user)

        user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore[misc]
        user.username = user.username.value
        user.email = user.email.value
        user.password = user.password_hash.value
        user.first_name = user.first_name.value
        user.last_name = user.last_name.value
        user.save()
        return self._to_entity(user)

    def _to_entity(self, user: DjangoUser) -> User:
        return User(
            id=Id(user.pk),
            username=Username(user.username),
            email=Email(user.email),
            password_hash=PasswordHash(user.password),
            first_name=Name(user.first_name),
            last_name=Name(user.last_name),
        )
