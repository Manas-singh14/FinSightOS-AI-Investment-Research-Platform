"""
Test calculator server.
"""
import sys
sys.path.append('.')
import json

from mcp_servers.calculator_server import (
    calculate_technical_indicators,
    calculate_dcf,
    calculate_risk_metrics,
    calculate_sip_returns,
    compare_valuation
)

print("Testing Calculator MCP Server...")
print("="*50)

print("\n1. Technical Indicators (TCS):")
result = json.loads(calculate_technical_indicators("TCS"))
tech = result.get('technical_summary', {})
print(f"RSI: {tech.get('rsi', {}).get('value')} — {tech.get('rsi', {}).get('signal')}")
print(f"MA Signal: {tech.get('moving_averages', {}).get('signal')}")
print(f"Cross Signal: {tech.get('moving_averages', {}).get('cross_signal')}")
print(f"MACD Signal: {tech.get('macd', {}).get('signal')}")
print(f"Overall: {result.get('overall_technical')}")

print("\n2. DCF Valuation (TCS):")
result = json.loads(calculate_dcf("TCS"))
dcf = result.get('dcf_valuation', {})
print(f"Current price: ₹{dcf.get('current_price')}")
print(f"Intrinsic value: ₹{dcf.get('intrinsic_value_per_share')}")
print(f"Margin of safety: {dcf.get('margin_of_safety_pct')}%")
print(f"Verdict: {dcf.get('verdict')}")

print("\n3. Risk Metrics (TCS):")
result = json.loads(calculate_risk_metrics("TCS"))
risk = result.get('risk_metrics', {})
print(f"Beta: {risk.get('beta', {}).get('value')} — {risk.get('beta', {}).get('interpretation')}")
print(f"Sharpe: {risk.get('sharpe_ratio', {}).get('value')} — {risk.get('sharpe_ratio', {}).get('interpretation')}")
print(f"VaR 95%: {risk.get('var_95_pct', {}).get('value')}%")
print(f"Max Drawdown: {risk.get('max_drawdown_pct', {}).get('value')}%")
print(f"Risk Level: {result.get('risk_level')}")

print("\n4. SIP Calculator:")
result = json.loads(calculate_sip_returns(
    monthly_amount=10000,
    annual_return=12,
    years=10
))
sip = result.get('sip_calculation', {})
print(f"Monthly: ₹{sip.get('monthly_amount_inr')}")
print(f"Total invested: ₹{sip.get('total_invested_inr')}")
print(f"Final value: ₹{sip.get('final_value_inr')}")
print(f"Wealth created: ₹{sip.get('wealth_created_inr')}")
print(f"Total return: {sip.get('total_return_pct')}%")

print("\n5. Peer Valuation Comparison (TCS):")
result = json.loads(compare_valuation("TCS"))
print(f"TCS P/E: {result.get('target_stock', {}).get('pe_ratio')}")
print(f"Sector avg P/E: {result.get('sector_averages', {}).get('avg_pe')}")
print(f"PE Premium: {result.get('pe_premium_pct')}%")
print(f"Verdict: {result.get('valuation_verdict')}")

print("\n✅ Calculator server tests complete!")