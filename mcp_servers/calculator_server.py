"""
Calculator MCP Server
---------------------
Performs financial calculations for Indian stocks.

Why a separate calculator server?
Keeps calculation logic separate from data fetching.
Agents call this server to compute derived metrics
from raw data fetched by market/macro servers.

Tools provided:
1. calculate_technical_indicators — RSI, MACD, moving averages
2. calculate_dcf — Discounted Cash Flow valuation
3. calculate_risk_metrics — Beta, Sharpe ratio, VaR
4. calculate_sip_returns — SIP investment calculator
5. compare_valuation — Compare stock vs sector peers
6. calculate_financial_ratios — Derived ratios from financials
"""

import json
import numpy as np
import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calculator_server")


def get_nse_ticker(symbol: str) -> str:
    """Convert symbol to NSE format."""
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        return f"{symbol.upper()}.NS"
    return symbol.upper()


@mcp.tool()
def calculate_technical_indicators(symbol: str) -> str:
    """
    Calculate technical indicators for a stock.

    What are technical indicators?
    Mathematical calculations based on price and volume
    that help identify trends, momentum, and signals.

    Indicators calculated:

    RSI (Relative Strength Index):
    - Measures momentum on scale 0-100
    - Above 70 = overbought (likely to fall)
    - Below 30 = oversold (likely to rise)
    - Formula: 100 - (100 / (1 + avg_gain/avg_loss))

    MACD (Moving Average Convergence Divergence):
    - Measures trend direction and momentum
    - MACD line = 12-day EMA - 26-day EMA
    - Signal line = 9-day EMA of MACD
    - Crossover above signal = buy signal
    - Crossover below signal = sell signal

    Moving Averages:
    - 50-day MA = short term trend
    - 200-day MA = long term trend
    - Price above both = strong uptrend
    - Price below both = strong downtrend
    - 50-day crosses above 200-day = Golden Cross (bullish)
    - 50-day crosses below 200-day = Death Cross (bearish)

    Args:
        symbol: NSE stock symbol e.g. TCS, RELIANCE
    """
    try:
        ticker = yf.Ticker(get_nse_ticker(symbol))
        history = ticker.history(period="1y")

        if history.empty or len(history) < 50:
            return json.dumps({"error": "Insufficient data"})

        close = history['Close']
        volume = history['Volume']

        # ── RSI Calculation ──────────────────────────────
        # Step 1: Calculate daily price changes
        delta = close.diff()

        # Step 2: Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Step 3: Calculate 14-day average gain/loss
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        # Step 4: RSI formula
        rs = avg_gain / avg_loss
        rsi = round(float(100 - (100 / (1 + rs.iloc[-1]))), 2)

        # RSI interpretation
        rsi_signal = (
            "Overbought — potential sell signal"
            if rsi > 70
            else "Oversold — potential buy signal"
            if rsi < 30
            else "Neutral zone"
        )

        # ── Moving Averages ──────────────────────────────
        ma50 = round(float(close.rolling(50).mean().iloc[-1]), 2)
        ma200 = round(float(close.rolling(200).mean().iloc[-1]), 2)
        current_price = round(float(close.iloc[-1]), 2)

        # Price position relative to MAs
        above_ma50 = current_price > ma50
        above_ma200 = current_price > ma200

        ma_signal = (
            "Strong uptrend — price above both MAs"
            if above_ma50 and above_ma200
            else "Caution — price below 50MA but above 200MA"
            if not above_ma50 and above_ma200
            else "Downtrend — price below both MAs"
            if not above_ma50 and not above_ma200
            else "Recovery — price above 50MA but below 200MA"
        )

        # Golden/Death cross check
        ma50_prev = round(
            float(close.rolling(50).mean().iloc[-2]), 2
        )
        ma200_prev = round(
            float(close.rolling(200).mean().iloc[-2]), 2
        )

        cross_signal = "None"
        if ma50_prev < ma200_prev and ma50 > ma200:
            cross_signal = "Golden Cross — strong bullish signal"
        elif ma50_prev > ma200_prev and ma50 < ma200:
            cross_signal = "Death Cross — strong bearish signal"

        # ── MACD Calculation ─────────────────────────────
        # EMA = Exponential Moving Average
        # Gives more weight to recent prices than simple MA
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        macd_value = round(float(macd_line.iloc[-1]), 2)
        signal_value = round(float(signal_line.iloc[-1]), 2)
        hist_value = round(float(histogram.iloc[-1]), 2)

        macd_signal = (
            "Bullish — MACD above signal line"
            if macd_value > signal_value
            else "Bearish — MACD below signal line"
        )

        # ── Volume Analysis ──────────────────────────────
        avg_volume_20 = round(
            float(volume.rolling(20).mean().iloc[-1])
        )
        current_volume = int(volume.iloc[-1])
        volume_ratio = round(current_volume / avg_volume_20, 2)

        volume_signal = (
            "High volume — strong conviction in move"
            if volume_ratio > 1.5
            else "Low volume — weak conviction"
            if volume_ratio < 0.5
            else "Normal volume"
        )

        result = {
            "symbol": symbol,
            "current_price": current_price,
            "technical_summary": {
                "rsi": {
                    "value": rsi,
                    "signal": rsi_signal
                },
                "moving_averages": {
                    "ma50": ma50,
                    "ma200": ma200,
                    "above_ma50": above_ma50,
                    "above_ma200": above_ma200,
                    "signal": ma_signal,
                    "cross_signal": cross_signal
                },
                "macd": {
                    "macd_line": macd_value,
                    "signal_line": signal_value,
                    "histogram": hist_value,
                    "signal": macd_signal
                },
                "volume": {
                    "current": current_volume,
                    "20day_avg": avg_volume_20,
                    "ratio": volume_ratio,
                    "signal": volume_signal
                }
            },
            "overall_technical": (
                "Bullish" if sum([
                    rsi < 70,
                    above_ma50,
                    above_ma200,
                    macd_value > signal_value
                ]) >= 3
                else "Bearish" if sum([
                    rsi > 30,
                    not above_ma50,
                    not above_ma200,
                    macd_value < signal_value
                ]) >= 3
                else "Neutral"
            )
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def calculate_dcf(
    symbol: str,
    growth_rate: float = 0.10,
    discount_rate: float = 0.12,
    terminal_growth: float = 0.04,
    years: int = 5
) -> str:
    """
    Calculate DCF (Discounted Cash Flow) valuation.

    What is DCF?
    DCF estimates the intrinsic value of a stock by
    projecting future cash flows and discounting them
    back to present value.

    The core idea:
    ₹100 today is worth more than ₹100 next year
    because you could invest ₹100 today and get more.
    DCF accounts for this "time value of money."

    Formula:
    Intrinsic Value = Sum of (FCF × (1+g)^t / (1+r)^t)
                    + Terminal Value / (1+r)^n

    Where:
    FCF = Free Cash Flow (cash generated after capex)
    g = growth rate (how fast FCF grows)
    r = discount rate (your required return, usually 12%)
    t = year number
    n = total years

    Terminal Value:
    Value of all cash flows beyond year 5.
    = FCF_year5 × (1+terminal_growth) / (r - terminal_growth)

    Interpretation:
    If intrinsic value > current price → UNDERVALUED → Buy
    If intrinsic value < current price → OVERVALUED → Sell
    If intrinsic value ≈ current price → FAIRLY VALUED → Hold

    Args:
        symbol: NSE stock symbol
        growth_rate: Expected FCF growth (default 10%)
        discount_rate: Required return rate (default 12%)
        terminal_growth: Long term growth rate (default 4%)
        years: Projection years (default 5)
    """
    try:
        ticker = yf.Ticker(get_nse_ticker(symbol))
        info = ticker.info
        cashflow = ticker.cashflow

        # Get Free Cash Flow
        # FCF = Operating Cash Flow - Capital Expenditure
        if cashflow is not None and not cashflow.empty:
            try:
                operating_cf = float(
                    cashflow.loc['Operating Cash Flow'].iloc[0]
                )
                capex = float(
                    cashflow.loc['Capital Expenditure'].iloc[0]
                )
                fcf = operating_cf + capex  # capex is negative
            except:
                fcf = info.get('freeCashflow', 0)
        else:
            fcf = info.get('freeCashflow', 0)

        if not fcf or fcf <= 0:
            return json.dumps({
                "error": "Cannot calculate DCF — negative or zero FCF",
                "symbol": symbol
            })

        shares = info.get('sharesOutstanding', 1)
        current_price = info.get('currentPrice', 0)

        # Project FCF for each year
        projected_fcf = []
        for year in range(1, years + 1):
            projected = fcf * (1 + growth_rate) ** year
            discounted = projected / (1 + discount_rate) ** year
            projected_fcf.append({
                "year": year,
                "projected_fcf": round(projected / 1e9, 2),
                "discounted_fcf": round(discounted / 1e9, 2)
            })

        # Terminal value — value beyond year 5
        fcf_year5 = fcf * (1 + growth_rate) ** years
        terminal_value = (
            fcf_year5 * (1 + terminal_growth)
            / (discount_rate - terminal_growth)
        )
        discounted_terminal = (
            terminal_value / (1 + discount_rate) ** years
        )

        # Total intrinsic value
        pv_fcf = sum(
            y["discounted_fcf"] * 1e9
            for y in projected_fcf
        )
        total_value = pv_fcf + discounted_terminal
        intrinsic_per_share = round(total_value / shares, 2)

        # Margin of safety
        # Buy when stock trades 20-30% below intrinsic value
        margin_of_safety = round(
            (intrinsic_per_share - current_price)
            / intrinsic_per_share * 100, 2
        )

        result = {
            "symbol": symbol,
            "dcf_valuation": {
                "current_price": current_price,
                "intrinsic_value_per_share": intrinsic_per_share,
                "margin_of_safety_pct": margin_of_safety,
                "verdict": (
                    "Undervalued — potential buy"
                    if margin_of_safety > 20
                    else "Fairly valued — hold"
                    if margin_of_safety > -10
                    else "Overvalued — avoid"
                )
            },
            "assumptions": {
                "fcf_base_crore": round(fcf / 1e7, 2),
                "growth_rate_pct": growth_rate * 100,
                "discount_rate_pct": discount_rate * 100,
                "terminal_growth_pct": terminal_growth * 100,
                "projection_years": years
            },
            "projected_cashflows": projected_fcf,
            "terminal_value_billion": round(
                discounted_terminal / 1e9, 2
            )
        }

    except Exception as e:
        result = {"error": str(e), "symbol": symbol}

    return json.dumps(result, indent=2)


@mcp.tool()
def calculate_risk_metrics(symbol: str) -> str:
    """
    Calculate risk metrics for a stock.

    Metrics calculated:

    Beta:
    - Measures stock volatility vs market (Nifty 50)
    - Beta > 1 = more volatile than market
    - Beta < 1 = less volatile than market
    - Beta = 1 = moves exactly with market
    - Example: Beta 1.5 means if Nifty falls 10%,
      stock likely falls 15%

    Sharpe Ratio:
    - Measures return per unit of risk
    - Higher is better
    - Above 1.0 = good risk-adjusted return
    - Formula: (Return - Risk Free Rate) / Std Dev
    - Risk free rate = RBI repo rate (5.5%)

    Value at Risk (VaR):
    - Maximum expected loss in a day with 95% confidence
    - VaR of -2% means on 95% of days, loss won't exceed 2%
    - On 5% of days (worst case), loss could be more

    Maximum Drawdown:
    - Largest peak-to-trough decline in the period
    - Shows worst case scenario historically

    Args:
        symbol: NSE stock symbol
    """
    try:
        # Fetch stock and Nifty data
        ticker = yf.Ticker(get_nse_ticker(symbol))
        nifty = yf.Ticker("^NSEI")

        stock_hist = ticker.history(period="1y")
        nifty_hist = nifty.history(period="1y")

        if stock_hist.empty or nifty_hist.empty:
            return json.dumps({"error": "Insufficient data"})

        # Daily returns
        stock_returns = stock_hist['Close'].pct_change().dropna()
        nifty_returns = nifty_hist['Close'].pct_change().dropna()

        # Align dates
        common_dates = stock_returns.index.intersection(
            nifty_returns.index
        )
        stock_returns = stock_returns[common_dates]
        nifty_returns = nifty_returns[common_dates]

        # ── Beta Calculation ─────────────────────────────
        # Covariance of stock vs market / variance of market
        covariance = np.cov(
            stock_returns.values,
            nifty_returns.values
        )[0][1]
        market_variance = np.var(nifty_returns.values)
        beta = round(covariance / market_variance, 2)

        # ── Sharpe Ratio ─────────────────────────────────
        risk_free_rate = 0.055 / 252  # daily RBI repo rate
        excess_returns = stock_returns - risk_free_rate
        sharpe = round(
            float(
                excess_returns.mean()
                / excess_returns.std()
                * np.sqrt(252)  # annualize
            ), 2
        )

        # ── Value at Risk (95% confidence) ───────────────
        var_95 = round(
            float(np.percentile(stock_returns, 5)) * 100, 2
        )

        # ── Maximum Drawdown ─────────────────────────────
        cumulative = (1 + stock_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = round(float(drawdown.min()) * 100, 2)

        # ── Annualized Volatility ─────────────────────────
        volatility = round(
            float(stock_returns.std() * np.sqrt(252)) * 100, 2
        )

        # ── 1 Year Return ─────────────────────────────────
        annual_return = round(
            float(
                (stock_hist['Close'].iloc[-1]
                 - stock_hist['Close'].iloc[0])
                / stock_hist['Close'].iloc[0]
            ) * 100, 2
        )

        result = {
            "symbol": symbol,
            "risk_metrics": {
                "beta": {
                    "value": beta,
                    "interpretation": (
                        "High risk — very volatile vs market"
                        if beta > 1.5
                        else "Moderate risk — slightly volatile"
                        if beta > 1
                        else "Low risk — less volatile than market"
                    )
                },
                "sharpe_ratio": {
                    "value": sharpe,
                    "interpretation": (
                        "Excellent risk-adjusted return"
                        if sharpe > 2
                        else "Good risk-adjusted return"
                        if sharpe > 1
                        else "Poor risk-adjusted return"
                    )
                },
                "var_95_pct": {
                    "value": var_95,
                    "interpretation": (
                        f"In 95% of days, daily loss won't exceed {abs(var_95)}%"
                    )
                },
                "max_drawdown_pct": {
                    "value": max_drawdown,
                    "interpretation": (
                        f"Worst peak-to-trough decline was {abs(max_drawdown)}%"
                    )
                },
                "annualized_volatility_pct": volatility,
                "1yr_return_pct": annual_return,
            },
            "risk_level": (
                "High" if beta > 1.5 or volatility > 40
                else "Moderate" if beta > 1 or volatility > 25
                else "Low"
            )
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def calculate_sip_returns(
    monthly_amount: float,
    annual_return: float,
    years: int
) -> str:
    """
    Calculate SIP (Systematic Investment Plan) returns.

    What is SIP?
    Investing a fixed amount every month in a stock/fund.
    Rupee cost averaging — buy more units when price is low,
    fewer when price is high.

    Formula:
    FV = P × [(1+r)^n - 1] / r × (1+r)
    Where:
    P = monthly investment
    r = monthly return rate (annual/12)
    n = total months

    Example:
    ₹10,000/month for 10 years at 12% annual return
    → Total invested: ₹12,00,000
    → Final value: ₹23,00,390
    → Wealth created: ₹11,00,390

    Args:
        monthly_amount: Monthly SIP amount in INR
        annual_return: Expected annual return % (e.g. 12)
        years: Investment duration in years
    """
    try:
        monthly_rate = annual_return / 100 / 12
        months = years * 12

        # SIP future value formula
        if monthly_rate > 0:
            fv = (
                monthly_amount
                * ((1 + monthly_rate) ** months - 1)
                / monthly_rate
                * (1 + monthly_rate)
            )
        else:
            fv = monthly_amount * months

        total_invested = monthly_amount * months
        wealth_created = fv - total_invested
        returns_pct = round(
            (fv - total_invested) / total_invested * 100, 2
        )

        # Year by year breakdown
        yearly = []
        for year in range(1, years + 1):
            n = year * 12
            fv_year = (
                monthly_amount
                * ((1 + monthly_rate) ** n - 1)
                / monthly_rate
                * (1 + monthly_rate)
            )
            yearly.append({
                "year": year,
                "invested": round(monthly_amount * n, 2),
                "value": round(fv_year, 2),
                "gain": round(fv_year - monthly_amount * n, 2)
            })

        result = {
            "sip_calculation": {
                "monthly_amount_inr": monthly_amount,
                "annual_return_pct": annual_return,
                "duration_years": years,
                "total_invested_inr": round(total_invested, 2),
                "final_value_inr": round(fv, 2),
                "wealth_created_inr": round(wealth_created, 2),
                "total_return_pct": returns_pct,
            },
            "yearly_breakdown": yearly
        }

    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, indent=2)


@mcp.tool()
def compare_valuation(symbol: str) -> str:
    """
    Compare stock valuation vs sector peers.

    What it does:
    Fetches P/E, P/B, ROE for the stock and its peers.
    Determines if the stock is cheap or expensive
    relative to its sector.

    Why relative valuation matters:
    A P/E of 25 might be cheap if peers trade at 35.
    A P/E of 25 might be expensive if peers trade at 15.
    Absolute numbers mean little without context.

    Args:
        symbol: NSE stock symbol
    """
    peer_groups = {
        "TCS": ["INFY", "WIPRO", "HCLTECH", "TECHM"],
        "INFY": ["TCS", "WIPRO", "HCLTECH", "TECHM"],
        "HDFCBANK": ["ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
        "ICICIBANK": ["HDFCBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
        "RELIANCE": ["ONGC", "IOC", "BPCL"],
        "WIPRO": ["TCS", "INFY", "HCLTECH", "TECHM"],
        "BAJFINANCE": ["HDFCBANK", "ICICIBANK", "KOTAKBANK"],
        "MARUTI": ["TATAMOTORS", "M&M", "BAJAJ-AUTO"],
        "SBIN": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK"],
    }

    peers = peer_groups.get(symbol.upper(), [])

    def get_metrics(sym):
        try:
            t = yf.Ticker(get_nse_ticker(sym))
            info = t.info
            return {
                "symbol": sym,
                "pe_ratio": round(info.get("trailingPE", 0) or 0, 2),
                "pb_ratio": round(info.get("priceToBook", 0) or 0, 2),
                "roe_pct": round((info.get("returnOnEquity", 0) or 0) * 100, 2),
                "revenue_growth_pct": round((info.get("revenueGrowth", 0) or 0) * 100, 2),
                "profit_margin_pct": round((info.get("profitMargins", 0) or 0) * 100, 2),
            }
        except:
            return {"symbol": sym, "error": "Data unavailable"}

    # Get target stock metrics
    target_metrics = get_metrics(symbol)

    # Get peer metrics
    peer_metrics = [get_metrics(peer) for peer in peers]

    # Calculate sector averages
    valid_peers = [p for p in peer_metrics if "error" not in p]
    if valid_peers:
        avg_pe = round(
            sum(p["pe_ratio"] for p in valid_peers) / len(valid_peers), 2
        )
        avg_pb = round(
            sum(p["pb_ratio"] for p in valid_peers) / len(valid_peers), 2
        )
        avg_roe = round(
            sum(p["roe_pct"] for p in valid_peers) / len(valid_peers), 2
        )

        # Valuation verdict
        target_pe = target_metrics.get("pe_ratio", 0)
        pe_premium = round(
            (target_pe - avg_pe) / avg_pe * 100, 2
        ) if avg_pe > 0 else 0

        verdict = (
            f"Trading at {abs(pe_premium)}% discount to peers — cheap"
            if pe_premium < -10
            else f"Trading at {pe_premium}% premium to peers — expensive"
            if pe_premium > 10
            else "Trading in line with peers — fairly valued"
        )
    else:
        avg_pe = avg_pb = avg_roe = 0
        verdict = "Insufficient peer data"
        pe_premium = 0

    result = {
        "symbol": symbol,
        "target_stock": target_metrics,
        "sector_averages": {
            "avg_pe": avg_pe,
            "avg_pb": avg_pb,
            "avg_roe_pct": avg_roe
        },
        "pe_premium_pct": pe_premium,
        "valuation_verdict": verdict,
        "peer_comparison": peer_metrics
    }

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()