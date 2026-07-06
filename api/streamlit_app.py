import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
from datetime import date

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="FinSightOS",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .verdict-buy {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
    }
    .verdict-hold {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
    }
    .verdict-sell {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def api_get(endpoint: str) -> dict:
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=120)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def api_post(endpoint: str, data: dict) -> dict:
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=120)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# sidebar
st.sidebar.markdown("## 📈 FinSightOS")
st.sidebar.markdown("*AI Investment Research Platform*")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🔍 Stock Analysis", "💼 My Portfolio", "🌍 Market Overview"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Powered by:**")
st.sidebar.markdown("• LangGraph Multi-Agent")
st.sidebar.markdown("• Live NSE/BSE Data")
st.sidebar.markdown("• Groq Llama-3.3-70B")
st.sidebar.markdown("• RAG (Qdrant)")
st.sidebar.markdown("---")
st.sidebar.markdown("**Common NSE Symbols:**")
st.sidebar.code(
    "TCS, INFY, WIPRO, HCLTECH\n"
    "HDFCBANK, ICICIBANK, SBIN\n"
    "RELIANCE, ONGC, IOC\n"
    "MARUTI, TATAMOTORS, M&M\n"
    "BAJFINANCE, KOTAKBANK\n"
    "HINDUNILVR, ITC, NESTLEIND\n"
    "ETERNAL (Zomato), DMART\n"
    "ADANIENT, ADANIPORTS"
)
st.sidebar.caption("⚠️ For educational use only.")


