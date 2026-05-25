#!/usr/bin/env python3
"""
Web3 Job Hunter Bot - Main Entry Point
"""
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from modules.commands import (
    start, help_cmd, scan, track_whale, untrack_whale,
    list_whales, set_mcap, status, alerts_on, alerts_off
)
from modules.scanner import TokenScanner
from modules.whale_tracker import WhaleTracker
from modules.notifier import Notifier
from config import BOT_TOKEN, CHAT_ID

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("trackwhale", track_whale))
    app.add_handler(CommandHandler("untrackwhale", untrack_whale))
    app.add_handler(CommandHandler("whales", list_whales))
    app.add_handler(CommandHandler("setmcap", set_mcap))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("alertson", alerts_on))
    app.add_handler(CommandHandler("alertsoff", alerts_off))
    app.add_handler(CallbackQueryHandler(start))

    notifier = Notifier(app.bot, CHAT_ID)
    scanner = TokenScanner(notifier)
    whale_tracker = WhaleTracker(notifier)

    # Store shared state in bot_data
    app.bot_data["scanner"] = scanner
    app.bot_data["whale_tracker"] = whale_tracker
    app.bot_data["notifier"] = notifier
    app.bot_data["alerts_enabled"] = True

    logger.info("🚀 Web3 Job Hunter Bot starting...")

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        # Run background tasks
        await asyncio.gather(
            scanner.run_loop(),
            whale_tracker.run_loop(),
        )

        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
