import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dotenv import load_dotenv
from groq import Groq

from mcp_servers.market_server import get_stock_price, get_fundamentals
from mcp_servers.calculator_server import calculate_dcf, compare_valuation
from rag.retriever import search_financial_concepts

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_fundamental_agent(symbol: str) -> dict:
    print(f"[Fundamental Agent] Analyzing {symbol}...")

    # fetch raw data from mcp servers
    price_data = json.loads(get_stock_price(symbol))
    fundamental_data = json.loads(get_fundamentals(symbol))
    dcf_data = json.loads(calculate_dcf(symbol))
    peer_data = json.loads(compare_valuation(symbol))

    # format decimal values properly before passing to LLM
    # yfinance returns these as decimals e.g. 0.48 = 48%
    roe = fundamental_data.get('profitability', {}).get('roe', 0)
    roe_fmt = f"{round(float(roe) * 100, 2)}%" if roe else "N/A"

    profit_margin = fundamental_data.get('profitability', {}).get('profit_margin', 0)
    profit_margin_fmt = f"{round(float(profit_margin) * 100, 2)}%" if profit_margin else "N/A"

    operating_margin = fundamental_data.get('profitability', {}).get('operating_margin', 0)
    operating_margin_fmt = f"{round(float(operating_margin) * 100, 2)}%" if operating_margin else "N/A"

    revenue_growth = fundamental_data.get('growth', {}).get('revenue_growth', 0)
    revenue_growth_fmt = f"{round(float(revenue_growth) * 100, 2)}%" if revenue_growth else "N/A"

    earnings_growth = fundamental_data.get('growth', {}).get('earnings_growth', 0)
    earnings_growth_fmt = f"{round(float(earnings_growth) * 100, 2)}%" if earnings_growth else "N/A"

    # format free cash flow in billions for readability
    fcf = fundamental_data.get('financial_health', {}).get('free_cashflow', 0)
    fcf_fmt = f"₹{round(float(fcf) / 1e9, 2)}B" if fcf else "N/A"

    # get rag context for concept definitions
    rag_context = search_financial_concepts(
        "PE ratio ROE return on equity valuation margin of safety", top_k=2
    )
    rag_text = "\n".join([r['text'] for r in rag_context]) if rag_context else ""

    prompt = f"""You are a fundamental analyst specializing in Indian stocks.

Analyze {symbol} based on this data:

PRICE DATA:
Current Price: ₹{price_data.get('current_price')}
52-week High: ₹{price_data.get('52_week_high')}
52-week Low: ₹{price_data.get('52_week_low')}

VALUATION RATIOS:
P/E Ratio: {fundamental_data.get('valuation', {}).get('pe_ratio')}
P/B Ratio: {fundamental_data.get('valuation', {}).get('pb_ratio')}
EV/EBITDA: {fundamental_data.get('valuation', {}).get('ev_ebitda')}

PROFITABILITY:
ROE: {roe_fmt}
Profit Margin: {profit_margin_fmt}
Operating Margin: {operating_margin_fmt}

GROWTH:
Revenue Growth YoY: {revenue_growth_fmt}
Earnings Growth YoY: {earnings_growth_fmt}

FINANCIAL HEALTH:
Debt to Equity: {fundamental_data.get('financial_health', {}).get('debt_to_equity')}
Current Ratio: {fundamental_data.get('financial_health', {}).get('current_ratio')}
Free Cash Flow: {fcf_fmt}

DCF VALUATION:
Intrinsic Value per Share: ₹{dcf_data.get('dcf_valuation', {}).get('intrinsic_value_per_share')}
Current Price: ₹{dcf_data.get('dcf_valuation', {}).get('current_price')}
Margin of Safety: {dcf_data.get('dcf_valuation', {}).get('margin_of_safety_pct')}%
DCF Verdict: {dcf_data.get('dcf_valuation', {}).get('verdict')}

PEER COMPARISON:
PE Premium vs Peers: {peer_data.get('pe_premium_pct')}%
Valuation Verdict: {peer_data.get('valuation_verdict')}

REFERENCE CONCEPTS:
{rag_text}

Based on this data, provide fundamental analysis in this exact JSON format:
{{
    "verdict": "Bullish" or "Neutral" or "Bearish",
    "score": 1-10,
    "intrinsic_value": <number>,
    "current_price": <number>,
    "key_strengths": ["strength 1", "strength 2", "strength 3"],
    "key_concerns": ["concern 1", "concern 2"],
    "recommendation": "one sentence recommendation",
    "reasoning": "2-3 sentence detailed reasoning"
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

        # clean markdown code blocks if model adds them
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text)
        result["agent"] = "fundamental"
        result["symbol"] = symbol
        return result

    except Exception as e:
        return {
            "agent": "fundamental",
            "symbol": symbol,
            "error": str(e),
            "verdict": "Unknown",
            "score": 5
        }


if __name__ == "__main__":
    result = run_fundamental_agent("TCS")
    print(json.dumps(result, indent=2))