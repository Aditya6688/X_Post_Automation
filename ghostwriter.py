import feedparser
import requests
import random
import time
import os
from bs4 import BeautifulSoup
from openai import OpenAI
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

# Initialize Clients
client = OpenAI(api_key=OPENAI_API_KEY)
notion = Client(auth=NOTION_TOKEN)

# ==========================================
# MODULE 1: THE SOURCE FETCHERS
# ==========================================

def fetch_hacker_news():
    """Source: General Tech News"""
    print("📡 Source selected: HackerNews...")
    feed = feedparser.parse("https://news.ycombinator.com/rss")
    articles = []
    for entry in feed.entries[:3]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "type": "News"
        })
    return articles

def fetch_github_trending():
    """Source: Top Python Repos"""
    print("📡 Source selected: GitHub Trending...")
    url = "https://github.com/trending/python?since=daily"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    repos = []
    
    # Scrape the article tags
    for row in soup.select('article.Box-row')[:3]:
        name = row.select_one('h2 a').text.strip().replace('\n', '').replace(' ', '')
        link = "https://github.com" + row.select_one('h2 a')['href']
        desc = row.select_one('p').text.strip() if row.select_one('p') else "No description"
        repos.append({
            "title": f"Repo: {name} - {desc}", # Combine for context
            "link": link,
            "type": "Code"
        })
    return repos

def fetch_dev_to():
    """Source: Engineering Tutorials"""
    print("📡 Source selected: Dev.to...")
    # Get top articles from the last few days with 'python' tag
    url = "https://dev.to/api/articles?tag=python&top=2" 
    response = requests.get(url).json()
    articles = []
    for item in response[:3]:
        articles.append({
            "title": item['title'],
            "link": item['url'],
            "type": "Tutorial"
        })
    return articles

def fetch_arxiv_ai():
    """Source: Latest AI Papers (cs.AI)"""
    print("📡 Source selected: ArXiv (AI)...")
    # Fetch recent papers from CS.AI
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=3&sortBy=submittedDate&sortOrder=descending"
    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries:
        papers.append({
            "title": f"Paper: {entry.title}",
            "link": entry.link,
            "type": "Research"
        })
    return papers

# ==========================================
# MODULE 2: THE BRAIN (Dynamic Prompts)
# ==========================================

def generate_tweet(content, source_type):
    """Adapts the AI persona based on the source type."""
    
    # 1. Select the Persona based on Source
    if source_type == "Code":
        persona = "You are a pragmatic Senior Engineer looking at a new open-source tool. You value utility over hype."
        instruction = "Explain briefly what this repo does and why a developer should star it. Ask if it's better than existing tools."
    elif source_type == "Research":
        persona = "You are an AI Researcher breaking down complex papers. You make hard concepts simple."
        instruction = "Summarize the core innovation of this paper in one sentence. Ask 'Will this actually work in production?'"
    elif source_type == "Tutorial":
        persona = "You are a helpful mentor. You love sharing learning resources."
        instruction = "Tell people why this tutorial is worth their time. Mention a specific thing they will learn."
    else: # News
        persona = "You are a tech commentator with a cynical wit. You cut through the noise."
        instruction = "Give a hot take on this news. Is it good or bad for the industry?"

    # 2. The Core Prompt
    system_prompt = f"""
    {persona}
    
    Task: Write a Twitter thread hook (1st tweet) for this content.
    
    Rules:
    - Casual tone (lowercase ok).
    - NO hashtags.
    - NO emojis (unless it's a code snippet like ⚡️).
    - Length: Under 200 characters.
    - {instruction}
    """

    user_prompt = f"Title: {content['title']}\nLink: {content['link']}"

    response = client.chat.completions.create(
        model="gpt-5-nano-2025-08-07",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

# ==========================================
# MODULE 3: THE ENGINE
# ==========================================

def run_ghostwriter_v2():
    print("--- 🎲 Rolling the Dice for Content Source ---")
    
    # Randomly select ONE source for today
    # Weights: 40% GitHub, 30% News, 20% Papers, 10% Dev.to
    sources = [fetch_github_trending, fetch_hacker_news, fetch_arxiv_ai, fetch_dev_to]
    weights = [0.4, 0.3, 0.2, 0.1]
    
    selected_fetcher = random.choices(sources, weights=weights, k=1)[0]
    
    # Fetch content
    items = selected_fetcher()
    
    if not items:
        print("❌ Failed to fetch items.")
        return

    print(f"✅ Found {len(items)} items. Generating drafts...")

    for item in items:
        draft = generate_tweet(item, item['type'])
        
        # Save to Notion
        try:
            notion.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties={
                    "Name": {"title": [{"text": {"content": item['title']}}]},
                    "Tweet Draft": {"rich_text": [{"text": {"content": draft}}]},
                    "Source URL": {"url": item['link']},
                    "Status": {"select": {"name": "Draft"}},
                    "Type": {"select": {"name": item['type']}} # Ensure you add this column in Notion!
                }
            )
            print(f"📝 Saved Draft: {item['title'][:30]}...")
        except Exception as e:
            print(f"Error saving to Notion: {e}")

if __name__ == "__main__":
    run_ghostwriter_v2()