"""
Notifier — formats and pushes alerts to Telegram (bold Web3/NFT style)
"""
import logging
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
from config import ALL_CHAT_IDS

logger = logging.getLogger(__name__)

CHAIN_BADGE = {
    "solana":   "◎ SOL",
    "ethereum": "Ξ ETH",
    "bsc":      "⬡ BSC",
    "base":     "🔵 BASE",
    "arbitrum": "🔶 ARB",
}

ROLE_EMOJI = {
    "🎙️ KOL / Shill":        ["twitter"],
    "⚔️ Raider":              ["twitter"],
    "👥 Community Manager":   ["telegram", "discord"],
    "🛡️ Moderator":           ["discord", "telegram"],
    "📣 Marketing":           [],
}

DIVIDER = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"


def detect_roles(socials):
    roles = []
    if socials.get("twitter"):
        roles += ["🎙️ KOL / Shill", "⚔️ Raider"]
    if socials.get("telegram"):
        roles += ["👥 Community Manager", "🛡️ Moderator"]
    if socials.get("discord"):
        if "🛡️ Moderator" not in roles:
            roles.append("🛡️ Moderator")
    if len(socials) >= 2:
        roles.append("📣 Marketing")
    return list(dict.fromkeys(roles))


def social_block(socials):
    lines = []
    if socials.get("twitter"):
        lines.append(f"  🐦 <a href='{socials['twitter']}'>Twitter / X</a>")
    if socials.get("telegram"):
        lines.append(f"  ✈️ <a href='{socials['telegram']}'>Telegram</a>")
    if socials.get("discord"):
        lines.append(f"  💬 <a href='{socials['discord']}'>Discord</a>")
    if socials.get("website"):
        lines.append(f"  🌐 <a href='{socials['website']}'>Website</a>")
    return "\n".join(lines) if lines else "  —"


