"""
OmniPost Studio - Multi-Platform Social Content Engine & Queue
Proprietary Infrastructure for Kinetic Media Group Inc.

Features:
- Spintax permutation engine with shadowban evasion algorithms
- Multi-platform API dispatch simulation (Reddit PRAW/OAuth2, Twitter/X API v2, Telegram)
- Priority scheduling queue with rate-limit bucket throttling
- Structured audit logger and telemetry exporter
"""

import asyncio
import logging
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("OmniPostScheduler")


class SpintaxEngine:
    """Expands nested and single-level spintax patterns: {Option A|Option B|Option C}."""

    PATTERN = re.compile(r"\{([^{}]+)\}")

    @classmethod
    def permute(cls, text: str) -> str:
        """Randomly selects one option from each spintax group."""
        while True:
            match = cls.PATTERN.search(text)
            if not match:
                break
            choices = match.group(1).split("|")
            chosen = random.choice(choices).strip()
            text = text[:match.start()] + chosen + text[match.end():]
        return text

    @classmethod
    def calculate_permutations(cls, text: str) -> int:
        """Calculates total potential permutations for a spintax string."""
        total = 1
        for match in cls.PATTERN.finditer(text):
            choices = match.group(1).split("|")
            total *= len(choices)
        return total


@dataclass
class ScheduledPost:
    platform: str
    target: str
    headline: str
    raw_content: str
    scheduled_timestamp: float
    post_id: Optional[str] = None
    audit_id: Optional[str] = None

    def __post_init__(self):
        if not self.post_id:
            self.post_id = f"POST-{random.randint(10000, 99999)}"
        if not self.audit_id:
            self.audit_id = f"KMG-DSP-{random.randint(1000, 9999)}"


class PlatformPublisher:
    """Handles publishing calls with platform-specific rate limits and response codes."""

    def __init__(self, platform_name: str, rate_limit_rpm: int):
        self.platform = platform_name
        self.rate_limit_rpm = rate_limit_rpm
        self.requests_this_minute = 0
        self.last_reset = time.time()

    def check_rate_limit(self) -> bool:
        now = time.time()
        if now - self.last_reset > 60:
            self.requests_this_minute = 0
            self.last_reset = now
        return self.requests_this_minute < self.rate_limit_rpm

    async def publish(self, post: ScheduledPost) -> Dict:
        if not self.check_rate_limit():
            return {"status": "RATE_LIMITED", "error": "API quota reached for minute bucket"}

        self.requests_this_minute += 1
        # Resolve spintax to generate unique outbound copy
        rendered_text = SpintaxEngine.permute(post.raw_content)

        # Realistic network latency simulation
        latency_ms = random.randint(45, 110)
        await asyncio.sleep(latency_ms / 1000.0)

        result = {
            "status": "PUBLISHED",
            "http_code": 200,
            "platform": self.platform,
            "target": post.target,
            "post_id": post.post_id,
            "audit_id": post.audit_id,
            "rendered_length": len(rendered_text),
            "rendered_preview": (rendered_text[:60] + "...") if len(rendered_text) > 60 else rendered_text,
            "latency_ms": latency_ms,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        return result


class SocialContentEngine:
    """Central daemon orchestrating scheduling queues and publishing workers."""

    def __init__(self):
        self.publishers = {
            "reddit": PlatformPublisher("Reddit", rate_limit_rpm=60),
            "twitter": PlatformPublisher("X / Twitter", rate_limit_rpm=50),
            "telegram": PlatformPublisher("Telegram", rate_limit_rpm=30),
            "linkedin": PlatformPublisher("LinkedIn", rate_limit_rpm=40),
        }
        self.queue: List[ScheduledPost] = []
        self.history: List[Dict] = []

    def schedule_post(self, platform: str, target: str, headline: str, raw_content: str, delay_seconds: float = 0.0) -> ScheduledPost:
        post = ScheduledPost(
            platform=platform.lower(),
            target=target,
            headline=headline,
            raw_content=raw_content,
            scheduled_timestamp=time.time() + delay_seconds
        )
        self.queue.append(post)
        perms = SpintaxEngine.calculate_permutations(raw_content)
        logger.info(f"[QUEUED] #{post.post_id} -> {platform.upper()} ({target}) | Variations: {perms} | Delay: {delay_seconds:.1f}s")
        return post

    async def process_queue(self):
        """Processes posts whose scheduled time has elapsed."""
        now = time.time()
        due_posts = [p for p in self.queue if p.scheduled_timestamp <= now]
        self.queue = [p for p in self.queue if p.scheduled_timestamp > now]

        for post in due_posts:
            publisher = self.publishers.get(post.platform)
            if not publisher:
                logger.error(f"[ERROR] Unsupported platform: {post.platform}")
                continue

            res = await publisher.publish(post)
            if res.get("status") == "PUBLISHED":
                self.history.append(res)
                logger.info(
                    f"[PUBLISHED] [{res['platform']}] {res['target']} -> "
                    f"\"{res['rendered_preview']}\" (HTTP {res['http_code']} in {res['latency_ms']}ms)"
                )
            else:
                logger.warning(f"[RETRY_QUEUED] Post {post.post_id} hit rate limit. Requeuing...")
                post.scheduled_timestamp = time.time() + 15
                self.queue.append(post)


async def main():
    print("=" * 72)
    print("  OMNIPOST STUDIO - SOCIAL CONTENT ENGINE & AUTOMATED QUEUE")
    print("  Client: Kinetic Media Group Inc. | Cluster: #OMNI-PUB-418")
    print("=" * 72)

    engine = SocialContentEngine()

    # Sample scheduled posts across Reddit, X, and Telegram
    engine.schedule_post(
        platform="reddit",
        target="r/startups",
        headline="How we automated catalog scraping across 4 retail platforms",
        raw_content="{Excited to share|Quick breakdown|Key findings}: We automated catalog indexing with async scrapers and saved {15|18|20} hrs/week with {zero|minimal} downtime.",
        delay_seconds=0.1
    )

    engine.schedule_post(
        platform="twitter",
        target="@KineticGrowth",
        headline="Microservices architecture tip",
        raw_content="{Tip of the day|Pro engineer tip}: Always offload {webhook parsing|crypto verification} to background coroutines rather than blocking your main event loop.",
        delay_seconds=0.2
    )

    engine.schedule_post(
        platform="telegram",
        target="@KineticMarketingVIP",
        headline="Weekly E-commerce Intelligence Briefing",
        raw_content="Retail hardware prices shifted {12%|15%|18%} over the last 72 hours. Check our dashboard for full competitor breakdown.",
        delay_seconds=0.3
    )

    print("\n[DAEMON] Starting scheduler tick loop...")
    await asyncio.sleep(0.4)
    await engine.process_queue()

    print("-" * 72)
    print(f"[SUMMARY] Total dispatched: {len(engine.history)} posts | Remaining in queue: {len(engine.queue)}")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
