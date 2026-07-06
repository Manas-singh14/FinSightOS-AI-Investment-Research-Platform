import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import yfinance as yf

from graph.orchestrator import run_analysis
from mcp_servers.portfolio_server import (
    add_holding, get_portfolio,
    get_allocation, get_portfolio_performance
)
from mcp_servers.market_server import (
    get_stock_price, get_sector_performance,
    get_nifty50_performance
)
from mcp_servers.macro_server import get_macro_summary

app = FastAPI(
    title="FinSightOS API",
    description="AI-powered Indian stock market research platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class AnalyzeRequest(BaseModel):
    symbol: str
    sector: Optional[str] = "IT"


class HoldingRequest(BaseModel):
    symbol: str
    quantity: float
    avg_buy_price: float
    buy_date: Optional[str] = None
    notes: Optional[str] = ""


@app.get("/")
def root():
    return {
        "name": "FinSightOS API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze")
def analyze_stock(request: AnalyzeRequest):
    """Run complete AI analysis pipeline for any NSE stock."""
    try:
        symbol = request.symbol.upper().strip()
        sector = request.sector or "IT"

        if not symbol:
            raise HTTPException(
                status_code=400,
                detail="Symbol cannot be empty"
            )

        report = run_analysis(symbol, sector=sector)
        return {"success": True, "data": report}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/search/{query}")
def search_symbol(query: str):
    """
    Validate NSE symbol and return company name.
    Helps users find correct symbol before analyzing.
    """
    try:
        ticker = yf.Ticker(f"{query.upper()}.NS")
        info = ticker.info
        name = info.get("longName", "")
        price = info.get("currentPrice", 0)

        if name and price:
            return {
                "success": True,
                "data": {
                    "symbol": query.upper(),
                    "company_name": name,
                    "current_price": price,
                    "valid": True
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "symbol": query.upper(),
                    "valid": False,
                    "message": "Symbol not found on NSE"
                }
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/market/price/{symbol}")
def get_price(symbol: str):
    """Get current price and basic info for any NSE stock."""
    try:
        data = json.loads(get_stock_price(symbol.upper()))
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/nifty")
def get_nifty():
    """Get current Nifty 50 performance."""
    try:
        data = json.loads(get_nifty50_performance())
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/sectors")
def get_sectors():
    """Get performance of all major Indian sectors."""
    try:
        data = json.loads(get_sector_performance())
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/macro/summary")
def macro_summary():
    """Get complete Indian macro snapshot."""
    try:
        data = json.loads(get_macro_summary())
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/add")
def add_stock_to_portfolio(request: HoldingRequest):
    """Add or update a stock holding in the portfolio."""
    try:
        result = json.loads(add_holding(
            symbol=request.symbol.upper(),
            quantity=request.quantity,
            avg_buy_price=request.avg_buy_price,
            buy_date=request.buy_date,
            notes=request.notes
        ))
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio")
def view_portfolio():
    """Get complete portfolio with live P&L."""
    try:
        data = json.loads(get_portfolio())
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/allocation")
def view_allocation():
    """Get portfolio allocation by stock and sector."""
    try:
        data = json.loads(get_allocation())
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/performance")
def view_performance():
    """Get portfolio performance summary."""
    try:
        data = json.loads(get_portfolio_performance())
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))