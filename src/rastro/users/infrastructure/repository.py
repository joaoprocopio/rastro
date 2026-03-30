from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.tokens import default_token_generator

from rastro.base.entity import Id
from rastro.users.domain.aggregates import User
from rastro.users.domain.errors import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from rastro.users.domain.repository import UserRepository
from rastro.users.domain.value_objects import (
    Email,
    HashedPassword,
    Username,
)


class DjangoUserRepository(UserRepository):
    def create(
        self, username: Username, email: Email, hashed_password: HashedPassword
    ) -> User:
        if self.exists_by_email(email):
            raise EmailAlreadyExistsError(f"Email {email.value} already exists")
        if self.exists_by_username(username):
            raise UsernameAlreadyExistsError(
                f"Username {username.value} already exists"
            )

        django_user = DjangoUser.objects.create(  # type: ignore[misc]
            username=username.value,
            email=email.value,
            password=hashed_password.value,
        )
        django_user.is_active = True
        django_user.save()

        return self._to_domain(django_user)

    def get_by_id(self, id: Id) -> User | None:
        try:
            django_user = DjangoUser.objects.get(pk=id.value)  # type: ignore[misc]
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: Email) -> User | None:
        try:
            django_user = DjangoUser.objects.get(email=email.value)  # type: ignore[misc]
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: Username) -> User | None:
        try:
            django_user = DjangoUser.objects.get(username=username.value)  # type: ignore[misc]
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def update(self, user: User) -> User:
        try:
            django_user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore[misc]

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
            raise ValueError(f"User with id {user.id.value} not found")

    def delete(self, id: Id) -> None:
        try:
            django_user = DjangoUser.objects.get(pk=id.value)  # type: ignore[misc]
            django_user.delete()
        except DjangoUser.DoesNotExist:
            pass

    def exists_by_email(self, email: Email) -> bool:
        return DjangoUser.objects.filter(email=email.value).exists()  # type: ignore[misc]

    def exists_by_username(self, username: Username) -> bool:
        return DjangoUser.objects.filter(username=username.value).exists()  # type: ignore[misc]

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
        django_user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore[misc]
        return default_token_generator.make_token(django_user)

    def verify_password_reset_token(self, user: User, token: str) -> bool:
        django_user = DjangoUser.objects.get(pk=user.id.value)  # type: ignore[misc]
        return default_token_generator.check_token(django_user, token)
