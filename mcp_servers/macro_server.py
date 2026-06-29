"""
Macro MCP Server
----------------
Fetches Indian macroeconomic indicators.

Data sources (all free, no API key):
1. yfinance       — USD/INR rate, Nifty performance
2. NSE India API  — FII/DII daily flows
3. World Bank API — GDP, inflation historical data
4. Hardcoded RBI  — Repo rate (RBI meets 6x/year,
                    we update manually after each meeting)

Why hardcoded repo rate?
RBI doesn't provide a simple REST API for current rate.
Their website requires scraping which breaks frequently.
Since RBI meets only 6 times a year, hardcoding is
practical — just update after each MPC meeting.
"""

import json
import requests
import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("macro_server")


@mcp.tool()
def get_usdinr_rate() -> str:
    """
    Get current USD/INR exchange rate and trend.

    What it returns:
    - Current rate (how many rupees per dollar)
    - 1 month, 3 month, 1 year change
    - Which sectors benefit/suffer

    Why agents need this:
    Rupee movement has opposite effects on different sectors:

    Weak rupee (more INR per USD):
    → IT companies BENEFIT — earn in USD, report in INR
    → Oil companies SUFFER — buy crude in USD, sell in INR
    → Pharma exporters BENEFIT — export revenue in USD

    Strong rupee (less INR per USD):
    → IT companies SUFFER — same USD earnings = less INR
    → Import companies BENEFIT — cheaper imports
    """
    try:
        ticker = yf.Ticker("USDINR=X")
        history = ticker.history(period="1y")

        if history.empty:
            return json.dumps({"error": "No data available"})

        current = round(history['Close'].iloc[-1], 2)
        month_ago = round(history['Close'].iloc[-22], 2)
        three_months_ago = round(history['Close'].iloc[-66], 2)
        year_ago = round(history['Close'].iloc[0], 2)

        # Positive change = rupee weakened
        # (more INR needed to buy 1 USD)
        year_change = round(current - year_ago, 2)

        result = {
            "pair": "USD/INR",
            "current_rate": current,
            "interpretation": f"1 USD = ₹{current}",
            "trend": {
                "1_month_change": round(current - month_ago, 2),
                "3_month_change": round(current - three_months_ago, 2),
                "1_year_change": year_change,
                "direction": (
                    "Rupee weakening"
                    if year_change > 0
                    else "Rupee strengthening"
                )
            },
            "sector_impact": {
                "IT_exports": (
                    "Positive" if year_change > 0 else "Negative"
                ),
                "oil_imports": (
                    "Negative" if year_change > 0 else "Positive"
                ),
                "pharma_exports": (
                    "Positive" if year_change > 0 else "Negative"
                ),
                "FMCG_imports": (
                    "Negative" if year_change > 0 else "Positive"
                ),
            }
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_repo_rate() -> str:
    """
    Get current RBI repo rate and recent history.

    What is repo rate?
    Rate at which RBI lends money to commercial banks.
    It's the most important number in Indian macro.

    How it affects stocks:
    Rate CUT → banks borrow cheaper from RBI
             → banks lend cheaper to companies
             → companies borrow cheaper → profits improve
             → market rallies

    Rate HIKE → opposite → market falls

    Sectors most sensitive to rate changes:
    - Banking (HDFCBANK, ICICIBANK) — margins affected
    - Real Estate (DLF, Godrej) — home loans cheaper/costlier
    - Auto (Maruti, Tata Motors) — vehicle loans affected
    - NBFCs (Bajaj Finance) — borrowing costs change

    Note: Update this list after each RBI MPC meeting.
    RBI meets every 2 months (6 times a year).
    """
    # Last 5 RBI decisions
    # Update manually after each MPC meeting
    repo_history = [
        {
            "date": "June 2025",
            "rate": 5.50,
            "action": "Cut",
            "change": -0.25,
            "reason": "Inflation within target, growth support needed"
        },
        {
            "date": "April 2025",
            "rate": 5.75,
            "action": "Cut",
            "change": -0.25,
            "reason": "Global slowdown concerns, domestic growth support"
        },
        {
            "date": "February 2025",
            "rate": 6.00,
            "action": "Cut",
            "change": -0.25,
            "reason": "First cut of easing cycle, inflation under control"
        },
        {
            "date": "December 2024",
            "rate": 6.25,
            "action": "Hold",
            "change": 0,
            "reason": "Monitoring inflation before cutting"
        },
        {
            "date": "October 2024",
            "rate": 6.50,
            "action": "Hold",
            "change": 0,
            "reason": "Inflation above comfort zone"
        },
    ]

    current_rate = repo_history[0]["rate"]
    recent_trend = repo_history[0]["action"]

    # Count consecutive cuts or holds
    consecutive = 0
    for decision in repo_history:
        if decision["action"] == recent_trend:
            consecutive += 1
        else:
            break

    result = {
        "current_repo_rate_pct": current_rate,
        "recent_action": recent_trend,
        "consecutive_decisions": consecutive,
        "easing_cycle": recent_trend == "Cut",
        "market_impact": (
            "Positive — RBI in easing cycle, "
            "borrowing costs falling"
            if recent_trend == "Cut"
            else "Neutral — rates on hold"
        ),
        "most_benefited_sectors": (
            ["Banking", "Real Estate", "Auto", "NBFCs"]
            if recent_trend == "Cut"
            else ["Defensives", "FMCG", "Pharma"]
        ),
        "rate_history": repo_history
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_india_gdp() -> str:
    """
    Get India GDP data from World Bank API.

    What it returns:
    - Annual GDP in USD billions
    - YoY growth rate
    - Last 5 years of data

    Why agents need this:
    GDP growth = overall economic health.
    High GDP growth → more corporate earnings → bullish
    Slowing GDP → earnings pressure → bearish

    World Bank API:
    - Completely free, no API key
    - Official international organization data
    - Updated annually
    - Reliable, never goes down
    """
    try:
        # World Bank API
        # NY.GDP.MKTP.CD = GDP in current USD
        url = (
            "https://api.worldbank.org/v2/country/IN"
            "/indicator/NY.GDP.MKTP.CD"
        )
        params = {"format": "json", "per_page": 5, "mrv": 5}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        # World Bank returns [metadata, data_array]
        gdp_data = data[1] if len(data) > 1 else []

        gdp_list = []
        for item in gdp_data:
            if item.get("value"):
                gdp_list.append({
                    "year": item["date"],
                    "gdp_usd_billion": round(item["value"] / 1e9, 2),
                })

        # Calculate latest growth rate
        if len(gdp_list) >= 2:
            latest = gdp_list[0]["gdp_usd_billion"]
            previous = gdp_list[1]["gdp_usd_billion"]
            growth = round((latest - previous) / previous * 100, 2)
        else:
            growth = None

        result = {
            "indicator": "India GDP",
            "source": "World Bank",
            "latest_gdp_usd_billion": gdp_list[0]["gdp_usd_billion"] if gdp_list else None,
            "gdp_growth_pct": growth,
            "market_signal": (
                "Positive — strong GDP growth"
                if growth and growth > 6
                else "Neutral — moderate growth"
                if growth and growth > 4
                else "Negative — slow growth"
            ),
            "historical_data": gdp_list
        }

    except Exception as e:
        result = {"error": str(e), "indicator": "India GDP"}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_india_inflation() -> str:
    """
    Get India CPI inflation from World Bank.

    What it returns:
    - Annual CPI inflation rate
    - Comparison with RBI target (4%)
    - Policy implication

    Why agents need this:
    RBI targets 4% inflation (tolerance 2-6%).

    CPI > 6% → RBI MUST raise rates → negative for market
    CPI 4-6% → RBI holds rates → neutral
    CPI < 4% → RBI can cut rates → positive for market

    This directly determines what RBI does next,
    which affects every stock in the market.
    """
    try:
        # FP.CPI.TOTL.ZG = CPI inflation annual %
        url = (
            "https://api.worldbank.org/v2/country/IN"
            "/indicator/FP.CPI.TOTL.ZG"
        )
        params = {"format": "json", "per_page": 5, "mrv": 5}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        inflation_data = data[1] if len(data) > 1 else []

        inflation_list = []
        for item in inflation_data:
            if item.get("value"):
                inflation_list.append({
                    "year": item["date"],
                    "cpi_pct": round(item["value"], 2)
                })

        latest = (
            inflation_list[0]["cpi_pct"]
            if inflation_list else None
        )

        result = {
            "indicator": "India CPI Inflation",
            "source": "World Bank",
            "latest_cpi_pct": latest,
            "rbi_target_pct": 4.0,
            "rbi_tolerance": "2% to 6%",
            "policy_implication": (
                "Rate hike pressure — inflation above tolerance"
                if latest and latest > 6
                else "Neutral — inflation within tolerance"
                if latest and 2 <= latest <= 6
                else "Rate cut possible — inflation below target"
                if latest
                else "Unknown"
            ),
            "historical_data": inflation_list
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_fii_dii_flows() -> str:
    """
    Get FII and DII daily buying/selling data from NSE.

    What is FII/DII?
    FII = Foreign Institutional Investors
          (foreign funds, hedge funds buying Indian stocks)
    DII = Domestic Institutional Investors
          (Indian mutual funds, insurance companies)

    Why this matters:
    FII control huge amounts of capital.
    FII buying heavily → market rallies
    FII selling heavily → market falls

    DII often buy when FII sells (providing support):
    FII sold ₹5000 crore + DII bought ₹4000 crore
    → net ₹1000 crore outflow → market falls but supported

    Risk Agent uses this to gauge institutional sentiment.
    """
    try:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Referer': 'https://www.nseindia.com'
        }

        session = requests.Session()
        # NSE requires homepage visit first for cookies
        session.get(
            "https://www.nseindia.com",
            headers=headers,
            timeout=10
        )
        response = session.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            flows = []
            for item in data[:10]:
                fii_net = float(item.get("fiiNet", 0))
                dii_net = float(item.get("diiNet", 0))
                flows.append({
                    "date": item.get("date", ""),
                    "fii_net_crore": round(fii_net, 2),
                    "dii_net_crore": round(dii_net, 2),
                    "fii_action": "Buying" if fii_net > 0 else "Selling",
                    "dii_action": "Buying" if dii_net > 0 else "Selling",
                    "net_flow": round(fii_net + dii_net, 2)
                })

            # 5-day summary
            recent = flows[:5]
            fii_5day = sum(f["fii_net_crore"] for f in recent)
            dii_5day = sum(f["dii_net_crore"] for f in recent)

            result = {
                "source": "NSE India",
                "5_day_summary": {
                    "fii_net_crore": round(fii_5day, 2),
                    "dii_net_crore": round(dii_5day, 2),
                    "net_flow_crore": round(fii_5day + dii_5day, 2),
                    "fii_trend": (
                        "Net Buyer" if fii_5day > 0 else "Net Seller"
                    ),
                    "dii_trend": (
                        "Net Buyer" if dii_5day > 0 else "Net Seller"
                    ),
                    "market_signal": (
                        "Strongly Positive — both buying"
                        if fii_5day > 0 and dii_5day > 0
                        else "Positive — FII buying"
                        if fii_5day > 0
                        else "Negative — FII selling"
                        if fii_5day < 0 and dii_5day < 0
                        else "Mixed — FII selling, DII supporting"
                    )
                },
                "daily_flows": flows
            }
        else:
            result = {
                "error": f"NSE returned {response.status_code}",
                "daily_flows": []
            }

    except Exception as e:
        result = {"error": str(e), "daily_flows": []}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_macro_summary() -> str:
    """
    Combined macro snapshot — all indicators in one call.

    Why this tool?
    Instead of agents making 4 separate tool calls,
    they call this one tool to get the complete
    macro picture. Faster, fewer API calls.

    Used by:
    - Macro Agent — primary tool
    - Risk Agent — for macro risk component
    - Writer Agent — for macro section of report
    """
    # Fetch USD/INR
    usdinr = json.loads(get_usdinr_rate())
    current_rate = usdinr.get("current_rate", "N/A")
    rupee_direction = usdinr.get(
        "trend", {}
    ).get("direction", "N/A")

    # Fetch repo rate
    repo = json.loads(get_repo_rate())
    repo_rate = repo.get("current_repo_rate_pct", "N/A")
    rate_trend = repo.get("recent_action", "N/A")
    easing = repo.get("easing_cycle", False)

    # Fetch Nifty performance
    try:
        nifty = yf.Ticker("^NSEI")
        history = nifty.history(period="1y")
        nifty_current = round(history['Close'].iloc[-1], 2)
        nifty_1yr = round(
            (history['Close'].iloc[-1] - history['Close'].iloc[0])
            / history['Close'].iloc[0] * 100, 2
        )
        nifty_trend = "Bullish" if nifty_1yr > 0 else "Bearish"
    except:
        nifty_current = "N/A"
        nifty_1yr = "N/A"
        nifty_trend = "N/A"

    # Fetch FII flows
    fii_data = json.loads(get_fii_dii_flows())
    fii_signal = fii_data.get(
        "5_day_summary", {}
    ).get("market_signal", "N/A")
    fii_trend = fii_data.get(
        "5_day_summary", {}
    ).get("fii_trend", "N/A")

    # Overall macro assessment
    positive_signals = sum([
        easing,  # RBI cutting rates
        isinstance(nifty_1yr, float) and nifty_1yr > 0,
        "Buying" in fii_trend,
        "strengthening" in rupee_direction.lower()
    ])

    overall = (
        "Strongly Positive" if positive_signals >= 3
        else "Cautiously Positive" if positive_signals == 2
        else "Neutral" if positive_signals == 1
        else "Negative"
    )

    result = {
        "macro_snapshot": {
            "overall_assessment": overall,
            "positive_signals": f"{positive_signals}/4",
            "indicators": {
                "nifty_50": {
                    "current": nifty_current,
                    "1_year_return_pct": nifty_1yr,
                    "trend": nifty_trend
                },
                "rbi_policy": {
                    "repo_rate_pct": repo_rate,
                    "trend": rate_trend,
                    "easing_cycle": easing
                },
                "currency": {
                    "usdinr": current_rate,
                    "direction": rupee_direction
                },
                "institutional_flows": {
                    "fii_trend": fii_trend,
                    "signal": fii_signal
                }
            }
        }
    }

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()