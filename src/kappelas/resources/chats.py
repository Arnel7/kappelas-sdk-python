from __future__ import annotations

from typing import AsyncGenerator

from kappelas._http import HttpClient
from kappelas._parsers import parse_chats_result
from kappelas.types import Chat, ChatsResult


class ChatsResource:
    """Access and iterate over chats."""

    def __init__(self, http: HttpClient, base: str) -> None:
        self._http = http
        self._base = base

    async def list(
        self,
        *,
        limit:  int = 20,
        offset: int = 0,
    ) -> ChatsResult:
        """Return a page of chats.

        Args:
            limit:  Maximum number of chats to return (default 20).
            offset: Number of chats to skip (default 0).
        """
        params: dict[str, str] = {}
        if limit  != 20: params['limit']  = str(limit)
        if offset != 0:  params['offset'] = str(offset)

        qs = ('?' + '&'.join(f'{k}={v}' for k, v in params.items())) if params else ''
        raw = await self._http.get(f'{self._base}/getChats{qs}')
        return parse_chats_result(raw)

    async def iterate(self, page_size: int = 50) -> AsyncGenerator[Chat, None]:
        """Async generator that yields every chat, handling pagination automatically.

        Args:
            page_size: Number of chats to fetch per request (default 50).

        Example::

            async for chat in bot.chats.iterate():
                print(chat.title)
        """
        offset = 0
        while True:
            page = await self.list(limit=page_size, offset=offset)
            for chat in page.chats:
                yield chat
            if not page.has_more:
                break
            offset += len(page.chats)
