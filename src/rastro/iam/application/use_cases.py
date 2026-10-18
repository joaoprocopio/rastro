from typing import Optional

from rastro.iam.application.dtos import IdentityOutputDTO
from rastro.iam.domain.services import SessionService
from rastro.iam.shared.mappers import OutputIdentityMapper
from rastro_base.use_case import UseCase


class GetCurrentIdentityUseCase(UseCase):
    def __init__(
        self,
        session_service: SessionService,
    ):
        self.session_service = session_service

    def execute(self) -> Optional[IdentityOutputDTO]:
        identity = self.session_service.current_identity()

        if identity is None:
            return None

        return OutputIdentityMapper.map(identity)


class EndSessionUseCase(UseCase):
    def __init__(self, session_service: SessionService):
        self.session_service = session_service

    def execute(self) -> None:
        self.session_service.end()
