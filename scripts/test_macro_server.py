"""
Test macro server — verify all tools work.
"""
import sys
sys.path.append('.')
import json

from mcp_servers.macro_server import (
    get_usdinr_rate,
    get_repo_rate,
    get_india_gdp,
    get_india_inflation,
    get_fii_dii_flows,
    get_macro_summary
)

print("Testing Macro MCP Server...")
print("="*50)

print("\n1. USD/INR Rate:")
result = json.loads(get_usdinr_rate())
print(f"Current: {result.get('interpretation')}")
print(f"Direction: {result.get('trend', {}).get('direction')}")
print(f"IT sector impact: {result.get('sector_impact', {}).get('IT_exports')}")

print("\n2. RBI Repo Rate:")
result = json.loads(get_repo_rate())
print(f"Current: {result.get('current_repo_rate_pct')}%")
print(f"Trend: {result.get('recent_action')}")
print(f"Easing cycle: {result.get('easing_cycle')}")
print(f"Impact: {result.get('market_impact')}")

print("\n3. India GDP:")
result = json.loads(get_india_gdp())
print(f"Latest GDP: ${result.get('latest_gdp_usd_billion')}B")
print(f"Growth: {result.get('gdp_growth_pct')}%")
print(f"Signal: {result.get('market_signal')}")

print("\n4. India Inflation:")
result = json.loads(get_india_inflation())
print(f"Latest CPI: {result.get('latest_cpi_pct')}%")
print(f"RBI target: {result.get('rbi_target_pct')}%")
print(f"Implication: {result.get('policy_implication')}")

print("\n5. FII/DII Flows:")
result = json.loads(get_fii_dii_flows())
summary = result.get('5_day_summary', {})
print(f"FII 5-day: ₹{summary.get('fii_net_crore')} crore")
print(f"DII 5-day: ₹{summary.get('dii_net_crore')} crore")
print(f"Signal: {summary.get('market_signal')}")

print("\n6. Full Macro Summary:")
result = json.loads(get_macro_summary())
snapshot = result.get('macro_snapshot', {})
print(f"Overall: {snapshot.get('overall_assessment')}")
print(f"Positive signals: {snapshot.get('positive_signals')}")
indicators = snapshot.get('indicators', {})
print(f"Nifty trend: {indicators.get('nifty_50', {}).get('trend')}")
print(f"RBI easing: {indicators.get('rbi_policy', {}).get('easing_cycle')}")
print(f"FII: {indicators.get('institutional_flows', {}).get('fii_trend')}")

print("\n✅ Macro server tests complete!")