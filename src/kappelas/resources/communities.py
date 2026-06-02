"""Gestion des communautés par un bot (membres, rôles, invites, demandes).

Un bot administre une communauté seulement s'il en est **admin**. Pour rendre
quelqu'un (personne OU bot) admin : on l'ajoute d'abord membre, puis on le promeut.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .._http import HttpClient


# ─── Types (résultats) ────────────────────────────────────────────────────────

@dataclass
class Community:
    id: int
    name: str
    created_by: str
    requires_approval: bool
    created_at: str
    description: str | None = None
    avatar_url: str | None = None
    announcement_channel_id: int | None = None
    #: Rôle DANS LA COMMUNAUTÉ ('member'|'admin'), renseigné par ``list()`` seulement.
    #: ⚠️ distinct du rôle dans un groupe rattaché.
    role: str | None = None


@dataclass
class CommunityMember:
    community_id: int
    user_id: str
    role: str
    joined_at: str
    name: str | None = None
    avatar_url: str | None = None


@dataclass
class CommunityGroup:
    id: int
    type: str
    joined: bool
    pending: bool
    participants_count: int
    title: str | None = None
    avatar_url: str | None = None


@dataclass
class CommunityDetail:
    community: Community
    groups: list[CommunityGroup]
    members: list[CommunityMember]


@dataclass
class CommunityInvite:
    code: str
    community_id: int
    created_by: str
    max_uses: int
    use_count: int
    created_at: str
    expires_at: str | None = None
    revoked_at: str | None = None


@dataclass
class CommunityInvitePreview:
    code: str
    community_id: int
    community_name: str
    member_count: int
    expires_at: str | None = None
    avatar_url: str | None = None
    description: str | None = None


@dataclass
class CommunityJoinRequest:
    id: int
    community_id: int
    user_id: str
    status: str
    created_at: str
    requester_name: str | None = None
    requester_avatar_url: str | None = None


@dataclass
class CommunityGroupRequest:
    id: int
    community_id: int
    conversation_id: int
    group_name: str
    requested_by: str
    status: str
    created_at: str


@dataclass
class CommunityActionResult:
    #: ``True`` au succès ; ``pending`` ``True`` si une adhésion est mise en attente.
    done: bool = False
    pending: bool = False


@dataclass
class GetMyCommunitiesResult:
    communities: list[Community]


@dataclass
class GetCommunityInviteLinksResult:
    invites: list[CommunityInvite]


@dataclass
class AcceptCommunityInviteResult:
    community_id: int


# ─── Params ───────────────────────────────────────────────────────────────────

@dataclass
class GetCommunityParams:
    community_id: int


@dataclass
class CreateCommunityParams:
    name: str
    description: str | None = None
    avatar_url: str | None = None
    requires_approval: bool | None = None


@dataclass
class UpdateCommunityParams:
    community_id: int
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    announcement_channel_id: int | None = None
    requires_approval: bool | None = None


@dataclass
class AddCommunityMemberParams:
    community_id: int
    user_id: str
    role: str = 'member'  # 'member' | 'admin'


@dataclass
class PromoteCommunityMemberParams:
    community_id: int
    user_id: str
    role: str  # 'admin' promeut, 'member' rétrograde


@dataclass
class BanCommunityMemberParams:
    community_id: int
    user_id: str


@dataclass
class CreateCommunityInviteLinkParams:
    community_id: int
    max_uses: int = 0           # 0 = illimité
    expires_in: str | None = None  # '1h'|'24h'|'7d'|'30d'|'never'


@dataclass
class RevokeCommunityInviteLinkParams:
    community_id: int
    code: str


@dataclass
class CommunityInviteCodeParams:
    code: str


@dataclass
class CommunityRequestActionParams:
    community_id: int
    request_id: int


@dataclass
class AddCommunityGroupParams:
    community_id: int
    conversation_id: int


@dataclass
class RemoveCommunityGroupParams:
    community_id: int
    conversation_id: int


# ─── Parsers ──────────────────────────────────────────────────────────────────

def _community(d: dict[str, Any]) -> Community:
    return Community(
        id=int(d['id']), name=str(d['name']), created_by=str(d.get('created_by', '')),
        requires_approval=bool(d.get('requires_approval', False)),
        created_at=str(d.get('created_at', '')),
        description=d.get('description'), avatar_url=d.get('avatar_url'),
        announcement_channel_id=d.get('announcement_channel_id'), role=d.get('role'),
    )


def _member(d: dict[str, Any]) -> CommunityMember:
    return CommunityMember(
        community_id=int(d['community_id']), user_id=str(d['user_id']),
        role=str(d.get('role', 'member')), joined_at=str(d.get('joined_at', '')),
        name=d.get('name'), avatar_url=d.get('avatar_url'),
    )


def _group(d: dict[str, Any]) -> CommunityGroup:
    return CommunityGroup(
        id=int(d['id']), type=str(d.get('type', '')),
        joined=bool(d.get('joined', False)), pending=bool(d.get('pending', False)),
        participants_count=int(d.get('participants_count', 0)),
        title=d.get('title'), avatar_url=d.get('avatar_url'),
    )


def _invite(d: dict[str, Any]) -> CommunityInvite:
    return CommunityInvite(
        code=str(d['code']), community_id=int(d['community_id']),
        created_by=str(d.get('created_by', '')), max_uses=int(d.get('max_uses', 0)),
        use_count=int(d.get('use_count', 0)), created_at=str(d.get('created_at', '')),
        expires_at=d.get('expires_at'), revoked_at=d.get('revoked_at'),
    )


def _join_request(d: dict[str, Any]) -> CommunityJoinRequest:
    return CommunityJoinRequest(
        id=int(d['id']), community_id=int(d['community_id']), user_id=str(d['user_id']),
        status=str(d.get('status', '')), created_at=str(d.get('created_at', '')),
        requester_name=d.get('requester_name'), requester_avatar_url=d.get('requester_avatar_url'),
    )


def _group_request(d: dict[str, Any]) -> CommunityGroupRequest:
    return CommunityGroupRequest(
        id=int(d['id']), community_id=int(d['community_id']),
        conversation_id=int(d['conversation_id']), group_name=str(d.get('group_name', '')),
        requested_by=str(d.get('requested_by', '')), status=str(d.get('status', '')),
        created_at=str(d.get('created_at', '')),
    )


def _action(d: Any) -> CommunityActionResult:
    d = d or {}
    return CommunityActionResult(done=bool(d.get('done', False)), pending=bool(d.get('pending', False)))


def _body(params: Any) -> dict[str, Any]:
    """asdict en omettant les champs None (pour que update() n'écrase pas les champs absents)."""
    return {k: v for k, v in asdict(params).items() if v is not None}


class CommunitiesResource:
    """``bot.communities`` — gestion des communautés."""

    def __init__(self, http: HttpClient, base: str) -> None:
        self._http = http
        self._base = base

    # ── Lecture / CRUD ──
    async def list(self) -> GetMyCommunitiesResult:
        raw = await self._http.post_json(f'{self._base}/getMyCommunities', {})
        return GetMyCommunitiesResult(communities=[_community(c) for c in (raw or {}).get('communities', [])])

    async def list_admin(self) -> list[Community]:
        """Communautés où le bot est admin (filtre role=='admin')."""
        res = await self.list()
        return [c for c in res.communities if c.role == 'admin']

    async def get(self, params: GetCommunityParams) -> CommunityDetail:
        raw = await self._http.post_json(f'{self._base}/getCommunity', _body(params))
        return CommunityDetail(
            community=_community(raw['community']),
            groups=[_group(g) for g in raw.get('groups', [])],
            members=[_member(m) for m in raw.get('members', [])],
        )

    async def create(self, params: CreateCommunityParams) -> Community:
        return _community(await self._http.post_json(f'{self._base}/createCommunity', _body(params)))

    async def update(self, params: UpdateCommunityParams) -> Community:
        return _community(await self._http.post_json(f'{self._base}/updateCommunity', _body(params)))

    async def delete(self, params: GetCommunityParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/deleteCommunity', _body(params)))

    async def join(self, params: GetCommunityParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/joinCommunity', _body(params)))

    # ── Membres ──
    async def add_member(self, params: AddCommunityMemberParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/addCommunityMember', _body(params)))

    async def promote_member(self, params: PromoteCommunityMemberParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/promoteCommunityMember', _body(params)))

    async def ban_member(self, params: BanCommunityMemberParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/banCommunityMember', _body(params)))

    async def leave(self, params: GetCommunityParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/leaveCommunity', _body(params)))

    # ── Liens d'invitation ──
    async def create_invite_link(self, params: CreateCommunityInviteLinkParams) -> CommunityInvite:
        return _invite(await self._http.post_json(f'{self._base}/createCommunityInviteLink', _body(params)))

    async def get_invite_links(self, params: GetCommunityParams) -> GetCommunityInviteLinksResult:
        raw = await self._http.post_json(f'{self._base}/getCommunityInviteLinks', _body(params))
        return GetCommunityInviteLinksResult(invites=[_invite(i) for i in (raw or {}).get('invites', [])])

    async def revoke_invite_link(self, params: RevokeCommunityInviteLinkParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/revokeCommunityInviteLink', _body(params)))

    async def preview_invite(self, params: CommunityInviteCodeParams) -> CommunityInvitePreview:
        d = await self._http.post_json(f'{self._base}/previewCommunityInvite', _body(params))
        return CommunityInvitePreview(
            code=str(d['code']), community_id=int(d['community_id']),
            community_name=str(d.get('community_name', '')), member_count=int(d.get('member_count', 0)),
            expires_at=d.get('expires_at'), avatar_url=d.get('avatar_url'), description=d.get('description'),
        )

    async def accept_invite(self, params: CommunityInviteCodeParams) -> AcceptCommunityInviteResult:
        d = await self._http.post_json(f'{self._base}/acceptCommunityInvite', _body(params))
        return AcceptCommunityInviteResult(community_id=int((d or {}).get('community_id', 0)))

    # ── Demandes d'adhésion (user → communauté) ──
    async def get_join_requests(self, params: GetCommunityParams) -> list[CommunityJoinRequest]:
        raw = await self._http.post_json(f'{self._base}/getCommunityJoinRequests', _body(params))
        return [_join_request(r) for r in (raw or [])]

    async def approve_join_request(self, params: CommunityRequestActionParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/approveCommunityJoinRequest', _body(params)))

    async def reject_join_request(self, params: CommunityRequestActionParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/rejectCommunityJoinRequest', _body(params)))

    # ── Demandes de groupe + liaison de groupes ──
    async def get_group_requests(self, params: GetCommunityParams) -> list[CommunityGroupRequest]:
        raw = await self._http.post_json(f'{self._base}/getCommunityGroupRequests', _body(params))
        return [_group_request(r) for r in (raw or [])]

    async def approve_group_request(self, params: CommunityRequestActionParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/approveCommunityGroupRequest', _body(params)))

    async def reject_group_request(self, params: CommunityRequestActionParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/rejectCommunityGroupRequest', _body(params)))

    async def add_group(self, params: AddCommunityGroupParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/addCommunityGroup', _body(params)))

    async def remove_group(self, params: RemoveCommunityGroupParams) -> CommunityActionResult:
        return _action(await self._http.post_json(f'{self._base}/removeCommunityGroup', _body(params)))
