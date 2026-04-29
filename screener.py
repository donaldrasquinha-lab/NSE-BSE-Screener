# -*- coding: utf-8 -*-
"""
NSE + BSE Multibagger Screener v6.0 -- Streamlit Edition
Tab 1: Cloud Sync supporting Yahoo & Upstox in Batches of 50
Tab 2: Master Ledger Database that continuously appends results
Tab 3: Clustered Momentum Results Grid sorted from the full database

INSTALL:  pip install streamlit requests numpy pandas yfinance plotly
RUN:      streamlit run screener_st.py
"""

import io
import math
import requests
import numpy  as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import logging

# Configure logging for fallback tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================================================================
#  CONFIG & HARDCODED INDICES
# ===========================================================================
UPSTOX_BASE = "https://api.upstox.com/v2"

# [TICKERS CONFIGURATION - UNCHANGED]
BSE_500_TICKERS = (
    "GRSE,ETERNAL,RELIANCE,BANDHANBNK,VEDL,MAZDOCK,HDFCBANK,SUNPHARMA,COCHINSHIP,CEATLTD,"
    # ... (keep your full ticker list)
    "TRAVELFOOD"
)

NIFTY_50_TICKERS = (
    "RELIANCE,TCS,HDFCBANK,ICICIBANK,INFY,BHARTIARTL,HINDUNILVR,ITC,SBIN,LTIM,ADANIENT,ADANIPORTS,"
    # ... (keep your full ticker list)
    "WIPRO"
)

SECTOR_MAP = {
    "HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", 
    # ... (keep your full sector map)
    "TITAN": "Consumer Durables"
}

# ===========================================================================
#  HELPER FUNCTIONS FOR FALLBACK & ERROR HANDLING
# ===========================================================================

def safe_extract_price(price_value):
    """Safely extract numeric price from various formats."""
    try:
        if isinstance(price_value, (int, float)):
            return float(price_value)
        if isinstance(price_value, str):
            clean = price_value.replace('₹', '').replace(',', '').strip()
            return float(clean) if clean else 1.0
        return 1.0
    except Exception as e:
        logger.warning(f"Price extraction failed for {price_value}: {e}. Using fallback 1.0")
        return 1.0

def safe_build_treemap_data(df):
    """Safely build hierarchical data for Plotly Treemap with fallback."""
    try:
        if df.empty:
            logger.warning("DataFrame is empty, returning minimal treemap structure")
            return {
                "labels": ["No Data"],
                "parents": [""],
                "values": [1],
            }
        
        # Clean and validate data
        df = df.copy()
        df['Clean_Price'] = df['Live Price'].apply(safe_extract_price)
        df['Sector'] = df['Sector'].fillna("Other / Diversified").replace("", "Other / Diversified")
        
        sectors = df['Sector'].unique().tolist()
        symbols = df['Symbol'].tolist()
        
        labels = sectors + symbols
        parents = ["" for _ in sectors] + df['Sector'].tolist()
        
        sector_sums = df.groupby('Sector')['Clean_Price'].sum().to_dict()
        values = [sector_sums[sec] for sec in sectors] + df['Clean_Price'].tolist()
        
        return {
            "labels": labels,
            "parents": parents,
            "values": values,
        }
    except Exception as e:
        logger.error(f"Treemap data building failed: {e}. Using fallback structure")
        return {
            "labels": ["Error: Unable to build map"],
            "parents": [""],
            "values": [1],
        }

