"""
News MCP Server — Improved Version
------------------------------------
Changes from v1:
1. Title + summary combined for better context
2. Groq LLM for deep sentiment analysis
   (swap to fine-tuned model later — one line change)
3. Better article formatting before analysis

Why Groq for sentiment?
- BioMistral is medical — doesn't understand finance
- FinSight model not trained yet
- Groq Llama-3.3-70B is free and understands financial context
- When FinSight is trained, replace GROQ with HF InferenceClient

Why title + summary?
- Google News gives 2-3 sentence summaries
- Much better than title alone
- Free, no scraping needed
- Avoids paywall issues completely
"""

import json
import os
import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq
from mcp.server.fastmcp import FastMCP
import yfinance as yf

load_dotenv()

mcp = FastMCP("news_server")

# Initialize Groq client
# Why Groq? Free, fast, understands financial context
# To swap to fine-tuned model later:
# Replace this with InferenceClient(model="your-username/finsight-model")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.
    RSS feeds often contain HTML in descriptions.
    """
    if not text:
        return ""
    soup = BeautifulSoup(text, "lxml")
    return soup.get_text(separator=" ").strip()


def fetch_google_news(query: str, max_items: int = 10) -> list:
    """
    Fetch news from Google News RSS.

    Key improvement:
    We now combine title + summary into one 'content' field
    so sentiment analysis has more text to work with.

    Why requests + feedparser separately?
    feedparser.parse(url) uses default headers Google rejects.
    requests.get() gives us control over headers.
    feedparser.parse(content) just parses XML — no HTTP call.
    """
    url = (
        f"https://news.google.com/rss/search"
        f"?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        feed = feedparser.parse(response.content)
        articles = []

        for entry in feed.entries[:max_items]:
            title = entry.get("title", "")
            summary = clean_html(entry.get("summary", ""))

            # Combine title + summary for richer context
            # This is the key improvement over v1
            # Title alone: "TCS Q4 results out"
            # Combined: "TCS Q4 results out. Revenue up 4.5% YoY
            #            at ₹63,437 crore, below analyst estimates
            #            of ₹64,200 crore. Management guided cautiously."
            combined_content = f"{title}. {summary}".strip()

            articles.append({
                "title": title,
                "summary": summary,
                "content": combined_content,  # new field — used for sentiment
                "published": entry.get("published", ""),
                "link": entry.get("link", ""),
                "source": entry.get(
                    "source", {}
                ).get("title", "Google News")
            })

        return articles

    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


def analyze_with_groq(text: str, context: str = "") -> dict:
    """
    Use Groq LLM for financial sentiment analysis.

    Why LLM over keywords?
    Keywords miss context completely:
    - "TCS faces headwinds" → keyword: no match → neutral (WRONG)
    - LLM understands "headwinds" = negative in finance

    Keywords also miss negations:
    - "Not a strong quarter" → keyword finds "strong" → positive (WRONG)
    - LLM understands the negation → negative

    How to swap to fine-tuned model later:
    Replace groq_client.chat.completions.create() with:
    client = InferenceClient(model="your-username/finsight-model")
    response = client.text_generation(prompt, max_new_tokens=200)

    Args:
        text: Article title + summary to analyze
        context: Optional company/sector context
    """
    prompt = f"""You are a financial analyst analyzing Indian stock market news.

Analyze the following news text and provide sentiment analysis.

{f'Context: {context}' if context else ''}

News text:
{text}

Respond in this exact JSON format:
{{
    "sentiment": "positive" or "negative" or "neutral",
    "confidence": 0.0 to 1.0,
    "score": -1.0 (very negative) to 1.0 (very positive),
    "key_points": ["point 1", "point 2", "point 3"],
    "market_impact": "brief impact on stock price",
    "reasoning": "one sentence explanation"
}}

Only respond with the JSON. No other text."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # low temperature = more consistent analysis
            max_tokens=300
        )

        response_text = response.choices[0].message.content.strip()

        # Clean response in case model adds markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text)

    except Exception as e:
        # Fallback to keyword analysis if Groq fails
        return keyword_sentiment(text)


