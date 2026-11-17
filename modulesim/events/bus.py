"""A simple publish and subscribe event bus.

Interface:
    subscribe(name, handler)  sign a handler up for one message name
    publish(name, payload)    send a message to every handler signed up for it

In the target design this is a managed message queue and handlers run in
separate services. In the prototype, publish calls each handler straight
away, in the order they subscribed. Services use only these two methods,
so swapping in a real queue changes this file and nothing else.
"""

from collections import defaultdict
from typing import Any, Callable

from .messages import ALL

Handler = Callable[[dict], Any]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        # A record of every message sent. Used by tests and for debugging.
        self.history: list[tuple[str, dict]] = []

    def subscribe(self, name: str, handler: Handler) -> None:
        if name not in ALL:
            raise ValueError(f"Unknown message name: {name!r}")
        self._handlers[name].append(handler)

    def publish(self, name: str, payload: dict | None = None) -> None:
        if name not in ALL:
            raise ValueError(f"Unknown message name: {name!r}")
        payload = dict(payload or {})
        self.history.append((name, payload))
        for handler in list(self._handlers[name]):
            handler(payload)
