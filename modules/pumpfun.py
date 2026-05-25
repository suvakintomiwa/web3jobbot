"""
Pump.fun Scanner — catches new launches and graduation alerts
"""
import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from config import (
    PUMPFUN_API, PUMPFUN_GRADUATING,
    PUMPFUN_INTERVAL_SECONDS, SEEN_PUMPFUN_FILE, DATA_DIR
)

logger = logging.getLogger(__name__)


def load_seen():
    if os.path.exists(SEEN_PUMPFUN_FILE):
        with open(SEEN_PUMPFUN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_PUMPFUN_FILE, "w") as f:
        json.dump(list(seen)[-3000:], f)


class PumpFunScanner:
    def __init__(self, notifier):
        self.notifier = notifier
        self.seen = load_seen()
        self.running = True
        self.launch_count = 0
        self.grad_count = 0

    async def run_loop(self):
        logger.info("PumpFun scanner started")
        while self.running:
            try:
                await self.scan_new()
                await self.scan_graduating()
            except Exception as e:
                logger.error(f"PumpFun error: {e}")
            await asyncio.sleep(PUMPFUN_INTERVAL_SECONDS)

    async def scan_new(self):
        params = {"limit": 20, "sort": "created_timestamp", "order": "DESC", "includeNsfw": "false"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(PUMPFUN_API, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200:
                        return
                    data = await r.json()
                    coins = data if isinstance(data, list) else data.get("coins", [])
                    for coin in coins:
                        mint = coin.get("mint", "")
                        if not mint or mint in self.seen:
                            continue
                        self.seen.add(mint)
                        self.launch_count += 1

                        socials = {}
                        if coin.get("twitter"):
                            socials["twitter"] = coin["twitter"]
                        if coin.get("telegram"):
                            socials["telegram"] = coin["telegram"]
                        if coin.get("website"):
                            socials["website"] = coin["website"]

                        if not socials:
                            continue

                        token = {
                            "mint": mint,
                            "name": coin.get("name", "Unknown"),
                            "symbol": coin.get("symbol", "???"),
                            "description": (coin.get("description") or "")[:120],
                            "image": coin.get("image_uri", ""),
                            "market_cap": coin.get("usd_market_cap", 0),
                            "socials": socials,
                            "pumpfun_url": f"https://pump.fun/{mint}",
                            "created_at": coin.get("created_timestamp", ""),
                        }
                        await self.notifier.notify_pumpfun_launch(token)
                    save_seen(self.seen)
            except Exception as e:
                logger.warning(f"PumpFun new scan error: {e}")

    async def scan_graduating(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(PUMPFUN_GRADUATING, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200:
                        return
                    data = await r.json()
                    coins = data if isinstance(data, list) else data.get("coins", [])
                    for coin in coins:
                        mint = coin.get("mint", "")
                        grad_key = f"grad_{mint}"
                        if not mint or grad_key in self.seen:
                            continue
                        self.seen.add(grad_key)
                        self.grad_count += 1

                        token = {
                            "mint": mint,
                            "name": coin.get("name", "Unknown"),
                            "symbol": coin.get("symbol", "???"),
                            "market_cap": coin.get("usd_market_cap", 0),
                            "progress": coin.get("bonding_curve_percentage", 0),
                            "pumpfun_url": f"https://pump.fun/{mint}",
                            "socials": {
                                k: coin.get(k) for k in ["twitter", "telegram", "website"] if coin.get(k)
                            },
                        }
                        await self.notifier.notify_pumpfun_graduating(token)
                    save_seen(self.seen)
            except Exception as e:
                logger.warning(f"PumpFun graduating scan error: {e}")

    def get_stats(self):
        return {
            "launch_count": self.launch_count,
            "grad_count": self.grad_count,
            "seen_total": len(self.seen),
        }
