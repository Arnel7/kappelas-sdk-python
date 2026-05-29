from __future__ import annotations

from dataclasses import asdict
from typing import Any, AsyncGenerator

from kappelas._http import HttpClient
from kappelas._parsers import (
    parse_add_chat_member_result,
    parse_ban_chat_member_result,
    parse_bot_group_entry,
    parse_chat_invite_link,
    parse_chat_member_info,
    parse_chats_result,
    parse_get_chat_administrators_result,
    parse_get_chat_invite_links_result,
    parse_get_my_groups_result,
    parse_leave_chat_result,
    parse_promote_chat_member_result,
    parse_revoke_chat_invite_link_result,
)
from kappelas.types import (
    AddChatMemberParams,
    AddChatMemberResult,
    BanChatMemberParams,
    BanChatMemberResult,
    BotGroupEntry,
    Chat,
    ChatInviteLink,
    ChatMemberInfo,
    ChatsResult,
    CreateChatInviteLinkParams,
    GetChatAdministratorsParams,
    GetChatAdministratorsResult,
    GetChatInviteLinksParams,
    GetChatInviteLinksResult,
    GetChatMemberParams,
    GetMyGroupsResult,
    LeaveChatParams,
    LeaveChatResult,
    PromoteChatMemberParams,
    PromoteChatMemberResult,
    RevokeChatInviteLinkParams,
    RevokeChatInviteLinkResult,
)


