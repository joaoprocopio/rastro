from django.contrib.auth.models import User as DjangoUser

from rastro.base.mappers import Mapper
from rastro.users.dto import UserOutput


class DjangoUserDTOMapper(Mapper[DjangoUser, UserOutput]):
    @staticmethod
    def map(input: DjangoUser) -> UserOutput:
        return UserOutput(
            id=input.id,
            email=input.email,
            first_name=input.first_name,
            last_name=input.last_name,
            password=input.password,
            username=input.username,
        )
