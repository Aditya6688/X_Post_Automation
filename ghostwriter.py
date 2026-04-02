"""
Ghostwriter — AI-powered Twitter/X content drafting system.

Fetches trending tech content from configurable sources, generates
tweet drafts via OpenAI, and saves them to a Notion database.
"""

import json
import logging
import os
import random
import sys
import time

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from notion_client import Client

# ==========================================
# CONFIGURATION
# ==========================================

CONFIG_PATH = os.getenv("GHOSTWRITER_CONFIG", "config.yaml")


def load_config(path: str = CONFIG_PATH) -> dict:
    """Load and return the YAML configuration file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ==========================================
# LOGGING
# ==========================================

class JSONFormatter(logging.Formatter):
    """Outputs each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Attach any extra structured fields passed via `extra={"data": {...}}`
        if hasattr(record, "data"):
            log_entry["data"] = record.data
        return json.dumps(log_entry)


def setup_logging(config: dict) -> logging.Logger:
    """Configure and return the application logger based on config."""
    log_cfg = config.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    fmt = log_cfg.get("format", "json")
    log_file = log_cfg.get("file")

    logger = logging.getLogger("ghostwriter")
    logger.setLevel(level)
    logger.handlers.clear()

    if fmt == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s"
        )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Optional file handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


# ==========================================
# MODULE 1: SOURCE FETCHERS
# ==========================================

def fetch_hacker_news(cfg: dict, log: logging.Logger) -> list[dict]:
    """Fetch top stories from Hacker News RSS."""
    src = cfg["sources"]["hacker_news"]
    log.info("Fetching from Hacker News", extra={"data": {"url": src["url"]}})

    feed = feedparser.parse(src["url"])
    articles = []
    for entry in feed.entries[: src["max_items"]]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "type": "News",
        })

    log.info("Hacker News fetch complete", extra={"data": {"count": len(articles)}})
    return articles


def fetch_github_trending(cfg: dict, log: logging.Logger) -> list[dict]:
    """Scrape trending Python repos from GitHub."""
    src = cfg["sources"]["github_trending"]
    log.info("Fetching from GitHub Trending", extra={"data": {"url": src["url"]}})

    response = requests.get(src["url"])
    soup = BeautifulSoup(response.text, "html.parser")
    repos = []

    for row in soup.select("article.Box-row")[: src["max_items"]]:
        name = row.select_one("h2 a").text.strip().replace("\n", "").replace(" ", "")
        link = "https://github.com" + row.select_one("h2 a")["href"]
        desc = row.select_one("p").text.strip() if row.select_one("p") else "No description"
        repos.append({
            "title": f"Repo: {name} - {desc}",
            "link": link,
            "type": "Code",
        })

    log.info("GitHub Trending fetch complete", extra={"data": {"count": len(repos)}})
    return repos


def fetch_dev_to(cfg: dict, log: logging.Logger) -> list[dict]:
    """Fetch top Python articles from Dev.to."""
    src = cfg["sources"]["dev_to"]
    log.info("Fetching from Dev.to", extra={"data": {"url": src["url"]}})

    response = requests.get(src["url"]).json()
    articles = []
    for item in response[: src["max_items"]]:
        articles.append({
            "title": item["title"],
            "link": item["url"],
            "type": "Tutorial",
        })

    log.info("Dev.to fetch complete", extra={"data": {"count": len(articles)}})
    return articles


def fetch_arxiv_ai(cfg: dict, log: logging.Logger) -> list[dict]:
    """Fetch latest AI papers from ArXiv (cs.AI)."""
    src = cfg["sources"]["arxiv_ai"]
    log.info("Fetching from ArXiv", extra={"data": {"url": src["url"]}})

    feed = feedparser.parse(src["url"])
    papers = []
    for entry in feed.entries[: src["max_items"]]:
        papers.append({
            "title": f"Paper: {entry.title}",
            "link": entry.link,
            "type": "Research",
        })

    log.info("ArXiv fetch complete", extra={"data": {"count": len(papers)}})
    return papers


