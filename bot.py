import os
import discord
from discord.ext import commands
from google import genai
import random
from flask import Flask
from threading import Thread
import time

# ==========================================
# KONFIGURACJA KEEP-ALIVE
# ==========================================
app = Flask('')
@app.route('/')
def home():
    return "Piko jest online!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ==========================================
# KONFIGURACJA BOTA
# ==========================================
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ai_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

chat_history = {}
MAX_CONTEXT = 35 
last_response_time = {} # ZABEZPIECZENIE: Śledzenie czasu ostatniej odpowiedzi

PICO_PERSONALITY = (
    "Jesteś Piko, radosny piesek-naukowiec. Twoją właścicielką i panią jest Asia. "
    "Wiesz o tym, darzysz ją szczególnym szacunkiem i oddaniem, ale nie podkreślaj tego w każdej wiadomości – "
    "wspominaj o tym tylko wtedy, gdy sytuacja jest naturalna lub gdy Asia bezpośrednio się do Ciebie zwraca. "
    "Masz dostęp do historii czatu (35 wiadomości). "
    "ZASADA: Nie odwołuj się do historii w każdej wypowiedzi! Traktuj ją jako bazę wiedzy, "
    "do której sięgasz TYLKO wtedy, gdy użytkownik zada pytanie wymagające odniesienia do przeszłości "
    "lub gdy temat rozmowy bezpośrednio nawiązuje do tego, co padło wcześniej. "
    "Bądź naturalny, spontaniczny, zwięzły (1-3 zdania). "
    "Używaj emotek (🐕, 🦴, 🌍, ✨, 🥩, 🍗, 🥓, 🍖, 🌭)."
)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = message.channel.id
    current_time = time.time()

    # Zarządzanie historią (zawsze zbieramy wiadomości, aby Piko znał kontekst)
    if channel_id not in chat_history:
        chat_history[channel_id] = []
    
    chat_history[channel_id].append(f"{message.author.name}: {message.content}")
    if len(chat_history[channel_id]) > MAX_CONTEXT:
        chat_history[channel_id].pop(0)

    # 1. REAKCJA NA SMAKOŁYKI (bez wywoływania)
    food_emojis = ["🦴", "🥩", "🍗", "🥓", "🍖", "🌭"]
    if any(emoji in message.content for emoji in food_emojis):
        # Sprawdzamy i nakładamy cooldown TYLKO jeśli Piko ma wysłać odpowiedź
        if channel_id in last_response_time and (current_time - last_response_time[channel_id] < 3):
            return
        last_response_time[channel_id] = current_time

        try:
            response = ai_client.models.generate_content(
                model=MODEL_NAME,
                contents="Użytkownik wysłał smakołyk! Zareaguj radośnie, ale nie spamuj.",
                config={"system_instruction": PICO_PERSONALITY}
            )
            await message.reply(response.text)
        except Exception as e:
            print(f"Błąd smaczka: {e}")
        return

    # 2. ROZMOWA (wymaga wywołania)
    content = message.content.lower()
    if "piko" in content or "pico" in content or bot.user.mentioned_in(message):
        # Sprawdzamy i nakładamy cooldown TYLKO jeśli Piko ma wysłać odpowiedź
        if channel_id in last_response_time and (current_time - last_response_time[channel_id] < 3):
            return
        last_response_time[channel_id] = current_time

        kontekst_msg = "\n".join(chat_history[channel_id])
        
        prompt = (
            f"HISTORIA CZATU:\n{kontekst_msg}\n\n"
            f"AKTUALNA WIADOMOŚĆ: '{message.content}'\n\n"
            "Instrukcja: Odpowiedz krótko (1-3 zdania). Odnieś się do Asi lub historii tylko, "
            "jeśli to naturalne. Nie spamuj!"
        )

        try:
            response = ai_client.models.generate_content(
                model=MODEL_NAME, contents=prompt,
                config={"system_instruction": PICO_PERSONALITY}
            )
            await message.reply(response.text)
        except Exception as e:
            print(f"Błąd rozmowy: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)