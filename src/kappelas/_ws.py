from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# Cap reconnect delay at 60 s (matching the 30 s server ping window)
_MAX_BACKOFF = 60.0


class WSClient:
    """Async WebSocket client with automatic exponential-backoff reconnection.

    Args:
        url:         WebSocket URL to connect to.
        max_retries: Maximum number of reconnect attempts (default 12).

    Callbacks (all async callables, set by the owner before calling
    :meth:`connect`):

    * ``on_raw(event_dict)``        — called for every parsed JSON message.
    * ``on_connected()``            — called when the socket opens.
    * ``on_disconnected(code, reason)`` — called when the socket closes.
    * ``on_error(exc)``             — called on connection / parse errors.
    """

    def __init__(self, url: str, max_retries: int = 12) -> None:
        self._url         = url
        self._max_retries = max_retries

        # Display URL hides api_key= param value
        self._display_url = _redact_url(url)

        self._stopped   = False
        self._connected = False
        self._attempts  = 0
        self._ws: Any   = None          # websockets.WebSocketClientProtocol
        self._recv_task: asyncio.Task[None] | None = None

        # Callbacks — owner must set these before connect()
        self.on_raw:          Callable[..., Coroutine[Any, Any, None]] | None = None
        self.on_connected:    Callable[..., Coroutine[Any, Any, None]] | None = None
        self.on_disconnected: Callable[..., Coroutine[Any, Any, None]] | None = None
        self.on_error:        Callable[..., Coroutine[Any, Any, None]] | None = None

    # ─── Public API ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Connect and start the background receive loop."""
        self._stopped  = False
        self._attempts = 0
        await self._connect()

    async def disconnect(self) -> None:
        """Close the connection and stop reconnecting."""
        self._stopped    = True
        self._connected  = False
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
            try:
                await self._recv_task
            except (asyncio.CancelledError, Exception):
                pass
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    def is_connected(self) -> bool:
        """Return ``True`` if the WebSocket is currently open."""
        return self._connected

    # ─── Internal ─────────────────────────────────────────────────────────────

    async def _connect(self) -> None:
        if self._stopped:
            return

        import websockets  # import deferred so the library is optional at import time

        try:
            self._ws = await websockets.connect(
                self._url,
                ping_interval=30,
                ping_timeout=60,
            )
        except Exception as exc:
            await self._handle_error(
                Exception(f'WebSocket connect error ({self._display_url}): {exc}')
            )
            await self._schedule_reconnect()
            return

        self._connected = True
        self._attempts  = 0

        if self.on_connected:
            try:
                await self.on_connected()
            except Exception:
                pass

        self._recv_task = asyncio.get_event_loop().create_task(self._recv_loop())

    async def _recv_loop(self) -> None:
        try:
            async for raw in self._ws:
                if self._stopped:
                    break
                try:
                    event = json.loads(raw)
                except Exception:
                    continue  # ignore malformed frames

                if self.on_raw:
                    try:
                        await self.on_raw(event)
                    except Exception:
                        pass
        except asyncio.CancelledError:
            return
        except Exception as exc:
            if not self._stopped:
                await self._handle_error(
                    Exception(f'WebSocket error ({self._display_url}): {exc}')
                )

        # Socket closed (either cleanly or with an error)
        self._connected = False
        code   = getattr(self._ws, 'close_code',   1006) or 1006
        reason = getattr(self._ws, 'close_reason', '')   or ''

        if self.on_disconnected:
            try:
                await self.on_disconnected(code, str(reason))
            except Exception:
                pass

        if not self._stopped:
            await self._schedule_reconnect()

    async def _schedule_reconnect(self) -> None:
        if self._attempts >= self._max_retries:
            await self._handle_error(
                Exception(
                    f'WebSocket: max reconnect attempts ({self._max_retries}) reached'
                )
            )
            return

        delay = min(1.0 * (2 ** self._attempts), _MAX_BACKOFF)
        self._attempts += 1
        logger.debug(
            'WebSocket reconnect attempt %d/%d in %.1fs',
            self._attempts, self._max_retries, delay,
        )
        await asyncio.sleep(delay)
        await self._connect()

    async def _handle_error(self, exc: Exception) -> None:
        if self.on_error:
            try:
                await self.on_error(exc)
            except Exception:
                pass
        else:
            logger.error('WSClient error: %s', exc)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _redact_url(url: str) -> str:
    import re
    return re.sub(r'([?&]api_key=)[^&]+', r'\g<1>***', url)
