"""
Tests live du SDK Kappelas Python — v0.2.0.

Ce fichier teste :
  - Connexion WebSocket
  - Profil bot
  - Chats : list (avec offset), iterate, get_my_groups
  - Messages : texte, formatage riche, photo, vidéo, document, audio, carousel
  - Keyboards : inline, reply, scroll (formes courte + longue + mixte)
  - reply_to_id (citation)
  - delete_previous
  - bot.reply() : depuis Message
  - Edit texte + Edit clavier seul (new_extra_data)
  - Delete
  - Typing indicator
  - Webhooks : get_info, handle_webhook (unit test sans serveur HTTP)
  - Membres du groupe : get_administrators, get_member, get_member NOT_FOUND
  - Invite links (admin requis — skippé si pas de groupe admin)
  - Messages dans le groupe : texte, reply_to_id, photo, carousel, inline
  - Gestion erreurs attendues : FORBIDDEN, KappelaError fields

Usage :
    python test_all.py <TOKEN> [CHAT_ID]
ou via variables d'environnement :
    KAPPELA_TOKEN=xxx CHAT_ID=130 python test_all.py
"""
import asyncio
import base64
import json
import os
import sys

sys.path.insert(0, 'src')

from kappelas import KappelaBot, KappelaError
from kappelas.types import (
    AddChatMemberParams,
    BanChatMemberParams,
    CarouselCard,
    ChatInviteLink,
    CreateChatInviteLinkParams,
    FileData,
    GetChatAdministratorsParams,
    GetChatInviteLinksParams,
    GetChatMemberParams,
    GetMyGroupsResult,
    InlineKeyboard,
    InlineKeyboardButton,
    LeaveChatParams,
    PromoteChatMemberParams,
    ReplyKeyboard,
    ReplyKeyboardButton,
    RevokeChatInviteLinkParams,
    ScrollKeyboard,
    ScrollKeyboardButton,
)

TOKEN   = os.environ.get('KAPPELA_TOKEN') or (sys.argv[1] if len(sys.argv) > 1 else None)
CHAT_ID = int(os.environ.get('CHAT_ID') or (sys.argv[2] if len(sys.argv) > 2 else 130))

if not TOKEN:
    print('Usage: python test_all.py <TOKEN> [CHAT_ID]')
    sys.exit(1)

# ─── Fichiers de test en mémoire ─────────────────────────────────────────────

# PNG 1×1 pixel transparent valide
PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)

# WAV silence PCM 16bit
WAV = bytes.fromhex(
    '52494646' '26000000' '57415645'
    '666d7420' '10000000' '01000100' '44ac0000' '88580100' '02001000'
    '64617461' '02000000' '0000'
)

