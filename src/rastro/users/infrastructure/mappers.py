from django.contrib.auth.models import User as DjangoUser

from rastro.base import Id
from rastro.base.mappers import Mapper
from rastro.users.domain.aggregates import User
from rastro.users.domain.value_objects import Email, HashedPassword, Username


class DjangoUserToDomainMapper(Mapper[DjangoUser, User]):
    @staticmethod
    def map(input: DjangoUser) -> User:
        return User(
            id=Id(input.pk),
            username=Username(input.username),
            email=Email(input.email),
            hashed_password=HashedPassword(input.password),
            is_active=input.is_active,
            is_verified=input.is_active,
        )


class DomainUserToOutputMapper(Mapper[User, dict]):
    @staticmethod
    def map(input: User) -> dict:
        return {
            "id": input.id.value if input.id else None,
            "username": input.username.value,
            "email": input.email.value,
            "is_active": input.is_active,
            "is_verified": input.is_verified,
        }
