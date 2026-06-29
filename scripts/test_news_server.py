"""
Test improved news server.
Now checks sentiment quality not just article count.
"""
import sys
sys.path.append('.')
import json

from mcp_servers.news_server import (
    get_market_news,
    get_rbi_news,
    analyze_sentiment,
    get_stock_news
)

print("Testing Improved News MCP Server...")
print("="*50)

# Test 1 — Market news with sentiment
print("\n1. Testing get_market_news:")
result = json.loads(get_market_news("markets"))
print(f"Articles found: {result['articles_found']}")
print(f"Market sentiment: {result['market_sentiment']['overall']}")
print(f"Sentiment score: {result['market_sentiment']['score']}")
if result['analyzed_articles']:
    first = result['analyzed_articles'][0]
    print(f"Latest headline: {first['title']}")
    print(f"Article sentiment: {first['sentiment_analysis']['sentiment']}")
    print(f"Key points: {first['sentiment_analysis'].get('key_points', [])}")

# Test 2 — RBI news with policy sentiment
print("\n2. Testing get_rbi_news:")
result = json.loads(get_rbi_news())
print(f"RBI articles: {result['articles_found']}")
if result['articles']:
    first = result['articles'][0]
    print(f"Latest: {first['title']}")
    print(f"Sentiment: {first['sentiment_analysis']['sentiment']}")
    print(f"Impact: {first['sentiment_analysis'].get('market_impact')}")

# Test 3 — Stock news with per-article sentiment
print("\n3. Testing get_stock_news (TCS):")
result = json.loads(get_stock_news("TCS", max_articles=5))
print(f"Overall TCS sentiment: {result['overall_sentiment']['sentiment']}")
print(f"Average score: {result['overall_sentiment']['average_score']}")
print(f"Articles analyzed: {result['overall_sentiment']['articles_analyzed']}")
if result['news_articles']['articles']:
    for article in result['news_articles']['articles'][:3]:
        print(f"\n  Title: {article['title']}")
        print(f"  Sentiment: {article['sentiment_analysis']['sentiment']}")
        print(f"  Score: {article['sentiment_analysis']['score']}")
        print(f"  Reasoning: {article['sentiment_analysis']['reasoning']}")

# Test 4 — Direct sentiment analysis
print("\n4. Testing analyze_sentiment (LLM):")
result = json.loads(analyze_sentiment(
    "TCS misses Q4 revenue estimates, management gives cautious guidance "
    "citing weak demand from BFSI sector in North America"
))
print(f"Sentiment: {result['sentiment']}")
print(f"Score: {result['score']}")
print(f"Reasoning: {result['reasoning']}")
print(f"Market impact: {result['market_impact']}")

print("\n✅ Improved news server tests complete!")