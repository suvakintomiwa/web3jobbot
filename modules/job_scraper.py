"""
Job Board Scraper — scrapes Web3 job listings from free boards
"""
import asyncio
import aiohttp
import json
import logging
import os
import re
from datetime import datetime
from config import JOB_SCAN_INTERVAL_SECONDS, SEEN_JOBS_FILE, DATA_DIR

logger = logging.getLogger(__name__)

TARGET_ROLES = [
    "community manager", "community moderator", "moderator",
    "community lead", "discord moderator", "telegram moderator",
    "kol", "ambassador", "content creator", "social media",
    "growth", "marketing", "raider", "engagement"
]

JOB_SOURCES = [
    {
        "name": "Web3.Career",
        "url": "https://web3.career/community-manager-jobs+moderator-jobs+marketing-jobs",
        "base": "https://web3.career",
    },
    {
        "name": "CryptoJobsList",
        "url": "https://cryptojobslist.com/community",
        "base": "https://cryptojobslist.com",
    },
    {
        "name": "Remote3",
        "url": "https://remote3.co/web3-jobs?category=community",
        "base": "https://remote3.co",
    },
]


def load_seen():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen)[-1000:], f)


def extract_jobs_from_html(html, source):
    """Simple regex-based job extractor — works without BeautifulSoup"""
    jobs = []

    # Match <a href="...">Job Title</a> patterns
    link_pattern = re.compile(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{10,80})</a>',
        re.IGNORECASE
    )

    for match in link_pattern.finditer(html):
        href, title = match.group(1), match.group(2).strip()
        title_lower = title.lower()

        if any(role in title_lower for role in TARGET_ROLES):
            # Build full URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = source["base"] + href
            else:
                continue

            job_id = re.sub(r'[^a-z0-9]', '', title_lower[:40])
            if job_id:
                jobs.append({
                    "title": title,
                    "url": full_url,
                    "source": source["name"],
                    "id": job_id,
                    "found_at": datetime.utcnow().isoformat(),
                })

    return jobs


class JobScraper:
    def __init__(self, notifier):
        self.notifier = notifier
        self.seen = load_seen()
        self.running = True
        self.found_count = 0

    async def run_loop(self):
        logger.info("Job scraper started")
        # First scan after 30 seconds
        await asyncio.sleep(30)
        while self.running:
            try:
                await self.scrape_all()
            except Exception as e:
                logger.error(f"Job scraper error: {e}")
            await asyncio.sleep(JOB_SCAN_INTERVAL_SECONDS)

    async def scrape_all(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        new_jobs = []

        async with aiohttp.ClientSession(headers=headers) as session:
            for source in JOB_SOURCES:
                try:
                    async with session.get(source["url"], timeout=aiohttp.ClientTimeout(total=20)) as r:
                        if r.status != 200:
                            logger.warning(f"{source['name']} returned {r.status}")
                            continue
                        html = await r.text()
                        jobs = extract_jobs_from_html(html, source)
                        for job in jobs:
                            if job["id"] not in self.seen:
                                self.seen.add(job["id"])
                                new_jobs.append(job)
                                self.found_count += 1
                except Exception as e:
                    logger.warning(f"Job scrape error {source['name']}: {e}")

        save_seen(self.seen)

        if new_jobs:
            # Batch notify — group up to 5 per message
            batch = new_jobs[:8]
            await self.notifier.notify_job_listings(batch)
            logger.info(f"Found {len(new_jobs)} new jobs")

    def get_stats(self):
        return {"found_count": self.found_count, "seen_total": len(self.seen)}
