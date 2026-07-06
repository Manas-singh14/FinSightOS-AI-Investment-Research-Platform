import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from typing import TypedDict
from datetime import date
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from agents.fundamental_agent import run_fundamental_agent
from agents.technical_agent import run_technical_agent
from agents.sentiment_agent import run_sentiment_agent
from agents.macro_agent import run_macro_agent
from agents.risk_agent import run_risk_agent
from agents.writer_agent import run_writer_agent

load_dotenv()


# state holds everything passed between nodes
# TypedDict ensures type safety
class AnalysisState(TypedDict):
    symbol: str
    sector: str
    fundamental: dict
    technical: dict
    sentiment: dict
    macro: dict
    risk: dict
    report: dict
    error: str


# ── Node functions ────────────────────────────────────────────
# each node is one step in the graph
# nodes receive state and return updated state

def fundamental_node(state: AnalysisState) -> AnalysisState:
    result = run_fundamental_agent(state["symbol"])
    return {"fundamental": result}


def technical_node(state: AnalysisState) -> AnalysisState:
    result = run_technical_agent(state["symbol"])
    return {"technical": result}


def sentiment_node(state: AnalysisState) -> AnalysisState:
    result = run_sentiment_agent(state["symbol"])
    return {"sentiment": result}


def macro_node(state: AnalysisState) -> AnalysisState:
    result = run_macro_agent(
        state["symbol"],
        sector=state.get("sector", "IT")
    )
    return {"macro": result}


def risk_node(state: AnalysisState) -> AnalysisState:
    result = run_risk_agent(state["symbol"])
    return {"risk": result}


def writer_node(state: AnalysisState) -> AnalysisState:
    # writer runs after ALL other agents complete
    # receives their results from state
    report = run_writer_agent(
        symbol=state["symbol"],
        fundamental=state["fundamental"],
        technical=state["technical"],
        sentiment=state["sentiment"],
        macro=state["macro"],
        risk=state["risk"]
    )
    return {"report": report}


# ── Build the graph ───────────────────────────────────────────
def build_graph():
    graph = StateGraph(AnalysisState)

    # add all nodes
    graph.add_node("fundamental", fundamental_node)
    graph.add_node("technical",   technical_node)
    graph.add_node("sentiment",   sentiment_node)
    graph.add_node("macro",       macro_node)
    graph.add_node("risk",        risk_node)
    graph.add_node("writer",      writer_node)

    # phase 1 — all 5 agents run in parallel from START
    # LangGraph runs nodes with no dependencies simultaneously
    graph.set_entry_point("fundamental")
    graph.add_edge("__start__", "fundamental")
    graph.add_edge("__start__", "technical")
    graph.add_edge("__start__", "sentiment")
    graph.add_edge("__start__", "macro")
    graph.add_edge("__start__", "risk")

    # phase 2 — writer runs only after ALL 5 complete
    graph.add_edge("fundamental", "writer")
    graph.add_edge("technical",   "writer")
    graph.add_edge("sentiment",   "writer")
    graph.add_edge("macro",       "writer")
    graph.add_edge("risk",        "writer")

    # writer → end
    graph.add_edge("writer", END)

    return graph.compile()


def run_analysis(symbol: str, sector: str = "IT") -> dict:
    """
    Main entry point — runs complete analysis pipeline.
    
    Args:
        symbol: NSE stock symbol e.g. TCS, RELIANCE
        sector: Stock's sector for macro analysis
    
    Returns:
        Complete investment research report
    """
    print(f"\nStarting FinSightOS analysis for {symbol}...")
    print("="*50)

    graph = build_graph()

    # initial state
    initial_state = {
        "symbol": symbol,
        "sector": sector,
        "fundamental": {},
        "technical": {},
        "sentiment": {},
        "macro": {},
        "risk": {},
        "report": {},
        "error": ""
    }

    # run the graph
    final_state = graph.invoke(initial_state)
    return final_state["report"]


def print_report(report: dict):
    """Pretty print the final report."""
    print("\n" + "="*60)
    print(f"  FINSIGHTOS RESEARCH REPORT — {report.get('symbol')}")
    print("="*60)
    print(f"  Date:          {report.get('date')}")
    print(f"  Price:         ₹{report.get('current_price')}")
    print(f"  Overall Score: {report.get('overall_score')}/10")
    print(f"  Verdict:       {report.get('verdict_emoji')} {report.get('final_verdict')}")
    print("="*60)

    print("\n📋 EXECUTIVE SUMMARY")
    print(report.get('executive_summary'))

    print("\n📊 FUNDAMENTAL ANALYSIS")
    print(report.get('fundamental_section'))

    print("\n📈 TECHNICAL ANALYSIS")
    print(report.get('technical_section'))

    print("\n📰 SENTIMENT")
    print(report.get('sentiment_section'))

    print("\n🌍 MACRO ENVIRONMENT")
    print(report.get('macro_section'))

    print("\n⚠️  RISK ASSESSMENT")
    print(report.get('risk_section'))

    print("\n💡 INVESTMENT STRATEGY")
    strategy = report.get('investment_strategy', {})
    print(f"  Verdict:       {strategy.get('verdict')}")
    print(f"  Target Price:  ₹{strategy.get('target_price')}")
    print(f"  Entry Price:   ₹{strategy.get('entry_price')}")
    print(f"  Stop Loss:     ₹{strategy.get('stop_loss')}")
    print(f"  Time Horizon:  {strategy.get('time_horizon')}")
    print(f"  Position Size: {strategy.get('position_size')}")

    print("\n🚀 KEY CATALYSTS")
    for c in report.get('key_catalysts', []):
        print(f"  • {c}")

    print("\n🔴 RISKS TO WATCH")
    for r in report.get('key_risks_to_watch', []):
        print(f"  • {r}")

    print("\n" + "="*60)
    print(f"  ⚠️  {report.get('disclaimer')}")
    print("="*60)


if __name__ == "__main__":
    import time
    start = time.time()

    report = run_analysis("TCS", sector="IT")
    print_report(report)

    elapsed = round(time.time() - start, 1)
    print(f"\nTotal analysis time: {elapsed} seconds")