def render_treemap(data, title="Sector Distribution"):
    """Render treemap with error handling and fallback."""
    try:
        fig = go.Figure(go.Treemap(
            labels=data["labels"],
            parents=data["parents"],
            values=data["values"],
            textinfo="label+value",
            marker=dict(colorscale='Blues', showscale=True)
        ))
        
        fig.update_layout(
            title=f"<b>{title}</b>",
            title_font=dict(color="#f0f4ff", family="'DM Sans', sans-serif"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#a8b4cc', family="'DM Sans', sans-serif"),
            height=600,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        return fig, None
    except Exception as e:
        logger.error(f"Treemap rendering failed: {e}")
        return None, f"Chart rendering failed: {str(e)}"

# ===========================================================================
#  PAGE SETUP & CSS STYLING
# ===========================================================================
st.set_page_config(page_title="NSE+BSE Screener", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://googleapis.com');
:root{
  --bg:#0a0d14;--surf:#0f1320;--card:#131928;--card2:#181f2e;
  --border:#1e2740;--sky:#38bdf8;--sage:#34d399;--amber:#fbbf24;
  --t1:#f0f4ff;--t2:#a8b4cc;--t3:#5c6a88;--sans:'DM Sans',sans-serif;--mono:'JetBrains Mono',monospace;
}
*{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{
  background:var(--bg)!important;color:var(--t2)!important;font-family:var(--sans)!important;}
[data-testid="stSidebar"]{background:#0c1018!important;border-right:1px solid var(--border)!important;}
.stButton>button{background:linear-gradient(135deg,#1a3a6e,#0e2350)!important;
  color:var(--sky)!important;border:1px solid rgba(56,189,248,.3)!important;
  border-radius:8px!important;font-weight:600!important;transition:all .18s!important;}
.stButton>button:hover{background:linear-gradient(135deg,#1e4a8a,#1432a0)!important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{
  background:#131928!important;border:1px solid #253050!important;color:var(--t1)!important;
  border-radius:7px!important;font-family:var(--mono)!important;}
.stSelectbox>div>div{background:#131928!important;border-color:#253050!important;}
.stTabs [role="tablist"]{background:#0f1320;border:1px solid #1e2740;border-radius:10px;padding:3px;}
.stTabs [role="tab"]{color:#5c6a88!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{background:#131928!important;color:var(--sky)!important;}
.stProgress>div>div{background:linear-gradient(90deg,var(--sky),var(--sage))!important;}
#MainMenu,footer,header{visibility:hidden!important;}

.hdr{background:linear-gradient(135deg,#0e1525,#131928);border:1px solid #1e2740;
  border-radius:12px;padding:20px 26px 16px;margin-bottom:18px;position:relative;}
.hdr::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--sky) 30%,var(--sage) 65%,var(--amber) 88%,transparent);}
.hdr h1{font-weight:700;font-size:1.5rem;color:var(--t1);}
.slbl{font-family:var(--mono);font-size:.58rem;text-transform:uppercase;
  color:var(--sky);border-left:2px solid var(--sky);padding-left:8px;margin:14px 0 9px;}
.scard{background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:14px 16px;margin-bottom:8px;position:relative;}
.scard.hit{background:linear-gradient(160deg,#0f1d14,var(--card));border-color:rgba(52,211,153,.3);}
.scard .ch{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.scard .sym{font-weight:700;font-size:1rem;color:var(--t1);}
.scard .live-px{font-family:var(--mono);font-weight:700;font-size:1.05rem;color:var(--sage);margin-left:auto;}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:5px;margin:10px 0;}
.met{background:var(--card2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;}
.met .ml{font-size:.55rem;color:var(--t3);text-transform:uppercase;}
.met .mv{font-size:.84rem;font-weight:600;color:var(--t1);font-family:var(--mono);margin-top:2px;}
.ribbon{position:absolute;top:10px;right:10px;background:linear-gradient(90deg, #10b981, #059669);
  color:#fff;font-family:var(--mono);font-size:0.55rem;font-weight:700;padding:3px 8px;border-radius:4px;}
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
    """Verifies Upstox Token validity using official v2 API profiles."""
    clean_token = token.strip() if token else ""
    if not clean_token:
        return False
    url = f"{UPSTOX_BASE}/user/profile"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {clean_token}', 'Api-Version': '2.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Upstox token check failed: {e}")
        return False

def pull_upstox_price(symbol: str, token: str, exchange: str) -> float:
    """Retrieves live last traded price from Upstox API with fallback."""
    inst_key = f"NSE_EQ|{symbol}" if exchange == "NSE" else f"BSE_EQ|{symbol}"
    url = f"{UPSTOX_BASE}/market-quote/quotes"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {token}', 'Api-Version': '2.0'}
    params = {'instrument_key': inst_key}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data['data'][inst_key]['last_price']
    except Exception as e:
        logger.warning(f"Upstox price pull failed for {symbol}: {e}. Fallback to Yahoo Finance")
    return 0.0

def calculate_momentum_node(symbol: str, source: str, token: str = "", exchange: str = "NSE") -> dict:
    """Calculates momentum matrix with comprehensive error handling and fallback."""
    res = {
        "Symbol": symbol, "Live Price": 0.0, "EPS Accel": "No Data", 
        "RS Resilient": "❌ NO", "21MA Buy Zone": "❌ OUTSIDE", "Sector": SECTOR_MAP.get(symbol, "Other")
    }
    
    close_px = 0.0
    yf_symbol = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
    
    # Attempt Upstox price fetch
    if source == "Upstox" and token:
        try:
            close_px = pull_upstox_price(symbol, token, exchange)
        except Exception as e:
            logger.warning(f"Upstox fetch failed for {symbol}: {e}. Continuing with Yahoo")
        
    # Execution via Yahoo Finance with comprehensive error handling
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="1y")
        
        if hist.empty:
            logger.warning(f"No historical data for {symbol}")
            return res
        
        if close_px == 0.0:
            close_px = hist['Close'].iloc[-1]
            
        hist['21EMA'] = hist['Close'].ewm(span=21, adjust=False).mean()
        ema_21 = hist['21EMA'].iloc[-1]
        
        if close_px > ema_21 and close_px < (ema_21 * 1.025):
            res["21MA Buy Zone"] = "🔥 HIT"
            
        wh_52 = hist['Close'].max()
        if (close_px / wh_52) >= 0.85:
            res["RS Resilient"] = "✅ YES"
            
        try:
            info = stock.info
            if "sector" in info and info["sector"]:
                res["Sector"] = info["sector"]
            if "forwardEps" in info and "trailingEps" in info:
                if info["forwardEps"] is not None and info["trailingEps"] is not None:
                    res["EPS Accel"] = "✅ Yes" if info["forwardEps"] > info["trailingEps"] else "❌ No"
        except Exception as e:
            logger.warning(f"Stock info extraction failed for {symbol}: {e}")
            
    except Exception as e:
        logger.error(f"Momentum calculation failed for {symbol}: {e}")
        
    res["Live Price"] = round(close_px, 2)
    return res

# ===========================================================================
#  MAIN APP LAYOUT
# ===========================================================================

def main():
    # 🟢 STATE INITIALIZATION: Ensures continuous addition of lists
    if 'scanned_df' not in st.session_state:
        st.session_state['scanned_df'] = pd.DataFrame(
            columns=["Symbol", "Live Price", "EPS Accel", "RS Resilient", "21MA Buy Zone", "Sector"]
        )

    st.markdown("""
    <div class='hdr'>
        <h1>NSE + BSE Multibagger Screener</h1>
        <div class='sub'>V6.0 • DYNAMIC ACCUMULATING ENGINE</div>
    </div>
    """, unsafe_allow_html=True)

    tab_screener, tab_db, tab_momentum, tab_charts, tab_heatmap = st.tabs(
        ["Screener", "Database", "Momentum Strategy", "🎯 Momentum Hub (Charts)", "🗺️ Sector Heatmap"]
    )

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
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            data_source = st.selectbox("Select Price/Data Source", ["Yahoo Finance", "Upstox"])
        with col_s2:
            target_index = st.selectbox("Select Target Pool to Scan", ["BSE 500 (Custom Input)", "Nifty 50", "Custom List"])
            
        custom_list = ""
        if target_index == "Custom List":
            custom_list = st.text_area("Enter Custom Tickers (Comma Separated):", "RELIANCE,TCS,INFY")

        # Set up assets list
        if target_index == "BSE 500 (Custom Input)":
            unique_assets = BSE_500_TICKERS.split(",")
            exch = "NSE"
        elif target_index == "Nifty 50":
            unique_assets = NIFTY_50_TICKERS.split(",")
            exch = "NSE"
        else:
            unique_assets = [x.strip().upper() for x in custom_list.split(",") if x.strip()]
            exch = "NSE"

        # 🟢 BATCH SELECTION LOGIC (Set to 50 as requested)
        batch_size = 50
        total_assets = len(unique_assets)
        num_batches = math.ceil(total_assets / batch_size)
        
        batch_labels = []
        for i in range(num_batches):
            start = i * batch_size
            end = min((i + 1) * batch_size, total_assets)
            batch_labels.append(f"Batch {i+1}: Stocks {start+1} to {end}")
            
        selected_batch_idx = st.selectbox("Select Asset Cluster to Process", range(num_batches), format_func=lambda x: batch_labels[x])
        
        loop_start = selected_batch_idx * batch_size
        loop_end = min((selected_batch_idx + 1) * batch_size, total_assets)
        execution_pool = unique_assets[loop_start:loop_end]

        if st.button("🛰️ Pull & Process Selected Batch"):
            st.info(f"Targeting {len(execution_pool)} items in {batch_labels[selected_batch_idx]}. Executing thread...")
            
            prog_bar = st.progress(0.0)
            status_box = st.empty()
            processed_results = []
            
            for idx, symbol in enumerate(execution_pool):
                try:
                    status_box.text(f"Extracting [{data_source}]: {symbol}")
                    data_node = calculate_momentum_node(symbol, data_source, st.session_state['upstox_token'], exch)
                    processed_results.append(data_node)
                except Exception as e:
                    logger.error(f"Failed to process {symbol}: {e}")
                    # Add fallback entry
                    processed_results.append({
                        "Symbol": symbol, "Live Price": 0.0, "EPS Accel": "Error",
                        "RS Resilient": "❌ NO", "21MA Buy Zone": "❌ OUTSIDE", 
                        "Sector": SECTOR_MAP.get(symbol, "Other")
                    })
                prog_bar.progress((idx + 1) / len(execution_pool))
                
            status_box.success("Scan cluster limits hit successfully!")
            
            # 🟢 CONTINUOUS APPENDING LOGIC
            if processed_results:
                new_df = pd.DataFrame(processed_results)
                combined_df = pd.concat([st.session_state['scanned_df'], new_df], ignore_index=True)
                combined_df.drop_duplicates(subset=["Symbol"], keep='last', inplace=True)
                st.session_state['scanned_df'] = combined_df
                st.success(f"✅ Added {len(new_df)} records. Database now has {len(combined_df)} unique assets.")
            else:
                st.error("❌ No data could be processed. Check logs for details.")

    # --- TAB 2: DATABASE ---
    with tab_db:
        st.markdown("<div class='slbl'>Database Grid</div>", unsafe_allow_html=True)
        
        if st.session_state['scanned_df'].empty:
            st.info("No scanned assets in registry. Go to Tab 1 and click the 'Process' button.")
        else:
            df_full = st.session_state['scanned_df'].copy()
            
            col_db1, col_db2 = st.columns([5, 1])
            with col_db1:
                st.write(f"📊 Currently holding **{len(df_full)}** unique processed assets.")
            with col_db2:
                if st.button("🗑️ Clear Database"):
                    st.session_state['scanned_df'] = pd.DataFrame(
                        columns=["Symbol", "Live Price", "EPS Accel", "RS Resilient", "21MA Buy Zone", "Sector"]
                    )
                    st.rerun()

            # Build and render treemap safely
            treemap_data = safe_build_treemap_data(df_full)
            fig, error_msg = render_treemap(treemap_data, "Scanned Portfolio Mapped by Sector (Box size = Price)")
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            elif error_msg:
                st.error(f"📊 {error_msg}")
            
            st.markdown("<div class='slbl'>Raw Database Sorted by Sector</div>", unsafe_allow_html=True)
            try:
                st.dataframe(df_full.sort_values(by='Sector').reset_index(drop=True), use_container_width=True)
            except Exception as e:
                logger.error(f"DataFrame display failed: {e}")
                st.dataframe(df_full, use_container_width=True)

    # --- TAB 3: MOMENTUM STRATEGY HUB ---
    with tab_momentum:
        st.markdown("<div class='slbl'>Momentum Strategy Hub</div>", unsafe_allow_html=True)
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
                st.info("No assets met all calculated parameters in this cluster.")
            
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

    # --- TAB 4: MOMENTUM HUB WITH CHARTS ---
    with tab_charts:
        st.markdown("<div class='slbl'>🎯 Active Momentum Executions</div>", unsafe_allow_html=True)
        if st.session_state['scanned_df'].empty:
            st.info("Database empty. You must process stocks on Tab 1 first.")
        else:
            df_full = st.session_state['scanned_df']
            perfect_hits = df_full[(df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT')]
            
            if perfect_hits.empty:
                st.info("No perfect momentum fits detected in the current scanned array.")
            else:
                st.write(f"Found **{len(perfect_hits)}** highly optimized momentum setups:")
                
                for idx, row in perfect_hits.iterrows():
                    symbol = row['Symbol']
                    live_px = row['Live Price']
                    
                    st.markdown(f"""
                    <div class="scard hit">
                        <div class="ribbon">🔥 MOMENTUM PICK</div>
                        <div class="ch">
                            <div class="sym">{symbol}</div>
                            <div class="live-px">₹{live_px}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Render live candlestick chart with fallback
                    try:
                        ticker_data = yf.Ticker(f"{symbol}.NS")
                        hist_6m = ticker_data.history(period="6m")
                        
                        if not hist_6m.empty:
                            hist_6m['21EMA'] = hist_6m['Close'].ewm(span=21, adjust=False).mean()
                            
                            fig = go.Figure(data=[
                                go.Candlestick(
                                    x=hist_6m.index,
                                    open=hist_6m['Open'],
                                    high=hist_6m['High'],
                                    low=hist_6m['Low'],
                                    close=hist_6m['Close'],
                                    name="Candles"
                                ),
                                go.Scatter(
                                    x=hist_6m.index, 
                                    y=hist_6m['21EMA'], 
                                    mode='lines', 
                                    line=dict(color='#fb923c', width=1.5), 
                                    name="21 EMA"
                                )
                            ])
                            
                            fig.update_layout(
                                xaxis_rangeslider_visible=False,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#a8b4cc'),
                                xaxis=dict(gridcolor='#1e2740'),
                                yaxis=dict(gridcolor='#1e2740'),
                                height=400,
                                margin=dict(l=10, r=10, t=20, b=20)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"No 6-month data available for {symbol}")
                    except Exception as e:
                        logger.error(f"Chart rendering failed for {symbol}: {e}")
                        st.warning(f"⚠️ Unable to load chart for {symbol}: {str(e)}")

    # --- TAB 5: SECTOR HEATMAP (CONSOLIDATED) ---
    with tab_heatmap:
        st.markdown("<div class='slbl'>🗺️ Sector Heatmap Distribution</div>", unsafe_allow_html=True)
        
        if st.session_state['scanned_df'].empty:
            st.info("Database empty. You must process stocks on Tab 1 first.")
        else:
            df_full = st.session_state['scanned_df'].copy()
            
            # Build and render treemap safely
            treemap_data = safe_build_treemap_data(df_full)
            fig, error_msg = render_treemap(treemap_data, "Scanned Portfolio Mapped by Sector (Box size = Price)")
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            elif error_msg:
                st.error(f"📊 {error_msg}")
            
            st.markdown("<div class='slbl'>Raw Database Sorted by Sector</div>", unsafe_allow_html=True)
            try:
                st.dataframe(df_full.sort_values(by='Sector').reset_index(drop=True), use_container_width=True)
            except Exception as e:
                logger.error(f"DataFrame display failed: {e}")
                st.dataframe(df_full, use_container_width=True)


if __name__ == "__main__":
    main()
