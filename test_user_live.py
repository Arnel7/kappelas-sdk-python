"""Test LIVE de l'API user (stories + parité) contre le backend déployé.
Lancer : KAPPELA_API_KEY=sk_xxx PYTHONPATH=src python test_user_live.py
"""
import asyncio
import os
import sys
import urllib.request

from kappelas import FileData, KappelaUser


async def main() -> int:
    key = os.environ.get('KAPPELA_API_KEY')
    if not key:
        print('KAPPELA_API_KEY non défini — test live ignoré')
        return 0

    me = KappelaUser(key)
    ok = ko = 0

    async def step(name, coro):
        nonlocal ok, ko
        try:
            r = await coro
            ok += 1
            print(f'[OK] {name}')
            return r
        except Exception as e:  # noqa: BLE001
            ko += 1
            print(f'[KO] {name} — {type(e).__name__}: {str(e).splitlines()[0]}')
            return None

    p = await step('getMe', me.profile.get())
    if p:
        print('     ->', getattr(p, 'username', '?'))

    await step('stories.get_preferences', me.stories.get_preferences())
    await step('stories.list_mine', me.stories.list_mine())
    await step('stories.list', me.stories.list())

    st = await step('stories.create(text)', me.stories.create(type='text', caption='Py SDK live test', audience='all'))
    if st:
        await step('stories.get', me.stories.get(st.id))
        await step('stories.get_viewers', me.stories.get_viewers(st.id))
        await step('stories.delete', me.stories.delete(st.id))

    try:
        data = urllib.request.urlopen('https://picsum.photos/400/600', timeout=15).read()
        img = await step(
            'stories.create(image)',
            me.stories.create(type='image', media=FileData(data=data, filename='t.jpg', content_type='image/jpeg'), caption='img'),
        )
        if img:
            await step('stories.delete(image)', me.stories.delete(img.id))
    except Exception as e:  # noqa: BLE001
        print('     image skip:', e)

    await step('communities.list', me.communities.list())
    c = await step('chats.list', me.chats.list(limit=5))
    if c:
        print('     -> chats:', len(c.chats))

    await me.stop()
    print(f"\n{'ALL OK' if ko == 0 else 'FAIL'}: {ok} OK, {ko} KO")
    return 0 if ko == 0 else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
