"""
DM Drafter — generates outreach pitch messages for new projects
"""

ROLE_PITCHES = {
    "cm": {
        "label": "Community Manager",
        "pitch": (
            "Hey! I just discovered {name} and I love what you're building 🔥\n\n"
            "I'm an experienced Web3 Community Manager looking to join an exciting project.\n"
            "I can help you:\n"
            "• Grow and moderate your Telegram/Discord community\n"
            "• Create engaging content and announcements\n"
            "• Onboard new members and keep engagement high\n"
            "• Run AMAs, giveaways and community events\n\n"
            "I'm available immediately and work for a fair token/salary package.\n"
            "Would love to chat! Are you looking for community help? 🤝"
        )
    },
    "mod": {
        "label": "Moderator",
        "pitch": (
            "Hey {name} team! 👋\n\n"
            "I'm an active Web3 moderator with experience keeping communities safe and engaged.\n\n"
            "I can moderate your:\n"
            "• Telegram group (anti-spam, answering questions)\n"
            "• Discord server (roles, channels, moderation)\n\n"
            "Available in multiple timezones for 24/7 coverage.\n"
            "Happy to do a trial period to show my value!\n\n"
            "Are you looking for mods? Let me know 🛡️"
        )
    },
    "kol": {
        "label": "KOL / Content Creator",
        "pitch": (
            "Gm {name} team! 🌅\n\n"
            "I'm a Web3 content creator and KOL interested in your project.\n\n"
            "I can offer:\n"
            "• Twitter/X threads and spaces about {name}\n"
            "• Telegram channel promotions\n"
            "• Honest project reviews to my community\n"
            "• Consistent shilling and awareness campaigns\n\n"
            "Let's discuss a collaboration deal — I work with tokens, revenue share, or flat fee.\n"
            "What's your marketing budget looking like? 🎙️"
        )
    },
    "raider": {
        "label": "Raider / Engagement",
        "pitch": (
            "Hey {name}! Just found your project and it looks solid 🔥\n\n"
            "I run an active Web3 raid squad — we can help with:\n"
            "• Twitter raids (likes, RTs, comments on your posts)\n"
            "• Trending your hashtags\n"
            "• Building social proof fast\n\n"
            "We're available daily and work for tokens or small fee.\n"
            "Want to see what we can do? ⚔️"
        )
    },
}


def generate_dm(token: dict, role_key: str = "cm") -> str:
    role = ROLE_PITCHES.get(role_key, ROLE_PITCHES["cm"])
    name = token.get("name", "your project")
    symbol = token.get("symbol", "")
    display = f"{name} (${symbol})" if symbol else name
    pitch = role["pitch"].replace("{name}", display)
    return pitch


def generate_all_pitches(token: dict) -> dict:
    return {key: generate_dm(token, key) for key in ROLE_PITCHES}


def format_dm_message(token: dict) -> str:
    name = token.get("name", "Unknown")
    symbol = token.get("symbol", "")
    socials = token.get("socials", {})

    lines = [
        f"✍️ <b>Auto-Draft DMs for {name}" + (f" (${symbol})" if symbol else "") + "</b>\n",
        "<b>Pick a role and copy your pitch:</b>\n",
    ]

    for key, role in ROLE_PITCHES.items():
        pitch = generate_dm(token, key)
        lines.append(f"━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"<b>{role['label']}</b>")
        lines.append(f"<pre>{pitch}</pre>")

    if socials.get("twitter"):
        lines.append(f"\n🐦 Send to: <a href='{socials['twitter']}'>Twitter DM</a>")
    if socials.get("telegram"):
        lines.append(f"✈️ Or join: <a href='{socials['telegram']}'>Their Telegram</a>")

    return "\n".join(lines)
