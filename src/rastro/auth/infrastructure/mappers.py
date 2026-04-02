from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from rastro.auth.application.dtos import UserOutput, UserPublic
from rastro.auth.domain.entities import User
from rastro.auth.domain.value_objects import Email, HashedPassword, Username
from rastro_base.mapper import Mapper
from rastro_shared_kernel.value_objects import Id

if TYPE_CHECKING:
    from django.contrib.auth.models import User as DjangoUser
else:
    DjangoUser = get_user_model()


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
            id=input.id.root,
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


class OutputToPublicUserMapper(Mapper[UserOutput, UserPublic]):
    @staticmethod
    def map(input: UserOutput) -> UserPublic:
        return UserPublic(
            email=input.email,
            username=input.username,
        )


class DomainToOutputUserMapper(Mapper[User, UserOutput]):
    @staticmethod
    def map(input: User) -> UserOutput:
        return UserOutput(
            id=input.id.root,
            email=input.email.value,
            username=input.username.value,
            password=input.hashed_password.value,
            is_active=input.is_active,
        )


class DomainToPublicUserMapper(Mapper[User, UserPublic]):
    @staticmethod
    def map(input: User) -> UserPublic:
        return UserPublic(
            email=input.email.value,
            username=input.username.value,
        )