# page 1 — stock analysis
if page == "🔍 Stock Analysis":
    st.markdown(
        '<div class="main-header">📈 FinSightOS Stock Analyzer</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        symbol = st.text_input(
            "Enter NSE Stock Symbol",
            placeholder="e.g. TCS, RELIANCE, HDFCBANK",
            help="Enter exact NSE symbol. Check sidebar for common symbols."
        ).upper().strip()

    with col2:
        sector = st.selectbox(
            "Sector",
            ["IT", "Banking", "Auto", "Pharma",
             "Energy", "FMCG", "Realty", "Metal", "NBFC", "Others"]
        )

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button(
            "🔍 Analyze Stock",
            type="primary",
            use_container_width=True
        )

    # live symbol validation
    if symbol and len(symbol) >= 2:
        check = api_get(f"/market/search/{symbol}")
        if check.get("success"):
            data = check.get("data", {})
            if data.get("valid"):
                st.success(
                    f"✅ Found: **{data['company_name']}** "
                    f"— Current Price: ₹{data['current_price']}"
                )
                # show quick price metrics
                price_data = api_get(f"/market/price/{symbol}")
                if price_data.get("success"):
                    d = price_data["data"]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Price", f"₹{d.get('current_price')}")
                    c2.metric("Day High", f"₹{d.get('day_high')}")
                    c3.metric("Day Low", f"₹{d.get('day_low')}")
                    c4.metric("52W High", f"₹{d.get('52_week_high')}")
            else:
                st.error(
                    f"❌ '{symbol}' not found on NSE. "
                    f"Check sidebar for correct symbols. "
                    f"Example: use **HDFCBANK** not HDFC"
                )

    # run full analysis
    if analyze_btn and symbol:
        with st.spinner(
            f"🤖 Running AI analysis for {symbol}... (~20 seconds)"
        ):
            result = api_post("/analyze", {
                "symbol": symbol,
                "sector": sector
            })

        if result.get("success"):
            report = result["data"]

            verdict = report.get("final_verdict", "")
            emoji = report.get("verdict_emoji", "")
            score = report.get("overall_score", 0)

            if "BUY" in verdict:
                css_class = "verdict-buy"
            elif "SELL" in verdict or "AVOID" in verdict:
                css_class = "verdict-sell"
            else:
                css_class = "verdict-hold"

            st.markdown(
                f'<div class="{css_class}">'
                f'{emoji} {verdict} — Score: {score}/10'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

            strategy = report.get("investment_strategy", {})
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Current Price", f"₹{report.get('current_price')}")
            m2.metric("Target Price", f"₹{strategy.get('target_price')}")
            m3.metric("Entry Price", f"₹{strategy.get('entry_price')}")
            m4.metric("Stop Loss", f"₹{strategy.get('stop_loss')}")
            m5.metric(
                "Horizon",
                strategy.get('time_horizon', 'N/A')[:10]
            )

            st.markdown("---")
            st.subheader("📋 Executive Summary")
            st.info(report.get("executive_summary"))

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Fundamental",
                "📈 Technical",
                "📰 Sentiment",
                "🌍 Macro",
                "⚠️ Risk"
            ])

            scores = report.get("agent_scores", {})

            with tab1:
                st.write(report.get("fundamental_section"))
                st.progress(
                    scores.get("fundamental", 5) / 10,
                    text=f"Fundamental Score: {scores.get('fundamental')}/10"
                )

            with tab2:
                st.write(report.get("technical_section"))
                st.progress(
                    scores.get("technical", 5) / 10,
                    text=f"Technical Score: {scores.get('technical')}/10"
                )

            with tab3:
                st.write(report.get("sentiment_section"))
                st.progress(
                    scores.get("sentiment", 5) / 10,
                    text=f"Sentiment Score: {scores.get('sentiment')}/10"
                )

            with tab4:
                st.write(report.get("macro_section"))
                st.progress(
                    scores.get("macro", 5) / 10,
                    text=f"Macro Score: {scores.get('macro')}/10"
                )

            with tab5:
                st.write(report.get("risk_section"))
                st.progress(
                    scores.get("risk", 5) / 10,
                    text=f"Risk Score: {scores.get('risk')}/10"
                )

            st.markdown("---")
            col_a, col_b = st.columns(2)

            with col_a:
                st.subheader("🚀 Key Catalysts")
                for c in report.get("key_catalysts", []):
                    st.success(f"✅ {c}")

            with col_b:
                st.subheader("🔴 Risks to Watch")
                for r in report.get("key_risks_to_watch", []):
                    st.error(f"⚠️ {r}")

            st.markdown("---")
            st.caption(f"⚠️ {report.get('disclaimer')}")

        else:
            st.error(
                f"Analysis failed: {result.get('detail', 'Unknown error')}"
            )

    elif analyze_btn and not symbol:
        st.warning("Please enter a stock symbol first.")


