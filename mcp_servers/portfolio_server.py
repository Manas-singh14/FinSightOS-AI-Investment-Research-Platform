"""
Portfolio MCP Server
--------------------
Manages user's stock portfolio stored in PostgreSQL.

Why local database instead of fetching from broker?
- Broker APIs (Zerodha, Groww) require OAuth — complex
- PostgreSQL gives us full control
- User enters holdings manually once
- System tracks everything from there

Tools:
1. add_holding — add a stock to portfolio
2. get_portfolio — view all holdings with current P&L
3. get_allocation — portfolio breakdown by sector/stock
4. get_portfolio_performance — overall returns
5. check_concentration — is portfolio too concentrated?
"""

import json
import os
import psycopg2
import yfinance as yf
from datetime import date
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("portfolio_server")


def get_db_connection():
    """
    Create database connection.
    Why a function? So every tool creates fresh connection
    instead of sharing one that might time out.
    """
    return psycopg2.connect(os.getenv("POSTGRES_URL"))


def get_current_price(symbol: str) -> float:
    """Get current NSE price for a stock."""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        return float(info.get("currentPrice", 0))
    except:
        return 0.0


@mcp.tool()
def add_holding(
    symbol: str,
    quantity: float,
    avg_buy_price: float,
    buy_date: str = None,
    notes: str = ""
) -> str:
    """
    Add a stock holding to the portfolio.

    What it does:
    Saves the stock you own into PostgreSQL so
    the system knows your current portfolio.

    Args:
        symbol: NSE stock symbol e.g. TCS, RELIANCE
        quantity: Number of shares you own
        avg_buy_price: Average price you paid per share
        buy_date: When you bought (YYYY-MM-DD format)
        notes: Any personal notes about this holding
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if holding already exists
        # If yes — update it, if no — insert new
        cursor.execute(
            "SELECT id FROM holdings WHERE symbol = %s",
            (symbol.upper(),)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE holdings
                SET quantity = %s,
                    avg_buy_price = %s,
                    buy_date = %s,
                    notes = %s
                WHERE symbol = %s
            """, (
                quantity, avg_buy_price,
                buy_date, notes, symbol.upper()
            ))
            action = "updated"
        else:
            cursor.execute("""
                INSERT INTO holdings
                (symbol, quantity, avg_buy_price, buy_date, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                symbol.upper(), quantity,
                avg_buy_price, buy_date, notes
            ))
            action = "added"

        # Also log as transaction
        cursor.execute("""
            INSERT INTO transactions
            (symbol, action, quantity, price, date)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            symbol.upper(), "BUY",
            quantity, avg_buy_price,
            buy_date or date.today().isoformat()
        ))

        conn.commit()
        cursor.close()
        conn.close()

        result = {
            "status": "success",
            "action": action,
            "symbol": symbol.upper(),
            "quantity": quantity,
            "avg_buy_price": avg_buy_price,
            "total_invested": round(quantity * avg_buy_price, 2)
        }

    except Exception as e:
        result = {"status": "error", "message": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_portfolio() -> str:
    """
    Get complete portfolio with current P&L.

    What it returns:
    For each stock:
    - Shares owned and average buy price
    - Current market price (live from NSE)
    - Current value vs invested value
    - Profit/Loss in rupees and percentage

    Why agents need this:
    Before recommending "buy more TCS", the system
    needs to know if you already have too much TCS.
    Also shows overall portfolio health.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT symbol, quantity, avg_buy_price, buy_date, notes
            FROM holdings
            ORDER BY symbol
        """)
        holdings = cursor.fetchall()
        cursor.close()
        conn.close()

        if not holdings:
            return json.dumps({
                "message": "Portfolio is empty. Add holdings first.",
                "holdings": []
            })

        portfolio = []
        total_invested = 0
        total_current_value = 0

        for holding in holdings:
            symbol, qty, avg_price, buy_date, notes = holding

            # Get live price
            current_price = get_current_price(symbol)

            invested = round(qty * avg_price, 2)
            current_value = round(qty * current_price, 2)
            pnl = round(current_value - invested, 2)
            pnl_pct = round(
                (pnl / invested * 100) if invested > 0 else 0, 2
            )

            total_invested += invested
            total_current_value += current_value

            portfolio.append({
                "symbol": symbol,
                "quantity": qty,
                "avg_buy_price": avg_price,
                "current_price": current_price,
                "invested_inr": invested,
                "current_value_inr": current_value,
                "pnl_inr": pnl,
                "pnl_pct": pnl_pct,
                "status": "Profit ✅" if pnl > 0 else "Loss ❌"
            })

        total_pnl = round(total_current_value - total_invested, 2)
        total_pnl_pct = round(
            (total_pnl / total_invested * 100)
            if total_invested > 0 else 0, 2
        )

        result = {
            "portfolio_summary": {
                "total_invested_inr": round(total_invested, 2),
                "current_value_inr": round(total_current_value, 2),
                "total_pnl_inr": total_pnl,
                "total_pnl_pct": total_pnl_pct,
                "overall_status": (
                    "Profit ✅" if total_pnl > 0 else "Loss ❌"
                )
            },
            "holdings": portfolio
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_allocation() -> str:
    """
    Get portfolio allocation by stock and sector.

    What it returns:
    - What % of portfolio is in each stock
    - What % is in each sector
    - Whether portfolio is well diversified

    Why agents need this:
    Concentration risk — if 60% is in one stock
    and it crashes, your whole portfolio crashes.
    SEBI recommends no single stock > 10-15% for
    retail investors.

    Risk Agent uses this to flag over-concentration.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT symbol, quantity, avg_buy_price FROM holdings"
        )
        holdings = cursor.fetchall()
        cursor.close()
        conn.close()

        if not holdings:
            return json.dumps({"message": "Portfolio empty"})

        # Sector mapping for major Indian stocks
        sector_map = {
            "TCS": "IT", "INFY": "IT", "WIPRO": "IT",
            "HCLTECH": "IT", "TECHM": "IT",
            "HDFCBANK": "Banking", "ICICIBANK": "Banking",
            "SBIN": "Banking", "KOTAKBANK": "Banking",
            "AXISBANK": "Banking",
            "RELIANCE": "Energy", "ONGC": "Energy",
            "IOC": "Energy", "BPCL": "Energy",
            "MARUTI": "Auto", "TATAMOTORS": "Auto",
            "BAJAJ-AUTO": "Auto", "M&M": "Auto",
            "SUNPHARMA": "Pharma", "DRREDDY": "Pharma",
            "CIPLA": "Pharma", "DIVISLAB": "Pharma",
            "HINDUNILVR": "FMCG", "ITC": "FMCG",
            "NESTLEIND": "FMCG", "BRITANNIA": "FMCG",
            "BAJFINANCE": "NBFC", "BAJAJFINSV": "NBFC",
        }

        total_value = 0
        stock_values = {}

        for symbol, qty, avg_price in holdings:
            current_price = get_current_price(symbol)
            value = qty * (current_price or avg_price)
            stock_values[symbol] = value
            total_value += value

        # Stock allocation
        stock_allocation = []
        for symbol, value in stock_values.items():
            pct = round(value / total_value * 100, 2)
            stock_allocation.append({
                "symbol": symbol,
                "value_inr": round(value, 2),
                "allocation_pct": pct,
                "concentration_risk": (
                    "High ⚠️" if pct > 20
                    else "Moderate" if pct > 10
                    else "Low ✅"
                )
            })

        # Sort by allocation descending
        stock_allocation.sort(
            key=lambda x: x["allocation_pct"],
            reverse=True
        )

        # Sector allocation
        sector_values = {}
        for symbol, value in stock_values.items():
            sector = sector_map.get(symbol, "Others")
            sector_values[sector] = (
                sector_values.get(sector, 0) + value
            )

        sector_allocation = [
            {
                "sector": sector,
                "value_inr": round(value, 2),
                "allocation_pct": round(
                    value / total_value * 100, 2
                )
            }
            for sector, value in sector_values.items()
        ]
        sector_allocation.sort(
            key=lambda x: x["allocation_pct"],
            reverse=True
        )

        # Diversification score
        # Simple: more stocks + more sectors = better
        num_stocks = len(stock_values)
        num_sectors = len(sector_values)
        max_concentration = max(
            s["allocation_pct"] for s in stock_allocation
        )

        diversification = (
            "Well diversified ✅"
            if num_stocks >= 8 and max_concentration < 15
            else "Moderately diversified"
            if num_stocks >= 5
            else "Concentrated portfolio ⚠️ — consider diversifying"
        )

        result = {
            "total_portfolio_value": round(total_value, 2),
            "diversification": diversification,
            "number_of_stocks": num_stocks,
            "number_of_sectors": num_sectors,
            "stock_allocation": stock_allocation,
            "sector_allocation": sector_allocation
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_portfolio_performance() -> str:
    """
    Get overall portfolio performance metrics.

    What it returns:
    - Best and worst performing stocks
    - Overall portfolio return
    - Which stocks to review

    Why agents need this:
    Writer Agent uses this to frame the report:
    "Given your portfolio is down 12% overall,
    and TCS is your biggest loser at -30%..."
    Personalized advice is far more valuable.
    """
    try:
        portfolio_raw = json.loads(get_portfolio())

        if "error" in portfolio_raw or "message" in portfolio_raw:
            return json.dumps(portfolio_raw)

        holdings = portfolio_raw.get("holdings", [])
        summary = portfolio_raw.get("portfolio_summary", {})

        if not holdings:
            return json.dumps({"message": "No holdings found"})

        # Sort by P&L percentage
        sorted_by_pnl = sorted(
            holdings,
            key=lambda x: x["pnl_pct"],
            reverse=True
        )

        best = sorted_by_pnl[0] if sorted_by_pnl else None
        worst = sorted_by_pnl[-1] if sorted_by_pnl else None

        # Stocks needing review (loss > 20%)
        review_needed = [
            h for h in holdings if h["pnl_pct"] < -20
        ]

        result = {
            "performance_summary": summary,
            "best_performer": {
                "symbol": best["symbol"],
                "pnl_pct": best["pnl_pct"],
                "pnl_inr": best["pnl_inr"]
            } if best else None,
            "worst_performer": {
                "symbol": worst["symbol"],
                "pnl_pct": worst["pnl_pct"],
                "pnl_inr": worst["pnl_inr"]
            } if worst else None,
            "stocks_needing_review": [
                {
                    "symbol": h["symbol"],
                    "pnl_pct": h["pnl_pct"],
                    "suggestion": "Consider reviewing position"
                }
                for h in review_needed
            ],
            "all_holdings_performance": sorted_by_pnl
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()