"""
Test portfolio server.
First adds sample holdings, then tests all tools.
"""
import sys
sys.path.append('.')
import json

from mcp_servers.portfolio_server import (
    add_holding,
    get_portfolio,
    get_allocation,
    get_portfolio_performance
)

print("Testing Portfolio MCP Server...")
print("="*50)

# Step 1 — Add sample holdings
print("\n1. Adding sample holdings:")
holdings_to_add = [
    ("TCS", 10, 3200, "2024-01-15"),
    ("HDFCBANK", 20, 1650, "2024-02-10"),
    ("RELIANCE", 15, 2400, "2024-03-05"),
    ("INFY", 25, 1800, "2024-04-20"),
    ("SBIN", 50, 780, "2024-05-15"),
]

for symbol, qty, price, date in holdings_to_add:
    result = json.loads(add_holding(symbol, qty, price, date))
    print(f"  {symbol}: {result['action']} — ₹{result['total_invested']} invested")

# Step 2 — View portfolio with P&L
print("\n2. Portfolio P&L:")
result = json.loads(get_portfolio())
summary = result.get('portfolio_summary', {})
print(f"Total invested: ₹{summary.get('total_invested_inr')}")
print(f"Current value: ₹{summary.get('current_value_inr')}")
print(f"Total P&L: ₹{summary.get('total_pnl_inr')} ({summary.get('total_pnl_pct')}%)")
print(f"Status: {summary.get('overall_status')}")

print("\nIndividual holdings:")
for h in result.get('holdings', []):
    print(f"  {h['symbol']}: ₹{h['avg_buy_price']} → ₹{h['current_price']} | P&L: {h['pnl_pct']}% {h['status']}")

# Step 3 — Allocation
print("\n3. Portfolio Allocation:")
result = json.loads(get_allocation())
print(f"Diversification: {result.get('diversification')}")
print(f"Stocks: {result.get('number_of_stocks')}, Sectors: {result.get('number_of_sectors')}")
print("\nTop holdings:")
for s in result.get('stock_allocation', [])[:3]:
    print(f"  {s['symbol']}: {s['allocation_pct']}% — {s['concentration_risk']}")
print("\nSector breakdown:")
for s in result.get('sector_allocation', []):
    print(f"  {s['sector']}: {s['allocation_pct']}%")

# Step 4 — Performance
print("\n4. Performance Summary:")
result = json.loads(get_portfolio_performance())
best = result.get('best_performer', {})
worst = result.get('worst_performer', {})
print(f"Best: {best.get('symbol')} at {best.get('pnl_pct')}%")
print(f"Worst: {worst.get('symbol')} at {worst.get('pnl_pct')}%")
review = result.get('stocks_needing_review', [])
if review:
    print(f"Needs review: {[r['symbol'] for r in review]}")

print("\n Portfolio server tests complete!")