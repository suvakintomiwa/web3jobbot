"""
Bot Commands — all /command handlers
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

HELP_TEXT = """
🤖 <b>Web3 Job Hunter Bot — Commands</b>

<b>🔍 Token Scanner</b>
/scan — manually trigger a scan right now
/setmcap [amount] — set min MCap filter (e.g. /setmcap 10000)
/alertson — enable real-time alerts
/alertsoff — pause alerts

<b>🐋 Whale Tracker</b>
/trackwhale [address] [chain] [label]
  e.g. /trackwhale 0xABC123 ethereum BigFund
/untrackwhale [address] — stop tracking a wallet
/whales — list all tracked wallets

<b>📊 Info</b>
/status — bot stats and current settings
/help — show this message

<b>💼 Job Tips</b>
Every new token alert shows you:
• Twitter/X link to DM the project
• Telegram/Discord to join early
• What roles they likely need
• Tips to get noticed fast

<i>The early bird gets the Web3 job! 🐦</i>
"""


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Scan Now", callback_data="scan"),
         InlineKeyboardButton("🐋 My Whales", callback_data="whales")],
        [InlineKeyboardButton("📊 Status", callback_data="status"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = (
        "👋 <b>Welcome to Web3 Job Hunter Bot!</b>\n\n"
        "I scan new crypto projects and help you land roles as:\n"
        "🎙️ KOL  👥 Community Manager  🛡️ Moderator  ⚔️ Raider  📣 Marketer\n\n"
        "I'm already scanning DexScreener for new tokens.\n"
        "Use the buttons below or /help for all commands."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scanner = ctx.bot_data.get("scanner")
    if not scanner:
        await update.message.reply_text("❌ Scanner not initialized.")
        return
    msg = await update.message.reply_text("🔍 Scanning now... please wait.")
    try:
        await scanner.scan()
        stats = scanner.get_stats()
        await msg.edit_text(
            f"✅ Scan complete!\n"
            f"📊 Total scans: {stats['scan_count']}\n"
            f"🆕 Tokens found ever: {stats['found_count']}\n"
            f"💰 Min MCap filter: ${stats['min_mcap']:,}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Scan error: {e}")


async def track_whale(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Usage: /trackwhale [address] [chain] [optional label]\n"
            "Chains: solana, ethereum, bsc, base\n\n"
            "Example:\n"
            "<code>/trackwhale 0xABC123 ethereum BigFund</code>",
            parse_mode=ParseMode.HTML
        )
        return

    address = args[0]
    chain = args[1].lower()
    label = " ".join(args[2:]) if len(args) > 2 else address[:8] + "..."

    valid_chains = ["solana", "ethereum", "bsc", "base", "arbitrum"]
    if chain not in valid_chains:
        await update.message.reply_text(f"❌ Invalid chain. Use: {', '.join(valid_chains)}")
        return

    tracker = ctx.bot_data.get("whale_tracker")
    tracker.add_wallet(address, chain, label)
    await update.message.reply_text(
        f"✅ Now tracking wallet!\n"
        f"👤 Label: <b>{label}</b>\n"
        f"📍 Address: <code>{address}</code>\n"
        f"⛓️ Chain: {chain.upper()}\n\n"
        f"I'll alert you on moves ≥ $10,000",
        parse_mode=ParseMode.HTML
    )


async def untrack_whale(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /untrackwhale [address]")
        return
    address = args[0]
    tracker = ctx.bot_data.get("whale_tracker")
    if tracker.remove_wallet(address):
        await update.message.reply_text(f"✅ Removed wallet: <code>{address}</code>", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ Wallet not found in tracking list.")


async def list_whales(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tracker = ctx.bot_data.get("whale_tracker")
    wallets = tracker.list_wallets()
    if not wallets:
        await update.message.reply_text(
            "🐋 No wallets tracked yet.\n\nUse /trackwhale to add one!"
        )
        return

    lines = ["🐋 <b>Tracked Whale Wallets</b>\n"]
    for addr, info in wallets.items():
        lines.append(
            f"• <b>{info.get('label')}</b> [{info.get('chain','?').upper()}]\n"
            f"  <code>{addr[:20]}...</code>"
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def set_mcap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /setmcap [amount]\nExample: /setmcap 10000")
        return
    try:
        mcap = int(args[0].replace(",", "").replace("$", ""))
        scanner = ctx.bot_data.get("scanner")
        scanner.set_min_mcap(mcap)
        await update.message.reply_text(f"✅ Min MCap filter set to <b>${mcap:,}</b>", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Example: /setmcap 10000")


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scanner = ctx.bot_data.get("scanner")
    tracker = ctx.bot_data.get("whale_tracker")
    notifier = ctx.bot_data.get("notifier")
    alerts = ctx.bot_data.get("alerts_enabled", True)

    s = scanner.get_stats()
    w = tracker.get_stats()

    msg = (
        f"📊 <b>Bot Status</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔔 Alerts: {'✅ ON' if alerts else '❌ OFF'}\n"
        f"💰 Min MCap: <b>${s['min_mcap']:,}</b>\n\n"
        f"<b>🔍 Scanner</b>\n"
        f"  Scans run: {s['scan_count']}\n"
        f"  Tokens found: {s['found_count']}\n"
        f"  Tokens seen (DB): {s['seen_total']}\n\n"
        f"<b>🐋 Whale Tracker</b>\n"
        f"  Wallets tracked: {w['wallet_count']}\n"
        f"  Checks run: {w['check_count']}\n\n"
        f"<b>📨 Notifications</b>\n"
        f"  Messages sent: {notifier.sent_count}"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def alerts_on(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.bot_data["alerts_enabled"] = True
    notifier = ctx.bot_data.get("notifier")
    notifier.alerts_enabled = True
    await update.message.reply_text("✅ Real-time alerts are now <b>ON</b>", parse_mode=ParseMode.HTML)


async def alerts_off(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.bot_data["alerts_enabled"] = False
    notifier = ctx.bot_data.get("notifier")
    notifier.alerts_enabled = False
    await update.message.reply_text("🔕 Alerts paused. Use /alertson to resume.", parse_mode=ParseMode.HTML)
