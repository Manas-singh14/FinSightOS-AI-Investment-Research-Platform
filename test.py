# import sys
# sys.path.append('.')
# import json

# from mcp_servers.news_server import fetch_google_news

# articles = fetch_google_news("TCS NSE stock India", max_items=3)

# for i, article in enumerate(articles):
#     print(f"\n{'='*50}")
#     print(f"Article {i+1}")
#     print(f"{'='*50}")
#     print(f"TITLE: {article['title']}")
#     print(f"SOURCE: {article['source']}")
#     print(f"PUBLISHED: {article['published']}")
#     print(f"LINK: {article['link']}")
#     print(f"SUMMARY: {article['summary']}")
#     print(f"CONTENT LENGTH: {len(article['content'])} characters")
#     print(f"FULL CONTENT: {article['content']}")

# import sys
# sys.path.append('.')
# import requests
# from bs4 import BeautifulSoup

# def get_real_url(google_url: str) -> str:
#     """
#     Google News links are redirects.
#     Follow redirect to get actual article URL.
#     """
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
#     }
#     try:
#         response = requests.get(
#             google_url,
#             headers=headers,
#             allow_redirects=True,
#             timeout=10
#         )
#         return response.url  # final URL after redirect
#     except:
#         return google_url

# def scrape_article(url: str) -> str:
#     """
#     Scrape article text from the actual URL.
#     """
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
#     }
#     try:
#         response = requests.get(url, headers=headers, timeout=10)
#         soup = BeautifulSoup(response.text, 'lxml')

#         # Remove unwanted elements
#         for tag in soup(['script', 'style', 'nav',
#                         'footer', 'header', 'aside']):
#             tag.decompose()

#         # Try common article content selectors
#         # Different sites use different class names
#         selectors = [
#             'article',
#             '[class*="article-body"]',
#             '[class*="article_body"]',
#             '[class*="story-body"]',
#             '[class*="content-body"]',
#             '[class*="article-content"]',
#             'div.article',
#             'div.story',
#             'main',
#         ]

#         text = ""
#         for selector in selectors:
#             element = soup.select_one(selector)
#             if element:
#                 text = element.get_text(separator=' ', strip=True)
#                 if len(text) > 200:  # meaningful content found
#                     break

#         # Fallback — get all paragraph text
#         if len(text) < 200:
#             paragraphs = soup.find_all('p')
#             text = ' '.join(p.get_text() for p in paragraphs)

#         # Clean and limit to 1500 chars
#         # Why 1500? Enough for sentiment, fits in LLM context
#         text = ' '.join(text.split())
#         return text[:1500] if text else ""

#     except Exception as e:
#         return ""

# # Test on first article
# from mcp_servers.news_server import fetch_google_news
# articles = fetch_google_news("TCS NSE stock India", max_items=3)

# for article in articles[:2]:
#     print(f"\nTitle: {article['title']}")
#     print(f"Google URL: {article['link'][:80]}...")

#     # Step 1 - get real URL
#     real_url = get_real_url(article['link'])
#     print(f"Real URL: {real_url}")

#     # Step 2 - scrape content
#     content = scrape_article(real_url)
#     print(f"Content length: {len(content)} chars")
#     print(f"Content preview: {content[:300]}")
#     print("-"*50)

import sys
sys.path.append('.')
import json

from mcp_servers.news_server import fetch_google_news

articles = fetch_google_news("Tata Consultancy Services TCS NSE stock", max_items=10)

print(f"Total articles: {len(articles)}")
print("\nChecking TCS relevance:")
print("="*50)

for i, article in enumerate(articles):
    title = article['title']
    
    # Check if TCS is actually mentioned
    tcs_mentioned = any(kw in title.lower() for kw in 
                       ['tcs', 'tata consultancy'])
    
    print(f"\n{i+1}. {title}")
    print(f"   TCS mentioned: {'✅ Yes' if tcs_mentioned else '❌ No — general article'}")