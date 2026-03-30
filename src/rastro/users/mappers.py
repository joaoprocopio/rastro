from django.contrib.auth.models import User as DjangoUser

from rastro.base.entities import Id
from rastro.base.mappers import Mapper
from rastro.users.dto import UserOutput
from rastro.users.entities import User
from rastro.users.value_objects import Email, Password, Username


class DjangoUserToDTOMapper(Mapper[DjangoUser, UserOutput]):
    @staticmethod
    def map(input: DjangoUser) -> UserOutput:
        return UserOutput(
            id=input.id,
            email=input.email,
            password=input.password,
            username=input.username,
        )


class DjangoUserToEntityMapper(Mapper[DjangoUser, User]):
    @staticmethod
    def map(input: DjangoUser) -> User:
        return User(
            id=Id(input.id),
            email=Email(input.email),
            password=Password(input.password),
            username=Username(input.username),
        )


class UserToDTOMapper(Mapper[User, UserOutput]):
    @staticmethod
    def map(input: User) -> UserOutput:
        return UserOutput(
            id=input.id.value,  # type: ignore
            email=input.email.value,
            password=input.password.value,
            username=input.username.value,
        )