class ChatsResource:
    """Access and iterate over chats, manage members, and handle invite links."""

    def __init__(self, http: HttpClient, base: str) -> None:
        self._http = http
        self._base = base

    # ─── Chat listing ─────────────────────────────────────────────────────────

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

    # ─── Chat member management ───────────────────────────────────────────────

    async def add_member(self, params: AddChatMemberParams) -> AddChatMemberResult:
        """Add a user to a group or channel.

        The bot must be admin of the conversation.

        Example::

            from kappelas.types import AddChatMemberParams
            result = await bot.chats.add_member(
                AddChatMemberParams(chat_id=42, user_id='user-uuid')
            )
        """
        raw = await self._http.post_json(
            f'{self._base}/addChatMember', asdict(params)
        )
        return parse_add_chat_member_result(raw)

    async def ban_member(self, params: BanChatMemberParams) -> BanChatMemberResult:
        """Remove (kick) a user from a group or channel.

        The bot must be admin. To remove itself, use :meth:`leave_chat`.

        Example::

            from kappelas.types import BanChatMemberParams
            result = await bot.chats.ban_member(
                BanChatMemberParams(chat_id=42, user_id='user-uuid')
            )
        """
        raw = await self._http.post_json(
            f'{self._base}/banChatMember', asdict(params)
        )
        return parse_ban_chat_member_result(raw)

    async def leave_chat(self, params: LeaveChatParams) -> LeaveChatResult:
        """Make the bot leave a group or channel.

        Example::

            from kappelas.types import LeaveChatParams
            await bot.chats.leave_chat(LeaveChatParams(chat_id=42))
        """
        raw = await self._http.post_json(
            f'{self._base}/leaveChat', asdict(params)
        )
        return parse_leave_chat_result(raw)

    async def promote_member(self, params: PromoteChatMemberParams) -> PromoteChatMemberResult:
        """Promote or demote a member.

        The bot must be admin.

        * ``role='admin'``   — grants admin rights
        * ``role='member'``  — revokes admin rights

        Example::

            from kappelas.types import PromoteChatMemberParams
            result = await bot.chats.promote_member(
                PromoteChatMemberParams(chat_id=42, user_id='user-uuid', role='admin')
            )
        """
        raw = await self._http.post_json(
            f'{self._base}/promoteChatMember', asdict(params)
        )
        return parse_promote_chat_member_result(raw)

    async def get_administrators(
        self, params: GetChatAdministratorsParams
    ) -> GetChatAdministratorsResult:
        """Return all admins of a group or channel.

        The bot must be a member of the conversation.

        Example::

            from kappelas.types import GetChatAdministratorsParams
            result = await bot.chats.get_administrators(
                GetChatAdministratorsParams(chat_id=42)
            )
            for admin in result.admins:
                print(admin.user_id, admin.role)
        """
        # The API returns the admins array directly as result (not wrapped in an object).
        raw = await self._http.post_json(
            f'{self._base}/getChatAdministrators', asdict(params)
        )
        # raw is a list[dict]
        if isinstance(raw, list):
            return parse_get_chat_administrators_result({'admins': raw})
        return parse_get_chat_administrators_result(raw)

    async def get_member(self, params: GetChatMemberParams) -> ChatMemberInfo:
        """Return info for a specific member (user_id + role).

        The bot must be a member of the conversation.
        Raises ``KappelaError(error_code='NOT_FOUND')`` if the user is not in the chat.

        Example::

            from kappelas.types import GetChatMemberParams
            member = await bot.chats.get_member(
                GetChatMemberParams(chat_id=42, user_id='user-uuid')
            )
            print(member.role)  # 'admin' | 'member'
        """
        raw = await self._http.post_json(
            f'{self._base}/getChatMember', asdict(params)
        )
        return parse_chat_member_info(raw)

    # ─── Invite links ─────────────────────────────────────────────────────────

    async def create_invite_link(
        self, params: CreateChatInviteLinkParams
    ) -> ChatInviteLink:
        """Create an invite link for a group or channel.

        The bot must be admin of the conversation.

        Example::

            from kappelas.types import CreateChatInviteLinkParams

            # Permanent link, unlimited uses
            link = await bot.chats.create_invite_link(
                CreateChatInviteLinkParams(chat_id=42)
            )
            print(link.url)  # "https://kappelas.com/invite/aBcD123xyz"

            # Max 5 uses, expires in 24 hours
            link = await bot.chats.create_invite_link(
                CreateChatInviteLinkParams(chat_id=42, max_uses=5, expires_in='24h')
            )
        """
        body: dict[str, Any] = {'chat_id': params.chat_id}
        if params.max_uses:   body['max_uses']   = params.max_uses
        if params.expires_in: body['expires_in'] = params.expires_in
        raw = await self._http.post_json(f'{self._base}/createChatInviteLink', body)
        return parse_chat_invite_link(raw)

    async def create_single_use_invite_link(
        self, params: CreateChatInviteLinkParams
    ) -> ChatInviteLink:
        """Shorthand to create a single-use invite link.

        Equivalent to :meth:`create_invite_link` with ``max_uses=1``.
        The bot must be admin.

        Example::

            from kappelas.types import CreateChatInviteLinkParams
            link = await bot.chats.create_single_use_invite_link(
                CreateChatInviteLinkParams(chat_id=42)
            )
        """
        from dataclasses import replace
        return await self.create_invite_link(replace(params, max_uses=1))

    async def get_invite_links(
        self, params: GetChatInviteLinksParams
    ) -> GetChatInviteLinksResult:
        """Return all active invite links for a group or channel.

        The bot must be admin.

        Example::

            from kappelas.types import GetChatInviteLinksParams
            result = await bot.chats.get_invite_links(
                GetChatInviteLinksParams(chat_id=42)
            )
            for link in result.invite_links:
                print(f'{link.url} — {link.use_count}/{link.max_uses} uses')
        """
        raw = await self._http.post_json(
            f'{self._base}/getChatInviteLinks', asdict(params)
        )
        return parse_get_chat_invite_links_result(raw)

    async def revoke_invite_link(
        self, params: RevokeChatInviteLinkParams
    ) -> RevokeChatInviteLinkResult:
        """Revoke an active invite link so it can no longer be used.

        The bot must be admin.

        Example::

            from kappelas.types import RevokeChatInviteLinkParams
            result = await bot.chats.revoke_invite_link(
                RevokeChatInviteLinkParams(chat_id=42, code='aBcD123xyz')
            )
        """
        raw = await self._http.post_json(
            f'{self._base}/revokeChatInviteLink', asdict(params)
        )
        return parse_revoke_chat_invite_link_result(raw)

    # ─── Bot group membership ──────────────────────────────────────────────────

    async def get_my_groups(self) -> GetMyGroupsResult:
        """Return every group and channel the bot is a member of.

        Also includes the bot's own role in each conversation.
        Useful to discover which groups the bot can manage.

        Example::

            result = await bot.chats.get_my_groups()
            for group in result.groups:
                print(group.chat_id, group.type, group.title, group.bot_role)
                if group.bot_role == 'admin':
                    # bot can create invite links, manage members…
                    pass
        """
        raw = await self._http.post_json(f'{self._base}/getMyGroups', {})
        return parse_get_my_groups_result(raw)
