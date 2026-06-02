"""Tests unitaires du module communautés (mock de HttpClient — aucun réseau).
Lancer : PYTHONPATH=src python test_communities.py
"""
import asyncio
import sys

from kappelas.resources.communities import (
    CommunitiesResource,
    GetCommunityParams, CreateCommunityParams, UpdateCommunityParams,
    AddCommunityMemberParams, PromoteCommunityMemberParams, BanCommunityMemberParams,
    CreateCommunityInviteLinkParams, RevokeCommunityInviteLinkParams,
    CommunityInviteCodeParams, CommunityRequestActionParams,
    AddCommunityGroupParams, RemoveCommunityGroupParams,
)


class FakeHttp:
    def __init__(self):
        self.path = None
        self.body = None
        self.result = {'done': True}

    async def post_json(self, path, body):
        self.path = path
        self.body = body
        return self.result


async def main() -> int:
    h = FakeHttp()
    base = '/v1/test-token'
    r = CommunitiesResource(h, base)
    fails = 0

    def chk(name, cond):
        nonlocal fails
        if cond:
            print(f'  [OK] {name}')
        else:
            fails += 1
            print(f'  [FAIL] {name} — path={h.path} body={h.body}')

    async def expect(name, method, want, coro, result=None):
        if result is not None:
            h.result = result
        h.path, h.body = None, None
        await coro
        chk(f'{name} -> {method}', h.path == f'{base}/{method}')
        if want is not None:
            chk(f'{name} payload', h.body == want)
        h.result = {'done': True}

    cid = {'community_id': 7}
    community = {'id': 7, 'name': 'X'}
    await expect('list', 'getMyCommunities', {}, r.list())
    await expect('get', 'getCommunity', cid, r.get(GetCommunityParams(7)),
                 result={'community': community, 'groups': [], 'members': []})
    await expect('create', 'createCommunity', {'name': 'Devs', 'requires_approval': True},
                 r.create(CreateCommunityParams(name='Devs', requires_approval=True)), result=community)
    await expect('update', 'updateCommunity', {'community_id': 7, 'description': 'd'},
                 r.update(UpdateCommunityParams(community_id=7, description='d')), result=community)
    await expect('delete', 'deleteCommunity', cid, r.delete(GetCommunityParams(7)))
    await expect('join', 'joinCommunity', cid, r.join(GetCommunityParams(7)))
    await expect('add_member', 'addCommunityMember', {'community_id': 7, 'user_id': 'u', 'role': 'member'},
                 r.add_member(AddCommunityMemberParams(7, 'u')))
    await expect('promote_member', 'promoteCommunityMember', {'community_id': 7, 'user_id': 'u', 'role': 'admin'},
                 r.promote_member(PromoteCommunityMemberParams(7, 'u', 'admin')))
    await expect('ban_member', 'banCommunityMember', {'community_id': 7, 'user_id': 'u'},
                 r.ban_member(BanCommunityMemberParams(7, 'u')))
    await expect('leave', 'leaveCommunity', cid, r.leave(GetCommunityParams(7)))
    await expect('create_invite_link', 'createCommunityInviteLink', {'community_id': 7, 'max_uses': 1, 'expires_in': '24h'},
                 r.create_invite_link(CreateCommunityInviteLinkParams(7, 1, '24h')),
                 result={'code': 'c', 'community_id': 7, 'created_by': '', 'max_uses': 1, 'use_count': 0, 'created_at': ''})
    await expect('get_invite_links', 'getCommunityInviteLinks', cid, r.get_invite_links(GetCommunityParams(7)))
    await expect('revoke_invite_link', 'revokeCommunityInviteLink', {'community_id': 7, 'code': 'c'},
                 r.revoke_invite_link(RevokeCommunityInviteLinkParams(7, 'c')))

    # endpoints renvoyant un objet → on fournit un résultat compatible
    await expect('preview_invite', 'previewCommunityInvite', {'code': 'c'}, r.preview_invite(CommunityInviteCodeParams('c')),
                 result={'code': 'c', 'community_id': 7, 'community_name': 'X', 'member_count': 3})
    await expect('accept_invite', 'acceptCommunityInvite', {'code': 'c'}, r.accept_invite(CommunityInviteCodeParams('c')),
                 result={'community_id': 7})

    # endpoints renvoyant un tableau
    await expect('get_join_requests', 'getCommunityJoinRequests', cid, r.get_join_requests(GetCommunityParams(7)), result=[])
    await expect('get_group_requests', 'getCommunityGroupRequests', cid, r.get_group_requests(GetCommunityParams(7)), result=[])

    rb = {'community_id': 7, 'request_id': 3}
    await expect('approve_join_request', 'approveCommunityJoinRequest', rb, r.approve_join_request(CommunityRequestActionParams(7, 3)))
    await expect('reject_join_request', 'rejectCommunityJoinRequest', rb, r.reject_join_request(CommunityRequestActionParams(7, 3)))
    await expect('approve_group_request', 'approveCommunityGroupRequest', rb, r.approve_group_request(CommunityRequestActionParams(7, 3)))
    await expect('reject_group_request', 'rejectCommunityGroupRequest', rb, r.reject_group_request(CommunityRequestActionParams(7, 3)))
    await expect('add_group', 'addCommunityGroup', {'community_id': 7, 'conversation_id': 9}, r.add_group(AddCommunityGroupParams(7, 9)))
    await expect('remove_group', 'removeCommunityGroup', {'community_id': 7, 'conversation_id': 9}, r.remove_group(RemoveCommunityGroupParams(7, 9)))

    # list_admin filtre role=='admin' + désérialisation
    h.result = {'communities': [
        {'id': 1, 'name': 'A', 'role': 'admin'},
        {'id': 2, 'name': 'B', 'role': 'member'},
        {'id': 3, 'name': 'C', 'role': 'admin'},
    ]}
    admins = await r.list_admin()
    chk('list_admin filtre role=admin', [c.id for c in admins] == [1, 3])

    print(f'\n=== {("ECHECS: " + str(fails)) if fails else "TOUT PASSE"} ===')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
