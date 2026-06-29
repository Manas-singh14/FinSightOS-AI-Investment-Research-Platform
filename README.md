# 🏦 FinSightOS — AI Investment Research Platform

<div align="center">

![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blue?style=for-the-badge)
![Market](https://img.shields.io/badge/Market-NSE%20%2F%20BSE-green?style=for-the-badge)
![LLM](https://img.shields.io/badge/LLM-Fine--tuned%20Mistral--7B-purple?style=for-the-badge)

**Ask "Should I buy RELIANCE?" — get a complete investment research report in 90 seconds.**

Powered by 7 specialized AI agents, 6 MCP servers, and a fine-tuned financial LLM.

</div>

---

## 🎯 What It Does

A user types: *"Should I increase my position in TCS given current market conditions?"*

FinSightOS responds with a complete investment memo covering:
- Fundamental analysis (DCF valuation, peer comparison)
- Technical analysis (RSI, MACD, moving averages)
- News sentiment (LLM-powered, not keyword counting)
- Macro environment (RBI rates, FII flows, USD/INR)
- Risk assessment (Beta, Sharpe ratio, VaR, drawdown)
- Final verdict: **Buy / Accumulate / Hold / Avoid**

---

## 🏗️ Architecture

```
User Query
    ↓
FastAPI Backend
    ↓
LangGraph Orchestrator
    ↓
┌─────────────────────────────────────────┐
│         6 Agents (parallel)             │
│                                         │
│  Fundamental  Technical  Sentiment      │
│  Agent        Agent      Agent          │
│                                         │
│  Macro        Risk       Writer         │
│  Agent        Agent      Agent          │
└─────────────────────────────────────────┘
    ↓
6 MCP Servers fetch live data
    ↓
Fine-tuned Mistral-7B analyzes data
    ↓
Final Investment Report
```

---

## 🤖 The 7 Agents

| Agent | What it does | Model used |
|---|---|---|
| Fundamental Agent | DCF valuation, peer comparison, financial ratios | Fine-tuned Mistral-7B |
| Technical Agent | RSI, MACD, moving averages, volume analysis | Fine-tuned Mistral-7B |
| Sentiment Agent | News sentiment from 10+ articles per stock | Fine-tuned Mistral-7B |
| Macro Agent | RBI rates, FII flows, GDP, inflation impact | Fine-tuned Mistral-7B |
| Risk Agent | Beta, Sharpe ratio, VaR, max drawdown | Fine-tuned Mistral-7B |
| Competitor Agent | Relative valuation vs sector peers | Fine-tuned Mistral-7B |
| Writer Agent | Produces final 8-section research report | Groq Llama-3.3-70B |

---

## 🔌 The 6 MCP Servers

| Server | Tools | Data Source |
|---|---|---|
| `market_server` | 7 tools | yfinance — NSE/BSE live prices, fundamentals |
| `news_server` | 5 tools | Google News RSS + Groq LLM sentiment |
| `macro_server` | 6 tools | World Bank API, RBI data, NSE FII/DII flows |
| `calculator_server` | 5 tools | DCF, RSI, MACD, Sharpe, VaR, SIP (CFA-standard) |
| `portfolio_server` | 5 tools | PostgreSQL — user holdings, P&L (coming soon) |
| `filing_server` | 4 tools | BSE corporate announcements (coming soon) |

---

## 📊 Financial Calculations (Industry Standard)

All formulas follow CFA Institute curriculum and industry standards:

| Calculation | Formula | Industry Use |
|---|---|---|
| RSI | Wilder 1978 formula, 14-day | Bloomberg, Zerodha Kite |
| MACD | 12-26-9 Appel parameters | TradingView, Upstox |
| DCF | CFA Level 2 standard | Investment banking |
| Beta | CAPM (Nobel Prize 1990) | All mutual fund factsheets |
| Sharpe Ratio | Nobel Prize 1990, SEBI mandated | All SEBI-registered funds |
| VaR 95% | JP Morgan RiskMetrics 1994 | Basel III banking regulation |
| SIP Returns | Standard annuity formula | AMFI, Groww, Paytm Money |

---

## 🧠 Fine-tuned Model

Base model: **Mistral-7B**
Training data: **FinQA + ConvFinQA** (financial Q&A on earnings reports)
Method: **QLoRA** (4-bit NF4, r=16, same approach as MedQA project)
Benchmark: **FinanceBench** (same benchmark as BloombergGPT)
Status: **Training in progress**

```python
# Agents use fine-tuned model for financial reasoning
client = InferenceClient(
    model="Singhmanas14/finsight-mistral-finetuned"
)
```

---

## 🗂️ Project Structure

```
FinSightOS/
├── agents/
│   ├── fundamental_agent.py
│   ├── technical_agent.py
│   ├── sentiment_agent.py
│   ├── macro_agent.py
│   ├── risk_agent.py
│   └── writer_agent.py
├── mcp_servers/
│   ├── market_server.py      ✅ Complete
│   ├── news_server.py        ✅ Complete
│   ├── macro_server.py       ✅ Complete
│   ├── calculator_server.py  ✅ Complete
│   ├── portfolio_server.py   🔄 In progress
│   └── filing_server.py      🔄 In progress
├── rag/
│   ├── pipeline.py           🔄 In progress
│   ├── retriever.py          🔄 In progress
│   └── reranker.py           🔄 In progress
├── graph/
│   └── orchestrator.py       🔄 In progress
├── api/
│   └── main.py               🔄 In progress
├── docker-compose.yml        ✅ Complete
└── requirements.txt          ✅ Complete
```

---

## ⚡ Tech Stack

| Layer | Technology |
|---|---|
| Fine-tuned LLM | Mistral-7B on FinQA (QLoRA) |
| General LLM | Groq Llama-3.3-70B (free) |
| Orchestration | LangGraph |
| RAG | Qdrant + all-MiniLM-L6-v2 + Cohere reranking |
| MCP Transport | FastMCP (stdio) |
| Database | PostgreSQL 16 |
| Cache | Redis |
| Backend | FastAPI |
| Frontend | Streamlit |
| Observability | LangSmith |
| Containerization | Docker Compose |

---

## 📈 Live Data Sources (All Free)

| Data | Source | Coverage |
|---|---|---|
| Stock prices | yfinance (.NS/.BO suffix) | All NSE/BSE stocks |
| News & sentiment | Google News RSS + Groq LLM | All Indian financial news |
| GDP & inflation | World Bank API | Annual India macro data |
| Repo rate | RBI (hardcoded, updated after MPC) | Updated 6x/year |
| FII/DII flows | NSE India API | Daily institutional flows |
| USD/INR rate | yfinance (USDINR=X) | Real-time |
| Sector indices | yfinance (^CNXIT, ^NSEBANK etc) | 8 major sectors |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/Singhmanas14/FinSightOS
cd FinSightOS

# Start infrastructure
docker-compose up -d

# Install dependencies
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Test MCP servers
python scripts/test_market_server.py
python scripts/test_news_server.py
python scripts/test_macro_server.py
python scripts/test_calculator_server.py
```

---

## 📋 Development Roadmap

- [x] Project setup and Docker infrastructure
- [x] Market MCP Server (live NSE/BSE data)
- [x] News MCP Server (Google News + LLM sentiment)
- [x] Macro MCP Server (RBI, World Bank, FII flows)
- [x] Calculator MCP Server (DCF, RSI, MACD, risk metrics)
- [ ] Portfolio MCP Server
- [ ] Filing MCP Server
- [ ] RAG pipeline (Qdrant + hybrid search)
- [ ] 6 AI Agents with LangGraph orchestration
- [ ] Fine-tune Mistral-7B on FinQA dataset
- [ ] FastAPI backend
- [ ] Streamlit frontend
- [ ] End-to-end testing and deployment

---

## ⚠️ Disclaimer

This system is for **educational and research purposes only**.
Not financial advice. Always consult a SEBI-registered advisor
before making investment decisions.

---

<div align="center">
Built by <a href="https://huggingface.co/Singhmanas14">Singhmanas14</a> | IIIT Lucknow
</div>
