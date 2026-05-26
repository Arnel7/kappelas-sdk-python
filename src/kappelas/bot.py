from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, overload

from kappelas._emitter import EventEmitter
from kappelas._http import HttpClient
from kappelas._parsers import MESSAGE_TYPES, parse_webhook_body, parse_ws_event
from kappelas._ws import WSClient
from kappelas.resources.chats import ChatsResource
from kappelas.resources.messages import MessagesResource
from kappelas.resources.profile import ProfileResource
from kappelas.resources.webhooks import WebhooksResource
from kappelas.types import CallbackQuery, Message


def _to_ws_url(http_url: str, path: str) -> str:
    """Convert an https:// base URL + path into a wss:// WebSocket URL."""
    base = http_url.rstrip('/')
    if base.startswith('https://'):
        ws_base = 'wss://' + base[len('https://'):]
    elif base.startswith('http://'):
        ws_base = 'ws://' + base[len('http://'):]
    else:
        ws_base = base
    return ws_base + path


class KappelaBot(EventEmitter):
    """Bot SDK for Kappela.

    Authenticate with a bot token to send messages and receive events as a bot.

    Args:
        token:          Bot token issued by the Kappela BotFather.
        base_url:       Override the API base URL (default ``'https://api.kappelas.com'``).
        max_retries:    HTTP retry count on 429 / 5xx (default 2).
        timeout:        HTTP request timeout in seconds (default 30.0).
        ws_max_retries: WebSocket reconnect attempt limit (default 12).

    Example::

        import asyncio
        from kappelas import KappelaBot

        bot = KappelaBot('YOUR_BOT_TOKEN')

        @bot.on('message')
        async def on_message(msg):
            await bot.messages.send(msg.chat_id, f'Echo: {msg.text}')

        @bot.on('callback_query')
        async def on_callback(cb):
            await bot.messages.send(cb.chat_id, f'Button: {cb.callback_data}')

        asyncio.run(bot.start())
    """

    #: Send and manage messages.
    messages: MessagesResource
    #: Access and iterate over chats.
    chats: ChatsResource
    #: Manage webhooks (production deployments).
    webhooks: WebhooksResource
    #: Read bot profile.
    profile: ProfileResource

    def __init__(
        self,
        token:          str,
        *,
        base_url:       str   = 'https://api.kappelas.com',
        max_retries:    int   = 2,
        timeout:        float = 30.0,
        ws_max_retries: int   = 12,
    ) -> None:
        super().__init__()

        self._base = f'/v1/{token}'

        self._http = HttpClient(
            base_url    = base_url,
            auth_header = f'Bearer {token}',
            max_retries = max_retries,
            timeout     = timeout,
        )

        ws_url  = _to_ws_url(base_url, f'{self._base}/ws')
        self._ws = WSClient(ws_url, max_retries=ws_max_retries)

        # Wire WS callbacks
        self._ws.on_raw          = self._on_ws_raw
        self._ws.on_connected    = self._on_ws_connected
        self._ws.on_disconnected = self._on_ws_disconnected
        self._ws.on_error        = self._on_ws_error

        self.messages = MessagesResource(self._http, self._base)
        self.chats    = ChatsResource(self._http, self._base)
        self.webhooks = WebhooksResource(self._http, self._base)
        self.profile  = ProfileResource(self._http, self._base, is_bot=True)

    # ─── WS callbacks ────────────────────────────────────────────────────────

    async def _on_ws_raw(self, event_dict: dict[str, Any]) -> None:
        await self.emit('raw', event_dict)
        parsed = parse_ws_event(event_dict)
        if parsed is not None:
            event_name, obj = parsed
            await self.emit(event_name, obj)

    async def _on_ws_connected(self) -> None:
        await self.emit('connected')

    async def _on_ws_disconnected(self, code: int, reason: str) -> None:
        await self.emit('disconnected', code, reason)

    async def _on_ws_error(self, exc: Exception) -> None:
        await self.emit('error', exc)

    # ─── Public API ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Connect via WebSocket in the background.

        Returns immediately after the connection is established.
        Use :meth:`run` if you want to block until the bot is stopped.

        Example::

            async def main():
                await bot.start()
                await asyncio.Event().wait()   # keep the loop alive

            asyncio.run(main())
        """
        await self._ws.connect()

    async def run(self) -> None:
        """Connect via WebSocket and block until :meth:`stop` is called.

        This is the idiomatic entry point for a long-running bot.

        Example::

            asyncio.run(bot.run())
        """
        self._stop_event = asyncio.Event()
        await self.start()
        await self._stop_event.wait()

    async def stop(self) -> None:
        """Close the WebSocket connection and stop reconnecting."""
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
        await self._ws.disconnect()
        await self._http.close()

    @property
    def connected(self) -> bool:
        """``True`` if the WebSocket is currently open."""
        return self._ws.is_connected()

    def handle_webhook(self, body: dict[str, Any]) -> None:
        """Process a flat webhook payload from Kappela.

        Call this inside your HTTP route handler and respond 200 immediately.
        The same ``on('message')`` and ``on('callback_query')`` handlers fire
        whether you use WebSocket or webhooks.

        Args:
            body: Parsed JSON body of the incoming POST request.

        Example (FastAPI)::

            @app.post('/webhook')
            async def webhook(request: Request):
                bot.handle_webhook(await request.json())
                return {'ok': True}
        """
        parsed = parse_webhook_body(body)
        if parsed is None:
            return

        event_name, obj = parsed

        # Emit 'raw' in { type, data } shape — consistent with WS listeners
        raw_type = 'callback_query' if event_name == 'callback_query' else event_name
        raw_event = {'type': raw_type, 'data': obj}

        loop = self._get_loop()
        if loop and loop.is_running():
            loop.create_task(self._dispatch_webhook(raw_event, event_name, obj))
        else:
            # Fallback: run synchronously in a new event loop (scripts)
            asyncio.run(self._dispatch_webhook(raw_event, event_name, obj))

    async def _dispatch_webhook(
        self,
        raw_event:  dict[str, Any],
        event_name: str,
        obj:        Any,
    ) -> None:
        await self.emit('raw', raw_event)
        await self.emit(event_name, obj)

    @staticmethod
    def _get_loop() -> asyncio.AbstractEventLoop | None:
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return None

    # ─── Context manager ─────────────────────────────────────────────────────

    async def __aenter__(self) -> KappelaBot:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.stop()
