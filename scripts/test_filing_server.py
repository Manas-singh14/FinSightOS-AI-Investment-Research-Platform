import sys
sys.path.append('.')
import json

from mcp_servers.filing_server import (
    get_shareholding_pattern
)

print("Testing Filing MCP Server...")
print("="*50)

# print("\n1. Corporate Announcements (RELIANCE):")
# result = json.loads(get_corporate_announcements("RELIANCE"))
# print(f"Source: {result.get('source')}")
# print(f"Count: {result.get('count')}")
# for ann in result.get('announcements', [])[:3]:
#     print(f"  [{ann.get('date', '')[:10]}] {ann.get('headline', '')[:70]}")

print("\n2. Shareholding Pattern (TCS):")
result = json.loads(get_shareholding_pattern("TCS"))
sh = result.get('shareholding', {})
signals = result.get('signals', {})
print(f"Promoter holding: {sh.get('promoter_insider_pct')}%")
print(f"Institutional holding: {sh.get('institutional_pct')}%")
print(f"Institutions count: {sh.get('institutions_count')}")
print(f"Promoter confidence: {signals.get('promoter_confidence')}")
print(f"Institutional trust: {signals.get('institutional_trust')}")

print("\nFiling server tests complete!")