"""
Market MCP Server
-----------------
Provides tools for fetching Indian stock market data.
Uses yfinance for NSE/BSE data (free, no API key needed).

Why yfinance for Indian stocks?
- Supports NSE stocks with .NS suffix (e.g. RELIANCE.NS)
- Supports BSE stocks with .BO suffix (e.g. 500325.BO)
- Provides price, fundamentals, financials all in one library
- Completely free, no rate limits for reasonable usage
"""

import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

# FastMCP creates an MCP server with minimal boilerplate
# Think of it like FastAPI but for AI tool servers
mcp = FastMCP("market_server")


def get_nse_ticker(symbol: str) -> str:
    """
    Convert plain symbol to NSE format.
    Why? yfinance needs .NS suffix for NSE stocks.
    Example: RELIANCE → RELIANCE.NS
    """
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        return f"{symbol.upper()}.NS"
    return symbol.upper()


@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """
    Get current stock price and basic info for an Indian stock.
    
    What it returns:
    - Current price
    - Day high/low
    - Volume
    - Market cap
    - 52-week high/low
    
    Why agents need this:
    The fundamental and technical agents need current price
    as the starting point for all analysis.
    
    Args:
        symbol: NSE symbol e.g. RELIANCE, TCS, INFY, HDFCBANK
    """
    ticker_symbol = get_nse_ticker(symbol)
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    result = {
        "symbol": symbol,
        "current_price": info.get("currentPrice"),
        "previous_close": info.get("previousClose"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
        "currency": "INR",
        "exchange": "NSE"
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_stock_history(symbol: str, period: str = "1y") -> str:
    """
    Get historical price data for technical analysis.
    
    What it returns:
    - Daily OHLCV data (Open, High, Low, Close, Volume)
    
    Why agents need this:
    Technical Agent uses this to calculate:
    - Moving averages (50-day, 200-day)
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Support and resistance levels
    
    Args:
        symbol: NSE stock symbol
        period: "1mo", "3mo", "6mo", "1y", "2y", "5y"
    """
    ticker_symbol = get_nse_ticker(symbol)
    ticker = yf.Ticker(ticker_symbol)
    history = ticker.history(period=period)

    # Convert to dict for JSON serialization
    # Reset index to make Date a column not index
    history = history.reset_index()
    history['Date'] = history['Date'].dt.strftime('%Y-%m-%d')

    result = {
        "symbol": symbol,
        "period": period,
        "data_points": len(history),
        "data": history[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict('records')
    }

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_fundamentals(symbol: str) -> str:
    """
    Get fundamental financial ratios for valuation analysis.
    
    What it returns:
    - P/E ratio (Price to Earnings)
    - P/B ratio (Price to Book)
    - ROE (Return on Equity)
    - Debt to Equity
    - EPS (Earnings Per Share)
    - Dividend yield
    
    Why agents need this:
    Fundamental Agent uses these ratios to determine if
    a stock is overvalued, undervalued, or fairly priced
    compared to its peers and historical averages.
    
    Args:
        symbol: NSE stock symbol
    """
    ticker_symbol = get_nse_ticker(symbol)
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    result = {
        "symbol": symbol,
        "valuation": {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
        },
        "profitability": {
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "gross_margin": info.get("grossMargins"),
        },
        "growth": {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
        },
        "financial_health": {
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "free_cashflow": info.get("freeCashflow"),
        },
        "per_share": {
            "eps": info.get("trailingEps"),
            "book_value": info.get("bookValue"),
            "dividend_yield": info.get("dividendYield"),
        }
    }

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_financials(symbol: str) -> str:
    """
    Get income statement, balance sheet, and cash flow data.
    
    What it returns:
    - Annual revenue, profit, EBITDA
    - Assets, liabilities, equity
    - Operating cash flow, capex, free cash flow
    
    Why agents need this:
    Fundamental Agent reads these to understand the actual
    business performance — not just ratios but real numbers.
    This is what analysts read in quarterly results.
    
    Args:
        symbol: NSE stock symbol
    """
    ticker_symbol = get_nse_ticker(symbol)
    ticker = yf.Ticker(ticker_symbol)

    # Income statement
    income = ticker.financials
    balance = ticker.balance_sheet
    cashflow = ticker.cashflow

    def df_to_dict(df):
        if df is None or df.empty:
            return {}
        df.columns = [str(c)[:10] for c in df.columns]
        return df.to_dict()

    result = {
        "symbol": symbol,
        "income_statement": df_to_dict(income),
        "balance_sheet": df_to_dict(balance),
        "cash_flow": df_to_dict(cashflow),
    }

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_nifty50_performance() -> str:
    """
    Get current Nifty 50 index performance.
    
    What it returns:
    - Current Nifty 50 level
    - Day change and % change
    - 1 month, 3 month, 1 year returns
    
    Why agents need this:
    Macro Agent uses this to understand overall market
    sentiment. If Nifty is down 2% today, individual
    stock analysis needs that context.
    """
    nifty = yf.Ticker("^NSEI")
    info = nifty.info
    history = nifty.history(period="1y")

    current = history['Close'].iloc[-1]
    month_ago = history['Close'].iloc[-22]
    three_months_ago = history['Close'].iloc[-66]
    year_ago = history['Close'].iloc[0]

    result = {
        "index": "Nifty 50",
        "current_level": round(current, 2),
        "day_change_pct": round(info.get("regularMarketChangePercent", 0), 2),
        "returns": {
            "1_month_pct": round((current - month_ago) / month_ago * 100, 2),
            "3_month_pct": round((current - three_months_ago) / three_months_ago * 100, 2),
            "1_year_pct": round((current - year_ago) / year_ago * 100, 2),
        }
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_sector_performance() -> str:
    """
    Get performance of major Indian market sectors.
    
    What it returns:
    - Returns for IT, Banking, Auto, Pharma, Energy sectors
    
    Why agents need this:
    Competitor Agent and Macro Agent use sector data to
    understand whether a stock's movement is company-specific
    or sector-wide. If all IT stocks are down, that's macro.
    If only TCS is down, that's company-specific.
    """
    # Nifty sector indices
    sectors = {
        "IT": "^CNXIT",
        "Banking": "^NSEBANK",
        "Auto": "^CNXAUTO",
        "Pharma": "^CNXPHARMA",
        "Energy": "^CNXENERGY",
        "FMCG": "^CNXFMCG",
        "Realty": "^CNXREALTY",
        "Metal": "^CNXMETAL",
    }

    result = {}
    for sector_name, ticker_sym in sectors.items():
        try:
            ticker = yf.Ticker(ticker_sym)
            history = ticker.history(period="1mo")
            if not history.empty:
                current = history['Close'].iloc[-1]
                month_ago = history['Close'].iloc[0]
                change_pct = (current - month_ago) / month_ago * 100
                result[sector_name] = {
                    "current": round(current, 2),
                    "1_month_return_pct": round(change_pct, 2)
                }
        except:
            result[sector_name] = {"error": "Data unavailable"}

    return json.dumps(result, indent=2)


@mcp.tool()
def get_competitors(symbol: str) -> str:
    """
    Get list of competitor stocks in same sector.
    
    Why agents need this:
    Competitor Agent compares the target stock against
    peers on valuation, growth, and profitability.
    A stock with P/E of 30 might be cheap if peers
    trade at P/E of 50, or expensive if peers are at 15.
    
    Args:
        symbol: NSE stock symbol
    """
    # Predefined peer groups for major Indian stocks
    # In production this would come from a database
    peer_groups = {
        "TCS": ["INFY", "WIPRO", "HCLTECH", "TECHM"],
        "INFY": ["TCS", "WIPRO", "HCLTECH", "TECHM"],
        "RELIANCE": ["ONGC", "IOC", "BPCL", "GAIL"],
        "HDFCBANK": ["ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
        "ICICIBANK": ["HDFCBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
        "WIPRO": ["TCS", "INFY", "HCLTECH", "TECHM"],
        "BAJFINANCE": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK"],
        "ASIANPAINT": ["BERGER", "KANSAINER", "INDIGO"],
        "MARUTI": ["TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO"],
    }

    symbol_upper = symbol.upper()
    peers = peer_groups.get(symbol_upper, [])

    peer_data = []
    for peer in peers:
        try:
            ticker = yf.Ticker(get_nse_ticker(peer))
            info = ticker.info
            peer_data.append({
                "symbol": peer,
                "pe_ratio": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margin": info.get("profitMargins"),
            })
        except:
            pass

    result = {
        "symbol": symbol,
        "competitors": peer_data
    }

    return json.dumps(result, indent=2, default=str)


# Run the MCP server
if __name__ == "__main__":
    mcp.run()