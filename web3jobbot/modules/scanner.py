"""
Token Scanner — polls DexScreener for new tokens with socials above min MCap
"""
import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from config import (
    DEXSCREENER_LATEST, DEXSCREENER_NEW_PAIRS, DEXSCREENER_PAIRS,
    TARGET_CHAINS, MIN_MCAP_USD, SCAN_INTERVAL_SECONDS,
    SEEN_TOKENS_FILE, DATA_DIR
)

logger = logging.getLogger(__name__)


def load_seen_tokens():
    if os.path.exists(SEEN_TOKENS_FILE):
        with open(SEEN_TOKENS_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen_tokens(seen):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_TOKENS_FILE, "w") as f:
        json.dump(list(seen)[-2000:], f)  # keep last 2000


class TokenScanner:
    def __init__(self, notifier):
        self.notifier = notifier
        self.seen_tokens = load_seen_tokens()
        self.min_mcap = MIN_MCAP_USD
        self.running = True
        self.scan_count = 0
        self.found_count = 0

    def set_min_mcap(self, mcap):
        self.min_mcap = mcap

    async def run_loop(self):
        logger.info(f"TokenScanner started — min MCap: ${self.min_mcap:,}")
        while self.running:
            try:
                await self.scan()
            except Exception as e:
                logger.error(f"Scanner error: {e}")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

    async def scan(self):
        self.scan_count += 1
        new_tokens = []

        async with aiohttp.ClientSession() as session:
            # Source 1: DexScreener latest token profiles (boosted/new)
            try:
                async with session.get(DEXSCREENER_LATEST, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        data = await r.json()
                        tokens = self._parse_profiles(data)
                        new_tokens.extend(tokens)
            except Exception as e:
                logger.warning(f"Profile fetch error: {e}")

            # Source 2: Token boosts (trending new launches)
            try:
                async with session.get(DEXSCREENER_NEW_PAIRS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        data = await r.json()
                        tokens = self._parse_profiles(data)
                        new_tokens.extend(tokens)
            except Exception as e:
                logger.warning(f"Boosts fetch error: {e}")

        # Deduplicate by address
        seen_this_scan = set()
        unique_new = []
        for t in new_tokens:
            key = t["address"]
            if key not in self.seen_tokens and key not in seen_this_scan:
                seen_this_scan.add(key)
                unique_new.append(t)

        for token in unique_new:
            self.seen_tokens.add(token["address"])
            self.found_count += 1
            await self.notifier.notify_new_token(token)

        save_seen_tokens(self.seen_tokens)
        logger.info(f"Scan #{self.scan_count} done — {len(unique_new)} new tokens found")

    def _parse_profiles(self, data):
        results = []
        if not isinstance(data, list):
            return results

        for item in data:
            try:
                chain = item.get("chainId", "").lower()
                if chain not in TARGET_CHAINS:
                    continue

                address = item.get("tokenAddress", "")
                if not address:
                    continue

                # Extract socials
                links = item.get("links", [])
                socials = self._extract_socials(links)

                # Only care about tokens with at least one social
                if not socials:
                    continue

                token = {
                    "address": address,
                    "chain": chain,
                    "name": item.get("description", "Unknown")[:40],
                    "url": item.get("url", ""),
                    "icon": item.get("icon", ""),
                    "socials": socials,
                    "mcap": 0,  # will be enriched if possible
                    "found_at": datetime.utcnow().isoformat(),
                }
                results.append(token)
            except Exception as e:
                logger.debug(f"Parse error on item: {e}")

        return results

    def _extract_socials(self, links):
        socials = {}
        for link in links:
            label = (link.get("label") or link.get("type") or "").lower()
            url = link.get("url", "")
            if not url:
                continue
            if "twitter" in url or "x.com" in url or label in ("twitter", "x"):
                socials["twitter"] = url
            elif "telegram" in url or "t.me" in url or label == "telegram":
                socials["telegram"] = url
            elif "discord" in url or label == "discord":
                socials["discord"] = url
            elif "website" in label or label in ("", "website"):
                if "http" in url and "twitter" not in url and "t.me" not in url:
                    socials["website"] = url
        return socials

    def get_stats(self):
        return {
            "scan_count": self.scan_count,
            "found_count": self.found_count,
            "seen_total": len(self.seen_tokens),
            "min_mcap": self.min_mcap,
        }
