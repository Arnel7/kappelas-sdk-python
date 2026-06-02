"""Test LIVE du module communautés contre le backend déployé.
Lancer : KAPPELA_TOKEN=xxxx PYTHONPATH=src python test_communities_live.py
"""
import asyncio
import os
import sys

from kappelas import KappelaBot
from kappelas.resources.communities import (
    CreateCommunityParams, GetCommunityParams,
    CreateCommunityInviteLinkParams, RevokeCommunityInviteLinkParams,
)


async def main() -> int:
    token = os.environ.get('KAPPELA_TOKEN')
    if not token:
        print('KAPPELA_TOKEN non défini — test live ignoré')
        return 0
    bot = KappelaBot(token)

    c = await bot.communities.create(CreateCommunityParams(name='Py SDK live test (auto)'))
    print(f'[OK] create id={c.id}')
    try:
        res = await bot.communities.list()
        role = next((x.role for x in res.communities if x.id == c.id), None)
        print(f"[{'OK' if role == 'admin' else 'FAIL'}] list role={role}")

        inv = await bot.communities.create_invite_link(
            CreateCommunityInviteLinkParams(community_id=c.id, max_uses=1, expires_in='1h'))
        print(f'[OK] invite code={inv.code}')
        await bot.communities.revoke_invite_link(
            RevokeCommunityInviteLinkParams(community_id=c.id, code=inv.code))
        print('[OK] revoke')
    finally:
        await bot.communities.delete(GetCommunityParams(community_id=c.id))
        print(f'[OK] delete id={c.id}')
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
