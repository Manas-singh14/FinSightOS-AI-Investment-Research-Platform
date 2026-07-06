import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import date
from dotenv import load_dotenv
from groq import Groq

from mcp_servers.market_server import get_stock_price
from mcp_servers.portfolio_server import get_portfolio

load_dotenv()

# writer agent uses groq for long coherent report generation
# fine-tuned model will replace this later
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_writer_agent(
    symbol: str,
    fundamental: dict,
    technical: dict,
    sentiment: dict,
    macro: dict,
    risk: dict
) -> dict:
    print(f"[Writer Agent] Generating report for {symbol}...")

    # get current price for report header
    price_data = json.loads(get_stock_price(symbol))
    current_price = price_data.get("current_price", "N/A")

    # get portfolio context
    portfolio = json.loads(get_portfolio())
    portfolio_summary = portfolio.get("portfolio_summary", {})

    # calculate weighted overall score
    # fundamental gets highest weight since we're long term focused
    weights = {
        "fundamental": 0.30,
        "technical":   0.20,
        "sentiment":   0.20,
        "macro":       0.15,
        "risk":        0.15
    }

    scores = {
        "fundamental": fundamental.get("score", 5),
        "technical":   technical.get("score", 5),
        "sentiment":   sentiment.get("score", 5),
        "macro":       macro.get("score", 5),
        "risk":        10 - risk.get("risk_score", 5)  # invert risk score
    }

    weighted_score = sum(
        scores[k] * weights[k] for k in weights
    )
    weighted_score = round(weighted_score, 1)

    # determine final verdict from weighted score
    if weighted_score >= 7:
        final_verdict = "BUY"
        verdict_emoji = "✅"
    elif weighted_score >= 5:
        final_verdict = "ACCUMULATE ON DIPS"
        verdict_emoji = "⚠️"
    elif weighted_score >= 3.5:
        final_verdict = "HOLD / AVOID"
        verdict_emoji = "🔶"
    else:
        final_verdict = "SELL / AVOID"
        verdict_emoji = "❌"

    prompt = f"""You are a senior investment analyst at a top Indian brokerage.
Write a professional investment research report for {symbol}.

Today's Date: {date.today().strftime("%B %d, %Y")}
Current Price: ₹{current_price}
Overall Score: {weighted_score}/10
Final Verdict: {final_verdict}

AGENT VERDICTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FUNDAMENTAL ANALYSIS (Score: {fundamental.get('score')}/10)
Verdict: {fundamental.get('verdict')}
Strengths: {', '.join(fundamental.get('key_strengths', []))}
Concerns: {', '.join(fundamental.get('key_concerns', []))}
Intrinsic Value: ₹{fundamental.get('intrinsic_value')}
Reasoning: {fundamental.get('reasoning')}

TECHNICAL ANALYSIS (Score: {technical.get('score')}/10)
Verdict: {technical.get('verdict')}
Trend: {technical.get('trend')}
Entry Point: {technical.get('entry_point')}
Stop Loss: {technical.get('stop_loss')}
Key Signals: {', '.join(technical.get('key_signals', []))}
Reasoning: {technical.get('reasoning')}

SENTIMENT ANALYSIS (Score: {sentiment.get('score')}/10)
Verdict: {sentiment.get('verdict')}
News Sentiment: {sentiment.get('news_sentiment')}
Key Themes: {', '.join(sentiment.get('key_themes', []))}
Red Flags: {', '.join(sentiment.get('red_flags', []))}
Reasoning: {sentiment.get('reasoning')}

MACRO ANALYSIS (Score: {macro.get('score')}/10)
Verdict: {macro.get('verdict')}
Market Environment: {macro.get('market_environment')}
Currency Impact: {macro.get('currency_impact')}
FII Sentiment: {macro.get('fii_sentiment')}
Key Risks: {', '.join(macro.get('key_macro_risks', []))}
Reasoning: {macro.get('reasoning')}

RISK ANALYSIS (Risk Score: {risk.get('risk_score')}/10)
Verdict: {risk.get('verdict')}
Return Quality: {risk.get('return_quality')}
Max Loss Scenario: {risk.get('max_loss_scenario')}
Key Risks: {', '.join(risk.get('key_risks', []))}
Reasoning: {risk.get('reasoning')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PORTFOLIO CONTEXT:
Total Portfolio Value: ₹{portfolio_summary.get('current_value_inr')}
Portfolio P&L: {portfolio_summary.get('total_pnl_pct')}%

Write a professional investment report in this exact JSON format:
{{
    "executive_summary": "2-3 sentence overview of the investment case",
    "fundamental_section": "3-4 sentences on fundamentals",
    "technical_section": "3-4 sentences on technicals and entry strategy",
    "sentiment_section": "2-3 sentences on news and market sentiment",
    "macro_section": "2-3 sentences on macro environment",
    "risk_section": "2-3 sentences on key risks",
    "investment_strategy": {{
        "verdict": "{final_verdict}",
        "target_price": <number based on intrinsic value>,
        "entry_price": <suggested entry price>,
        "stop_loss": <stop loss price>,
        "time_horizon": "Short term (1-3 months)" or "Medium term (6-12 months)" or "Long term (1-3 years)",
        "position_size": "Small (2-5%)" or "Moderate (5-10%)" or "Large (10-15%)"
    }},
    "key_catalysts": ["catalyst 1", "catalyst 2", "catalyst 3"],
    "key_risks_to_watch": ["risk 1", "risk 2", "risk 3"],
    "disclaimer": "standard investment disclaimer"
}}

Respond with JSON only. No other text."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500
        )

        response_text = response.choices[0].message.content.strip()

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text)

        # add metadata
        result["symbol"] = symbol
        result["date"] = date.today().isoformat()
        result["current_price"] = current_price
        result["overall_score"] = weighted_score
        result["final_verdict"] = final_verdict
        result["verdict_emoji"] = verdict_emoji
        result["agent_scores"] = scores

        return result

    except Exception as e:
        return {
            "symbol": symbol,
            "error": str(e),
            "final_verdict": final_verdict,
            "overall_score": weighted_score
        }


if __name__ == "__main__":
    # import all agents and run full pipeline
    from agents.fundamental_agent import run_fundamental_agent
    from agents.technical_agent import run_technical_agent
    from agents.sentiment_agent import run_sentiment_agent
    from agents.macro_agent import run_macro_agent
    from agents.risk_agent import run_risk_agent

    symbol = "TCS"

    print(f"\nRunning full analysis pipeline for {symbol}...")
    print("="*50)

    fundamental = run_fundamental_agent(symbol)
    technical = run_technical_agent(symbol)
    sentiment = run_sentiment_agent(symbol)
    macro = run_macro_agent(symbol, sector="IT")
    risk = run_risk_agent(symbol)

    report = run_writer_agent(
        symbol, fundamental, technical, sentiment, macro, risk
    )

    print("\n" + "="*60)
    print(f"FINSIGHTOS RESEARCH REPORT — {symbol}")
    print("="*60)
    print(f"Date: {report.get('date')}")
    print(f"Price: ₹{report.get('current_price')}")
    print(f"Overall Score: {report.get('overall_score')}/10")
    print(f"Verdict: {report.get('verdict_emoji')} {report.get('final_verdict')}")
    print("\nEXECUTIVE SUMMARY:")
    print(report.get('executive_summary'))
    print("\nFUNDAMENTAL ANALYSIS:")
    print(report.get('fundamental_section'))
    print("\nTECHNICAL ANALYSIS:")
    print(report.get('technical_section'))
    print("\nSENTIMENT:")
    print(report.get('sentiment_section'))
    print("\nMACRO ENVIRONMENT:")
    print(report.get('macro_section'))
    print("\nRISK ASSESSMENT:")
    print(report.get('risk_section'))
    print("\nINVESTMENT STRATEGY:")
    strategy = report.get('investment_strategy', {})
    print(f"  Verdict: {strategy.get('verdict')}")
    print(f"  Target Price: ₹{strategy.get('target_price')}")
    print(f"  Entry Price: ₹{strategy.get('entry_price')}")
    print(f"  Stop Loss: ₹{strategy.get('stop_loss')}")
    print(f"  Time Horizon: {strategy.get('time_horizon')}")
    print(f"  Position Size: {strategy.get('position_size')}")
    print("\nKEY CATALYSTS:")
    for c in report.get('key_catalysts', []):
        print(f"  • {c}")
    print("\nRISKS TO WATCH:")
    for r in report.get('key_risks_to_watch', []):
        print(f"  • {r}")
    print("\n" + "="*60)
    print("⚠️  Disclaimer:", report.get('disclaimer'))
    print("="*60)