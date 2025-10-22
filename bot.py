import logging
import random
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION (No changes) ---
# Environment variables are still used for the token.

# --- WORD LISTS (No changes) ---
CURSE_WORDS = {
    "fuck", "shit", "bitch", "cunt", "asshole", "damn", "motherfucker", "dick",
    "блять", "сука", "хуй", "пизда", "ебать", "ебал", "заебал", "мудак", "пидорас", "гандон"
}
GREET_NAMES = {"asad", "assad", "асад", "ассад"}
ASAD_CURSE_RESPONSES = [
    "Пошел нахуй",
    "Я тебя грохну",
    "Гандон"
]
HOW_ARE_YOU_TRIGGERS = {"how are you", "whats up", "what's up", "как дела", "че там", "васап", "васап?", "че делаешь", "че делаешь?", "че делаете", "че делаете?", "как асад", "как асад?"}
HOW_ARE_YOU_RESPONSES = [
    "норм", "пойдет", "бля штраф словил", "бля менты остановили", "че там че мутишь",
    "давайте массажку замутим", "приходите в мьюз", "дай на ход ноги", "закинь за бензу", "пацаны я штраф поймал"
]
KUDA_TRIGGERS = {"куда"}
GDE_TRIGGERS = {"где", "where"}
MUSE_TRIGGERS = {"muse", "мьюзе", "мьюз"}
THINK_TRIGGERS = {"че думаете", "че думаешь", "че думаете?", "че думаешь?", "да?", "нет?", "давайте", "давайте?", "надо", "го?", "гоу?", "what do you think", "what do you think?", "think", "yes?", "no?", "lets", "opinion", "should"}
THINK_RESPONSES = [
    "да", "нет", "не знаю", "наверное", "хз", "очень круто", "мне нравится", "я за", "че бля"
]

# --- PRIORITY SYSTEM SETUP (No changes) ---
PRIORITY_CHECKS = [
    {'priority': 1, 'response': ASAD_CURSE_RESPONSES, 'check_type': 'asad_curse', 'response_type': 'random'},
    {'priority': 2, 'triggers': GREET_NAMES, 'response': "Салам", 'check_type': 'intersection', 'response_type': 'static'},
    {'priority': 3, 'check_type': 'or_question'},
    {'priority': 4, 'triggers': HOW_ARE_YOU_TRIGGERS, 'response': HOW_ARE_YOU_RESPONSES, 'check_type': 'contains', 'response_type': 'random'},
    {'priority': 5, 'triggers': KUDA_TRIGGERS, 'response': "В Мьюз", 'check_type': 'contains', 'response_type': 'static'},
    {'priority': 6, 'triggers': GDE_TRIGGERS, 'response': "В Мьюзе", 'check_type': 'contains', 'response_type': 'static'},
    {'priority': 7, 'triggers': MUSE_TRIGGERS, 'response': "MUSE MENTIONED!!!", 'check_type': 'contains', 'response_type': 'static'},
    {'priority': 8, 'triggers': THINK_TRIGGERS, 'response': THINK_RESPONSES, 'check_type': 'contains', 'response_type': 'random'},
]
PRIORITY_CHECKS.sort(key=lambda x: x['priority'])

# --- BOT LOGIC (No changes) ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Салам! Я Асад бот ")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    message_text_lower = update.message.text.lower()
    words_in_message = set(message_text_lower.split())
    for check in PRIORITY_CHECKS:
        triggered = False
        response_text = None
        if check['check_type'] == 'asad_curse':
            if GREET_NAMES.intersection(words_in_message) and CURSE_WORDS.intersection(words_in_message):
                triggered = True
        elif check['check_type'] == 'intersection':
            if check['triggers'].intersection(words_in_message):
                triggered = True
        elif check['check_type'] == 'contains':
            if any(trigger in message_text_lower for trigger in check['triggers']):
                triggered = True
        elif check['check_type'] == 'or_question':
            or_separators = [" or ", " или "]
            separator_found = next((sep for sep in or_separators if sep in message_text_lower), None)
            if separator_found:
                parts = message_text_lower.split(separator_found, 1)
                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                    choice1_raw = parts[0].split()[-1]
                    choice2_raw = parts[1].split()[0]
                    punctuation_to_remove = "?.,!"
                    choice1 = choice1_raw.strip().rstrip(punctuation_to_remove)
                    choice2 = choice2_raw.strip().rstrip(punctuation_to_remove)
                    if choice1 and choice2:
                        response_text = random.choice([choice1, choice2])
                        triggered = True
        if triggered:
            if response_text:
                await update.message.reply_text(response_text)
            elif check['response_type'] == 'static':
                await update.message.reply_text(check['response'])
            elif check['response_type'] == 'random':
                await update.message.reply_text(random.choice(check['response']))
            return
    if CURSE_WORDS.intersection(words_in_message):
        user = update.message.from_user
        logger.info(f"Curse word detected from user: {user.first_name} ({user.id})")
        await update.message.reply_text("Эй, не матерись")

# --- REFACTORED WEBHOOK STARTUP LOGIC ---

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
SECRET_PATH = f"/{TOKEN}"

# Build the application object once. It will be used by the lifespan manager and webhook endpoint.
application = Application.builder().token(TOKEN).build()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles the bot's setup and shutdown procedures."""
    # On startup:
    logger.info("Setting up bot handlers and webhook...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}{SECRET_PATH}")
    logger.info("Webhook has been set!")
    
    yield  # The application runs while the server is alive.
    
    # On shutdown:
    logger.info("Cleaning up and deleting webhook...")
    await application.bot.delete_webhook()
    logger.info("Webhook has been deleted.")

# Create the FastAPI app with our new lifespan manager.
fastapi_app = FastAPI(lifespan=lifespan)

@fastapi_app.post(SECRET_PATH)
async def telegram_webhook(update: dict) -> Response:
    """This endpoint receives the updates from Telegram."""
    try:
        await application.process_update(Update.de_json(data=update, bot=application.bot))
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return Response(status_code=500)

@fastapi_app.get("/health")
async def health_check() -> Response:
    """A simple endpoint for Render's health checks."""
    return Response(status_code=200, content="OK")

if __name__ == "__main__":
    # This block allows you to run the bot by executing `python bot.py`.
    # It will be used by Render's start command.
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    
    # Check if required environment variables are set before trying to run.
    if not TOKEN or not WEBHOOK_URL:
        logger.error("FATAL: TELEGRAM_TOKEN and RENDER_EXTERNAL_URL must be set.")
    else:
        uvicorn.run(fastapi_app, host="0.0.0.0", port=PORT)

