from __future__ import annotations

import asyncio
from typing import Any

from kappelas._emitter import EventEmitter
from kappelas._http import HttpClient
from kappelas._parsers import parse_webhook_body, parse_ws_event
from kappelas._ws import WSClient
from kappelas.bot import _to_ws_url
from kappelas.resources.chats import ChatsResource
from kappelas.resources.messages import MessagesResource
from kappelas.resources.profile import ProfileResource
from kappelas.resources.webhooks import WebhooksResource
from kappelas.types import CallbackQuery, Message


class KappelaUser(EventEmitter):
    """Personal automation SDK for Kappela.

    Authenticate with a personal API key (``sk_...``) to send messages and
    receive events as yourself.

    Args:
        api_key:        Personal API key issued from the Kappela dashboard.
        base_url:       Override the API base URL (default ``'https://api.kappelas.com'``).
        max_retries:    HTTP retry count on 429 / 5xx (default 2).
        timeout:        HTTP request timeout in seconds (default 30.0).
        ws_max_retries: WebSocket reconnect attempt limit (default 12).

    Example::

        import asyncio
        from kappelas import KappelaUser

        me = KappelaUser('sk_...')

        @me.on('message')
        async def on_message(msg):
            print('New message from', msg.sender_name, ':', msg.text)

        asyncio.run(me.start())
    """

    #: Send and manage messages.
    messages: MessagesResource
    #: Access and iterate over chats.
    chats: ChatsResource
    #: Manage webhooks (production deployments).
    webhooks: WebhooksResource
    #: Read your profile.
    profile: ProfileResource

    def __init__(
        self,
        api_key:        str,
        *,
        base_url:       str   = 'https://api.kappelas.com',
        max_retries:    int   = 2,
        timeout:        float = 30.0,
        ws_max_retries: int   = 12,
    ) -> None:
        super().__init__()

        self._base = '/v1/me'

        self._http = HttpClient(
            base_url    = base_url,
            auth_header = f'ApiKey {api_key}',
            max_retries = max_retries,
            timeout     = timeout,
        )

        ws_path  = f'{self._base}/ws?api_key={api_key}'
        ws_url   = _to_ws_url(base_url, ws_path)
        self._ws = WSClient(ws_url, max_retries=ws_max_retries)

        # Wire WS callbacks
        self._ws.on_raw          = self._on_ws_raw
        self._ws.on_connected    = self._on_ws_connected
        self._ws.on_disconnected = self._on_ws_disconnected
        self._ws.on_error        = self._on_ws_error

        self.messages = MessagesResource(self._http, self._base)
        self.chats    = ChatsResource(self._http, self._base)
        self.webhooks = WebhooksResource(self._http, self._base)
        self.profile  = ProfileResource(self._http, self._base, is_bot=False)

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
        """Connect via WebSocket and start receiving events.

        Prefer ``webhooks.set()`` for production. Use ``start()`` in
        development or local scripts.
        """
        await self._ws.connect()

    async def stop(self) -> None:
        """Close the WebSocket connection and stop reconnecting."""
        await self._ws.disconnect()
        await self._http.close()

    @property
    def connected(self) -> bool:
        """``True`` if the WebSocket is currently open."""
        return self._ws.is_connected()

    def handle_webhook(self, body: dict[str, Any]) -> None:
        """Process a flat webhook payload from Kappela.

        Args:
            body: Parsed JSON body of the incoming POST request.
        """
        parsed = parse_webhook_body(body)
        if parsed is None:
            return

        event_name, obj = parsed
        raw_type  = 'callback_query' if event_name == 'callback_query' else event_name
        raw_event = {'type': raw_type, 'data': obj}

        loop = self._get_loop()
        if loop and loop.is_running():
            loop.create_task(self._dispatch_webhook(raw_event, event_name, obj))
        else:
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

    async def __aenter__(self) -> KappelaUser:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.stop()
