from abc import ABC
from dataclasses import dataclass, field

from rastro.base.domain_event import DomainEvent


@dataclass
class Aggregate(ABC):
    _domain_events: list[DomainEvent] = field(default_factory=list, init=False)

    def add_domain_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def remove_domain_event(self, event: DomainEvent) -> None:
        self._domain_events.remove(event)

    def clear_domain_events(self) -> list[DomainEvent]:
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    @property
    def domain_events(self) -> list[DomainEvent]:
        return self._domain_events.copy()
