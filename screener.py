# -*- coding: utf-8 -*-
"""
NSE + BSE Multibagger Screener v6.0 -- Streamlit Edition
Tab 1: Upstox Hub with Token Status
Tab 2: Database Tab populated with Sector Analytics and Plots
Tab 3: Momentum Strategy Hub with Priority Sorting & Ribbon Banners

INSTALL:  pip install streamlit requests numpy pandas yfinance plotly
RUN:      streamlit run screener_st.py
"""

import io, csv, gzip, json, math, time, datetime, sqlite3, threading, traceback
from pathlib import Path
from typing   import Optional

import requests
import numpy  as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===========================================================================
#  CONFIG & HARDCODED INDICES & SECTOR MAP
# ===========================================================================
UPSTOX_BASE  = "https://upstox.com"

# Hardcoded index asset mappings for standard and momentum scanning
INDICES_MAP = {
    "Nifty 50": "RELIANCE,TCS,HDFCBANK,ICICIBANK,INFY,BHARTIARTL,HINDUNILVR,ITC,SBI,LTIM,ADANIENT,ADANIPORTS,ASIANPAINT,AXISBANK,BAJAJ-AUTO,BAJFINANCE,BAJAJFINSV,BPCL,BRITANNIA,CIPLA,COALINDIA,DIVISLAB,DRREDDY,EICHERMOT,GRASIM,HCLTECH,HEROMOTOCO,HINDALCO,INDUSINDBK,JSWSTEEL,KOTAKBANK,LT,M&M,MARUTI,NESTLEIND,NTPC,ONGC,POWERGRID,SBILIFE,SUNPHARMA,TATACONSUM,TATAMOTORS,TATASTEEL,TECHM,TITAN,ULTRACEMCO,UPL,WIPRO,SHRIRAMFIN",
    
    "Bank Nifty": "HDFCBANK,ICICIBANK,SBI,AXISBANK,KOTAKBANK,INDUSINDBK,PNB,FEDERALBNK,BANKBARODA,IDFCFIRSTB,AUBANK,CANBK",
    
    "Fin Nifty": "HDFCBANK,ICICIBANK,AXISBANK,KOTAKBANK,SBI,BAJFINANCE,BAJAJFINSV,CHOLAFIN,HDFCLIFE,SBILIFE,RECLTD,PFC,SHRIRAMFIN,MUTHOOTFIN,ICICIGI,ICICIPRULI,SBICARD,HDFCAMC,LICHSGFIN",
    
    "Sensex": "RELIANCE,HDFCBANK,TCS,ICICIBANK,INFY,ITC,BHARTIARTL,HINDUNILVR,SBI,LT,AXISBANK,KOTAKBANK,M&M,HCLTECH,BAJFINANCE,SUNPHARMA,MARUTI,TATAMOTORS,NTPC,ASIANPAINT,TITAN,ULTRACEMCO,POWERGRID,BAJAJFINSV,JSWSTEEL,TATASTEEL,TECHM,BAJAJ-AUTO,INDUSINDBK,NESTLEIND"
}

