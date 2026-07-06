import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dotenv import load_dotenv
from groq import Groq

from mcp_servers.news_server import get_stock_news, get_market_news
from mcp_servers.filing_server import get_shareholding_pattern

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_sentiment_agent(symbol: str) -> dict:
    print(f"[Sentiment Agent] Analyzing {symbol}...")

    # fetch news with pre-computed sentiment from news server
    news_data = json.loads(get_stock_news(symbol, max_articles=8))
    market_data = json.loads(get_market_news("markets"))
    shareholding = json.loads(get_shareholding_pattern(symbol))

    # extract pre-computed overall sentiment
    overall = news_data.get("overall_sentiment", {})
    articles = news_data.get("news_articles", {}).get("articles", [])

    # build article summaries for prompt
    article_summaries = []
    for a in articles[:5]:
        sentiment = a.get("sentiment_analysis", {})
        article_summaries.append(
            f"- {a['title']} "
            f"[{sentiment.get('sentiment', 'neutral')}, "
            f"score: {sentiment.get('score', 0)}]"
        )
    articles_text = "\n".join(article_summaries)

    # shareholding signals
    sh = shareholding.get("shareholding", {})
    sh_signals = shareholding.get("signals", {})

    prompt = f"""You are a sentiment analyst specializing in Indian stocks.

Analyze market sentiment for {symbol}:

NEWS SENTIMENT:
Overall Sentiment: {overall.get('sentiment')}
Average Score: {overall.get('average_score')} (-1 very negative to +1 very positive)
Articles Analyzed: {overall.get('articles_analyzed')}

RECENT HEADLINES:
{articles_text}

MARKET SENTIMENT:
Overall Market: {market_data.get('market_sentiment', {}).get('overall')}
Market Score: {market_data.get('market_sentiment', {}).get('score')}

SHAREHOLDING PATTERN:
Promoter/Insider Holding: {sh.get('promoter_insider_pct')}%
Institutional Holding: {sh.get('institutional_pct')}%
Number of Institutions: {sh.get('institutions_count')}
Promoter Confidence: {sh_signals.get('promoter_confidence')}
Institutional Trust: {sh_signals.get('institutional_trust')}

Based on this sentiment data, provide analysis in this exact JSON format:
{{
    "verdict": "Positive" or "Neutral" or "Negative",
    "score": 1-10,
    "news_sentiment": "Positive" or "Neutral" or "Negative",
    "institutional_confidence": "High" or "Moderate" or "Low",
    "key_themes": ["theme 1", "theme 2", "theme 3"],
    "red_flags": ["flag 1"] or [],
    "recommendation": "one sentence sentiment recommendation",
    "reasoning": "2-3 sentence reasoning"
}}

Respond with JSON only. No other text."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )

        response_text = response.choices[0].message.content.strip()

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text)
        result["agent"] = "sentiment"
        result["symbol"] = symbol
        return result

    except Exception as e:
        return {
            "agent": "sentiment",
            "symbol": symbol,
            "error": str(e),
            "verdict": "Unknown",
            "score": 5
        }


if __name__ == "__main__":
    result = run_sentiment_agent("TCS")
    print(json.dumps(result, indent=2))