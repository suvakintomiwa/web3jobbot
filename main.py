#!/usr/bin/env python3
"""
Web3 Job Hunter Bot — Main Entry Point
"""
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from modules.commands import (
    start, help_cmd, scan, pumpscan, jobscan, dm_cmd,
    track_whale, untrack_whale, list_whales,
    set_mcap, status, alerts_on, alerts_off
)
from modules.scanner import TokenScanner
from modules.whale_tracker import WhaleTracker
from modules.pumpfun import PumpFunScanner
from modules.job_scraper import JobScraper
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
    import os
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("pumpscan", pumpscan))
    app.add_handler(CommandHandler("jobscan", jobscan))
    app.add_handler(CommandHandler("dm", dm_cmd))
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
    pumpfun = PumpFunScanner(notifier)
    job_scraper = JobScraper(notifier)

    app.bot_data["scanner"] = scanner
    app.bot_data["whale_tracker"] = whale_tracker
    app.bot_data["pumpfun"] = pumpfun
    app.bot_data["job_scraper"] = job_scraper
    app.bot_data["notifier"] = notifier

    logger.info("🚀 Web3 Job Hunter Bot starting...")

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await notifier.notify_startup()

        await asyncio.gather(
            scanner.run_loop(),
            whale_tracker.run_loop(),
            pumpfun.run_loop(),
            job_scraper.run_loop(),
        )

        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
