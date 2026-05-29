"""Bot live — envoie un message avec boutons et attend les clics. Ctrl+C pour arrêter."""
import asyncio, sys
sys.path.insert(0, 'src')

from kappelas import KappelaBot, KappelaError
from kappelas.types import InlineKeyboard, InlineKeyboardButton

TOKEN   = sys.argv[1] if len(sys.argv) > 1 else None
CHAT_ID = int(sys.argv[2]) if len(sys.argv) > 2 else 130

if not TOKEN:
    print('Usage: python test_live.py <TOKEN> [CHAT_ID]')
    sys.exit(1)

bot = KappelaBot(token=TOKEN)

@bot.on('connected')
async def on_connected():
    print('[✓] Connecté')
    await bot.messages.send(
        CHAT_ID,
        'Clique sur un bouton 👇',
        reply_markup=InlineKeyboard(inline_keyboard=[[
            InlineKeyboardButton(text='✅ Oui', callback_data='oui'),
            InlineKeyboardButton(text='❌ Non', callback_data='non'),
        ]])
    )
    print('[→] Message avec boutons envoyé — clique !')

@bot.on('callback_query')
async def on_callback(cb):
    print(f'[→] Clic reçu — sender="{cb.sender_name or cb.sender_id}" data="{cb.callback_data}"')
    result = await bot.messages.send(cb.chat_id, f'Tu as cliqué : {cb.callback_data} ✅')
    print(f'[✓] Réponse envoyée — message_id={result.message_id}')

@bot.on('error')
def on_error(err):
    print(f'[✗] Erreur: {err}')

print('[…] Connexion...')
asyncio.run(bot.run())
