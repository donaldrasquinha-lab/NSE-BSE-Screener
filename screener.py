# -*- coding: utf-8 -*-
"""
NSE + BSE Multibagger Screener v6.0 -- Streamlit Edition
Tab 1: Live Cloud Sync for All Equities (Calculates EPS, RS, 21MA)
Tab 2: Master Ledger Database + Interactive Sector Distribution
Tab 3: Clustered Momentum Results Grid

INSTALL:  pip install streamlit requests numpy pandas yfinance plotly
RUN:      streamlit run screener_st.py
"""

import io
import requests
import numpy  as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ===========================================================================
#  CONFIG & CONSTANTS
# ===========================================================================
UPSTOX_BASE  = "https://api.upstox.com/v2"

# Direct URL to parse equities safely without CDN gzip restrictions
UPSTOX_DIRECT_URL = "https://api.upstox.com/v2"

# Fallback mapping to populate clean sectors for known top assets
SECTOR_MAP = {
    "HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", "SBI": "Financial Services", 
    "AXISBANK": "Financial Services", "KOTAKBANK": "Financial Services", "BAJFINANCE": "Financial Services",
    "BAJAJFINSV": "Financial Services", "TCS": "IT", "INFY": "IT", "HCLTECH": "IT", "TECHM": "IT", "WIPRO": "IT", 
    "RELIANCE": "Energy / Oil & Gas", "HINDUNILVR": "FMCG", "ITC": "FMCG", "TATAMOTORS": "Automobile", 
    "M&M": "Automobile", "SUNPHARMA": "Pharma / Healthcare", "TITAN": "Consumer Durables"
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

.ribbon{
  position:absolute;top:10px;right:10px;
  background:linear-gradient(90deg, #10b981, #059669);
  color:#fff;font-family:var(--mono);font-size:0.55rem;font-weight:700;
  padding:3px 8px;border-radius:4px;letter-spacing:1px;
  box-shadow:0 0 10px rgba(16,185,129,0.3);
}
.group-header {
  font-family: var(--sans); font-size: 1.1rem; font-weight: 700; color: #fff;
  margin: 15px 0 10px 0; border-bottom: 1px solid var(--border); padding-bottom: 5px;
}
</style>
""", unsafe_allow_html=True)

# ===========================================================================
#  LOGIC HANDLERS
# ===========================================================================

def check_upstox_token(token: str) -> bool:
    """Verifies Upstox Token validity using the strict v2 profile endpoint."""
    clean_token = token.strip() if token else ""
    if not clean_token:
        return False
    url = f"{UPSTOX_BASE}/user/profile"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {clean_token}', 'Api-Version': '2.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def calculate_momentum_node(symbol: str, exchange: str) -> dict:
    """Calculates price technicals and pulls rough fundamentals safely using yfinance."""
    yf_symbol = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
    res = {
        "Symbol": symbol, "Live Price": 0.0, "EPS Accel": "No Data", 
        "RS Resilient": "❌ NO", "21MA Buy Zone": "❌ OUTSIDE", "Sector": SECTOR_MAP.get(symbol, "Other")
    }
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="1y")
        if hist.empty:
            return res
            
        close_px = hist['Close'].iloc[-1]
        res["Live Price"] = round(close_px, 2)
        
        # 21 EMA Boundary check
        hist['21EMA'] = hist['Close'].ewm(span=21, adjust=False).mean()
        ema_21 = hist['21EMA'].iloc[-1]
        if close_px > ema_21 and close_px < (ema_21 * 1.025):
            res["21MA Buy Zone"] = "🔥 HIT"
            
        # RS Resilience (Top 15% of 52-week range)
        wh_52 = hist['Close'].max()
        if (close_px / wh_52) >= 0.85:
            res["RS Resilient"] = "✅ YES"
            
        # Fundamental Fallback
        info = stock.info
        if "forwardEps" in info and "trailingEps" in info:
            if info["forwardEps"] is not None and info["trailingEps"] is not None:
                res["EPS Accel"] = "✅ Yes" if info["forwardEps"] > info["trailingEps"] else "❌ No"
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
        <div class='sub'>V6.0 • REAL-TIME DATA PROCESSING ENGINE</div>
    </div>
    """, unsafe_allow_html=True)

    tab_screener, tab_db, tab_momentum = st.tabs(["Screener", "Database", "Momentum Strategy"])

    # --- TAB 1: SCREENER ---
    with tab_screener:
        st.markdown("<div class='slbl'>Upstox API Authentication (v2)</div>", unsafe_allow_html=True)
        if 'upstox_token' not in st.session_state:
            st.session_state['upstox_token'] = ""
            
        token_input = st.text_input("Enter Upstox Access Token", value=st.session_state['upstox_token'], type="password")
        
        if token_input:
            st.session_state['upstox_token'] = token_input
            if check_upstox_token(token_input):
                st.success("Upstox Status: Connected successfully!")
            else:
                st.error("Upstox Status: Disconnected. Invalid token.")
        else:
            st.warning("Upstox Status: Disconnected. Waiting for token input.")
            
        st.markdown("<div class='slbl'>Heavy Cloud Scan Extractor</div>", unsafe_allow_html=True)
        st.caption("Pulls the raw list from Upstox and builds Sectors, EPS, RS, and 21MA metrics for the scanner.")
        
        if st.button("🛰️ Pull & Process All Equities from Upstox"):
            try:
                with st.spinner("Downloading live symbol tapes from Upstox..."):
                    # Uses explicit User-Agent to stop Upstox CDN from returning JSON errors
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                    response = requests.get(UPSTOX_DIRECT_URL, headers=headers, timeout=15)
                    
                    if response.status_code != 200:
                        st.error(f"Failed to fetch data. Upstox server returned status {response.status_code}.")
                        return
                    
                    # Decodes direct CSV payload
                    df = pd.read_csv(io.StringIO(response.text))
                
                # Filter solely for cash shares
                df_filtered = df[(df['instrument_type'] == 'EQUITY')]
                unique_assets = df_filtered['tradingsymbol'].unique()
                
                # Capped limit to prevent execution timeouts
                cap_limit = 100
                st.info(f"Retrieved {len(unique_assets)} targets. Processing top {cap_limit} to prevent server freeze...")
                
                prog_bar = st.progress(0.0)
                status_box = st.empty()
                processed_results = []
                
                for idx, symbol in enumerate(unique_assets[:cap_limit]):
                    status_box.text(f"Extracting Tape + Technicals: {symbol}")
                    
                    # Assume NSE primarily, or detect dynamically
                    data_node = calculate_momentum_node(symbol, "NSE")
                    processed_results.append(data_node)
                    
                    prog_bar.progress((idx + 1) / cap_limit)
                    
                status_box.success("Execution boundary finished!")
                
                st.session_state['scanned_df'] = pd.DataFrame(processed_results)
                st.info("Heavy parameters extracted! Full table loaded to Tab 2 Database.")
                
            except Exception as e:
                st.error(f"Execution failed at the fetch boundary. Error: {e}")

    # --- TAB 2: DATABASE ---
    with tab_db:
        st.markdown("<div class='slbl'>Database Grid</div>", unsafe_allow_html=True)
        
        if st.session_state['scanned_df'].empty:
            st.info("No scanned assets in registry. Go to Tab 1 and click the 'Pull & Process' button.")
        else:
            df_full = st.session_state['scanned_df']
            
            sector_counts = df_full['Sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Count']
            fig = go.Figure(data=[go.Bar(
                x=sector_counts['Sector'], y=sector_counts['Count'],
                marker_color='#38bdf8', text=sector_counts['Count'], textposition='auto',
            )])
            fig.update_layout(
                title="<b>Scanned File Distribution by Sector</b>", title_font=dict(color="#f0f4ff"),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a8b4cc'), xaxis=dict(gridcolor='#1e2740'), yaxis=dict(gridcolor='#1e2740'),
                height=300, margin=dict(l=10, r=10, t=50, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("<div class='slbl'>Extracted Master Stock List (Sorted by Sector)</div>", unsafe_allow_html=True)
            st.dataframe(
                df_full.sort_values(by='Sector').reset_index(drop=True).style.map(
                    lambda v: 'color: #34d399; font-weight: bold;' if v in ['🔥 HIT', '✅ Yes', '✅ YES'] else '',
                    subset=["21MA Buy Zone", "RS Resilient", "EPS Accel"]
                ), use_container_width=True
            )

    # --- TAB 3: MOMENTUM STRATEGY HUB ---
    with tab_momentum:
        st.markdown("<div class='slbl'>Momentum Strategy Hub</div>", unsafe_allow_html=True)
        st.caption("Pulls directly from the master database to cluster your high-potential targets.")
        
        if st.session_state['scanned_df'].empty:
            st.info("Database empty. You must process stocks on Tab 1 first.")
        else:
            df_full = st.session_state['scanned_df']
            
            perfect_hits = df_full[(df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT')].to_dict('records')
            other_results = df_full[~((df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT'))].to_dict('records')
            
            st.markdown("<div class='group-header'>🔥 Group 1: Perfect Momentum Picks</div>", unsafe_allow_html=True)
            if perfect_hits:
                for r in perfect_hits:
                    st.markdown(f"""
                    <div class="scard hit">
                        <div class="ribbon">🔥 MOMENTUM PICK</div>
                        <div class="ch"><div class="sym">{r['Symbol']}</div><div class="live-px">₹{r['Live Price']}</div></div>
                        <div class="mgrid">
                            <div class="met"><div class="ml">EPS ACCEL</div><div class="mv">{r['EPS Accel']}</div></div>
                            <div class="met"><div class="ml">RS RESILIENT</div><div class="mv">✅ YES</div></div>
                            <div class="met"><div class="ml">21MA BUY ZONE</div><div class="mv">🔥 HIT</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No assets met all calculated momentum parameters in this specific run.")
            
            st.markdown("<div class='group-header'>📊 Group 2: Other Scanned Assets</div>", unsafe_allow_html=True)
            for r in other_results:
                st.markdown(f"""
                <div class="scard">
                    <div class="ch"><div class="sym">{r['Symbol']}</div><div class="live-px">₹{r['Live Price']}</div></div>
                    <div class="mgrid">
                        <div class="met"><div class="ml">EPS ACCEL</div><div class="mv">{r['EPS Accel']}</div></div>
                        <div class="met"><div class="ml">RS RESILIENT</div><div class="mv">{r['RS Resilient']}</div></div>
                        <div class="met"><div class="ml">21MA Buy Zone</div><div class="mv">{r['21MA Buy Zone']}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
