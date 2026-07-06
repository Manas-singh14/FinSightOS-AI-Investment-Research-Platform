
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dotenv import load_dotenv
from groq import Groq

from mcp_servers.calculator_server import calculate_technical_indicators
from rag.retriever import search_financial_concepts

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_technical_agent(symbol: str) -> dict:
    print(f"[Technical Agent] Analyzing {symbol}...")

    # fetch technical indicators from calculator server
    tech_data = json.loads(calculate_technical_indicators(symbol))

    if "error" in tech_data:
        return {
            "agent": "technical",
            "symbol": symbol,
            "error": tech_data["error"],
            "verdict": "Unknown",
            "score": 5
        }

    tech = tech_data.get("technical_summary", {})
    rsi = tech.get("rsi", {})
    ma = tech.get("moving_averages", {})
    macd = tech.get("macd", {})
    volume = tech.get("volume", {})

    # get rag context for technical concept definitions
    rag_context = search_financial_concepts(
        "RSI MACD moving average technical analysis", top_k=2
    )
    rag_text = "\n".join([r['text'] for r in rag_context]) if rag_context else ""

    prompt = f"""You are a technical analyst specializing in Indian stocks.

Analyze {symbol} based on these technical indicators:

PRICE:
Current Price: ₹{tech_data.get('current_price')}
Overall Technical Signal: {tech_data.get('overall_technical')}

RSI (14-day):
Value: {rsi.get('value')}
Signal: {rsi.get('signal')}

MOVING AVERAGES:
50-day MA: ₹{ma.get('ma50')}
200-day MA: ₹{ma.get('ma200')}
Price above 50MA: {ma.get('above_ma50')}
Price above 200MA: {ma.get('above_ma200')}
MA Signal: {ma.get('signal')}
Cross Signal: {ma.get('cross_signal')}

MACD:
MACD Line: {macd.get('macd_line')}
Signal Line: {macd.get('signal_line')}
Histogram: {macd.get('histogram')}
Signal: {macd.get('signal')}

VOLUME:
Current Volume: {volume.get('current')}
20-day Average: {volume.get('20day_avg')}
Volume Ratio: {volume.get('ratio')}x
Signal: {volume.get('signal')}

REFERENCE CONCEPTS:
{rag_text}

Based on this technical data, provide analysis in this exact JSON format:
{{
    "verdict": "Bullish" or "Neutral" or "Bearish",
    "score": 1-10,
    "trend": "Uptrend" or "Downtrend" or "Sideways",
    "entry_point": "suggested entry price or condition",
    "stop_loss": "suggested stop loss level",
    "key_signals": ["signal 1", "signal 2", "signal 3"],
    "recommendation": "one sentence technical recommendation",
    "reasoning": "2-3 sentence technical reasoning"
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
        result["agent"] = "technical"
        result["symbol"] = symbol
        return result

    except Exception as e:
        return {
            "agent": "technical",
            "symbol": symbol,
            "error": str(e),
            "verdict": "Unknown",
            "score": 5
        }


if __name__ == "__main__":
    result = run_technical_agent("TCS")
    print(json.dumps(result, indent=2))