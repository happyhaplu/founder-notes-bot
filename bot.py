import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode, ChatAction
from telegram.error import TelegramError

from youtube_service import process_youtube_url
from gemini_service import generate_founder_notes, split_long_message

# ─── Setup ─────────────────────────────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # e.g. @FounderNotesChannel or -100xxxxxxx

# ─── Helpers ───────────────────────────────────────────────────────────────────

async def send_notes_to_channel(bot: Bot, notes: str, source_url: str):
    """Send notes to the Founder Notes channel if CHANNEL_ID is configured."""
    if not CHANNEL_ID:
        return

    footer = f"\n\n🔗 Source: {source_url}"
    full_notes = notes + footer
    chunks = split_long_message(full_notes)

    for chunk in chunks:
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=chunk,
                parse_mode=None,
                disable_web_page_preview=True,
            )
            if len(chunks) > 1:
                await asyncio.sleep(0.5)
        except TelegramError as e:
            logger.error(f"Failed to send to channel: {e}")


async def send_long_message(update: Update, text: str):
    """Send a potentially long message, splitting if needed."""
    chunks = split_long_message(text)
    for i, chunk in enumerate(chunks):
        await update.message.reply_text(
            chunk,
            parse_mode=None,
            disable_web_page_preview=True,
        )
        if i < len(chunks) - 1:
            await asyncio.sleep(0.3)


# ─── Handlers ──────────────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome = (
        "👋 Welcome to Founder Notes Bot!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎙 I turn YouTube podcasts & videos into\n"
        "clean, structured notes.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📋 Each note includes:\n\n"
        "• 🎙 Title\n"
        "• 📌 Summary\n"
        "• 💡 Key Takeaways & Insights\n"
        "• 🛠 Tools / Systems Mentioned\n"
        "• ⚡ Actionable Ideas\n"
        "• 🧠 Mindset Shifts\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 Just drop a YouTube link to begin!"
    )
    await update.message.reply_text(welcome, disable_web_page_preview=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "📖 Help\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send any YouTube URL, for example:\n"
        "https://youtube.com/watch?v=xxxxx\n\n"
        "The bot will:\n"
        "1. Extract the transcript\n"
        "2. Generate structured notes via AI\n"
        "3. Send them here + to the channel\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⏱ Processing takes 15–60 seconds.\n"
        "Please be patient after sending a URL."
    )
    await update.message.reply_text(help_text)


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler: process YouTube URL → generate notes → send."""
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    url = update.message.text.strip()

    logger.info(f"User {user.id} ({user.username}) sent: {url}")

    # ── Step 1: Process & validate URL ──
    url_data = process_youtube_url(url)

    if not url_data["valid"]:
        await update.message.reply_text(
            "❌ Invalid URL\n\n"
            "Please send a valid YouTube link.\n\n"
            "Examples:\n"
            "• https://youtube.com/watch?v=xxxxx\n"
            "• https://youtu.be/xxxxx"
        )
        return

    # ── Step 2: Processing message ──
    processing_msg = await update.message.reply_text(
        "⏳ Processing your video...\n\n"
        "🔍 Extracting transcript & generating notes\n"
        "This takes 15–60 seconds. Please wait."
    )

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    try:
        # ── Step 3: Check transcript ──
        transcript = url_data.get("transcript")

        if not transcript:
            try:
                await processing_msg.delete()
            except TelegramError:
                pass
            await update.message.reply_text(
                "❌ Could not extract transcript from this video.\n\n"
                "This happens when the video has:\n"
                "• Subtitles/captions disabled\n"
                "• Auto-captions not yet generated\n"
                "• Age restriction or geo-block\n\n"
                "Please try a different video that has captions enabled."
            )
            return

        # ── Step 4: Generate notes ──
        notes = generate_founder_notes(url=url_data["url"], transcript=transcript)

        try:
            await processing_msg.delete()
        except TelegramError:
            pass

        # ── Step 5: Send to user ──
        await send_long_message(update, notes)

        # ── Step 6: Forward to channel ──
        await send_notes_to_channel(context.bot, notes, url_data["url"])

        logger.info(f"Notes successfully sent to user {user.id}")

    except ValueError as e:
        logger.error(f"Generation error: {e}")
        try:
            await processing_msg.delete()
        except TelegramError:
            pass
        err_str = str(e).lower()
        if "exhausted" in err_str or "rate" in err_str:
            msg = (
                "⏳ AI rate limit hit.\n\n"
                "Please wait 1–2 minutes and try again."
            )
        elif "no_transcript" in err_str:
            msg = (
                "❌ No transcript found for this video.\n\n"
                "Please try a video with captions enabled."
            )
        else:
            msg = (
                "❌ Could not generate notes.\n\n"
                f"Reason: {str(e)}\n\n"
                "Please try again or try a different video."
            )
        await update.message.reply_text(msg)

    except Exception as e:
        logger.exception(f"Unexpected error for user {user.id}: {e}")
        try:
            await processing_msg.delete()
        except TelegramError:
            pass
        await update.message.reply_text(
            "⚠️ Something went wrong while processing.\n\n"
            "Please try again in a moment.\n"
            "If the issue persists, try a different video."
        )


async def handle_non_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-URL text messages."""
    if not update.message or not update.message.text:
        return
    text = update.message.text or ""
    if "http" in text.lower() and "youtube" not in text.lower() and "youtu.be" not in text.lower():
        await update.message.reply_text(
            "❌ Not a YouTube URL\n\n"
            "I only process YouTube links.\n\n"
            "Please send a YouTube video URL."
        )
    else:
        await update.message.reply_text(
            "🎙 Send me a YouTube URL\n"
            "and I'll generate structured notes!\n\n"
            "Type /help for more info."
        )


