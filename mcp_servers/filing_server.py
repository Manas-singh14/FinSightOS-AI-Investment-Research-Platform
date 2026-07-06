import json
import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("filing_server")


@mcp.tool()
def get_shareholding_pattern(symbol: str) -> str:
    """
    Get insider/institutional shareholding from yfinance.

    What it returns:
    - Promoter/insider holding %
    - Institutional holding %
    - Number of institutions holding the stock

    Why agents need this:
    high promoter holding = founders confident, skin in game
    increasing institutional count = growing trust from
    professional investors.

    Args:
        symbol: NSE stock symbol
    """
    try:
        ticker = yf.Ticker(f"{symbol.upper()}.NS")
        holders = ticker.major_holders

        if holders is None or holders.empty:
            return json.dumps({
                "symbol": symbol,
                "error": "No shareholding data available"
            })

        insider_pct = None
        institution_pct = None
        institution_count = None

        if 'insidersPercentHeld' in holders.index:
            insider_pct = round(
                float(holders.loc['insidersPercentHeld', 'Value']) * 100, 2
            )
        if 'institutionsPercentHeld' in holders.index:
            institution_pct = round(
                float(holders.loc['institutionsPercentHeld', 'Value']) * 100, 2
            )
        if 'institutionsCount' in holders.index:
            institution_count = int(
                float(holders.loc['institutionsCount', 'Value'])
            )

        result = {
            "symbol": symbol,
            "source": "yfinance",
            "shareholding": {
                "promoter_insider_pct": insider_pct,
                "institutional_pct": institution_pct,
                "institutions_count": institution_count
            },
            "signals": {
                "promoter_confidence": (
                    "High — strong promoter holding"
                    if insider_pct and insider_pct > 50
                    else "Moderate"
                    if insider_pct and insider_pct > 25
                    else "Low"
                    if insider_pct is not None
                    else "Unknown"
                ),
                "institutional_trust": (
                    "High — wide institutional adoption"
                    if institution_count and institution_count > 200
                    else "Moderate"
                    if institution_count
                    else "Unknown"
                )
            }
        }

    except Exception as e:
        result = {"symbol": symbol, "error": str(e)}

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()