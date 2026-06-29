"""
Test script to verify market server tools work correctly
before integrating with agents.

Why test individually?
- Easier to debug data issues early
- Confirms API is returning expected format
- Catches any Indian market data quirks
"""
import sys
sys.path.append('.')

from mcp_servers.market_server import (
    get_stock_price,
    get_fundamentals,
    get_nifty50_performance,
    get_sector_performance
)

print("Testing Market MCP Server...")
print("="*50)

# Test 1 — Stock price
print("\n1. Testing get_stock_price (RELIANCE):")
result = get_stock_price("RELIANCE")
print(result)

# Test 2 — Fundamentals
print("\n2. Testing get_fundamentals (TCS):")
result = get_fundamentals("TCS")
print(result)

# Test 3 — Nifty 50
print("\n3. Testing get_nifty50_performance:")
result = get_nifty50_performance()
print(result)

# Test 4 — Sector performance
print("\n4. Testing get_sector_performance:")
result = get_sector_performance()
print(result)

print("\n✅ Market server tests complete!")