def keyword_sentiment(text: str) -> dict:
    """
    Fallback keyword-based sentiment.
    Used when Groq API is unavailable.
    Less accurate but always works offline.
    """
    text_lower = text.lower()

    positive_keywords = [
        'beat', 'beats', 'surge', 'surges', 'rally', 'profit',
        'growth', 'record', 'strong', 'upgrade', 'buy',
        'outperform', 'bullish', 'expansion', 'dividend',
        'order win', 'new contract', 'partnership', 'acquisition'
    ]

    negative_keywords = [
        'miss', 'misses', 'fall', 'falls', 'decline', 'loss',
        'weak', 'downgrade', 'sell', 'underperform', 'bearish',
        'fraud', 'investigation', 'default', 'pledging',
        'penalty', 'layoff', 'restructuring', 'write-off'
    ]

    pos = sum(1 for kw in positive_keywords if kw in text_lower)
    neg = sum(1 for kw in negative_keywords if kw in text_lower)
    total = pos + neg

    if total == 0:
        return {"sentiment": "neutral", "score": 0.0,
                "confidence": 0.5, "key_points": [],
                "market_impact": "No clear signal",
                "reasoning": "No strong sentiment keywords found"}
    elif pos > neg:
        return {"sentiment": "positive",
                "score": round(pos/total, 2),
                "confidence": 0.6, "key_points": [],
                "market_impact": "Likely positive for stock price",
                "reasoning": f"Found {pos} positive signals"}
    else:
        return {"sentiment": "negative",
                "score": round(-neg/total, 2),
                "confidence": 0.6, "key_points": [],
                "market_impact": "Likely negative for stock price",
                "reasoning": f"Found {neg} negative signals"}


def fetch_nse_announcements(symbol: str) -> list:
    """
    Fetch official corporate announcements from NSE.
    Official government API — never blocked.
    """
    try:
        url = (
            f"https://www.nseindia.com/api/corp-info"
            f"?symbol={symbol}&corpType=announcements"
        )
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Referer': 'https://www.nseindia.com'
        }

        session = requests.Session()
        session.get(
            "https://www.nseindia.com",
            headers=headers, timeout=10
        )
        response = session.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            announcements = data.get("data", [])[:10]
            return [{
                "title": a.get("desc", ""),
                "date": a.get("date", ""),
                "type": a.get("attchmntType", ""),
                "source": "NSE Official"
            } for a in announcements]
    except:
        pass
    return []


def get_company_query(symbol: str) -> str:
    # fetch real company name from yfinance
    # works for all 1800+ NSE stocks automatically
    try:
        ticker = yf.Ticker(f"{symbol.upper()}.NS")
        name = ticker.info.get("longName", "")
        if name:
            return f"{name} NSE stock India"
        else:
            return f"{symbol} NSE stock India"
    except:
        return f"{symbol} NSE stock India"
    