# ─── App Factory ───────────────────────────────────────────────────────────────

def create_app() -> Application:
    """Create and configure the Telegram Application."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    youtube_filter = filters.Regex(r"(youtube\.com|youtu\.be)")
    app.add_handler(MessageHandler(filters.TEXT & youtube_filter, handle_url))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_url))

    return app


# ─── Run Modes ─────────────────────────────────────────────────────────────────

async def _polling_coroutine():
    app = create_app()
    await app.initialize()
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    await app.start()
    # Run until interrupted
    await asyncio.Event().wait()


def run_polling():
    """Run bot in polling mode (local development)."""
    logger.info("Starting bot in POLLING mode...")
    asyncio.run(_polling_coroutine())


def run_webhook():
    """Run bot in webhook mode (Render production) with FastAPI + health check."""
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, Response

    webhook_url = os.getenv("WEBHOOK_URL")
    port = int(os.getenv("PORT", 10000))

    if not webhook_url:
        raise ValueError("WEBHOOK_URL environment variable is not set for webhook mode")

    logger.info(f"Starting bot in WEBHOOK mode on port {port}...")

    ptb_app = create_app()
    fastapi_app = FastAPI()

    @fastapi_app.get("/health")
    async def health():
        return JSONResponse({"status": "ok"})

    @fastapi_app.post("/webhook")
    async def webhook(request: Request):
        data = await request.json()
        update = Update.de_json(data, ptb_app.bot)
        await ptb_app.process_update(update)
        return Response(status_code=200)

    @fastapi_app.on_event("startup")
    async def on_startup():
        await ptb_app.initialize()
        await ptb_app.bot.set_webhook(url=f"{webhook_url}/webhook")
        await ptb_app.start()
        logger.info(f"Webhook set to {webhook_url}/webhook")

    @fastapi_app.on_event("shutdown")
    async def on_shutdown():
        await ptb_app.stop()
        await ptb_app.shutdown()

    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)


# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = os.getenv("RUN_MODE", "polling").lower()

    if mode == "webhook":
        run_webhook()
    else:
        run_polling()