# ==========================================
# MODULE 2: TWEET GENERATION
# ==========================================

def generate_tweet(content: dict, source_type: str, cfg: dict, client: OpenAI, log: logging.Logger) -> str:
    """Generate a tweet draft using OpenAI with a config-driven persona."""
    personas = cfg["personas"]
    tweet_cfg = cfg["tweet"]
    model = cfg["openai"]["model"]

    persona = personas.get(source_type, personas["News"])
    rules_block = "\n    - ".join(tweet_cfg["rules"])

    system_prompt = f"""
    {persona['role']}

    Task: Write a Twitter thread hook (1st tweet) for this content.

    Rules:
    - {rules_block}
    - Length: Under {tweet_cfg['max_length']} characters.
    - {persona['instruction']}
    """

    user_prompt = f"Title: {content['title']}\nLink: {content['link']}"

    log.info(
        "Requesting tweet generation",
        extra={"data": {"model": model, "source_type": source_type}},
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    draft = response.choices[0].message.content
    log.debug("Draft generated", extra={"data": {"draft": draft}})
    return draft


# ==========================================
# MODULE 3: ENGINE
# ==========================================

# Maps config keys to fetcher functions
SOURCE_REGISTRY = {
    "github_trending": fetch_github_trending,
    "hacker_news": fetch_hacker_news,
    "arxiv_ai": fetch_arxiv_ai,
    "dev_to": fetch_dev_to,
}


def run(cfg: dict, log: logging.Logger) -> None:
    """Main pipeline: pick source -> fetch -> generate -> save to Notion."""
    log.info("Pipeline started")

    # --- Build source list from config (only enabled sources) ---
    sources_cfg = cfg["sources"]
    enabled = [(k, v) for k, v in sources_cfg.items() if v.get("enabled", True)]

    if not enabled:
        log.error("No sources are enabled in config — aborting")
        return

    fetchers = [SOURCE_REGISTRY[k] for k, _ in enabled]
    weights = [v["weight"] for _, v in enabled]

    selected_key, _ = random.choices(list(zip([k for k, _ in enabled], fetchers)), weights=weights, k=1)[0]
    fetcher = SOURCE_REGISTRY[selected_key]

    log.info("Source selected", extra={"data": {"source": selected_key}})

    # --- Fetch items ---
    items = fetcher(cfg, log)

    if not items:
        log.warning("Fetcher returned no items", extra={"data": {"source": selected_key}})
        return

    # --- Pick a winner ---
    winner = random.choice(items)
    log.info(
        "Content item selected",
        extra={"data": {"title": winner["title"], "type": winner["type"]}},
    )

    # --- Generate draft ---
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    draft = generate_tweet(winner, winner["type"], cfg, openai_client, log)

    # --- Save to Notion ---
    log.info("Saving draft to Notion")
    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    notion_db_id = os.getenv("NOTION_DB_ID")

    try:
        notion.pages.create(
            parent={"database_id": notion_db_id},
            properties={
                "Name": {"title": [{"text": {"content": winner["title"]}}]},
                "Tweet Draft": {"rich_text": [{"text": {"content": draft}}]},
                "Source URL": {"url": winner["link"]},
                "Status": {"status": {"name": "Not started"}},
                "Type": {"select": {"name": winner["type"]}},
            },
        )
        log.info(
            "Draft saved to Notion successfully",
            extra={"data": {"title": winner["title"], "source": selected_key}},
        )
    except Exception:
        log.exception("Failed to save draft to Notion")


# ==========================================
# ENTRY POINT
# ==========================================

def main() -> None:
    load_dotenv()

    cfg = load_config()
    log = setup_logging(cfg)

    # Validate required env vars early
    required_env = ["OPENAI_API_KEY", "NOTION_TOKEN", "NOTION_DB_ID"]
    missing = [v for v in required_env if not os.getenv(v)]
    if missing:
        log.critical(
            "Missing required environment variables",
            extra={"data": {"missing": missing}},
        )
        sys.exit(1)

    run(cfg, log)


if __name__ == "__main__":
    main()
