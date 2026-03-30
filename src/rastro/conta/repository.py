from abc import ABC, abstractmethod

from rastro.conta.entities import Conta


class ContaRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Conta | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Conta | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> Conta | None: ...

    @abstractmethod
    def save(self, conta: Conta) -> Conta: ...