# Fallback mapping to populate Tab 2 cleanly
SECTOR_MAP = {
    # Financials
    "HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", "SBI": "Financial Services", 
    "AXISBANK": "Financial Services", "KOTAKBANK": "Financial Services", "BAJFINANCE": "Financial Services",
    "BAJAJFINSV": "Financial Services", "INDUSINDBK": "Financial Services", "SBILIFE": "Financial Services",
    "SHRIRAMFIN": "Financial Services", "PNB": "Financial Services", "FEDERALBNK": "Financial Services",
    "BANKBARODA": "Financial Services", "IDFCFIRSTB": "Financial Services", "AUBANK": "Financial Services",
    "CHOLAFIN": "Financial Services", "HDFCLIFE": "Financial Services", "RECLTD": "Financial Services",
    "PFC": "Financial Services", "MUTHOOTFIN": "Financial Services", "LICHSGFIN": "Financial Services",
    # IT
    "TCS": "IT", "INFY": "IT", "HCLTECH": "IT", "TECHM": "IT", "WIPRO": "IT", "LTIM": "IT",
    # Energy / Oil & Gas
    "RELIANCE": "Energy / Oil & Gas", "ONGC": "Energy / Oil & Gas", "BPCL": "Energy / Oil & Gas", 
    "NTPC": "Power", "POWERGRID": "Power",
    # FMCG
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG", "TATACONSUM": "FMCG",
    # Auto
    "TATAMOTORS": "Automobile", "M&M": "Automobile", "MARUTI": "Automobile", "BAJAJ-AUTO": "Automobile",
    "EICHERMOT": "Automobile", "HEROMOTOCO": "Automobile",
    # Pharma
    "SUNPHARMA": "Pharma / Healthcare", "CIPLA": "Pharma / Healthcare", "DRREDDY": "Pharma / Healthcare",
    "DIVISLAB": "Pharma / Healthcare", "APOLLOHOSP": "Pharma / Healthcare",
    # Metals & Mining
    "TATASTEEL": "Metals & Mining", "JSWSTEEL": "Metals & Mining", "HINDALCO": "Metals & Mining",
    "COALINDIA": "Metals & Mining", "ADANIENT": "Conglomerates",
    # Construction / Infrastructure
    "LT": "Infrastructure", "ADANIPORTS": "Infrastructure",
    # Consumer Durables / Others
    "TITAN": "Consumer Durables", "ASIANPAINT": "Paints", "ULTRACEMCO": "Cement", "GRASIM": "Cement"
}

