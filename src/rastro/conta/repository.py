from abc import ABC, abstractmethod

from django.contrib.auth.models import User

from rastro.base.entities import Id
from rastro.conta.entities import Conta
from rastro.conta.value_objects import Email, Name, PasswordHash, Username


class ContaRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Conta | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Conta | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> Conta | None: ...

    @abstractmethod
    def save(self, conta: Conta) -> Conta: ...


class DjangoContaRepository(ContaRepository):
    def get_by_id(self, id: int) -> Conta | None:
        try:
            user = User.objects.get(pk=id)  # type: ignore[misc]
            return self._to_entity(user)
        except User.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Conta | None:
        try:
            user = User.objects.get(email=email)  # type: ignore[misc]
            return self._to_entity(user)
        except User.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> Conta | None:
        try:
            user = User.objects.get(username=username)  # type: ignore[misc]
            return self._to_entity(user)
        except User.DoesNotExist:
            return None

    def save(self, conta: Conta) -> Conta:
        if conta.id is None:
            user = User.objects.create_user(  # type: ignore[misc]
                username=conta.username.value,
                email=conta.email.value,
                password=None,
                first_name=conta.first_name.value,
                last_name=conta.last_name.value,
            )
            user.password = conta.password_hash.value
            user.save()
            return self._to_entity(user)

        user = User.objects.get(pk=conta.id.value)  # type: ignore[misc]
        user.username = conta.username.value
        user.email = conta.email.value
        user.password = conta.password_hash.value
        user.first_name = conta.first_name.value
        user.last_name = conta.last_name.value
        user.save()
        return self._to_entity(user)

    def _to_entity(self, user: User) -> Conta:
        return Conta(
            id=Id(user.pk),
            username=Username(user.username),
            email=Email(user.email),
            password_hash=PasswordHash(user.password),
            first_name=Name(user.first_name),
            last_name=Name(user.last_name),
        )
