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

# ===========================================================================
#  CONFIG & HARDCODED INDICES
# ===========================================================================
UPSTOX_BASE = "https://api.upstox.com/v2"

# Hardcoded massive pool mapped exactly to your prompt input
BSE_500_TICKERS = (
    "GRSE,ETERNAL,RELIANCE,BANDHANBNK,VEDL,MAZDOCK,HDFCBANK,SUNPHARMA,COCHINSHIP,CEATLTD,"
    "M&M,SBIN,ADANIPOWER,MARUTI,GROWW,COALINDIA,ICICIBANK,BSE,DATAPATTNS,EMMVEE,ONGC,"
    "TENNIND,CHENNPETRO,BHARTIARTL,NETWEB,INFY,MCX,ITC,DIXON,SCI,ADANIENT,RECLTD,IDEA,"
    "SUZLON,TATASTEEL,AXISBANK,RBLBANK,LT,GMDCLTD,JIOFIN,STARHEALTH,CROMPTON,DRREDDY,"
    "INDIGO,OFSS,HCLTECH,TCS,WAAREEENER,SHRIRAMFIN,PFC,GODFRYPHLP,ATGL,BAJFINANCE,TMPV,"
    "GESHIP,JPPOWER,VBL,COHANCE,ADANIGREEN,BPCL,SWIGGY,POWERINDIA,INDUSTOWER,ADANIPORTS,"
    "ENRIN,HSCL,SWANCORP,EMCURE,TECHM,LODHA,NESTLEIND,SAIL,HINDZINC,FORCEMOT,BHEL,PERSISTENT,"
    "NATIONALUM,SAMMAANCAP,KAYNES,BHARATFORG,ULTRACEMCO,INDUSINDBK,PIRAMALFIN,TATAPOWER,ADANIENSOL,"
    "WELCORP,TVSMOTOR,EICHERMOT,HINDUNILVR,HINDALCO,NMDC,BAJAJ-AUTO,BEL,TATACHEM,PAYTM,JSWSTEEL,"
    "CANBK,GVT&D,ASHOKLEY,NHPC,TRENT,OIL,HDFCLIFE,HAL,WIPRO,OLAELEC,UNIONBANK,BRITANNIA,MAHABANK,"
    "TMCV,ABCAPITAL,NTPC,AWL,HAVELLS,POWERGRID,HINDCOPPER,HEROMOTOCO,YESBANK,SONACOMS,HFCL,"
    "NAUKRI,ABB,CDSL,JAINREC,KOTAKBANK,IDFCFIRSTB,AUROPHARMA,POLYCAB,KEI,BDL,TITAN,FEDERALBNK,"
    "RVNL,ATHERENERG,APOLLOHOSP,NAVINFLUOR,SAPPHIRE,INDIANB,JKTYRE,TARIL,MAXHEALTH,COFORGE,IGL,"
    "EXIDEIND,JSWENERGY,PNB,GRASIM,MOTHERSON,FIVESTAR,RPOWER,HDFCAMC,POLICYBZR,IIFL,GLENMARK,"
    "CONCORDBIO,CGPOWER,LAURUSLABS,MRF,TEJASNET,MRPL,BLUESTARCO,ASTRAL,HYUNDAI,GAIL,PPLPHARMA,"
    "CUMMINSIND,APARINDS,IOC,GODREJPROP,MUTHOOTFIN,DLF,BANKBARODA,SBILIFE,HINDPETRO,SBICARD,"
    "ONESOURCE,ASIANPAINT,MSUMI,TATAELXSI,KALYANKJIL,LLOYDSME,ANGELONE,SUPREMEIND,J&KBANK,NLCINDIA,"
    "MOTILALOFS,CANHLIFE,LUPIN,M&MFIN,PNBHOUSING,JINDALSTEL,AMBER,TATACONSUM,SOLARINDS,LENSKART,"
    "OLECTRA,BAJAJFINSV,NTPCGREEN,KPITTECH,INDHOTEL,BOSCHLTD,PETRONET,JUBLFOOD,RKFORGE,REDINGTON,"
    "GMRAIRPORT,SRF,RRKABEL,AUBANK,ABSLAMC,DIVISLAB,UPL,UNOMINDA,NAM-INDIA,JINDALSAW,HBLENGINE,"
    "CGCL,BANKINDIA,JYOTICNC,ZEEL,IRFC,VOLTAS,MPHASIS,DMART,ZENTEC,MANAPPURAM,PGEL,SHYAMMETL,"
    "IREDA,LTM,CIPLA,CONCOR,SYRMA,DALBHARAT,LICHSGFIN,IEX,LTF,PIIND,PHOENIXLTD,HUDCO,HEG,CHOLAFIN,"
    "GRAPHITE,DEVYANI,GPIL,INOXWIND,KIRLOSENG,AARTIIND,UNITDSPR,ENGINERSIN,LICI,PWL,NCC,APOLLOTYRE,"
    "ACUTAAS,ANANDRATHI,KIMS,LGEINDIA,ITCHOTELS,SIEMENS,VMM,RADICO,ANANTRAJ,POONAWALLA,GRANULES,"
    "TORNTPHARM,NBCC,INDIACEM,COLPAL,AMBUJACEM,PREMIERENE,IFCI,CUB,BALRAMCHIN,TORNTPOWER,ZYDUSLIFE,"
    "TATACAP,360ONE,IDBI,BIOCON,IRCTC,ARE&M,MEESHO,BAJAJHFL,PCBL,CAMS,FORTIS,TRITURBINE,BEML,AFFLE,"
    "PARADEEP,ICICIGI,DELHIVERY,MANKIND,INTELLECT,APLAPOLLO,CESC,ELGIEQUIP,IRCON,JWL,WOCKPHARMA,"
    "SJVN,NATCOPHARM,JBMA,OBEROIRLTY,KEC,TITAGARH,NYKAA,DEEPAKFERT,KARURVYSYA,JBCHEPHARM,DEEPAKNTR,"
    "MFSL,TIINDIA,ABFRL,ICICIAMC,CEMPRO,SAILIFE,KFINTECH,MARICO,PAGEIND,TATATECH,GILLETTE,ZENSARTECH,"
    "JSWINFRA,LEMONTREE,BALKRISIND,CHOICEIN,CARTRADE,PRESTIGE,THELEELA,NSLNISP,RAILTEL,FACT,NEWGEN,"
    "GLAXO,GODREJCP,LINDEINDIA,TATAINVEST,USHAMART,TATACOMM,IKS,CASTROLIND,GRAVITA,CYIENT,BELRISE,"
    "COROMANDEL,ASTERDM,WHIRLPOOL,JSL,PIDILITIND,CLEAN,PATANJALI,LTFOODS,SARDAEN,ACMESOLAR,THERMAX,"
    "DABUR,FINCABLES,NH,URBANCO,ABREL,GALLANTT,LALPATHLAB,FSL,SAGILITY,ICICIPRULI,HOMEFIRST,"
    "SONATSOFTW,NEULANDLAB,TRIDENT,PVRINOX,SYNGENE,IOB,CPPLUS,SIGNATURE,ALKEM,CCL,ESCORTS,FLUOROCHEM,"
    "ELECON,SCHAEFFLER,ATUL,GODREJIND,IRB,LTTS,FIRSTCRY,ECLERX,ENDURANCE,SUNTV,SOBHA,ABBOTINDIA,"
    "APTUS,VTL,JMFINANCIL,SHREECEM,BSOFT,ITI,KAJARIACER,CRAFTSMAN,CREDITACC,CHAMBLFERT,TECHNOE,"
    "CHOLAHLDNG,SUNDARMFIN,AFCONS,CARBORUNIV,BHARTIHEXA,ACC,AN_THEM,SCHNEIDER,BAJAJHLDNG,PINELABS,"
    "AEGISLOG,MINDACORP,IPCALAB,CANFINHOME,CENTRALBK,NUVAMA,BLS,NIVABUPA,UCOBANK,NAVA,WELSPUNLIV,"
    "AJANTPHARM,GICRE,MEDANTA,JUBLPHARMA,3MINDIA,LATENTVIEW,GABRIEL,TTML,GODIGIT,EMAMILTD,RAINBOW,"
    "JKCEMENT,INDGN,ACE,HDBFS,INDIAMART,ABDL,BLUEJET,POLYMED,ZYDUSWELL,CRISIL,KPRMILL,AEGISVOPAK,"
    "HEXT,GSPL,MMTC,MGL,AADHARHFC,UBL,ASAHIINDIA,BATAINDIA,EIDPARRY,NUVOCO,DOMS,UTIAMC,NIACL,"
    "HONASA,BIKAJI,RAMCOCEM,ZFCVINDIA,ANURAS,AIIL,JSWCEMENT,IGIL,HONAUT,SBFC,RITES,CAPLIPOINT,"
    "BRIGADE,SPLPETRO,ERIS,PTCIL,MAPMYINDIA,BAYERCROP,AAVAS,TEGA,SAREGAMA,TBOTEK,VIJAYA,DCMSHRIRAM,"
    "AIAENG,GLAND,TIMKEN,JUBLINGREA,CHALET,BERGEPAINT,BBTC,EIHOTEL,KPIL,SUMICHEM,ABLBL,BLUEDART,"
    "PFIZER,RHIM,JSWDULUX,TRAVELFOOD"
)