# PDF minimal valide
PDF = (
    b'%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj '
    b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj '
    b'3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\n'
    b'xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n'
    b'0000000058 00000 n\n0000000115 00000 n\n'
    b'trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF'
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

passed  = 0
failed  = 0
skipped = 0

SEP = '─' * 60
SEP2 = '═' * 60


def section(title: str) -> None:
    print(f'\n{SEP}\n  {title}\n{SEP}')


async def run(label: str, coro):
    global passed, failed
    print(f'\n→ {label}')
    try:
        result = await coro
        out = json.dumps(result, default=str)
        if len(out) > 200:
            out = out[:200] + '…'
        print(f'  [✓] OK  {out}')
        passed += 1
        return result
    except KappelaError as e:
        print(f'  [✗] FAIL  KappelaError {e.error_code} ({e.status}): {e.args[0]}')
        failed += 1
        return None
    except Exception as e:
        print(f'  [✗] FAIL  {e}')
        failed += 1
        return None


async def run_expect_error(label: str, expected_code: str, coro_fn):
    """Vérifie qu'une erreur avec le code attendu est bien retournée."""
    global passed, failed
    print(f'\n→ {label} (attendu : {expected_code})')
    try:
        coro = coro_fn()
        await coro
        print(f'  [✗] FAIL — aurait dû retourner une erreur')
        failed += 1
        return False
    except KappelaError as e:
        if e.error_code == expected_code:
            print(f'  [✓] OK  KappelaError {e.error_code} reçue comme attendu')
            passed += 1
            return True
        else:
            print(f'  [✗] FAIL — mauvaise erreur : {e.error_code} ({e.status})')
            failed += 1
            return False
    except Exception as e:
        print(f'  [✗] FAIL — exception inattendue : {e}')
        failed += 1
        return False


def skip_test(label: str, reason: str) -> None:
    global skipped
    print(f'\n→ {label}\n  [⊘] SKIPPED — {reason}')
    skipped += 1


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    bot = KappelaBot(token=TOKEN)

    connected = asyncio.Event()

    @bot.once('connected')
    async def on_connected():
        connected.set()

    @bot.on('callback_query')
    async def on_callback(cb):
        print(f'\n[→] Bouton cliqué — chat_id={cb.chat_id} sender="{cb.sender_nom or cb.sender_id}" data="{cb.callback_data}"')
        try:
            result = await bot.messages.send(cb.chat_id, f'Tu as cliqué : {cb.callback_data}')
            print(f'[✓] Réponse callback envoyée — message_id={result.message_id}')
        except KappelaError as e:
            print(f'[✗] KappelaError {e.error_code} ({e.status}): {e.args[0]}')

    await bot.start()

    try:
        await asyncio.wait_for(connected.wait(), timeout=10)
    except asyncio.TimeoutError:
        print('[✗] Timeout connexion WebSocket')
        sys.exit(1)

    print(f'[✓] Connecté — chat_id cible : {CHAT_ID}\n')

    # ═══════════════════════════════════════════════════════════════════════════
    section('1. PROFIL')
    # ═══════════════════════════════════════════════════════════════════════════

    await run('profile.get()', bot.profile.get())

    # ═══════════════════════════════════════════════════════════════════════════
    section('2. CHATS')
    # ═══════════════════════════════════════════════════════════════════════════

    await run('chats.list({ limit: 5 })', bot.chats.list(limit=5))
    await run('chats.list() — avec offset', bot.chats.list(limit=3, offset=1))

    async def _iterate_first():
        async for chat in bot.chats.iterate(page_size=1):
            return {'chat_id': chat.chat_id, 'type': chat.type}
        raise Exception('aucun chat retourné')

    await run('chats.iterate() — premier chat', _iterate_first())

    # GetMyGroups — récupéré pour les sections suivantes
    my_groups: GetMyGroupsResult | None = None
    res = await run('chats.get_my_groups()', bot.chats.get_my_groups())
    if res is not None:
        my_groups = res
        print(f'  [ℹ] {len(my_groups.groups)} groupe(s)/canal')
        for g in my_groups.groups:
            print(f'      {g.chat_id} ({g.type}) "{g.title or "(sans titre)"}" → {g.bot_role}')

    # Trouver un groupe quelconque et un groupe admin
    any_group_id = 0
    admin_group_id = 0
    if my_groups:
        for g in my_groups.groups:
            if not any_group_id:
                any_group_id = g.chat_id
            if g.bot_role == 'admin' and not admin_group_id:
                admin_group_id = g.chat_id

    if admin_group_id:
        print(f'  [ℹ] Groupe admin : chat_id={admin_group_id}')
    else:
        print('  [ℹ] Aucun groupe admin — certains tests seront ignorés')

    # ═══════════════════════════════════════════════════════════════════════════
    section('3. TEXTE SIMPLE + FORMATAGE')
    # ═══════════════════════════════════════════════════════════════════════════

    sent_plain = await run(
        'messages.send() — texte simple',
        bot.messages.send(CHAT_ID, '👋 Test SDK Python — texte simple'),
    )

    await run(
        'messages.send() — gras, italique, barré, code inline',
        bot.messages.send(CHAT_ID, '*gras*  __italique__  ~barré~  `code inline`'),
    )

    await run(
        'messages.send() — bloc code',
        bot.messages.send(CHAT_ID, 'Ta clé API :\n```\nsk_live_test_abc123xyz\n```'),
    )

    await run(
        'messages.send() — citation (>)',
        bot.messages.send(CHAT_ID, '> Question originale de l\'utilisateur\n\nVoici la réponse détaillée.'),
    )

    await run(
        'messages.send() — mention + commande',
        bot.messages.send(CHAT_ID, 'Merci @test ! Tape /help pour voir les commandes disponibles.'),
    )

    await run(
        'messages.send() — lien auto-détecté',
        bot.messages.send(CHAT_ID, 'Visitez kappelas.com ou https://kappelas.com/docs'),
    )

    await run(
        'messages.send() — formatage combiné',
        bot.messages.send(CHAT_ID, '\n'.join([
            '🛒 *Récapitulatif commande*',
            '',
            '> Widget A × 2',
            '',
            'Total : **49 980 FCFA**',
            'Statut : `CONFIRMÉ`',
            '',
            'Questions ? contact@example.com ou /help',
        ])),
    )

    # ═══════════════════════════════════════════════════════════════════════════
    section('4. REPLY_TO_ID (CITATION DE MESSAGE)')
    # ═══════════════════════════════════════════════════════════════════════════

    if sent_plain and sent_plain.message_id:
        await run(
            'messages.send() — reply_to_id cite le message précédent',
            bot.messages.send(
                CHAT_ID,
                '↩️ Réponse avec citation du message précédent',
                reply_to_id=sent_plain.message_id,
            ),
        )
    else:
        skip_test('messages.send() — reply_to_id', 'message de référence absent')

    # ═══════════════════════════════════════════════════════════════════════════
    section('4B. BOT.REPLY()')
    # ═══════════════════════════════════════════════════════════════════════════

    if sent_plain and sent_plain.message_id:
        from kappelas.types import Message as KMessage
        synthetic_msg = KMessage(
            id=sent_plain.message_id,
            chat_id=CHAT_ID,
            sender_id=None,
            type='text',
            text='(synthetic)',
            media_id=None,
            extra_data=None,
            status='sent',
            edited_at=None,
            deleted_at=None,
            created_at=0,
            reply_to_id=None,
            reply_to_snapshot=None,
            mentions=[],
            forwarded_from=None,
            expires_at=None,
        )
        await run(
            'bot.reply(msg, text) — reply_to_id injecté automatiquement',
            bot.reply(synthetic_msg, '↩️ bot.reply(msg) — reply_to_id injecté automatiquement'),
        )

        await run(
            'bot.reply(msg, text, reply_markup=...) — avec inline keyboard',
            bot.reply(
                synthetic_msg,
                'bot.reply() avec clavier inline :',
                reply_markup=InlineKeyboard(inline_keyboard=[[
                    InlineKeyboardButton(text='✅ OK', callback_data='reply_ok'),
                    InlineKeyboardButton(text='❌ Annuler', callback_data='reply_cancel'),
                ]]),
            ),
        )
    else:
        skip_test('bot.reply(msg)', 'message de référence absent')

    # ═══════════════════════════════════════════════════════════════════════════
    section('5. KEYBOARDS')
    # ═══════════════════════════════════════════════════════════════════════════

    # Inline keyboard
    await run(
        'messages.send() — inline keyboard',
        bot.messages.send(
            CHAT_ID,
            'Test inline keyboard :',
            reply_markup=InlineKeyboard(inline_keyboard=[
                [
                    InlineKeyboardButton(text='✅ Oui', callback_data='yes'),
                    InlineKeyboardButton(text='❌ Non', callback_data='no'),
                ],
                [InlineKeyboardButton(text='🌐 Site', url='https://kappelas.com')],
            ]),
        ),
    )

    # Reply keyboard — forme courte (label == callback)
    await run(
        'messages.send() — reply keyboard (forme courte)',
        bot.messages.send(
            CHAT_ID,
            'Test reply keyboard (forme courte) :',
            reply_markup=ReplyKeyboard(keyboard=[
                [ReplyKeyboardButton('📦 Mes commandes'), ReplyKeyboardButton('❓ Aide')],
                [ReplyKeyboardButton('🔙 Retour')],
            ]),
        ),
    )

    # Reply keyboard — plain strings (compatible shorthand)
    await run(
        'messages.send() — reply keyboard (chaînes simples)',
        bot.messages.send(
            CHAT_ID,
            'Test reply keyboard (strings) :',
            reply_markup=ReplyKeyboard(keyboard=[['Option A', 'Option B'], ['Annuler']]),
        ),
    )

    # Reply keyboard — forme longue (label ≠ callback)
    await run(
        'messages.send() — reply keyboard (forme longue)',
        bot.messages.send(
            CHAT_ID,
            'Test reply keyboard (forme longue) :',
            reply_markup=ReplyKeyboard(keyboard=[
                [
                    ReplyKeyboardButton(text='✅ Oui', callback_data='confirm_yes'),
                    ReplyKeyboardButton(text='❌ Non', callback_data='confirm_no'),
                ],
                [ReplyKeyboardButton(text='↩ Annuler', callback_data='cancel')],
            ]),
        ),
    )

    # Reply keyboard — mixte
    await run(
        'messages.send() — reply keyboard (mixte)',
        bot.messages.send(
            CHAT_ID,
            'Test reply keyboard (mixte) :',
            reply_markup=ReplyKeyboard(keyboard=[[
                ReplyKeyboardButton(text='✅ Confirmer', callback_data='confirm'),
                ReplyKeyboardButton(text='❓ Aide'),  # forme courte
            ]]),
        ),
    )

    # Scroll keyboard — forme courte
    await run(
        'messages.send() — scroll keyboard (forme courte)',
        bot.messages.send(
            CHAT_ID,
            'Test scroll keyboard (forme courte) :',
            reply_markup=ScrollKeyboard(scroll_keyboard=[
                ReplyKeyboardButton('📦 Commandes'),
                ReplyKeyboardButton('❓ Aide'),
                ReplyKeyboardButton('⚙️ Paramètres'),
            ]),
        ),
    )

    # Scroll keyboard — plain strings
    await run(
        'messages.send() — scroll keyboard (chaînes simples)',
        bot.messages.send(
            CHAT_ID,
            'Test scroll keyboard (strings) :',
            reply_markup=ScrollKeyboard(scroll_keyboard=['Petit', 'Moyen', 'Grand', 'XL']),
        ),
    )

    # Scroll keyboard — forme longue
    await run(
        'messages.send() — scroll keyboard (forme longue)',
        bot.messages.send(
            CHAT_ID,
            'Test scroll keyboard (forme longue) :',
            reply_markup=ScrollKeyboard(scroll_keyboard=[
                ScrollKeyboardButton(text='📦 Commandes', callback_data='menu_orders'),
                ScrollKeyboardButton(text='❓ Aide',      callback_data='menu_help'),
                ScrollKeyboardButton(text='⚙️ Paramètres', callback_data='menu_settings'),
            ]),
        ),
    )

    # Scroll keyboard — mixte
    await run(
        'messages.send() — scroll keyboard (mixte)',
        bot.messages.send(
            CHAT_ID,
            'Test scroll keyboard (mixte) :',
            reply_markup=ScrollKeyboard(scroll_keyboard=[
                ScrollKeyboardButton(text='📦 Commandes', callback_data='menu_orders'),
                ScrollKeyboardButton(text='❓ Aide'),  # forme courte
            ]),
        ),
    )

    # ═══════════════════════════════════════════════════════════════════════════
    section('6. MÉDIAS')
    # ═══════════════════════════════════════════════════════════════════════════

    await run('messages.send_typing() — show', bot.messages.send_typing(CHAT_ID))
    await run('messages.send_typing() — hide', bot.messages.send_typing(CHAT_ID, is_typing=False))

    await run(
        'messages.send_photo()',
        bot.messages.send_photo(
            CHAT_ID,
            FileData(data=PNG, filename='test.png', content_type='image/png'),
            caption='🖼 Photo test depuis le SDK Python',
        ),
    )

    await run(
        'messages.send_document()',
        bot.messages.send_document(
            CHAT_ID,
            FileData(data=PDF, filename='test.pdf', content_type='application/pdf'),
            caption='📄 Document PDF test',
        ),
    )

    await run(
        'messages.send_audio()',
        bot.messages.send_audio(
            CHAT_ID,
            FileData(data=WAV, filename='test.wav', content_type='audio/wav'),
            caption='🔊 Audio test',
        ),
    )

    await run(
        'messages.send_video()',
        bot.messages.send_video(
            CHAT_ID,
            FileData(data=PNG, filename='test.mp4', content_type='video/mp4'),
            caption='🎬 Vidéo test (PNG placeholder)',
        ),
    )

    # Photo avec reply_to_id
    if sent_plain and sent_plain.message_id:
        await run(
            'messages.send_photo() — avec reply_to_id',
            bot.messages.send_photo(
                CHAT_ID,
                FileData(data=PNG, filename='test.png', content_type='image/png'),
                caption='🖼 Photo en réponse',
                reply_to_id=sent_plain.message_id,
            ),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    section('7. CAROUSEL')
    # ═══════════════════════════════════════════════════════════════════════════

    await run(
        'messages.send_carousel() — quick_reply forme courte',
        bot.messages.send_carousel(
            CHAT_ID,
            carousel=[
                CarouselCard(id='p1', title='Widget A', subtitle='9 990 FCFA', button_text='Acheter'),
                CarouselCard(id='p2', title='Widget B', subtitle='19 990 FCFA', button_text='Acheter'),
            ],
            text='🛍 Nos produits :',
            quick_reply_buttons=['Voir plus', 'Annuler'],
        ),
    )

    await run(
        'messages.send_carousel() — quick_reply forme longue {text, callback_data}',
        bot.messages.send_carousel(
            CHAT_ID,
            carousel=[
                CarouselCard(id='p3', title='Widget C', subtitle='4 990 FCFA', button_text='Commander'),
            ],
            text='🛍 Sélection :',
            quick_reply_buttons=[
                ScrollKeyboardButton(text='✅ Confirmer', callback_data='confirm'),
                ScrollKeyboardButton(text='❌ Annuler',  callback_data='cancel'),
            ],
        ),
    )

    if sent_plain and sent_plain.message_id:
        await run(
            'messages.send_carousel() — avec reply_to_id',
            bot.messages.send_carousel(
                CHAT_ID,
                carousel=[
                    CarouselCard(id='p4', title='Offre spéciale', subtitle='2 990 FCFA', button_text='Commander'),
                ],
                text='↩️ Voici les produits en lien avec ta question :',
                reply_to_id=sent_plain.message_id,
            ),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    section('8. EDIT / DELETE')
    # ═══════════════════════════════════════════════════════════════════════════

    to_edit = await run(
        'messages.send() — message à éditer',
        bot.messages.send(
            CHAT_ID,
            '📝 Message original (sera modifié)',
            reply_markup=InlineKeyboard(inline_keyboard=[[
                InlineKeyboardButton(text='🔴 Avant', callback_data='before'),
            ]]),
        ),
    )

    if to_edit and to_edit.message_id:
        await run(
            'messages.edit() — nouveau texte',
            bot.messages.edit(CHAT_ID, to_edit.message_id, new_text='✅ Message modifié avec succès'),
        )

        # Edit clavier inline seul (new_extra_data sans new_text)
        new_kb = InlineKeyboard(inline_keyboard=[[
            InlineKeyboardButton(text='🟢 Après', callback_data='after'),
        ]])
        from dataclasses import asdict
        await run(
            'messages.edit() — clavier inline seul (sans changer le texte)',
            bot.messages.edit(
                CHAT_ID,
                to_edit.message_id,
                new_extra_data=asdict(new_kb),
            ),
        )

    # Supprimer le message texte du début
    if sent_plain and sent_plain.message_id:
        await run(
            f'messages.delete() — message_id={sent_plain.message_id}',
            bot.messages.delete(CHAT_ID, sent_plain.message_id),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    section('9. DELETE_PREVIOUS')
    # ═══════════════════════════════════════════════════════════════════════════

    dp1 = await run(
        'messages.send() — message 1 (sera remplacé)',
        bot.messages.send(CHAT_ID, '⏳ Message temporaire 1'),
    )
    if dp1:
        await run(
            'messages.send() — delete_previous=True efface le précédent',
            bot.messages.send(
                CHAT_ID,
                '✅ Remplace le message précédent (delete_previous)',
                delete_previous=True,
            ),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    section('10. WEBHOOKS')
    # ═══════════════════════════════════════════════════════════════════════════

    await run('webhooks.get_info()', bot.webhooks.get_info())

    skip_test('webhooks.set()', 'nécessite un serveur HTTPS public — skippé en local')
    skip_test('webhooks.delete()', 'skippé (aucun webhook actif à supprimer)')

    # ─── handle_webhook — unit test sans serveur HTTP ─────────────────────────

    print(f'\n→ bot.handle_webhook() — payload message')
    try:
        captured_msg = asyncio.Queue()
        test_msg_id = 99001

        @bot.on('message')
        async def _on_wh_msg(msg):
            if msg.id == test_msg_id:
                await captured_msg.put(msg)

        import time
        payload = {
            'type':       'text',
            'chat_id':    CHAT_ID,
            'message_id': test_msg_id,
            'sender_id':  'test-user-uuid',
            'text':       'webhook test',
            'sent_at':    int(time.time()),
        }
        bot.handle_webhook(payload)

        msg = await asyncio.wait_for(captured_msg.get(), timeout=0.5)
        if msg.text != 'webhook test':
            raise Exception(f'texte incorrect : {msg.text!r}')
        print(f'  [✓] OK  {{"events_received": 1, "text": "{msg.text}"}}')
        passed += 1
    except asyncio.TimeoutError:
        print('  [✗] FAIL — timeout, aucun event reçu')
        failed += 1
    except Exception as e:
        print(f'  [✗] FAIL — {e}')
        failed += 1

    print(f'\n→ bot.handle_webhook() — payload callback_query')
    try:
        captured_cb = asyncio.Queue()
        cb_marker = 'webhook_cb_test_99002'

        @bot.on('callback_query')
        async def _on_wh_cb(cb):
            if cb.callback_data == cb_marker:
                await captured_cb.put(cb)

        import time
        cb_payload = {
            'type':            'callback',
            'chat_id':         CHAT_ID,
            'sender_id':       'test-user-uuid',
            'sender_nom':      'Test User',
            'sender_username': 'testuser',
            'callback_data':   cb_marker,
            'sent_at':         int(time.time()),
        }
        bot.handle_webhook(cb_payload)

        cb_obj = await asyncio.wait_for(captured_cb.get(), timeout=0.5)
        if cb_obj.callback_data != cb_marker:
            raise Exception(f'callback_data incorrect : {cb_obj.callback_data!r}')
        print(f'  [✓] OK  {{"events_received": 1, "callback_data": "{cb_obj.callback_data}"}}')
        passed += 1
    except asyncio.TimeoutError:
        print('  [✗] FAIL — timeout, aucun event reçu')
        failed += 1
    except Exception as e:
        print(f'  [✗] FAIL — {e}')
        failed += 1

    # ═══════════════════════════════════════════════════════════════════════════
    section('11. MEMBRES DU GROUPE (lecture seule)')
    # ═══════════════════════════════════════════════════════════════════════════

    if not any_group_id:
        skip_test('chats.get_administrators()', 'aucun groupe trouvé')
        skip_test('chats.get_member()', 'aucun groupe trouvé')
        skip_test('chats.get_member() — NOT_FOUND', 'aucun groupe trouvé')
    else:
        gid = any_group_id

        admins_result = await run(
            f'chats.get_administrators({{ chat_id: {gid} }})',
            bot.chats.get_administrators(GetChatAdministratorsParams(chat_id=gid)),
        )
        if admins_result:
            print(f'  [ℹ] {len(admins_result.admins)} admin(s)')

        if admins_result and admins_result.admins:
            first_admin = admins_result.admins[0]
            await run(
                f'chats.get_member() — user_id={first_admin.user_id[:8]}…',
                bot.chats.get_member(GetChatMemberParams(chat_id=gid, user_id=first_admin.user_id)),
            )
        else:
            skip_test('chats.get_member()', 'aucun admin trouvé pour tester')

        # GetMember sur un user_id inexistant → NOT_FOUND
        await run_expect_error(
            'chats.get_member() — user inexistant → NOT_FOUND',
            'NOT_FOUND',
            lambda: bot.chats.get_member(GetChatMemberParams(
                chat_id=gid,
                user_id='00000000-0000-0000-0000-000000000000',
            )),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    section('12. INVITE LINKS (admin requis)')
    # ═══════════════════════════════════════════════════════════════════════════

    if not admin_group_id:
        skip_test('chats.create_invite_link()', 'aucun groupe admin')
        skip_test('chats.create_single_use_invite_link()', 'aucun groupe admin')
        skip_test('chats.create_invite_link() — max_uses+expires_in', 'aucun groupe admin')
        skip_test('chats.get_invite_links()', 'aucun groupe admin')
        skip_test('chats.revoke_invite_link()', 'aucun groupe admin')
    else:
        gid = admin_group_id

        perm_link: ChatInviteLink | None = None
        res = await run(
            'chats.create_invite_link() — permanent illimité',
            bot.chats.create_invite_link(CreateChatInviteLinkParams(chat_id=gid)),
        )
        if res:
            perm_link = res
            print(f'  [ℹ] URL : {res.url}')

        single_link: ChatInviteLink | None = None
        res = await run(
            'chats.create_single_use_invite_link() — usage unique',
            bot.chats.create_single_use_invite_link(CreateChatInviteLinkParams(chat_id=gid)),
        )
        if res:
            single_link = res

        await run(
            'chats.create_invite_link() — max_uses=5, expires_in=24h',
            bot.chats.create_invite_link(
                CreateChatInviteLinkParams(chat_id=gid, max_uses=5, expires_in='24h')
            ),
        )

        await run(
            'chats.get_invite_links() — liste les liens actifs',
            bot.chats.get_invite_links(GetChatInviteLinksParams(chat_id=gid)),
        )

        if perm_link:
            await run(
                f'chats.revoke_invite_link() — permanent code={perm_link.code}',
                bot.chats.revoke_invite_link(
                    RevokeChatInviteLinkParams(chat_id=gid, code=perm_link.code)
                ),
            )
        if single_link:
            await run(
                f'chats.revoke_invite_link() — single-use code={single_link.code}',
                bot.chats.revoke_invite_link(
                    RevokeChatInviteLinkParams(chat_id=gid, code=single_link.code)
                ),
            )

    # ═══════════════════════════════════════════════════════════════════════════
    section('13. MESSAGES DANS LE GROUPE')
    # ═══════════════════════════════════════════════════════════════════════════

    if not any_group_id:
        skip_test('envoi dans le groupe', 'aucun groupe trouvé')
    else:
        gid = any_group_id
        print(f'  [ℹ] Groupe cible : chat_id={gid}')

        group_msg = await run(
            f'messages.send() — texte dans groupe {gid}',
            bot.messages.send(gid, '👋 Test SDK Python — message dans le groupe'),
        )

        if group_msg and group_msg.message_id:
            mid = group_msg.message_id

            await run(
                'messages.send() — reply_to_id dans le groupe',
                bot.messages.send(gid, '↩️ Réponse avec citation dans le groupe', reply_to_id=mid),
            )

            await run(
                'messages.send_photo() — groupe avec reply_to_id',
                bot.messages.send_photo(
                    gid,
                    FileData(data=PNG, filename='test.png', content_type='image/png'),
                    caption='🖼 Photo dans le groupe',
                    reply_to_id=mid,
                ),
            )

            await run(
                'messages.send_carousel() — groupe sans reply_to_id',
                bot.messages.send_carousel(
                    gid,
                    carousel=[
                        CarouselCard(id='g1', title='Produit A', subtitle='9 990 FCFA', button_text='Voir'),
                        CarouselCard(id='g2', title='Produit B', subtitle='19 990 FCFA', button_text='Voir'),
                    ],
                    text='🛍 Nos produits :',
                    quick_reply_buttons=['Voir plus', 'Annuler'],
                ),
            )

            await run(
                'messages.send_carousel() — groupe avec reply_to_id',
                bot.messages.send_carousel(
                    gid,
                    carousel=[
                        CarouselCard(id='g3', title='Offre spéciale', subtitle='4 990 FCFA', button_text='Commander'),
                    ],
                    text='↩️ Voici notre sélection en réponse :',
                    quick_reply_buttons=[
                        ScrollKeyboardButton(text='✅ Confirmer', callback_data='confirm'),
                        ScrollKeyboardButton(text='❌ Annuler',  callback_data='cancel'),
                    ],
                    reply_to_id=mid,
                ),
            )

            await run(
                'messages.send() — inline keyboard dans le groupe',
                bot.messages.send(
                    gid,
                    'Boutons inline dans le groupe :',
                    reply_markup=InlineKeyboard(inline_keyboard=[[
                        InlineKeyboardButton(text='✅ Oui', callback_data='group_yes'),
                        InlineKeyboardButton(text='❌ Non', callback_data='group_no'),
                    ]]),
                ),
            )

    # ═══════════════════════════════════════════════════════════════════════════
    section('14. GESTION ERREURS')
    # ═══════════════════════════════════════════════════════════════════════════

    await run_expect_error(
        'messages.send() vers chat_id invalide → FORBIDDEN',
        'FORBIDDEN',
        lambda: bot.messages.send(-999999, 'test erreur'),
    )

    # Delete d'un message inexistant — ne doit pas planter
    await run(
        'messages.delete() message inexistant — pas d\'erreur levée',
        bot.messages.delete(CHAT_ID, 999999999),
    )

    await run_expect_error(
        'chats.create_invite_link() sur chat privé → FORBIDDEN',
        'FORBIDDEN',
        lambda: bot.chats.create_invite_link(CreateChatInviteLinkParams(chat_id=CHAT_ID)),
    )

    # Vérifier les champs de KappelaError
    print('\n→ KappelaError — vérification des champs (error_code, status, args[0], str())')
    try:
        await bot.messages.send(-999999, 'err fields')
        print('  [✗] FAIL — aurait dû retourner une erreur')
        failed += 1
    except KappelaError as e:
        ok = e.error_code and e.status and e.args[0] and str(e)
        if ok:
            print(f'  [✓] OK  KappelaError{{error_code:{e.error_code} status:{e.status} hasMsg:True hasStr:True}}')
            passed += 1
        else:
            print(f'  [✗] FAIL — champs manquants : error_code={e.error_code!r} status={e.status}')
            failed += 1
    except Exception as e:
        print(f'  [✗] FAIL — exception inattendue : {e}')
        failed += 1

    # ═══════════════════════════════════════════════════════════════════════════
    # Résumé
    # ═══════════════════════════════════════════════════════════════════════════

    await bot.stop()

    total = passed + failed + skipped
    print(f'\n{SEP2}')
    print(f'  Résultats : {passed} passés  {failed} échoués  {skipped} ignorés  ({total} total)')
    print(SEP2)

    if failed > 0:
        sys.exit(1)


asyncio.run(main())
