from django.contrib.auth.models import User as DjangoUser

from rastro.base.entities import Id
from rastro.base.mappers import Mapper
from rastro.users.dto import UserOutput
from rastro.users.entities import User
from rastro.users.value_objects import Email, Name, PasswordHash, Username


class DjangoUserMapper(Mapper[DjangoUser, User]):
    @staticmethod
    def to_target(source: User) -> DjangoUser:
        return DjangoUser(
            id=source.id.value,  # type: ignore
            username=source.username.value,
            email=source.email.value,
            password=source.password_hash.value,
            first_name=source.first_name.value,
            last_name=source.last_name.value,
        )

    @staticmethod
    def to_source(target: DjangoUser) -> User:
        return User(
            id=Id(target.pk),
            email=Email(target.email),
            first_name=Name(target.first_name),
            last_name=Name(target.last_name),
            password_hash=PasswordHash(target.password),
            username=Username(target.username),
        )


class DTOUserMapper(Mapper[User, UserOutput]):
    @staticmethod
    def to_target(source: UserOutput) -> User:
        return User(
            id=Id(source.id),
            email=Email(source.email),
            first_name=Name(source.first_name),
            last_name=Name(source.last_name),
            password_hash=PasswordHash(source.password),
            username=Username(source.username),
        )

    @staticmethod
    def to_source(target: User) -> UserOutput:
        return UserOutput(
            id=target.id.value,  # type: ignore
            email=target.email.value,
            first_name=target.first_name.value,
            last_name=target.last_name.value,
            password=target.password_hash.value,
            username=target.username.value,
        )
