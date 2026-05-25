"""
Bot Commands — all /command handlers (bold Web3 style)
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from modules.dm_drafter import format_dm_message, generate_dm, ROLE_PITCHES

logger = logging.getLogger(__name__)
DIVIDER = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"

HELP_TEXT = f"""
⚡ <b>WEB3 JOB HUNTER BOT</b> ⚡
{DIVIDER}

<b>🔍 SCANNING</b>
/scan — trigger DexScreener scan now
/pumpscan — scan Pump.fun launches now
/jobscan — scan job boards now
/setmcap [amount] — set min MCap filter

<b>🐋 WHALE TRACKER</b>
/trackwhale [address] [chain] [label]
/untrackwhale [address]
/whales — list tracked wallets

<b>✍️ DM DRAFTER</b>
/dm [token name] — generate outreach pitches
/dm cm — Community Manager pitch template
/dm mod — Moderator pitch template
/dm kol — KOL / Content Creator pitch
/dm raider — Raider pitch template

<b>⚙️ SETTINGS</b>
/alertson — enable all alerts
/alertsoff — pause all alerts
/status — bot stats

<b>💡 TIP</b>: Every new token alert has a /dm
shortcut — copy the pitch and send it fast!
{DIVIDER}
"""


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔍 Scan Tokens", callback_data="scan"),
            InlineKeyboardButton("🟣 Pump.fun", callback_data="pumpscan"),
        ],
        [
            InlineKeyboardButton("💼 Job Boards", callback_data="jobscan"),
            InlineKeyboardButton("🐋 My Whales", callback_data="whales"),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = (
        f"⚡ <b>WEB3 JOB HUNTER BOT</b> ⚡\n"
        f"{DIVIDER}\n"
        f"Your personal alpha tool for landing:\n"
        f"🎙️ KOL  |  👥 CM  |  🛡️ Mod  |  ⚔️ Raider\n\n"
        f"🟢 <b>Scanning:</b> DexScreener + Pump.fun + Job Boards\n"
        f"🐋 <b>Whale tracker:</b> Multi-chain\n"
        f"✍️ <b>Auto DM drafter:</b> Ready-to-send pitches\n"
        f"{DIVIDER}\n"
        f"Use the buttons below or /help"
    )
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        except Exception:
            pass
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scanner = ctx.bot_data.get("scanner")
    msg = await update.message.reply_text("🔍 Scanning DexScreener... hold tight.")
    try:
        await scanner.scan()
        s = scanner.get_stats()
        await msg.edit_text(
            f"✅ <b>Scan complete!</b>\n"
            f"Scans run: {s['scan_count']} | Found ever: {s['found_count']}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.edit_text(f"❌ Scan error: {e}")


async def pumpscan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pumpfun = ctx.bot_data.get("pumpfun")
    if not pumpfun:
        await update.message.reply_text("❌ Pump.fun scanner not initialized.")
        return
    msg = await update.message.reply_text("🟣 Scanning Pump.fun launches...")
    try:
        await pumpfun.scan_new()
        await pumpfun.scan_graduating()
        s = pumpfun.get_stats()
        await msg.edit_text(
            f"✅ <b>Pump.fun scan done!</b>\n"
            f"🚀 Launches found: {s['launch_count']}\n"
            f"🎓 Graduating found: {s['grad_count']}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.edit_text(f"❌ Pump.fun scan error: {e}")


async def jobscan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scraper = ctx.bot_data.get("job_scraper")
    if not scraper:
        await update.message.reply_text("❌ Job scraper not initialized.")
        return
    msg = await update.message.reply_text("💼 Scanning Web3 job boards...")
    try:
        await scraper.scrape_all()
        s = scraper.get_stats()
        await msg.edit_text(
            f"✅ <b>Job scan done!</b>\n"
            f"Jobs found ever: {s['found_count']}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await msg.edit_text(f"❌ Job scan error: {e}")


async def dm_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args

    # /dm with no args — show all templates
    if not args:
        lines = [f"✍️ <b>DM PITCH TEMPLATES</b>\n{DIVIDER}\n"]
        lines.append("Use: <code>/dm [role]</code> — roles: cm, mod, kol, raider\n")
        lines.append("Or: <code>/dm [project name]</code> — generates all pitches for that project\n")
        for key, role in ROLE_PITCHES.items():
            lines.append(f"\n<b>{role['label']}</b> → <code>/dm {key}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    role_key = args[0].lower()

    # /dm cm, /dm mod, /dm kol, /dm raider — show that role template
    if role_key in ROLE_PITCHES:
        role = ROLE_PITCHES[role_key]
        pitch = generate_dm({"name": "their project"}, role_key)
        msg = (
            f"✍️ <b>{role['label']} Pitch</b>\n"
            f"{DIVIDER}\n"
            f"<pre>{pitch}</pre>\n"
            f"{DIVIDER}\n"
            f"💡 Copy, personalise the project name, and send!"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    # /dm [project name] — generate all pitches for that project
    project_name = " ".join(args)
    token = {"name": project_name, "symbol": "", "socials": {}}
    msg = format_dm_message(token)
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def track_whale(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Usage: <code>/trackwhale [address] [chain] [label]</code>\n"
            "Chains: solana, ethereum, bsc, base\n\n"
            "Example:\n<code>/trackwhale 0xABC123 ethereum BigFund</code>",
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
        f"🐋 <b>Whale Added!</b>\n"
        f"{DIVIDER}\n"
        f"👤 Label: <b>{label}</b>\n"
        f"📍 <code>{address}</code>\n"
        f"⛓️ Chain: {chain.upper()}\n"
        f"🔔 Alert threshold: $10,000+",
        parse_mode=ParseMode.HTML
    )


async def untrack_whale(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /untrackwhale [address]")
        return
    tracker = ctx.bot_data.get("whale_tracker")
    if tracker.remove_wallet(args[0]):
        await update.message.reply_text(f"✅ Removed: <code>{args[0]}</code>", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ Wallet not found.")


async def list_whales(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tracker = ctx.bot_data.get("whale_tracker")
    wallets = tracker.list_wallets()
    if not wallets:
        await update.message.reply_text("🐋 No wallets tracked yet.\n\nUse /trackwhale to add one!")
        return
    lines = [f"🐋 <b>TRACKED WHALES</b>\n{DIVIDER}\n"]
    for addr, info in wallets.items():
        lines.append(f"• <b>{info.get('label')}</b> [{info.get('chain','?').upper()}]\n  <code>{addr[:22]}...</code>")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def set_mcap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /setmcap [amount]\nExample: /setmcap 10000")
        return
    try:
        mcap = int(args[0].replace(",", "").replace("$", ""))
        ctx.bot_data["scanner"].set_min_mcap(mcap)
        await update.message.reply_text(f"✅ Min MCap set to <b>${mcap:,}</b>", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.")


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scanner = ctx.bot_data.get("scanner")
    tracker = ctx.bot_data.get("whale_tracker")
    notifier = ctx.bot_data.get("notifier")
    pumpfun = ctx.bot_data.get("pumpfun")
    scraper = ctx.bot_data.get("job_scraper")

    s = scanner.get_stats()
    w = tracker.get_stats()
    p = pumpfun.get_stats() if pumpfun else {}
    j = scraper.get_stats() if scraper else {}
    alerts = notifier.alerts_enabled

    from config import ALL_CHAT_IDS
    user_count = len(ALL_CHAT_IDS)

    msg = (
        f"📊 <b>BOT STATUS</b>\n"
        f"{DIVIDER}\n"
        f"🔔 Alerts: {'✅ ON' if alerts else '❌ OFF'}\n"
        f"👥 Users notified: {user_count}\n\n"
        f"<b>🔍 DexScreener Scanner</b>\n"
        f"  Scans: {s['scan_count']} | Found: {s['found_count']}\n"
        f"  Min MCap: ${s['min_mcap']:,}\n\n"
        f"<b>🟣 Pump.fun Scanner</b>\n"
        f"  Launches: {p.get('launch_count',0)} | Grads: {p.get('grad_count',0)}\n\n"
        f"<b>💼 Job Scraper</b>\n"
        f"  Jobs found: {j.get('found_count',0)}\n\n"
        f"<b>🐋 Whale Tracker</b>\n"
        f"  Wallets: {w['wallet_count']} | Checks: {w['check_count']}\n\n"
        f"<b>📨 Total messages sent: {notifier.sent_count}</b>\n"
        f"{DIVIDER}"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def alerts_on(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.bot_data["notifier"].alerts_enabled = True
    await update.message.reply_text("✅ <b>Alerts ON</b> — you'll get notified in real-time!", parse_mode=ParseMode.HTML)


async def alerts_off(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.bot_data["notifier"].alerts_enabled = False
    await update.message.reply_text("🔕 Alerts paused. Use /alertson to resume.", parse_mode=ParseMode.HTML)
