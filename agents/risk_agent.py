import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dotenv import load_dotenv
from groq import Groq

from mcp_servers.calculator_server import calculate_risk_metrics, calculate_technical_indicators
from mcp_servers.portfolio_server import get_allocation
from rag.retriever import search_financial_concepts

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_risk_agent(symbol: str) -> dict:
    print(f"[Risk Agent] Analyzing {symbol}...")

    # fetch risk metrics
    risk_data = json.loads(calculate_risk_metrics(symbol))
    tech_data = json.loads(calculate_technical_indicators(symbol))
    portfolio = json.loads(get_allocation())

    if "error" in risk_data:
        return {
            "agent": "risk",
            "symbol": symbol,
            "error": risk_data["error"],
            "verdict": "Unknown",
            "score": 5
        }

    risk = risk_data.get("risk_metrics", {})

    # check portfolio concentration for this stock
    stock_allocation = portfolio.get("stock_allocation", [])
    symbol_allocation = next(
        (s for s in stock_allocation if s["symbol"] == symbol.upper()),
        None
    )
    concentration = (
        symbol_allocation.get("allocation_pct", 0)
        if symbol_allocation else 0
    )
    concentration_risk = (
        symbol_allocation.get("concentration_risk", "Unknown")
        if symbol_allocation else "Not in portfolio"
    )

    # rag context
    rag_context = search_financial_concepts(
        "beta sharpe ratio VaR maximum drawdown risk", top_k=2
    )
    rag_text = "\n".join([r['text'] for r in rag_context]) if rag_context else ""

    prompt = f"""You are a risk analyst specializing in Indian stocks.

Assess the risk profile of {symbol}:

RISK METRICS:
Beta: {risk.get('beta', {}).get('value')} — {risk.get('beta', {}).get('interpretation')}
Sharpe Ratio: {risk.get('sharpe_ratio', {}).get('value')} — {risk.get('sharpe_ratio', {}).get('interpretation')}
VaR 95%: {risk.get('var_95_pct', {}).get('value')}% daily
Max Drawdown: {risk.get('max_drawdown_pct', {}).get('value')}%
Annualized Volatility: {risk.get('annualized_volatility_pct')}%
1-Year Return: {risk.get('1yr_return_pct')}%
Overall Risk Level: {risk_data.get('risk_level')}

TECHNICAL RISK:
Overall Technical: {tech_data.get('overall_technical')}
Price vs 200MA: {"Below — downtrend risk" if not tech_data.get('technical_summary', {}).get('moving_averages', {}).get('above_ma200') else "Above — uptrend"}

PORTFOLIO CONCENTRATION:
Current Allocation: {concentration}%
Concentration Risk: {concentration_risk}
Portfolio Diversification: {portfolio.get('diversification')}

REFERENCE CONCEPTS:
{rag_text}

Based on this risk data, provide analysis in this exact JSON format:
{{
    "verdict": "Low Risk" or "Moderate Risk" or "High Risk",
    "risk_score": 1-10 (10 = extremely high risk),
    "beta_assessment": "one sentence on volatility",
    "return_quality": "Good" or "Poor" (based on Sharpe ratio),
    "max_loss_scenario": "worst case scenario description",
    "portfolio_fit": "suitable or not suitable given concentration",
    "key_risks": ["risk 1", "risk 2", "risk 3"],
    "recommendation": "one sentence risk recommendation",
    "reasoning": "2-3 sentence risk reasoning"
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
        result["agent"] = "risk"
        result["symbol"] = symbol
        return result

    except Exception as e:
        return {
            "agent": "risk",
            "symbol": symbol,
            "error": str(e),
            "verdict": "Unknown",
            "score": 5
        }


if __name__ == "__main__":
    result = run_risk_agent("TCS")
    print(json.dumps(result, indent=2))