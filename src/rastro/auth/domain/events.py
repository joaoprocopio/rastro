from dataclasses import dataclass

from rastro.base.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class UserCreated(DomainEvent):
    user_id: int
    username: str
    email: str


@dataclass(frozen=True, kw_only=True)
class UserActivated(DomainEvent):
    user_id: int


@dataclass(frozen=True, kw_only=True)
class UserDeactivated(DomainEvent):
    user_id: int


@dataclass(frozen=True, kw_only=True)
class PasswordChanged(DomainEvent):
    user_id: int


@dataclass(frozen=True, kw_only=True)
class UserLoggedIn(DomainEvent):
    user_id: int


@dataclass(frozen=True, kw_only=True)
class UserLoggedOut(DomainEvent):
    user_id: int
