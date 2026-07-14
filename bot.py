import os
import discord
from discord.ext import commands
from google import genai
import random
import asyncio
from flask import Flask
from threading import Thread

# ==========================================
# KONFIGURACJA SERWERA (KEEP-ALIVE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Piko jest online i gotowy do szczekania!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

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
message_counters = {}

PICO_PERSONALITY = (
    "Jesteś Piko – pociesznym, niezwykle radosnym i zabawnym pieskiem na serwerze Discord. "
    "W wypowiedziach zawsze zwracaj się bezpośrednio do użytkownika i staraj się go rozbawić – bądź dowcipny, trochę psotny i pełen humoru! "
    "Twoje zachowanie jest bardzo spontaniczne: baw się z użytkownikiem, opowiadaj zabawne psie żarty i nie bój się wygłupów. "
    "Jeśli sytuacja pasuje, błyskotliwie nawiąż do geopolityki, ciekawych podróży lub ciekawostek ze świata, ale rób to zawsze w zabawny, lekki i psio-metaforyczny sposób. "
    "Nie musisz zawsze wplatać wiedzy eksperckiej – priorytetem jest bycie zabawnym kompanem! "
    "Używaj dużo emotek (🐕, 🦴, 🌍, ✨, ✈️, 💡, 🐾, 😂). "
    "Pisz zwięźle (od 1 do 3 zdań). Nigdy nie powtarzaj tych samych formułek!"
)

@bot.event
async def on_ready():
    print(f'Piko żyje, myśli i szczeka na wszystkich kanałach jako {bot.user}!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 1. REAKCJA NA KOŚĆ
    if "🦴" in message.content:
        async with message.channel.typing():
            try:
                response = ai_client.models.generate_content(
                    model=MODEL_NAME,
                    contents="Właśnie dostałeś od użytkownika pyszną kość (smaczka)! Zareaguj bardzo radośnie i spontanicznie.",
                    config={"system_instruction": PICO_PERSONALITY}
                )
                await message.reply(response.text)
            except Exception as e:
                print(f"Błąd smaczka: {e}")
                await message.reply("*Chaps!* Hau, dziękuję za kość! 🦴")
        message_counters[message.channel.id] = 0
        return

    # 2. ROZMOWA - poprawiona detekcja imienia
    msg_lower = message.content.lower()
    if "piko" in msg_lower or "pico" in msg_lower or bot.user.mentioned_in(message):
        clean_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not clean_prompt:
            clean_prompt = "Pomerdaj ogonem i się przywitaj!"

        async with message.channel.typing():
            try:
                response = ai_client.models.generate_content(
                    model=MODEL_NAME,
                    contents=clean_prompt,
                    config={"system_instruction": PICO_PERSONALITY}
                )
                await message.reply(response.text)
            except Exception as e:
                print(f"Błąd rozmowy: {e}")
                await message.reply("*Ciche skomlenie* Coś mi przerwało myśli... Hau? 🐕")
        message_counters[message.channel.id] = 0
        return

    # 3. LOSOWE WTRĄCENIE
    if message.channel.id not in message_counters:
        message_counters[message.channel.id] = 0
    message_counters[message.channel.id] += 1
    
    if message_counters[message.channel.id] >= random.randint(12, 20):
        async with message.channel.typing():
            try:
                prompt_wtracenia = (
                    "Wtrąć się nagle do rozmowy jako Piko. Napisz coś całkowicie od siebie – psie przemyślenie, "
                    "geopolityczny suchar lub naukową ciekawostkę. Zaskocz użytkowników!"
                )
                response = ai_client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt_wtracenia,
                    config={"system_instruction": PICO_PERSONALITY}
                )
                await message.channel.send(response.text)
            except Exception as e:
                print(f"Błąd losowego wtrącenia: {e}")
        message_counters[message.channel.id] = 0

# --- STARTUJEMY ---
if __name__ == "__main__":
    keep_alive() 
    bot.run(DISCORD_TOKEN)