from __future__ import annotations

from kappelas._http import HttpClient
from kappelas._parsers import parse_bot_profile, parse_user_profile
from kappelas.types import BotProfile, UserProfile


class ProfileResource:
    """Fetch the profile of the authenticated bot or user."""

    def __init__(self, http: HttpClient, base: str, *, is_bot: bool) -> None:
        self._http   = http
        self._base   = base
        self._is_bot = is_bot

    async def get(self) -> BotProfile | UserProfile:
        """Return the authenticated entity's own profile."""
        if self._is_bot:
            raw = await self._http.post_json(f'{self._base}/getMe', {})
            return parse_bot_profile(raw)
        else:
            raw = await self._http.get(f'{self._base}/getMe')
            return parse_user_profile(raw)