NIFTY_50_TICKERS = (
    "RELIANCE,TCS,HDFCBANK,ICICIBANK,INFY,BHARTIARTL,HINDUNILVR,ITC,SBIN,LTIM,ADANIENT,ADANIPORTS,"
    "ASIANPAINT,AXISBANK,BAJAJ-AUTO,BAJFINANCE,BAJAJFINSV,BPCL,BRITANNIA,CIPLA,COALINDIA,DIVISLAB,"
    "DRREDDY,EICHERMOT,GRASIM,HCLTECH,HEROMOTOCO,HINDALCO,INDUSINDBK,JSWSTEEL,KOTAKBANK,LT,M&M,"
    "MARUTI,NESTLEIND,NTPC,ONGC,POWERGRID,SBILIFE,SUNPHARMA,TATACONSUM,TATAMOTORS,TATASTEEL,TECHM,"
    "TITAN,ULTRACEMCO,UPL,WIPRO"
)

# Baseline Sector mapping for fallbacks
SECTOR_MAP = {
    "HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", "SBIN": "Financial Services", 
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
    except Exception:
        return False

def pull_upstox_price(symbol: str, token: str, exchange: str) -> float:
    """Retrieves live last traded price from Upstox API."""
    inst_key = f"NSE_EQ|{symbol}" if exchange == "NSE" else f"BSE_EQ|{symbol}"
    url = f"{UPSTOX_BASE}/market-quote/quotes"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {token}', 'Api-Version': '2.0'}
    params = {'instrument_key': inst_key}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data['data'][inst_key]['last_price']
    except:
        pass
    return 0.0

def calculate_momentum_node(symbol: str, source: str, token: str = "", exchange: str = "NSE") -> dict:
    """Calculates momentum matrix dynamically via Yahoo or Upstox."""
    res = {
        "Symbol": symbol, "Live Price": 0.0, "EPS Accel": "No Data", 
        "RS Resilient": "❌ NO", "21MA Buy Zone": "❌ OUTSIDE", "Sector": SECTOR_MAP.get(symbol, "Other")
    }
    
    close_px = 0.0
    yf_symbol = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
    
    # Attempt Upstox price fetch
    if source == "Upstox" and token:
        close_px = pull_upstox_price(symbol, token, exchange)
        
    # Execution via Yahoo Finance
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="1y")
        if hist.empty: return res
        
        if close_px == 0.0:
            close_px = hist['Close'].iloc[-1]
            
        hist['21EMA'] = hist['Close'].ewm(span=21, adjust=False).mean()
        ema_21 = hist['21EMA'].iloc[-1]
        if close_px > ema_21 and close_px < (ema_21 * 1.025):
            res["21MA Buy Zone"] = "🔥 HIT"
            
        wh_52 = hist['Close'].max()
        if (close_px / wh_52) >= 0.85:
            res["RS Resilient"] = "✅ YES"
            
        info = stock.info
        if "sector" in info:
            res["Sector"] = info["sector"]
        if "forwardEps" in info and "trailingEps" in info:
            if info["forwardEps"] is not None and info["trailingEps"] is not None:
                res["EPS Accel"] = "✅ Yes" if info["forwardEps"] > info["trailingEps"] else "❌ No"
    except:
        pass
            
    res["Live Price"] = round(close_px, 2)
    return res

