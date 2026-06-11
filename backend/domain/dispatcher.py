from collections import defaultdict
from typing import Callable
from domain.events import DomainEvent

# Registry: event type → list of synchronous handler callables
_handlers: dict[type[DomainEvent], list[Callable[[DomainEvent], None]]] = defaultdict(list)


def on(event_type: type[DomainEvent]) -> Callable:
    """Decorator to register a handler for a specific event type."""
    def decorator(fn: Callable[[DomainEvent], None]) -> Callable:
        _handlers[event_type].append(fn)
        return fn
    return decorator


def dispatch(event: DomainEvent) -> None:
    """Call every registered handler for this event type in registration order."""
    for handler in _handlers[type(event)]:
        handler(event)
