"""
Notifier — formats and pushes alerts to Telegram
"""
import logging
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

CHAIN_EMOJI = {
    "solana": "🟣",
    "ethereum": "🔷",
    "bsc": "🟡",
    "base": "🔵",
    "arbitrum": "🔶",
}

ROLE_KEYWORDS = {
    "🎙️ KOL / Shill": ["kol", "influencer", "shill", "ambassador", "content"],
    "👥 Community Manager": ["community manager", "cm ", "community lead"],
    "🛡️ Moderator": ["mod", "moderator", "discord mod", "tg mod"],
    "⚔️ Raider": ["raider", "raid", "twitter raid", "engagement"],
    "📣 Marketing": ["marketing", "growth", "social media", "smm"],
}


def detect_job_opportunities(token):
    """Guess likely open roles based on token's social presence"""
    roles = []
    socials = token.get("socials", {})
    if socials.get("twitter"):
        roles.append("🎙️ KOL / Shill")
        roles.append("⚔️ Raider")
    if socials.get("telegram"):
        roles.append("👥 Community Manager")
        roles.append("🛡️ Moderator")
    if socials.get("discord"):
        roles.append("🛡️ Moderator")
    if len(socials) >= 2:
        roles.append("📣 Marketing")
    return list(dict.fromkeys(roles))  # dedupe, preserve order


class Notifier:
    def __init__(self, bot: Bot, chat_id: str):
        self.bot = bot
        self.chat_id = chat_id
        self.alerts_enabled = True
        self.sent_count = 0

    async def send(self, text: str, disable_preview=True):
        if not self.alerts_enabled:
            return
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=disable_preview,
            )
            self.sent_count += 1
        except TelegramError as e:
            logger.error(f"Telegram send error: {e}")

    async def notify_new_token(self, token: dict):
        chain = token.get("chain", "unknown")
        emoji = CHAIN_EMOJI.get(chain, "⛓️")
        socials = token.get("socials", {})
        roles = detect_job_opportunities(token)

        social_lines = []
        if socials.get("twitter"):
            social_lines.append(f"  🐦 <a href='{socials['twitter']}'>Twitter / X</a>")
        if socials.get("telegram"):
            social_lines.append(f"  ✈️ <a href='{socials['telegram']}'>Telegram</a>")
        if socials.get("discord"):
            social_lines.append(f"  💬 <a href='{socials['discord']}'>Discord</a>")
        if socials.get("website"):
            social_lines.append(f"  🌐 <a href='{socials['website']}'>Website</a>")

        role_lines = "\n".join(f"  {r}" for r in roles) if roles else "  None detected"
        social_block = "\n".join(social_lines) if social_lines else "  None"

        dex_url = token.get("url") or f"https://dexscreener.com/{chain}/{token.get('address','')}"

        msg = (
            f"🆕 <b>NEW TOKEN DETECTED</b> {emoji}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 <b>{token.get('name', 'Unknown')}</b>\n"
            f"⛓️ Chain: <code>{chain.upper()}</code>\n"
            f"📊 <a href='{dex_url}'>View on DexScreener</a>\n"
            f"\n<b>🔗 Socials:</b>\n{social_block}\n"
            f"\n<b>💼 Potential Job Roles:</b>\n{role_lines}\n"
            f"\n<b>💡 Job Hunting Tips:</b>\n"
            f"  • DM the project on Twitter — offer CM/mod help\n"
            f"  • Join their TG/Discord and be active early\n"
            f"  • Early supporters often get hired\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ {datetime.utcnow().strftime('%H:%M UTC')}"
        )
        await self.send(msg)

    async def notify_whale_move(self, move: dict):
        chain = move.get("chain", "unknown")
        emoji = CHAIN_EMOJI.get(chain, "⛓️")
        sig = move.get("sig", "")
        explorer_links = {
            "solana": f"https://solscan.io/tx/{sig}",
            "ethereum": f"https://etherscan.io/tx/{sig}",
            "bsc": f"https://bscscan.com/tx/{sig}",
            "base": f"https://basescan.org/tx/{sig}",
        }
        explorer = explorer_links.get(chain, "#")

        msg = (
            f"🐋 <b>WHALE ALERT</b> {emoji}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Wallet: <code>{move.get('label')}</code>\n"
            f"🔔 Action: <b>{move.get('action')}</b>\n"
            f"💰 Est. Value: <b>${move.get('usd_value', 0):,.0f}</b>\n"
            f"⛓️ Chain: <code>{chain.upper()}</code>\n"
            f"🔍 <a href='{explorer}'>View Transaction</a>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ {datetime.utcnow().strftime('%H:%M UTC')}"
        )
        await self.send(msg)

    async def notify_startup(self):
        msg = (
            "🚀 <b>Web3 Job Hunter Bot is LIVE!</b>\n\n"
            "I'm now scanning for:\n"
            "  🔍 New tokens with socials\n"
            "  🐋 Whale wallet moves\n"
            "  💼 Job opportunities (CM, Mod, KOL, Raider)\n\n"
            "Type /help to see all commands."
        )
        await self.send(msg)