# page 2 — portfolio
elif page == "💼 My Portfolio":
    st.markdown(
        '<div class="main-header">💼 My Portfolio</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    with st.expander("➕ Add New Holding", expanded=False):
        with st.form("add_holding_form", clear_on_submit = True):
            col1, col2 = st.columns(2)
            with col1:
                new_symbol = st.text_input(
                    "Stock Symbol", placeholder="e.g. TCS"
                )
                new_qty = st.number_input(
                    "Quantity", min_value=1.0, value=10.0
                )
            with col2:
                new_price = st.number_input(
                    "Average Buy Price (₹)",
                    min_value=1.0, value=1000.0
                )
                new_date = st.date_input(
                    "Buy Date", value=date.today()
                )

            submitted = st.form_submit_button(
                "Add to Portfolio", type="primary"
            )

            if submitted and new_symbol:
                result = api_post("/portfolio/add", {
                    "symbol": new_symbol.upper(),
                    "quantity": new_qty,
                    "avg_buy_price": new_price,
                    "buy_date": str(new_date)
                })
                if result.get("success"):
                    st.success(
                        f"✅ {new_symbol.upper()} added successfully!"
                    )
                    st.rerun()
                else:
                    st.error("Failed to add holding")

    portfolio = api_get("/portfolio")

    if portfolio.get("success"):
        data = portfolio["data"]
        summary = data.get("portfolio_summary", {})

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "Total Invested",
            f"₹{summary.get('total_invested_inr', 0):,.0f}"
        )
        col2.metric(
            "Current Value",
            f"₹{summary.get('current_value_inr', 0):,.0f}"
        )
        pnl = summary.get('total_pnl_inr', 0)
        pnl_pct = summary.get('total_pnl_pct', 0)
        col3.metric(
            "Total P&L",
            f"₹{pnl:,.0f}",
            delta=f"{pnl_pct}%"
        )
        col4.metric("Status", summary.get('overall_status', 'N/A'))

        st.markdown("---")
        st.subheader("📋 Holdings")

        for h in data.get("holdings", []):
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
            col1.write(f"**{h['symbol']}**")
            col2.write(f"Qty: {h['quantity']}")
            col3.write(f"Buy: ₹{h['avg_buy_price']}")
            col4.write(f"Now: ₹{h['current_price']}")

            pnl_pct = h['pnl_pct']
            if pnl_pct >= 0:
                col5.success(
                    f"▲ {pnl_pct}% (₹{h['pnl_inr']:,.0f})"
                )
            else:
                col5.error(
                    f"▼ {pnl_pct}% (₹{h['pnl_inr']:,.0f})"
                )

        st.markdown("---")
        st.subheader("📊 Allocation")
        allocation = api_get("/portfolio/allocation")

        if allocation.get("success"):
            alloc_data = allocation["data"]
            col1, col2 = st.columns(2)

            with col1:
                st.write("**By Stock**")
                for s in alloc_data.get("stock_allocation", []):
                    st.write(
                        f"{s['symbol']}: **{s['allocation_pct']}%** "
                        f"— {s['concentration_risk']}"
                    )

            with col2:
                st.write("**By Sector**")
                for s in alloc_data.get("sector_allocation", []):
                    st.write(
                        f"{s['sector']}: **{s['allocation_pct']}%**"
                    )

            st.info(
                f"Diversification: {alloc_data.get('diversification')}"
            )


# page 3 — market overview
elif page == "🌍 Market Overview":
    st.markdown(
        '<div class="main-header">🌍 Indian Market Overview</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Nifty 50")
        nifty = api_get("/market/nifty")
        if nifty.get("success"):
            d = nifty["data"]
            st.metric(
                "Nifty 50",
                f"{d.get('current_level'):,.0f}",
                delta=f"{d.get('day_change_pct')}% today"
            )
            returns = d.get("returns", {})
            st.write(f"1 Month: **{returns.get('1_month_pct')}%**")
            st.write(f"3 Month: **{returns.get('3_month_pct')}%**")
            st.write(f"1 Year: **{returns.get('1_year_pct')}%**")

    with col2:
        st.subheader("🌍 Macro Snapshot")
        macro = api_get("/macro/summary")
        if macro.get("success"):
            snapshot = macro["data"].get("macro_snapshot", {})
            indicators = snapshot.get("indicators", {})
            rbi = indicators.get("rbi_policy", {})
            currency = indicators.get("currency", {})
            fii = indicators.get("institutional_flows", {})

            st.metric("Repo Rate", f"{rbi.get('repo_rate_pct')}%")
            st.metric("USD/INR", f"₹{currency.get('usdinr')}")
            st.write(f"RBI Trend: **{rbi.get('trend')}**")
            st.write(f"FII: **{fii.get('fii_trend')}**")
            st.info(f"Overall: {snapshot.get('overall_assessment')}")

    st.markdown("---")
    st.subheader("📈 Sector Performance (1 Month)")

    sectors = api_get("/market/sectors")
    if sectors.get("success"):
        cols = st.columns(4)
        for i, (name, data) in enumerate(sectors["data"].items()):
            with cols[i % 4]:
                ret = data.get("1_month_return_pct", 0)
                if ret >= 0:
                    st.success(f"**{name}**\n▲ {ret}%")
                else:
                    st.error(f"**{name}**\n▼ {ret}%")