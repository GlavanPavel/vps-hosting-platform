from collections import defaultdict
from typing import Callable
from domain.events import DomainEvent

_handlers: dict[type[DomainEvent], list[Callable[[DomainEvent], None]]] = defaultdict(list)


def on(event_type: type[DomainEvent]) -> Callable:
    def decorator(fn: Callable[[DomainEvent], None]) -> Callable:
        _handlers[event_type].append(fn)
        return fn
    return decorator


def dispatch(event: DomainEvent) -> None:
    for handler in _handlers[type(event)]:
        handler(event)
