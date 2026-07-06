import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dotenv import load_dotenv
from groq import Groq

from mcp_servers.macro_server import get_macro_summary, get_repo_rate, get_usdinr_rate
from mcp_servers.market_server import get_sector_performance
from rag.retriever import search_financial_concepts

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_macro_agent(symbol: str, sector: str = "IT") -> dict:
    print(f"[Macro Agent] Analyzing macro environment for {symbol}...")

    # fetch macro data
    macro = json.loads(get_macro_summary())
    repo = json.loads(get_repo_rate())
    usdinr = json.loads(get_usdinr_rate())
    sectors = json.loads(get_sector_performance())

    # extract key indicators
    snapshot = macro.get("macro_snapshot", {})
    indicators = snapshot.get("indicators", {})
    nifty = indicators.get("nifty_50", {})
    rbi = indicators.get("rbi_policy", {})
    currency = indicators.get("currency", {})
    fii = indicators.get("institutional_flows", {})

    # get sector performance for the stock's sector
    sector_perf = sectors.get(sector, {})

    # rag context for macro concepts
    rag_context = search_financial_concepts(
        "RBI repo rate FII DII sector rotation macro economy", top_k=2
    )
    rag_text = "\n".join([r['text'] for r in rag_context]) if rag_context else ""

    prompt = f"""You are a macro analyst specializing in Indian markets.

Analyze the macro environment impact on {symbol} (sector: {sector}):

MARKET:
Nifty 50 Current: {nifty.get('current')}
Nifty 1-year Return: {nifty.get('1_year_return_pct')}%
Market Trend: {nifty.get('trend')}

RBI POLICY:
Current Repo Rate: {rbi.get('repo_rate_pct')}%
Rate Trend: {rbi.get('trend')}
Easing Cycle: {rbi.get('easing_cycle')}

CURRENCY:
USD/INR Rate: ₹{currency.get('usdinr')}
Rupee Direction: {currency.get('direction')}

INSTITUTIONAL FLOWS:
FII Trend: {fii.get('fii_trend')}
Flow Signal: {fii.get('signal')}

SECTOR PERFORMANCE ({sector}):
1-month Return: {sector_perf.get('1_month_return_pct')}%

RATE HISTORY:
Current Rate: {repo.get('current_repo_rate_pct')}%
Recent Action: {repo.get('recent_action')}
Consecutive Decisions: {repo.get('consecutive_decisions')}
Most Benefited Sectors: {repo.get('most_benefited_sectors')}

CURRENCY IMPACT ON {sector}:
IT sector impact from rupee: {usdinr.get('sector_impact', {}).get('IT_exports')}

OVERALL MACRO ASSESSMENT: {snapshot.get('overall_assessment')}

REFERENCE CONCEPTS:
{rag_text}

Based on macro data, provide analysis in this exact JSON format:
{{
    "verdict": "Tailwind" or "Neutral" or "Headwind",
    "score": 1-10,
    "market_environment": "Bullish" or "Neutral" or "Bearish",
    "rate_environment": "Positive" or "Neutral" or "Negative",
    "currency_impact": "Positive" or "Neutral" or "Negative",
    "fii_sentiment": "Buying" or "Selling" or "Neutral",
    "sector_outlook": "one sentence on sector",
    "key_macro_risks": ["risk 1", "risk 2"],
    "recommendation": "one sentence macro recommendation",
    "reasoning": "2-3 sentence macro reasoning"
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
        result["agent"] = "macro"
        result["symbol"] = symbol
        return result

    except Exception as e:
        return {
            "agent": "macro",
            "symbol": symbol,
            "error": str(e),
            "verdict": "Unknown",
            "score": 5
        }


if __name__ == "__main__":
    result = run_macro_agent("TCS", sector="IT")
    print(json.dumps(result, indent=2))