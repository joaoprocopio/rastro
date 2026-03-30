from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.tokens import default_token_generator

from rastro.base import Id
from rastro.users.domain.aggregates import User
from rastro.users.domain.errors import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from rastro.users.domain.repository import UserRepository
from rastro.users.domain.value_objects import Email, HashedPassword, Username


class DjangoUserRepository(UserRepository):
    def get_by_id(self, id: int) -> User | None:
        try:
            django_user = DjangoUser.objects.get(pk=id)
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> User | None:
        try:
            django_user = DjangoUser.objects.get(email=email.value)
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: Username) -> User | None:
        try:
            django_user = DjangoUser.objects.get(username=username.value)
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def save(self, user: User) -> User:
        if user.id is None:
            return self._create(user)
        return self._update(user)

    def delete(self, user: User) -> None:
        if user.id is None:
            return
        try:
            django_user = DjangoUser.objects.get(pk=user.id.value)
            django_user.delete()
        except DjangoUser.DoesNotExist:
            pass

    def exists_by_email(self, email: Email) -> bool:
        return DjangoUser.objects.filter(email=email.value).exists()

    def exists_by_username(self, username: Username) -> bool:
        return DjangoUser.objects.filter(username=username.value).exists()

    def _create(self, user: User) -> User:
        if self.exists_by_email(user.email):
            raise EmailAlreadyExistsError(f"Email {user.email.value} already exists")
        if self.exists_by_username(user.username):
            raise UsernameAlreadyExistsError(
                f"Username {user.username.value} already exists"
            )

        django_user = DjangoUser.objects.create_user(
            username=user.username.value,
            email=user.email.value,
            password=user.hashed_password.value,
        )
        django_user.is_active = user.is_active
        django_user.save()

        return self._to_domain(django_user)

    def _update(self, user: User) -> User:
        try:
            django_user = DjangoUser.objects.get(pk=user.id.value)

            if django_user.email != user.email.value:
                if self.exists_by_email(user.email):
                    raise EmailAlreadyExistsError(
                        f"Email {user.email.value} already exists"
                    )
                django_user.email = user.email.value

            if django_user.username != user.username.value:
                if self.exists_by_username(user.username):
                    raise UsernameAlreadyExistsError(
                        f"Username {user.username.value} already exists"
                    )
                django_user.username = user.username.value

            django_user.is_active = user.is_active
            django_user.save()

            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            raise ValueError(f"User with id {user.id} not found")

    def _to_domain(self, django_user: DjangoUser) -> User:
        return User(
            id=Id(django_user.pk),
            username=Username(django_user.username),
            email=Email(django_user.email),
            hashed_password=HashedPassword(django_user.password),
            is_active=django_user.is_active,
            is_verified=django_user.is_active,
        )


class DjangoTokenRepository:
    def generate_password_reset_token(self, user: User) -> str:
        django_user = DjangoUser.objects.get(pk=user.id.value)
        return default_token_generator.make_token(django_user)

    def verify_password_reset_token(self, user: User, token: str) -> bool:
        django_user = DjangoUser.objects.get(pk=user.id.value)
        return default_token_generator.check_token(django_user, token)