@mcp.tool()
def get_stock_news(symbol: str, max_articles: int = 10) -> str:
    """
    Get latest news about a specific Indian stock
    with LLM-powered sentiment analysis.

    What it does:
    1. Fetches news from Google News (title + summary)
    2. Fetches official NSE announcements
    3. Runs Groq LLM sentiment on each article
    4. Returns articles with individual sentiment scores

    Args:
        symbol: NSE stock symbol e.g. TCS, RELIANCE, INFY
    """
    query = get_company_query(symbol)

    # Fetch articles
    articles = fetch_google_news(query, max_items=max_articles)

    # Run sentiment analysis on each article
    # Why per-article sentiment?
    # Different articles may have different angles —
    # one might be positive (good earnings) while
    # another is negative (regulatory issue)
    # Per-article gives more nuanced picture
    analyzed_articles = []
    for article in articles:
        sentiment = analyze_with_groq(
            text=article["content"],
            context=f"{symbol} Indian stock NSE"
        )
        article["sentiment_analysis"] = sentiment
        analyzed_articles.append(article)

    # Calculate overall sentiment
    # Average score across all articles
    if analyzed_articles:
        scores = [
            a["sentiment_analysis"].get("score", 0)
            for a in analyzed_articles
        ]
        avg_score = round(sum(scores) / len(scores), 2)
        overall = (
            "positive" if avg_score > 0.1
            else "negative" if avg_score < -0.1
            else "neutral"
        )
    else:
        avg_score = 0
        overall = "neutral"

    # Fetch NSE announcements
    announcements = fetch_nse_announcements(symbol)

    result = {
        "symbol": symbol,
        "overall_sentiment": {
            "sentiment": overall,
            "average_score": avg_score,
            "articles_analyzed": len(analyzed_articles)
        },
        "news_articles": {
            "count": len(analyzed_articles),
            "articles": analyzed_articles
        },
        "official_announcements": {
            "count": len(announcements),
            "announcements": announcements
        }
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def get_market_news(category: str = "markets") -> str:
    """
    Get general Indian market news with sentiment.

    Categories:
    - markets: Nifty, Sensex, FII flows
    - economy: GDP, inflation, trade
    - policy: RBI, SEBI decisions
    - global: US Fed, global impact on India
    - fii: FII/DII flows
    """
    queries = {
        "markets": "NSE Nifty Sensex Indian stock market today 2025",
        "economy": "India economy GDP inflation RBI 2025",
        "policy": "RBI monetary policy repo rate India 2025",
        "global": "global markets impact India FII 2025",
        "fii": "FII DII buying selling Indian market 2025",
    }

    query = queries.get(category, queries["markets"])
    articles = fetch_google_news(query, max_items=10)

    # Analyze overall market sentiment from top 5 articles
    # Why only 5? Groq has rate limits on free tier
    # 5 articles is enough to gauge market mood
    top_articles = articles[:5]
    analyzed = []
    for article in top_articles:
        sentiment = analyze_with_groq(
            text=article["content"],
            context="Indian stock market NSE Nifty"
        )
        article["sentiment_analysis"] = sentiment
        analyzed.append(article)

    # Remaining articles without sentiment
    remaining = articles[5:]

    if analyzed:
        scores = [a["sentiment_analysis"].get("score", 0) for a in analyzed]
        avg_score = round(sum(scores) / len(scores), 2)
        overall = (
            "positive" if avg_score > 0.1
            else "negative" if avg_score < -0.1
            else "neutral"
        )
    else:
        avg_score = 0
        overall = "neutral"

    result = {
        "category": category,
        "market_sentiment": {
            "overall": overall,
            "score": avg_score
        },
        "articles_found": len(articles),
        "analyzed_articles": analyzed,
        "remaining_articles": remaining
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def get_rbi_news() -> str:
    """
    Get RBI news with policy sentiment analysis.

    Why RBI news needs special handling:
    RBI language is deliberately vague —
    "calibrated tightening" = they might raise rates
    "accommodative stance" = rates staying low
    LLM understands these nuances, keywords don't.
    """
    query = "RBI Reserve Bank India repo rate monetary policy 2025"
    articles = fetch_google_news(query, max_items=10)

    rbi_keywords = [
        'rbi', 'reserve bank', 'repo rate', 'monetary policy',
        'inflation', 'cpi', 'interest rate', 'governor', 'mpc'
    ]

    filtered = []
    for article in articles:
        text = (article['title'] + article['summary']).lower()
        if any(kw in text for kw in rbi_keywords):
            # Deep sentiment for RBI news
            # Context helps LLM understand policy implications
            sentiment = analyze_with_groq(
                text=article["content"],
                context="RBI monetary policy Indian market impact"
            )
            article["sentiment_analysis"] = sentiment
            filtered.append(article)

    result = {
        "category": "RBI & Monetary Policy",
        "articles_found": len(filtered),
        "articles": filtered
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def analyze_sentiment(text: str) -> str:
    """
    Analyze sentiment of any financial text using Groq LLM.

    Upgrade from v1:
    v1 used keyword counting — missed context and negations
    v2 uses Groq LLM — understands financial language fully

    Fallback:
    If Groq is unavailable, falls back to keyword analysis
    so the system never completely fails.

    Args:
        text: Any financial text to analyze
    """
    result = analyze_with_groq(text)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()