class Notifier:
    def __init__(self, bot: Bot, chat_id: str):
        self.bot = bot
        self.chat_id = chat_id
        self.alerts_enabled = True
        self.sent_count = 0

    async def send(self, text: str, disable_preview=True):
        if not self.alerts_enabled:
            return
        for cid in ALL_CHAT_IDS:
            try:
                await self.bot.send_message(
                    chat_id=cid,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=disable_preview,
                )
                self.sent_count += 1
            except TelegramError as e:
                logger.error(f"Send error to {cid}: {e}")

    async def notify_new_token(self, token: dict):
        chain = token.get("chain", "unknown")
        badge = CHAIN_BADGE.get(chain, chain.upper())
        socials = token.get("socials", {})
        roles = detect_roles(socials)
        dex_url = token.get("url") or f"https://dexscreener.com/{chain}/{token.get('address','')}"
        role_str = "  " + "  |  ".join(roles) if roles else "  None detected"
        time_str = datetime.utcnow().strftime("%H:%M UTC")

        msg = (
            f"🚨 <b>NEW PROJECT ALERT</b> 🚨\n"
            f"{DIVIDER}\n"
            f"💎 <b>{token.get('name','Unknown')}</b>  [{badge}]\n"
            f"📊 <a href='{dex_url}'>View Chart on DexScreener</a>\n"
            f"\n🔗 <b>SOCIALS</b>\n{social_block(socials)}\n"
            f"\n💼 <b>OPEN ROLES</b>\n{role_str}\n"
            f"\n🔥 <b>HOW TO GET HIRED</b>\n"
            f"  → DM them on Twitter NOW (early = hired)\n"
            f"  → Join TG/Discord, be active from day 1\n"
            f"  → Use /dm command to get a ready pitch\n"
            f"{DIVIDER}\n"
            f"⏰ {time_str}"
        )
        await self.send(msg)

    async def notify_pumpfun_launch(self, token: dict):
        socials = token.get("socials", {})
        roles = detect_roles(socials)
        mcap = token.get("market_cap", 0)
        mcap_str = f"${mcap:,.0f}" if mcap else "< $4k"
        role_str = "  " + "  |  ".join(roles) if roles else "  None detected"
        time_str = datetime.utcnow().strftime("%H:%M UTC")

        msg = (
            f"🟣 <b>PUMP.FUN LAUNCH</b> 🟣\n"
            f"{DIVIDER}\n"
            f"🚀 <b>{token.get('name','?')} (${token.get('symbol','?')})</b>\n"
            f"💰 MCap: <b>{mcap_str}</b>  |  ◎ SOL\n"
            f"🔗 <a href='{token.get('pumpfun_url','#')}'>View on Pump.fun</a>\n"
            f"\n📣 <b>SOCIALS</b>\n{social_block(socials)}\n"
            f"\n💼 <b>ROLES NEEDED</b>\n{role_str}\n"
            f"\n⚡ <b>ALPHA</b>: Brand new launch — reach out first!\n"
            f"{DIVIDER}\n"
            f"⏰ {time_str}"
        )
        await self.send(msg)

    async def notify_pumpfun_graduating(self, token: dict):
        mcap = token.get("market_cap", 0)
        progress = token.get("progress", 0)
        socials = token.get("socials", {})
        time_str = datetime.utcnow().strftime("%H:%M UTC")

        msg = (
            f"🎓 <b>PUMP.FUN GRADUATION ALERT</b> 🎓\n"
            f"{DIVIDER}\n"
            f"📈 <b>{token.get('name','?')} (${token.get('symbol','?')})</b>\n"
            f"💰 MCap: <b>${mcap:,.0f}</b>\n"
            f"📊 Bonding Curve: <b>{progress:.1f}%</b> complete\n"
            f"🔗 <a href='{token.get('pumpfun_url','#')}'>View on Pump.fun</a>\n"
            f"\n📣 <b>SOCIALS</b>\n{social_block(socials)}\n"
            f"\n🔥 <b>WHY THIS MATTERS</b>\n"
            f"  → Graduating = moving to Raydium DEX\n"
            f"  → Serious project — more likely hiring CM/mods\n"
            f"  → High urgency: reach out before they list!\n"
            f"{DIVIDER}\n"
            f"⏰ {time_str}"
        )
        await self.send(msg)

    async def notify_job_listings(self, jobs: list):
        if not jobs:
            return
        time_str = datetime.utcnow().strftime("%H:%M UTC")
        lines = [
            f"💼 <b>WEB3 JOBS FOUND</b> ({len(jobs)} new)\n",
            f"{DIVIDER}\n",
        ]
        for job in jobs:
            lines.append(
                f"🟢 <b>{job['title']}</b>\n"
                f"   🏢 {job['source']}\n"
                f"   🔗 <a href='{job['url']}'>Apply Now</a>\n"
            )
        lines.append(f"{DIVIDER}\n⏰ {time_str}")
        await self.send("\n".join(lines))

    async def notify_whale_move(self, move: dict):
        chain = move.get("chain", "unknown")
        badge = CHAIN_BADGE.get(chain, chain.upper())
        sig = move.get("sig", "")
        explorer_links = {
            "solana":   f"https://solscan.io/tx/{sig}",
            "ethereum": f"https://etherscan.io/tx/{sig}",
            "bsc":      f"https://bscscan.com/tx/{sig}",
            "base":     f"https://basescan.org/tx/{sig}",
        }
        explorer = explorer_links.get(chain, "#")
        time_str = datetime.utcnow().strftime("%H:%M UTC")

        msg = (
            f"🐋 <b>WHALE ALERT</b> 🐋\n"
            f"{DIVIDER}\n"
            f"👤 <b>{move.get('label')}</b>  [{badge}]\n"
            f"🔔 Action: <b>{move.get('action')}</b>\n"
            f"💰 Value: <b>${move.get('usd_value', 0):,.0f}</b>\n"
            f"🔍 <a href='{explorer}'>View Transaction</a>\n"
            f"{DIVIDER}\n"
            f"⏰ {time_str}"
        )
        await self.send(msg)

    async def notify_startup(self):
        msg = (
            f"⚡ <b>WEB3 JOB HUNTER BOT — ONLINE</b> ⚡\n"
            f"{DIVIDER}\n"
            f"🟢 All systems running!\n\n"
            f"📡 Scanning:\n"
            f"  ◎ Pump.fun launches\n"
            f"  📊 DexScreener (SOL/ETH/BSC/BASE)\n"
            f"  🐋 Whale wallets\n"
            f"  💼 Web3 job boards\n\n"
            f"Type /help to see all commands.\n"
            f"{DIVIDER}"
        )
        await self.send(msg)
