import logging
import random
import os
import asyncio
from fastapi import FastAPI, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
# The bot token is now loaded from an environment variable for security.
# You will set this in the Render dashboard.

# --- WORD LISTS (remain the same) ---
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

# --- PRIORITY SYSTEM SETUP (remains the same) ---
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

# --- BOT LOGIC (remains the same) ---
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

# --- NEW WEBHOOK STARTUP LOGIC ---
async def main() -> None:
    """Initializes the bot and sets up the webhook server."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return

    # Render provides the public URL for the service.
    WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
    if not WEBHOOK_URL:
        logger.error("RENDER_EXTERNAL_URL environment variable not found. Cannot set webhook.")
        return

    # A secret path to receive updates from Telegram, for security.
    SECRET_PATH = f"/{TOKEN}"

    # Build the application. No proxy is needed on Render.
    application = Application.builder().token(TOKEN).build()

    # Register all your handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Tell Telegram where to send updates by setting the webhook.
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}{SECRET_PATH}")

    # This is the FastAPI app that will handle incoming HTTP requests from Telegram.
    fastapi_app = FastAPI()

    @fastapi_app.post(SECRET_PATH)
    async def telegram_webhook(update: dict) -> Response:
        """This endpoint receives the updates from Telegram."""
        await application.process_update(Update.de_json(data=update, bot=application.bot))
        return Response(status_code=200)

    @fastapi_app.get("/health")
    async def health_check() -> Response:
        """A simple endpoint for Render's health checks to ensure the app is live."""
        return Response(status_code=200, content="OK")

    # Start the web server that will listen for incoming webhook requests.
    PORT = int(os.getenv("PORT", 8000))
    import uvicorn
    web_server = uvicorn.Server(
        config=uvicorn.Config(
            app=fastapi_app,
            port=PORT,
            host="0.0.0.0",
        )
    )

    # Run the bot application and the web server concurrently.
    async with application:
        await application.start()
        await web_server.serve()
        await application.stop()

if __name__ == "__main__":
    # Use asyncio.run() to start the asynchronous main function.
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutting down...")