# ===========================================================================
#  PAGE SETUP & CSS STYLING
# ===========================================================================
st.set_page_config(page_title="NSE+BSE Screener", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://googleapis.com');
:root{
  --bg:#0a0d14;--surf:#0f1320;--card:#131928;--card2:#181f2e;
  --border:#1e2740;--border2:#253050;
  --sky:#38bdf8;--sage:#34d399;--amber:#fbbf24;--coral:#f87171;
  --lav:#a78bfa;--tang:#fb923c;
  --t1:#f0f4ff;--t2:#a8b4cc;--t3:#5c6a88;--t4:#2e3a52;
  --sans:'DM Sans',system-ui,sans-serif;
  --mono:'JetBrains Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{
  background:var(--bg)!important;color:var(--t2)!important;font-family:var(--sans)!important;}
[data-testid="stSidebar"]{background:#0c1018!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebar"] *{color:var(--t2)!important;}
.stButton>button{background:linear-gradient(135deg,#1a3a6e,#0e2350)!important;
  color:var(--sky)!important;border:1px solid rgba(56,189,248,.3)!important;
  border-radius:8px!important;font-family:var(--sans)!important;font-weight:600!important;transition:all .18s!important;}
.stButton>button:hover{background:linear-gradient(135deg,#1e4a8a,#1432a0)!important;
  box-shadow:0 4px 20px rgba(56,189,248,.2)!important;transform:translateY(-1px)!important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{
  background:#131928!important;border:1px solid #253050!important;color:var(--t1)!important;
  border-radius:7px!important;font-family:var(--mono)!important;}
.stSelectbox>div>div{background:#131928!important;border-color:#253050!important;}
.stTabs [role="tablist"]{background:#0f1320;border:1px solid #1e2740;border-radius:10px;padding:3px;}
.stTabs [role="tab"]{color:#5c6a88!important;border-radius:7px!important;font-family:var(--sans)!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{background:#131928!important;color:var(--sky)!important;}
.stProgress>div>div{background:linear-gradient(90deg,var(--sky),var(--sage))!important;}
#MainMenu,footer,header{visibility:hidden!important;}

.hdr{background:linear-gradient(135deg,#0e1525,#131928);border:1px solid #1e2740;
  border-radius:12px;padding:20px 26px 16px;margin-bottom:18px;position:relative;overflow:hidden;}
.hdr::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--sky) 30%,var(--sage) 65%,var(--amber) 88%,transparent);}
.hdr h1{font-weight:700;font-size:1.5rem;color:var(--t1);letter-spacing:-.3px;}
.hdr .sub{font-family:var(--mono);font-size:.6rem;color:var(--t3);margin-top:5px;letter-spacing:.8px;}
.slbl{font-family:var(--mono);font-size:.58rem;letter-spacing:2px;text-transform:uppercase;
  color:var(--sky);border-left:2px solid var(--sky);padding-left:8px;margin:14px 0 9px;}
.kpis{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;}
.kpi{flex:1;min-width:90px;background:var(--card);border:1px solid var(--border);
  border-radius:10px;padding:12px 14px;text-align:center;}
.kpi .v{font-family:var(--mono);font-weight:700;font-size:1.6rem;line-height:1;}
.kpi .l{font-size:.56rem;color:var(--t3);text-transform:uppercase;letter-spacing:1px;margin-top:4px;}
.csky{color:var(--sky);}.csage{color:var(--sage);}.camb{color:var(--amber);}

/* Cards & Banner Layouts */
.scard{background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:14px 16px;margin-bottom:8px;position:relative;}
.scard.hit{background:linear-gradient(160deg,#0f1d14,var(--card));border-color:rgba(52,211,153,.3);}
.scard .ch{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;}
.scard .sym{font-weight:700;font-size:1rem;color:var(--t1);}
.scard .live-px{font-family:var(--mono);font-weight:700;font-size:1.05rem;color:var(--sage);margin-left:auto;}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:5px;margin:10px 0;}
.met{background:var(--card2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;}
.met .ml{font-size:.55rem;color:var(--t4);text-transform:uppercase;letter-spacing:.8px;}
.met .mv{font-size:.84rem;font-weight:600;color:var(--t1);font-family:var(--mono);margin-top:2px;}

/* Glow Banner */
.ribbon{
  position:absolute;top:10px;right:10px;
  background:linear-gradient(90deg, #10b981, #059669);
  color:#fff;font-family:var(--mono);font-size:0.55rem;font-weight:700;
  padding:3px 8px;border-radius:4px;letter-spacing:1px;
  box-shadow:0 0 10px rgba(16,185,129,0.3);
}
</style>
""", unsafe_allow_html=True)

# ===========================================================================
#  LOGIC HANDLERS
# ===========================================================================

def check_upstox_token(token: str) -> bool:
    """Verifies Upstox Token validity by pinging the profile endpoint."""
    if not token:
        return False
    url = f"{UPSTOX_BASE}/user/profile"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def analyze_momentum_setup(symbol: str, exchange: str = "NSE") -> dict:
    """Calculates price technicals and pulls rough fundamentals safely using yfinance."""
    yf_symbol = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
    sector_str = SECTOR_MAP.get(symbol, "Other / Diversified")
    
    res = {
        "symbol": symbol, "live_px": 0.0, "ema_21": 0.0, 
        "eps_accel": "No Data", "surprise": "No Data", 
        "rs_resilient": False, "buy_zone": False, "sector": sector_str
    }
    
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="1y")
        if hist.empty:
            return res
            
        close_px = hist['Close'].iloc[-1]
        res["live_px"] = round(close_px, 2)
        
        # 21 EMA & Buy Zone (within 2.5% boundary)
        hist['21EMA'] = hist['Close'].ewm(span=21, adjust=False).mean()
        ema_21 = hist['21EMA'].iloc[-1]
        res["ema_21"] = round(ema_21, 2)
        res["buy_zone"] = close_px > ema_21 and close_px < (ema_21 * 1.025)
        
        # RS Resilience
        wh_52 = hist['Close'].max()
        res["rs_resilient"] = (close_px / wh_52) >= 0.85
        
        # Fundamental Fallback
        info = stock.info
        if "forwardEps" in info and "trailingEps" in info:
            if info["forwardEps"] is not None and info["trailingEps"] is not None:
                res["eps_accel"] = "✅ Yes" if info["forwardEps"] > info["trailingEps"] else "❌ No"
                res["surprise"] = "Checked"
            
    except Exception:
        pass
        
    return res

# ===========================================================================
#  MAIN APP LAYOUT
# ===========================================================================

def main():
    if 'scanned_df' not in st.session_state:
        st.session_state['scanned_df'] = pd.DataFrame()

    st.markdown("""
    <div class='hdr'>
        <h1>NSE + BSE Multibagger Screener</h1>
        <div class='sub'>V6.0 • HARDCODED INDEX MULTI-SCANNER</div>
    </div>
    """, unsafe_allow_html=True)

    tab_screener, tab_db, tab_momentum = st.tabs(["Screener", "Database", "Momentum Strategy"])

    # --- TAB 1: SCREENER ---
    with tab_screener:
        st.markdown("<div class='slbl'>Upstox API Authentication</div>", unsafe_allow_html=True)
        if 'upstox_token' not in st.session_state:
            st.session_state['upstox_token'] = ""
            
        token_input = st.text_input("Enter Upstox Access Token", value=st.session_state['upstox_token'], type="password")
        
        if token_input:
            st.session_state['upstox_token'] = token_input
            is_valid = check_upstox_token(token_input)
            if is_valid:
                st.success("Upstox Status: Connected successfully! Active token loaded.")
            else:
                st.error("Upstox Status: Disconnected. Invalid or expired token.")
        else:
            st.warning("Upstox Status: Disconnected. Waiting for token input.")
            
        st.markdown("<div class='slbl'>Market Scanner Control</div>", unsafe_allow_html=True)
        st.caption("Standard instrument operations. Switch to Tab 3 for heavily analyzed Momentum screening.")

    # --- TAB 2: DATABASE ---
    with tab_db:
        st.markdown("<div class='slbl'>Database & Sector Analytics</div>", unsafe_allow_html=True)
        
        if st.session_state['scanned_df'].empty:
            st.info("No scan data available yet. Please run a 'Momentum Scan' on Tab 3 to populate this view.")
        else:
            df_full = st.session_state['scanned_df']
            sector_counts = df_full['Sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Count']
            
            fig = go.Figure(data=[go.Bar(
                x=sector_counts['Sector'],
                y=sector_counts['Count'],
                marker_color='#38bdf8',
                text=sector_counts['Count'],
                textposition='auto',
            )])
            
            fig.update_layout(
                title="<b>Volume of Scanned Stocks by Sector</b>",
                title_font=dict(color="#f0f4ff", family="'DM Sans', sans-serif"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a8b4cc', family="'DM Sans', sans-serif"),
                xaxis=dict(gridcolor='#1e2740'),
                yaxis=dict(gridcolor='#1e2740'),
                height=350,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("<div class='slbl'>Scanned Portfolio Data (Sorted by Sector)</div>", unsafe_allow_html=True)
            sorted_df = df_full.sort_values(by='Sector').reset_index(drop=True)
            
            st.dataframe(
                sorted_df.style.map(
                    lambda v: 'color: #34d399; font-weight: bold;' if v in ['🔥 HIT', '✅ YES'] else '',
                    subset=["21MA BUY ZONE", "RS RESILIENT"]
                ),
                use_container_width=True
            )

    # --- TAB 3: MOMENTUM STRATEGY HUB ---
    with tab_momentum:
        st.markdown("<div class='slbl'>Momentum Strategy Hub</div>", unsafe_allow_html=True)
        st.caption("Candidates matching all criteria will be prioritized at the top with a ribbon banner.")
        
        indices_list = list(INDICES_MAP.keys())
        indices_list.insert(0, "All Indices (Mass Scan)")
        selected_index = st.selectbox("Select Target Index to Scan", indices_list)
        
        if selected_index == "All Indices (Mass Scan)":
            all_assets = []
            for k, v in INDICES_MAP.items():
                all_assets.extend(v.split(","))
            unique_assets = list(set(all_assets))
            loaded_tickers = ",".join(unique_assets)
        else:
            loaded_tickers = INDICES_MAP[selected_index]
            
        m_tickers = st.text_area("Asset Pool Mapping (Editable):", loaded_tickers, height=120)
        
        default_exch = "BSE" if selected_index == "Sensex" else "NSE"
        col1, col2 = st.columns(2)
        with col1:
            m_exch = st.selectbox("Source Route", ["NSE", "BSE"], index=0 if default_exch == "NSE" else 1)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            scan_clicked = st.button("🔥 Run Momentum Scan")

        if scan_clicked:
            tickers_list = [x.strip().upper() for x in m_tickers.replace('\n', ',').split(",") if x.strip()]
            
            if not tickers_list:
                st.error("No valid ticker payload found.")
                return
                
            st.write(f"Routing processing requests for {len(tickers_list)} chain targets...")
            
            prog_bar = st.progress(0.0)
            status_text = st.empty()
            momentum_results = []
            
            tab2_symbols, tab2_prices, tab2_sectors, tab2_zones, tab2_res = [], [], [], [], []
            
            for idx, ticker in enumerate(tickers_list):
                status_text.text(f"Fetching structural tape: {ticker}...")
                m_data = analyze_momentum_setup(ticker, m_exch)
                momentum_results.append(m_data)
                
                if m_data["live_px"] != 0.0:
                    tab2_symbols.append(ticker)
                    tab2_prices.append(f"₹{m_data['live_px']}")
                    tab2_sectors.append(m_data['sector'])
                    tab2_zones.append('🔥 HIT' if m_data['buy_zone'] else '❌ OUTSIDE')
                    tab2_res.append('✅ YES' if m_data['rs_resilient'] else '❌ NO')
                
                prog_bar.progress((idx + 1) / len(tickers_list))
                
            status_text.success("Scan network execution finished!")
            
            st.session_state['scanned_df'] = pd.DataFrame({
                "Symbol": tab2_symbols,
                "Sector": tab2_sectors,
                "Price": tab2_prices,
                "21MA BUY ZONE": tab2_zones,
                "RS RESILIENT": tab2_res
            })
            
            # Divide stocks into hits and others
            perfect_hits = []
            other_results = []
            
            for r in momentum_results:
                if r["live_px"] == 0.0:
                    continue
                if r["rs_resilient"] and r["buy_zone"]:
                    perfect_hits.append(r)
                else:
                    other_results.append(r)
            
            st.markdown("<div class='slbl'>Outcome Matrix (Qualified Fits Priority)</div>", unsafe_allow_html=True)
            
            # Display perfect hits with the green ribbon banner first
            for r in perfect_hits:
                st.markdown(f"""
                <div class="scard hit">
                    <div class="ribbon">🔥 MOMENTUM PICK</div>
                    <div class="ch">
                        <div class="sym">{r['symbol']}</div>
                        <div class="live-px">₹{r['live_px']}</div>
                    </div>
                    <div class="mgrid">
                        <div class="met"><div class="ml">EPS ACCEL</div><div class="mv">{r['eps_accel']}</div></div>
                        <div class="met"><div class="ml">SURPRISE</div><div class="mv">{r['surprise']}</div></div>
                        <div class="met"><div class="ml">RS RESILIENT</div><div class="mv">✅ YES</div></div>
                        <div class="met"><div class="ml">21MA BUY ZONE</div><div class="mv">🔥 HIT</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display the rest of the list without the banner
            for r in other_results:
                st.markdown(f"""
                <div class="scard">
                    <div class="ch">
                        <div class="sym">{r['symbol']}</div>
                        <div class="live-px">₹{r['live_px']}</div>
                    </div>
                    <div class="mgrid">
                        <div class="met"><div class="ml">EPS ACCEL</div><div class="mv">{r['eps_accel']}</div></div>
                        <div class="met"><div class="ml">SURPRISE</div><div class="mv">{r['surprise']}</div></div>
                        <div class="met"><div class="ml">RS RESILIENT</div><div class="mv">{'✅ YES' if r['rs_resilient'] else '❌ NO'}</div></div>
                        <div class="met"><div class="ml">21MA BUY ZONE</div><div class="mv">{'🔥 HIT' if r['buy_zone'] else '❌ OUTSIDE'}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<div class='slbl'>Active Telemetry</div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='kpis'>
                <div class='kpi'><div class='v csky'>{len(tickers_list)}</div><div class='l'>Tracked</div></div>
                <div class='kpi'><div class='v csage'>{len(perfect_hits)}</div><div class='l'>Strong Filters</div></div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