# ===========================================================================
#  MAIN APP LAYOUT
# ===========================================================================

def main():
    # 🟢 STATE INITIALIZATION: Ensures continuous addition of lists
    if 'scanned_df' not in st.session_state:
        st.session_state['scanned_df'] = pd.DataFrame(columns=["Symbol", "Live Price", "EPS Accel", "RS Resilient", "21MA Buy Zone", "Sector"])

    st.markdown("""
    <div class='hdr'>
        <h1>NSE + BSE Multibagger Screener</h1>
        <div class='sub'>V6.0 • DYNAMIC ACCUMULATING ENGINE</div>
    </div>
    """, unsafe_allow_html=True)

       tab_screener, tab_db, tab_momentum, tab_charts, tab_heatmap = st.tabs([
        "Screener", "Database", "Momentum Strategy", "🎯 Momentum Hub (Charts)", "🗺️ Sector Heatmap"
    ])


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
                status_box.text(f"Extracting [{data_source}]: {symbol}")
                
                data_node = calculate_momentum_node(symbol, data_source, st.session_state['upstox_token'], exch)
                processed_results.append(data_node)
                prog_bar.progress((idx + 1) / len(execution_pool))
                
            status_box.success("Scan cluster limits hit successfully!")
            
            # 🟢 CONTINUOUS APPENDING LOGIC
            new_df = pd.DataFrame(processed_results)
            
            # Pull old list, combine with new, and remove duplicates keeping the newest data
            combined_df = pd.concat([st.session_state['scanned_df'], new_df])
            combined_df.drop_duplicates(subset=["Symbol"], keep='last', inplace=True)
            
            # Save the extended list back to session state
            st.session_state['scanned_df'] = combined_df

    # --- TAB 2: DATABASE ---
    with tab_db:
        st.markdown("<div class='slbl'>Database Grid</div>", unsafe_allow_html=True)
        
        if st.session_state['scanned_df'].empty:
            st.info("No scanned assets in registry. Go to Tab 1 and click the 'Process' button.")
        else:
            col_db1, col_db2 = st.columns([5, 1])
            with col_db1:
                st.write(f"📊 Currently holding **{len(st.session_state['scanned_df'])}** unique processed assets.")
            with col_db2:
                # Button to clear session memory
                if st.button("🗑️ Clear Database"):
                    st.session_state['scanned_df'] = pd.DataFrame(columns=["Symbol", "Live Price", "EPS Accel", "RS Resilient", "21MA Buy Zone", "Sector"])
                    st.rerun()

            df_full = st.session_state['scanned_df']
            st.dataframe(df_full.sort_values(by='Symbol').reset_index(drop=True), use_container_width=True)

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
    # --- 🟢 TAB 4: MOMENTUM HUB WITH CHARTS ---
    with tab_charts:
        st.markdown("<div class='slbl'>🎯 Active Momentum Executions</div>", unsafe_allow_html=True)
        if st.session_state['scanned_df'].empty:
            st.info("Database empty. You must process stocks on Tab 1 first.")
        else:
            df_full = st.session_state['scanned_df']
            
            # Extract perfect hits matching both criteria
            perfect_hits = df_full[(df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT')]
            
            if perfect_hits.empty:
                st.info("No perfect momentum fits detected in the current scanned array.")
            else:
                st.write(f"Found **{len(perfect_hits)}** highly optimized momentum setups:")
                
                for idx, row in perfect_hits.iterrows():
                    symbol = row['Symbol']
                    live_px = row['Live Price']
                    
                    # Display standalone card
                    st.markdown(f"""
                    <div class="scard hit">
                        <div class="ribbon">🔥 MOMENTUM PICK</div>
                        <div class="ch">
                            <div class="sym">{symbol}</div>
                            <div class="live-px">₹{live_px}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Render live candlestick chart
                    try:
                        ticker_data = yf.Ticker(f"{symbol}.NS")
                        hist_6m = ticker_data.history(period="6m")
                        
                        if not hist_6m.empty:
                            # Map 21 EMA for chart visual
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
                    except Exception as e:
                        st.warning(f"Unable to load chart for {symbol}. Moving to next.")
    # --- 🟢 TAB 5: SECTOR HEATMAP ---
    with tab_heatmap:
        st.markdown("<div class='slbl'>🗺️ Sector Heatmap Distribution</div>", unsafe_allow_html=True)
        if st.session_state['scanned_df'].empty:
            st.info("Database empty. You must process stocks on Tab 1 first.")
        else:
            df_full = st.session_state['scanned_df']
            
            # Clean and clean prices for heatmap sizing
            df_full['Clean_Price'] = pd.to_numeric(df_full['Live Price'].astype(str).str.replace('₹', '').str.replace(',', ''), errors='coerce').fillna(1.0)
            
            # Create interactive treemap heatmap
            fig_hm = go.Figure(go.Treemap(
                labels=df_full['Symbol'],
                parents=df_full['Sector'],
                values=df_full['Clean_Price'],
                textinfo="label+value",
                marker=dict(
                    colorscale='Electric',
                    showscale=True
                )
            ))
            
            fig_hm.update_layout(
                title="<b>Scanned Portfolio Mapped by Sector (Box size = Stock Price)</b>",
                title_font=dict(color="#f0f4ff"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a8b4cc'),
                height=600,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            
            st.plotly_chart(fig_hm, use_container_width=True)
            
            # Secondary sorted grid visual
            st.markdown("<div class='slbl'>Raw Database Sorted by Sector</div>", unsafe_allow_html=True)
            st.dataframe(df_full.sort_values(by='Sector').reset_index(drop=True), use_container_width=True)

if __name__ == "__main__":

    main()
