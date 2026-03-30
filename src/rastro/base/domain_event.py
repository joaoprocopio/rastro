from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid7


@dataclass(frozen=True)
class DomainEvent(ABC):
    event_id: str = field(default_factory=lambda: str(uuid7()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_type", self.__class__.__name__)
