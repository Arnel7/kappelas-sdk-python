from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from typing import Any, Callable


class EventEmitter:
    """
    Async-capable event emitter base class.

    Supports both sync and async handlers. ``on()`` / ``once()`` work both as
    regular method calls and as decorators.

    Example::

        # method call
        emitter.on('message', handler)

        # decorator
        @emitter.on('message')
        async def handler(msg):
            ...
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    # ─── on ──────────────────────────────────────────────────────────────────

    def on(
        self,
        event:   str,
        handler: Callable[..., Any] | None = None,
    ) -> Any:
        """Register *handler* for *event*.

        Can be called as ``emitter.on('event', handler)`` or used as a
        decorator ``@emitter.on('event')``.
        """
        if handler is None:
            # Decorator usage: @emitter.on('event')
            def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
                self._listeners[event].append(fn)
                return fn
            return decorator

        self._listeners[event].append(handler)
        return self  # allow chaining

    # ─── once ────────────────────────────────────────────────────────────────

    def once(
        self,
        event:   str,
        handler: Callable[..., Any] | None = None,
    ) -> Any:
        """Register a one-shot handler that is automatically removed after the
        first call.

        Supports both method call and decorator usage.
        """
        if handler is None:
            def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
                self._register_once(event, fn)
                return fn
            return decorator

        self._register_once(event, handler)
        return self

    def _register_once(self, event: str, handler: Callable[..., Any]) -> None:
        wrapper: Callable[..., Any] | None = None

        async def _async_wrapper(*args: Any, **kwargs: Any) -> None:
            self.off(event, wrapper)  # type: ignore[arg-type]
            result = handler(*args, **kwargs)
            if inspect.isawaitable(result):
                await result

        def _sync_wrapper(*args: Any, **kwargs: Any) -> None:
            self.off(event, wrapper)  # type: ignore[arg-type]
            handler(*args, **kwargs)

        if inspect.iscoroutinefunction(handler):
            wrapper = _async_wrapper
        else:
            wrapper = _sync_wrapper

        self._listeners[event].append(wrapper)

    # ─── off ─────────────────────────────────────────────────────────────────

    def off(self, event: str, handler: Callable[..., Any]) -> None:
        """Remove a previously registered handler."""
        listeners = self._listeners.get(event)
        if listeners:
            try:
                listeners.remove(handler)
            except ValueError:
                pass

    # ─── emit ────────────────────────────────────────────────────────────────

    async def emit(self, event: str, *args: Any) -> None:
        """Fire *event*, passing *args* to every registered handler.

        Async handlers are awaited; sync handlers are called directly.
        """
        listeners = list(self._listeners.get(event, []))
        for handler in listeners:
            try:
                result = handler(*args)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                if event == 'error':
                    raise  # prevent infinite loop
                error_listeners = self._listeners.get('error', [])
                if error_listeners:
                    await self.emit('error', exc)
                # if no error listener, swallow silently to not break the loop

    # ─── convenience ─────────────────────────────────────────────────────────

    def listener_count(self, event: str) -> int:
        """Return the number of handlers registered for *event*."""
        return len(self._listeners.get(event, []))

    def remove_all_listeners(self, event: str | None = None) -> None:
        """Remove all handlers, optionally scoped to a single *event*."""
        if event is None:
            self._listeners.clear()
        else:
            self._listeners.pop(event, None)
