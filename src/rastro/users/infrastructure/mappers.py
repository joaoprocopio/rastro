from django.contrib.auth.models import User as DjangoUser

from rastro.base.entity import Id
from rastro.base.mapper import Mapper
from rastro.users.application.dtos import UserOutput
from rastro.users.domain.entities import User
from rastro.users.domain.value_objects import Email, HashedPassword, Username

# TODO: do this: DjangoUser = get_user_model()


class DjangoToDomainUserMapper(Mapper[DjangoUser, User]):
    @staticmethod
    def map(input: DjangoUser) -> User:
        return User(
            id=Id(input.pk),
            username=Username(input.username),
            email=Email(input.email),
            hashed_password=HashedPassword(input.password),
            is_active=input.is_active,
        )


class DomainToDjangoUserMapper(Mapper[User, DjangoUser]):
    @staticmethod
    def map(input: User) -> DjangoUser:
        return DjangoUser(
            id=input.id.value,
            username=input.username.value,
            email=input.email.value,
            password=input.hashed_password.value,
            is_active=input.is_active,
        )


class OutputToDomainUserMapper(Mapper[UserOutput, User]):
    @staticmethod
    def map(input: UserOutput) -> User:
        return User(
            id=Id(input.id),
            username=Username(input.username),
            email=Email(input.email),
            hashed_password=HashedPassword(input.password),
            is_active=input.is_active,
        )


class DomainToOutputUserMapper(Mapper[User, UserOutput]):
    @staticmethod
    def map(input: User) -> UserOutput:
        return UserOutput(
            id=input.id.value,
            email=input.email.value,
            username=input.username.value,
            password=input.hashed_password.value,
            is_active=input.is_active,
        )
