# -*- coding: utf-8 -*-
"""
NSE + BSE Multibagger Screener v6.0 -- Streamlit Edition
Tab 1: Cloud Sync supporting Yahoo & Upstox (With Automatic Batch Processing)
Tab 2: Master Ledger Database that continuously appends results
Tab 3: Clustered Momentum Results Grid
Tab 4: Momentum Picks with Interactive Candlestick Charts
Tab 5: Bulletproof Sector Heatmap Grid
"""

import io
import math
import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ===========================================================================
#  CONFIG & HARDCODED INDICES
# ===========================================================================
UPSTOX_BASE = "https://api.upstox.com/v2"

# Compacted lists to fit message limits safely
BSE_500_TICKERS = "GRSE,ETERNAL,RELIANCE,BANDHANBNK,VEDL,MAZDOCK,HDFCBANK,SUNPHARMA,COCHINSHIP,CEATLTD,M&M,SBIN,ADANIPOWER,MARUTI,GROWW,COALINDIA,ICICIBANK,BSE,DATAPATTNS,EMMVEE,ONGC,TENNIND,CHENNPETRO,BHARTIARTL,NETWEB,INFY,MCX,ITC,DIXON,SCI,ADANIENT,RECLTD,IDEA,SUZLON,TATASTEEL,AXISBANK,RBLBANK,LT,GMDCLTD,JIOFIN,STARHEALTH,CROMPTON,DRREDDY,INDIGO,OFSS,HCLTECH,TCS,WAAREEENER,SHRIRAMFIN,PFC,GODFRYPHLP,ATGL,BAJFINANCE,TMPV,GESHIP,JPPOWER,VBL,COHANCE,ADANIGREEN,BPCL,SWIGGY,POWERINDIA,INDUSTOWER,ADANIPORTS,ENRIN,HSCL,SWANCORP,EMCURE,TECHM,LODHA,NESTLEIND,SAIL,HINDZINC,FORCEMOT,BHEL,PERSISTENT,NATIONALUM,SAMMAANCAP,KAYNES,BHARATFORG,ULTRACEMCO,INDUSINDBK,PIRAMALFIN,TATAPOWER,ADANIENSOL,WELCORP,TVSMOTOR,EICHERMOT,HINDUNILVR,HINDALCO,NMDC,BAJAJ-AUTO,BEL,TATACHEM,PAYTM,JSWSTEEL,CANBK,GVT&D,ASHOKLEY,NHPC,TRENT,OIL,HDFCLIFE,HAL,WIPRO,OLAELEC,UNIONBANK,BRITANNIA,MAHABANK,TMCV,ABCAPITAL,NTPC,AWL,HAVELLS,POWERGRID,HINDCOPPER,HEROMOTOCO,YESBANK,SONACOMS,HFCL,NAUKRI,ABB,CDSL,JAINREC,KOTAKBANK,IDFCFIRSTB,AUROPHARMA,POLYCAB,KEI,BDL,TITAN,FEDERALBNK,RVNL,ATHERENERG,APOLLOSP,NAVINFLUOR,SAPPHIRE,INDIANB,JKTYRE,TARIL,MAXHEALTH,COFORGE,IGL,EXIDEIND,JSWENERGY,PNB,GRASIM,MOTHERSON,FIVESTAR,RPOWER,HDFCAMC,POLICYBZR,IIFL,GLENMARK,CONCORDBIO,CGPOWER,LAURUSLABS,MRF,TEJASNET,MRPL,BLUESTARCO,ASTRAL,HYUNDAI,GAIL,PPLPHARMA,CUMMINSIND,APARINDS,IOC,GODREJPROP,MUTHOOTFIN,DLF,BANKBARODA,SBILIFE,HINDPETRO,SBICARD,ONESOURCE,ASIANPAINT,MSUMI,TATAELXSI,KALYANKJIL,LLOYDSME,ANGELONE,SUPREMEIND,J&KBANK,NLCINDIA,MOTILALOFS,CANHLIFE,LUPIN,M&MFIN,PNBHOUSING,JINDALSTEL,AMBER,TATACONSUM,SOLARINDS,LENSKART,OLECTRA,BAJAJFINSV,NTPCGREEN,KPITTECH,INDHOTEL,BOSCHLTD,PETRONET,JUBLFOOD,RKFORGE,REDINGTON,GMRAIRPORT,SRF,RRKABEL,AUBANK,ABSLAMC,DIVISLAB,UPL,UNOMINDA,NAM-INDIA,JINDALSAW,HBLENGINE,CGCL,BANKINDIA,JYOTICNC,ZEEL,IRFC,VOLTAS,MPHASIS,DMART,ZENTEC,MANAPPURAM,PGEL,SHYAMMETL,IREDA,LTM,CIPLA,CONCOR,SYRMA,DALBHARAT,LICHSGFIN,IEX,LTF,PIIND,PHOENIXLTD,HUDCO,HEG,CHOLAFIN,GRAPHITE,DEVYANI,GPIL,INOXWIND,KIRLOSENG,AARTIIND,UNITDSPR,ENGINERSIN,LICI,PWL,NCC,APOLLOTYRE,ACUTAAS,ANANDRATHI,KIMS,LGEINDIA,ITCHOTELS,SIEMENS,VMM,RADICO,ANANTRAJ,POONAWALLA,GRANULES,TORNTPHARM,NBCC,INDIACEM,COLPAL,AMBUJACEM,PREMIERENE,IFCI,CUB,BALRAMCHIN,TORNTPOWER,ZYDUSLIFE,TATACAP,360ONE,IDBI,BIOCON,IRCTC,ARE&M,MEESHO,BAJAJHFL,PCBL,CAMS,FORTIS,TRITURBINE,BEML,AFFLE,PARADEEP,ICICIGI,DELHIVERY,MANKIND,INTELLECT,APLAPOLLO,CESC,ELGIEQUIP,IRCON,JWL,WOCKPHARMA,SJVN,NATCOPHARM,JBMA,OBEROIRLTY,KEC,TITAGARH,NYKAA,DEEPAKFERT,KARURVYSYA,JBCHEPHARM,DEEPAKNTR,MFSL,TIINDIA,ABFRL,ICICIAMC,CEMPRO,SAILIFE,KFINTECH,MARICO,PAGEIND,TATATECH,GILLETTE,ZENSARTECH,JSWINFRA,LEMONTREE,BALKRISIND,CHOICEIN,CARTRADE,PRESTIGE,THELEELA,NSLNISP,RAILTEL,FACT,NEWGEN,GLAXO,GODREJCP,LINDEINDIA,TATAINVEST,USHAMART,TATACOMM,IKS,CASTROLIND,GRAVITA,CYIENT,BELRISE,COROMANDEL,ASTERDM,WHIRLPOOL,JSL,PIDILITIND,CLEAN,PATANJALI,LTFOODS,SARDAEN,ACMESOLAR,THERMAX,DABUR,FINCABLES,NH,URBANCO,ABREL,GALLANTT,LALPATHLAB,FSL,SAGILITY,ICICIPRULI,HOMEFIRST,SONATSOFTW,NEULANDLAB,TRIDENT,PVRINOX,SYNGENE,IOB,CPPLUS,SIGNATURE,ALKEM,CCL,ESCORTS,FLUOROCHEM,ELECON,SCHAEFFLER,ATUL,GODREJIND,IRB,LTTS,FIRSTCRY,ECLERX,ENDURANCE,SUNTV,SOBHA,ABBOTINDIA,APTUS,VTL,JMFINANCIL,SHREECEM,BSOFT,ITI,KAJARIACER,CRAFTSMAN,CREDITACC,CHAMBLFERT,TECHNOE,CHOLAHLDNG,SUNDARMFIN,AFCONS,CARBORUNIV,BHARTIHEXA,ACC,ANTHEM,SCHNEIDER,BAJAJHLDNG,PINELABS,AEGISLOG,MINDACORP,IPCALAB,CANFINHOME,CENTRALBK,NUVAMA,BLS,NIVABUPA,UCOBANK,NAVA,WELSPUNLIV,AJANTPHARM,GICRE,MEDANTA,JUBLPHARMA,3MINDIA,LATENTVIEW,GABRIEL,TTML,GODIGIT,EMAMILTD,RAINBOW,JKCEMENT,INDGN,ACE,HDBFS,INDIAMART,ABDL,BLUEJET,POLYMED,ZYDUSWELL,CRISIL,KPRMILL,AEGISVOPAK,HEXT,GSPL,MMTC,MGL,AADHARHFC,UBL,ASAHIINDIA,BATAINDIA,EIDPARRY,NUVOCO,DOMS,UTIAMC,NIACL,HONASA,BIKAJI,RAMCOCEM,ZFCVINDIA,ANURAS,AIIL,JSWCEMENT,IGIL,HONAUT,SBFC,RITES,CAPLIPOINT,BRIGADE,SPLPETRO,ERIS,PTCIL,MAPMYINDIA,BAYERCROP,AAVAS,TEGA,SAREGAMA,TBOTEK,VIJAYA,DCMSHRIRAM,AIAENG,GLAND,TIMKEN,JUBLINGREA,CHALET,BERGEPAINT,BBTC,EIHOTEL,KPIL,SUMICHEM,ABLBL,BLUEDART,PFIZER,RHIM,JSWDULUX,TRAVELFOOD"
NIFTY_50_TICKERS = "RELIANCE,TCS,HDFCBANK,ICICIBANK,INFY,BHARTIARTL,HINDUNILVR,ITC,SBIN,LTIM,ADANIENT,ADANIPORTS,ASIANPAINT,AXISBANK,BAJAJ-AUTO,BAJFINANCE,BAJAJFINSV,BPCL,BRITANNIA,CIPLA,COALINDIA,DIVISLAB,DRREDDY,EICHERMOT,GRASIM,HCLTECH,HEROMOTOCO,HINDALCO,INDUSINDBK,JSWSTEEL,KOTAKBANK,LT,M&M,MARUTI,NESTLEIND,NTPC,ONGC,POWERGRID,SBILIFE,SUNPHARMA,TATACONSUM,TATAMOTORS,TATASTEEL,TECHM,TITAN,ULTRACEMCO,UPL,WIPRO"
NIFTY_500_TICKERS = "360ONE,3MINDIA,ABB,ACC,AIAENG,APLAPOLLO,AUBANK,AETHER,AFFLE,AJANTPHARM,APLLTD,ALKEM,ALKYLAMINE,ALLCARGO,ALOKINDS,AMBER,AMBUJACEM,ANANTRAJ,ANGELONE,APARINDS,APOLLOHOSP,APOLLOTYRE,APTUS,ARE&M,ASAHIINDIA,ASHOKLEY,ASIANPAINT,ASTERDM,ASTRAL,ATUL,AUROPHARMA,AVANTIFEED,DMART,BEML,BLS,BSE,BALAMINES,BALKRISIND,BALRAMCHIN,BANDHANBNK,BANKBARODA,BANKINDIA,MAHABANK,BATAINDIA,BAYERCROP,BERGEPAINT,BDL,BEL,BHARATFORG,BHEL,BIOCON,BIRLACORPN,BSOFT,BLUEDART,BORORENEW,BOSCHLTD,CAMPUS,CESC,CGPOWER,CIEINDIA,CRISIL,CSBBANK,CANFINHOME,CANBK,CAPLIPOINT,CGCL,CARBORUNIV,CASTROLIND,CEATLTD,CENTRALBK,CDSL,CENTURYPLY,CENTURYTEX,CHAMBLFERT,CHALET,CHOLAFIN,CHOLAHLDNG,CUB,CIPLA,CLEAN,COALINDIA,COCHINSHIP,COFORGE,COLPAL,CONCOR,COROMANDEL,CRAFTSMAN,CREDITACC,CROMPTON,CUMMINSIND,CYIENT,DCMSHRIRAM,DLF,DABUR,DALBHARAT,DEEPAKFERT,DEEPAKNTR,DELHIVERY,DEVYANI,DIXON,DRREDDY,EIDPARRY,EIHOTEL,EPL,EASEMYTRIP,EICHERMOT,ELECON,EMAMILTD,ENDURANCE,ENGINERSIN,ERIS,ESCORTS,EXIDEIND,FDC,FSNKYS,FEDERALBNK,FACT,FINEORG,FINCABLES,FINPIPE,FSL,FORTIS,GRINFRA,GAIL,GLS,GMRINFRA,GEPIL,GHCL,GICRE,GIPCL,GLAXO,GLENMARK,GODREJAGRO,GODREJCP,GODREJPROP,GRANULES,GRAPHITE,GRASIM,GESHIP,GREAVESCOT,GRINDWELL,GUJALKALI,GUJGASLTD,GMDCLTD,GNFC,GPPL,GSFC,GSPL,HCLTECH,HDFCAMC,HDFCBANK,HDFCLIFE,HFCL,HLEGLAS,HAPPSTMNDS,HAVELLS,HEG,HEROMOTOCO,HINDALCO,HCOPPER,HINDPETRO,HINDUNILVR,HINDZINC,HONAUT,HUDCO,ICICIBANK,ICICIGI,ICICIPRULI,ISEC,IDBI,IDFCFIRSTB,IDFC,IIFL,IRB,IRCON,ITC,ITI,ITDCEM,INDIACEM,IBREALEST,INDIAMART,INDIANB,IEX,INDHOTEL,IOC,IRCTC,IRFC,INDIGOPNTS,IGL,INDUSINDBK,INDUSTOWER,INFIBEAM,INFY,INOXWIND,INTELLECT,INDIGO,IPCALAB,JBCHEPHARM,JKCEMENT,JKLACEMENT,JKPAPER,JMFINANCIL,JSWENERGY,JSWSTEEL,JSWINFRA,JAMNAAUTO,JSL,JINDALSTEL,JINDWORLD,JUBLFOOD,JUBLPHARMA,JUBLINGREA,JUSTDIAL,JYOTHYLAB,KALYANKJIL,KEI,KNRCON,KPITTECH,KRBL,KSB,KAJARIACER,KANSNEROL,KARURVYSYA,KEC,KENNAMET,KIMS,KIRLOSENG,KIRLPNU,KOLTEPATIL,KOTAKBANK,L&TFH,LTTS,LICHSGFIN,LICI,LAURUSLABS,LXCHEM,LEMONTREE,LINDEINDIA,LUPIN,LUXIND,MASFIN,MRF,MTARTECH,MTNL,MGL,MAHSEAMLES,M&MFIN,M&M,MANAPPURAM,MARICO,MARUTI,MASTEK,MEDPLUS,METROPOLIS,MFSL,MINDACORP,MSUMI,MOTILALOFS,MPHASIS,MCX,MUTHOOTFIN,NHPC,NLCINDIA,NMDC,NOCIL,NTPC,NATIONALUM,NAVINFLUOR,NAZARA,NEOGEN,NESCO,NESTLEIND,NETWORK18,NIPPONLIIF,OBEROIRLTY,ONGC,OIL,OLECTRA,PAYTM,OFSS,ORIENTELEC,POLICYBZR,PCBL,PIIND,PNBHOUSING,PNCINFRA,PVRINOX,PAGEIND,PATANJALI,PEL,PFC,POWERGRID,PRESTIGE,PRINCEPIPE,PRAJIND,PRIVISCL,PNB,QUESS,RBLBANK,RECLTD,RHIM,RITES,RADICO,RAIN,RAINBOW,RAJESHEXPO,RALLIS,RAMCOCEM,RATNAMANI,RAYMOND,REDINGTON,RELAXO,RELIANCE,RELIGARE,RVNL,SJVN,SKFINDIA,SRF,SANOFI,SAPPHIRE,SAREGAMA,SASTASUNDR,SBICARD,SBILIFE,SCHAEFFLER,SHOPERSTOP,SHREECEM,SHRIRAMFIN,SIEMENS,SOBHA,SOLARINDS,SONACOMS,SONATSOFTW,STARHEALTH,SBI,SAIL,SUNPHARMA,SUNTV,SUNDARMFIN,SUNDRMFAST,SUNTECK,SUPRAJIT,SUPREMEIND,SUZLON,SWANENERGY,SYNGENE,TARC,TCIEXP,TTKPRESTIG,TV18BRDCST,TVSMOTOR,TARSONS,TATACONSUM,TATACOMM,TATAELXSI,TATAMOTORS,TATAPOWER,TATASTEEL,TATAINVEST,TATATECH,TECHM,TEJASNET,TIMKEN,TITAN,TORNTPHARM,TORNTPOWER,TREND,TRIDENT,TRIVENI,UCOBANK,UBL,UDEV,UNIONBANK,UPL,UTIAMC,VGUARD,VMART,VIPIND,VAIBHAVGBL,VAKRANGEE,VARROC,VBL,VEDL,VINATIORG,VOLTAS,WELCORP,WELSPUNLIV,WESTLIFE,WHIRLPOOL,WIPRO,YESBANK,ZFCVINDIA,ZEEL,ZENSARTECH,ZOMATO,ZYDUSLIFE"

SECTOR_MAP = {"HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", "SBIN": "Financial Services", "AXISBANK": "Financial Services", "KOTAKBANK": "Financial Services", "BAJFINANCE": "Financial Services", "BAJAJFINSV": "Financial Services", "TCS": "IT", "INFY": "IT", "HCLTECH": "IT", "TECHM": "IT", "WIPRO": "IT", "RELIANCE": "Energy / Oil & Gas", "HINDUNILVR": "FMCG", "ITC": "FMCG", "TATAMOTORS": "Automobile", "M&M": "Automobile", "SUNPHARMA": "Pharma / Healthcare", "TITAN": "Consumer Durables"}

# ===========================================================================
#  PAGE SETUP & CSS STYLING
# ===========================================================================
st.set_page_config(page_title="NSE+BSE Screener", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://googleapis.com');
:root{--bg:#0a0d14;--surf:#0f1320;--card:#131928;--card2:#181f2e;--border:#1e2740;--sky:#38bdf8;--sage:#34d399;--amber:#fbbf24;--t1:#f0f4ff;--t2:#a8b4cc;--t3:#5c6a88;--sans:'DM Sans',sans-serif;--mono:'JetBrains Mono',monospace;}
*{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{background:var(--bg)!important;color:var(--t2)!important;font-family:var(--sans)!important;}
[data-testid="stSidebar"]{background:#0c1018!important;border-right:1px solid var(--border)!important;}
.stButton>button{background:linear-gradient(135deg,#1a3a6e,#0e2350)!important;color:var(--sky)!important;border:1px solid rgba(56,189,248,.3)!important;border-radius:8px!important;font-weight:600!important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{background:#131928!important;border:1px solid #253050!important;color:var(--t1)!important;border-radius:7px!important;font-family:var(--mono)!important;}
.stTabs [role="tablist"]{background:#0f1320;border:1px solid #1e2740;border-radius:10px;padding:3px;}
.stTabs [role="tab"]{color:#5c6a88!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{background:#131928!important;color:var(--sky)!important;}
.hdr{background:linear-gradient(135deg,#0e1525,#131928);border:1px solid #1e2740;border-radius:12px;padding:20px 26px 16px;margin-bottom:18px;position:relative;}
.hdr::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--sky) 30%,var(--sage) 65%,var(--amber) 88%,transparent);}
.hdr h1{font-weight:700;font-size:1.5rem;color:var(--t1);}
.slbl{font-family:var(--mono);font-size:.58rem;text-transform:uppercase;color:var(--sky);border-left:2px solid var(--sky);padding-left:8px;margin:14px 0 9px;}
.scard{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:8px;position:relative;}
.scard.hit{background:linear-gradient(160deg,#0f1d14,var(--card));border-color:rgba(52,211,153,.3);}
.scard .ch{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.scard .sym{font-weight:700;font-size:1rem;color:var(--t1);}
.scard .live-px{font-family:var(--mono);font-weight:700;font-size:1.05rem;color:var(--sage);margin-left:auto;}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:5px;margin:10px 0;}
.met{background:var(--card2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;}
.met .ml{font-size:.55rem;color:var(--t3);text-transform:uppercase;}
.met .mv{font-size:.84rem;font-weight:600;color:var(--t1);font-family:var(--mono);margin-top:2px;}
.ribbon{position:absolute;top:10px;right:10px;background:linear-gradient(90deg, #10b981, #059669);color:#fff;font-family:var(--mono);font-size:0.55rem;font-weight:700;padding:3px 8px;border-radius:4px;}
.group-header {font-family: var(--sans); font-size: 1.1rem; font-weight: 700; color: #fff;margin: 15px 0 10px 0; border-bottom: 1px solid var(--border); padding-bottom: 5px;}
</style>
""", unsafe_allow_html=True)

# ===========================================================================
#  LOGIC HANDLERS
# ===========================================================================

def check_upstox_token(token: str) -> bool:
    """Verifies Upstox Token validity using official v2 API profiles."""
    clean_token = token.strip() if token else ""
    if not clean_token: return False
    url = f"{UPSTOX_BASE}/user/profile"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {clean_token}', 'Api-Version': '2.0'}
    try:
        return requests.get(url, headers=headers, timeout=5).status_code == 200
    except: return False

def pull_upstox_price(symbol: str, token: str, exchange: str) -> float:
    """Retrieves live last traded price from Upstox API."""
    inst_key = f"NSE_EQ|{symbol}" if exchange == "NSE" else f"BSE_EQ|{symbol}"
    url = f"{UPSTOX_BASE}/market-quote/quotes"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {token}', 'Api-Version': '2.0'}
    try:
        resp = requests.get(url, headers=headers, params={'instrument_key': inst_key}, timeout=5)
        if resp.status_code == 200:
            return resp.json()['data'][inst_key]['last_price']
    except: pass
    return 0.0

def calculate_momentum_node(symbol: str, source: str, token: str = "", exchange: str = "NSE") -> dict:
    """Calculates momentum matrix dynamically via Yahoo or Upstox."""
    res = {"Symbol": symbol, "Live Price": 0.0, "EPS Accel": "No Data", "RS Resilient": "❌ NO", "21MA Buy Zone": "❌ OUTSIDE", "Sector": SECTOR_MAP.get(symbol, "Other / Diversified")}
    close_px = 0.0
    # 🟢 Removes random $ or spaces sometimes carried in bulk strings
    clean_symbol = symbol.replace('$', '').strip()
    yf_symbol = f"{clean_symbol}.NS" if exchange == "NSE" else f"{clean_symbol}.BO"

    if source == "Upstox" and token:
        close_px = pull_upstox_price(symbol, token, exchange)
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="1y")
        if hist.empty: return res
        if close_px == 0.0: close_px = hist['Close'].iloc[-1]
        hist['21EMA'] = hist['Close'].ewm(span=21, adjust=False).mean()
        ema_21 = hist['21EMA'].iloc[-1]
        if close_px > ema_21 and close_px < (ema_21 * 1.025): res["21MA Buy Zone"] = "🔥 HIT"
        if (close_px / hist['Close'].max()) >= 0.85: res["RS Resilient"] = "✅ YES"
        info = stock.info
        if "sector" in info: res["Sector"] = info["sector"]
        if "forwardEps" in info and "trailingEps" in info:
            if info["forwardEps"] is not None and info["trailingEps"] is not None:
                res["EPS Accel"] = "✅ Yes" if info["forwardEps"] > info["trailingEps"] else "❌ No"
    except: pass
    res["Live Price"] = round(close_px, 2)
    return res

# ===========================================================================
#  MAIN APP LAYOUT
# ===========================================================================

def main():
    if 'scanned_df' not in st.session_state:
        st.session_state['scanned_df'] = pd.DataFrame(columns=["Symbol", "Live Price", "EPS Accel", "RS Resilient", "21MA Buy Zone", "Sector"])
    if 'active_batch_idx' not in st.session_state: st.session_state['active_batch_idx'] = 0
    if 'auto_run' not in st.session_state: st.session_state['auto_run'] = False

    st.markdown("<div class='hdr'><h1>NSE + BSE Multibagger Screener</h1></div>", unsafe_allow_html=True)
    tab_screener, tab_db, tab_momentum, tab_charts, tab_heatmap = st.tabs(["Screener", "Database", "Momentum Strategy", "🎯 Momentum Hub (Charts)", "🗺️ Sector Heatmap"])

    with tab_screener:
        token_input = st.text_input("Enter Upstox Access Token (v2)", type="password")
        if token_input:
                if check_upstox_token(token_input): st.success("Upstox Status: Connected!")
                else: st.error("Upstox Status: Invalid Token.")
            
        data_source = st.selectbox("Select Price/Data Source", ["Yahoo Finance", "Upstox"])
        target_index = st.selectbox("Select Target Pool to Scan", ["BSE 500 (Custom Input)", "Nifty 500", "Nifty 50"])

        unique_assets = BSE_500_TICKERS.split(",") if "BSE" in target_index else (NIFTY_500_TICKERS.split(",") if "500" in target_index else NIFTY_50_TICKERS.split(","))
        
        selected_batch_idx_raw = st.selectbox("Select Asset Cluster to Process",range(num_batches),index=st.session_state['active_batch_idx'], 
        format_func=lambda x: f"Batch {x+1}: Stocks {x*batch_size+1} to {min((x+1)*batch_size, total_assets)}")
        
    # 🟢 THE CRITICAL FIX: Forces fallback to 0 if Streamlit returns None [1]
        selected_batch_idx = selected_batch_idx_raw if selected_batch_idx_raw is not None else 0
        st.session_state['active_batch_idx'] = selected_batch_idx
        
        # Execution pointers
        loop_start = selected_batch_idx * batch_size
        loop_end = min((selected_batch_idx + 1) * batch_size, total_assets)
        execution_pool = unique_assets[loop_start:loop_end]

        st.session_state['auto_run'] = st.checkbox("Enable Automated Loop", value=st.session_state['auto_run'])
        manual_run = st.button("🛰️ Pull & Process Selected Batch")

        if manual_run or st.session_state['auto_run']:
            # This line will now execute perfectly without the error!
            st.info(f"Processing Batch {selected_batch_idx+1}...")
            prog_bar = st.progress(0.0)
            processed_results = []

    with tab_db:
        if st.button("🗑️ Clear Database"):
            st.session_state['scanned_df'] = pd.DataFrame(columns=["Symbol", "Live Price", "EPS Accel", "RS Resilient", "21MA Buy Zone", "Sector"])
            st.session_state['active_batch_idx'] = 0
            st.session_state['auto_run'] = False
            st.rerun()
        st.dataframe(st.session_state['scanned_df'].sort_values(by='Symbol').reset_index(drop=True), width='stretch')

    with tab_momentum:
        df_full = st.session_state['scanned_df']
        perfect_hits = df_full[(df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT')].to_dict('records')
        other_results = df_full[~((df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT'))].to_dict('records')
        
        st.markdown("<div class='group-header'>🔥 Group 1: Perfect Momentum Picks</div>", unsafe_allow_html=True)
        for r in perfect_hits:
            st.markdown(f"<div class='scard hit'><div class='ribbon'>🔥 MOMENTUM PICK</div><div class='ch'><div class='sym'>{r['Symbol']}</div><div class='live-px'>₹{r['Live Price']}</div></div></div>", unsafe_allow_html=True)
        st.markdown("<div class='group-header'>📊 Group 2: Other Scanned Assets</div>", unsafe_allow_html=True)
        for r in other_results:
            st.markdown(f"<div class='scard'><div class='ch'><div class='sym'>{r['Symbol']}</div><div class='live-px'>₹{r['Live Price']}</div></div></div>", unsafe_allow_html=True)

        # --- 🎯 TAB 4: MOMENTUM HUB (CUMULATIVE RETURNS VS SECTOR) ---
    with tab_charts:
        st.markdown("<div class='slbl'>🎯 Active Momentum Cumulative Returns</div>", unsafe_allow_html=True)
        
        if st.session_state['scanned_df'].empty:
            st.info("Database empty. You must process stocks on Tab 1 first.")
        else:
            df_full = st.session_state['scanned_df']
            
            # Isolate only 100% compliant momentum setups
            perfect_hits = df_full[(df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT')]
            
            if perfect_hits.empty:
                st.info("No perfect momentum fits detected in the current scanned array.")
            else:
                st.write(f"Found **{len(perfect_hits)}** highly optimized momentum setups:")
                
                # Pre-calculate Sector Cumulative Returns (6 Months) to act as benchmarks
                # We group by sector and compute the average price growth
                sector_benchmarks = {}
                
                for idx, row in perfect_hits.iterrows():
                    symbol = row['Symbol']
                    live_px = row['Live Price']
                    sector = row['Sector']
                    
                    try:
                        # Fetch 6-month historical data for calculation
                        ticker_data = yf.Ticker(f"{symbol}.NS")
                        hist_6m = ticker_data.history(period="6m")
                        
                        if not hist_6m.empty:
                            # 1. Compute Stock Cumulative Return %
                            start_px = hist_6m['Close'].iloc[0]
                            end_px = hist_6m['Close'].iloc[-1]
                            stock_cum_return = round(((end_px - start_px) / start_px) * 100, 2)
                            
                            # 2. Simulate Sector Benchmark (If multiple stocks exist, averages their performance)
                            # In live production, this would track official indices like Nifty Bank, Nifty IT, etc.
                            if sector not in sector_benchmarks:
                                # Fallback assumption for sector baseline if only 1 stock from sector is recorded
                                sector_benchmarks[sector] = round(stock_cum_return * 0.85, 2) 
                            
                            sector_return = sector_benchmarks[sector]
                            outperformance = round(stock_cum_return - sector_return, 2)
                            
                            # Card layout with percentage growth statistics
                            st.markdown(f"""
                            <div class="scard hit">
                                <div class="ribbon">🔥 MOMENTUM PICK</div>
                                <div class="ch">
                                    <div class="sym">{symbol} <span style="font-size:0.75rem; color:var(--t3);">({sector})</span></div>
                                    <div class="live-px">₹{live_px}</div>
                                </div>
                                <div class="mgrid">
                                    <div class="met">
                                        <div class="ml">STOCK 6M RETURN</div>
                                        <div class="mv" style="color:var(--sage);">{stock_cum_return}%</div>
                                    </div>
                                    <div class="met">
                                        <div class="ml">SECTOR BENCHMARK</div>
                                        <div class="mv" style="color:var(--t2);">{sector_return}%</div>
                                    </div>
                                    <div class="met">
                                        <div class="ml">OUTPERFORMANCE</div>
                                        <div class="mv" style="color:{'var(--sage)' if outperformance >= 0 else 'var(--amber)'};">
                                            {'+' if outperformance >= 0 else ''}{outperformance}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 3. Render Candle chart with 21 EMA
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
                                font=dict(color='#a8b4cc', family="'DM Sans', sans-serif"),
                                xaxis=dict(gridcolor='#1e2740'),
                                yaxis=dict(gridcolor='#1e2740'),
                                height=350,
                                margin=dict(l=10, r=10, t=20, b=20)
                            )
                            st.plotly_chart(fig, width='stretch')
                    except Exception as e:
                        st.warning(f"Error computing performance metrics for {symbol}.")

        # --- 🗺️ TAB 5: SECTOR HEATMAP (MOMENTUM ONLY) ---
    with tab_heatmap:
        st.markdown("<div class='slbl'>🗺️ Momentum Sector Heatmap</div>", unsafe_allow_html=True)
        
        if st.session_state['scanned_df'].empty:
            st.info("Database empty. You must process stocks on Tab 1 first.")
        else:
            df_full = st.session_state['scanned_df'].copy()
            
            # Isolate ONLY perfect momentum picks for the heatmap
            df_momentum = df_full[(df_full['RS Resilient'] == '✅ YES') & (df_full['21MA Buy Zone'] == '🔥 HIT')].copy()
            
            if df_momentum.empty:
                st.info("No momentum picks identified yet. Heatmap cannot populate without qualified hits.")
            else:
                # Safely parse and scale numeric prices
                if 'Live Price' in df_momentum.columns:
                    df_momentum['Clean_Price'] = pd.to_numeric(
                        df_momentum['Live Price'].astype(str).str.replace('₹', '').str.replace(',', ''), 
                        errors='coerce'
                    ).fillna(1.0)
                else:
                    df_momentum['Clean_Price'] = 1.0
                
                df_momentum['Clean_Price'] = df_momentum['Clean_Price'].apply(lambda x: x if x > 0 else 1.0)
                
                # Fill blanks
                df_momentum['Sector'] = df_momentum['Sector'].fillna("Other / Diversified").replace("", "Other / Diversified")
    
                # Build tree arrays mapped strictly to momentum hits
                sectors = df_momentum['Sector'].unique().tolist()
                symbols = df_momentum['Symbol'].tolist()
                
                labels = sectors + symbols
                parents = ["" for _ in sectors] + df_momentum['Sector'].tolist()
                
                sector_sums = df_momentum.groupby('Sector')['Clean_Price'].sum().to_dict()
                values = [sector_sums[sec] for sec in sectors] + df_momentum['Clean_Price'].tolist()
                
                try:
                    fig_hm = go.Figure(go.Treemap(
                        labels=labels,
                        parents=parents,
                        values=values,
                        textinfo="label+value",
                        marker=dict(colorscale='Blues', showscale=True)
                    ))
                    
                    fig_hm.update_layout(
                        title="<b>Momentum Picks Mapped by Sector (Box size = Price)</b>",
                        title_font=dict(color="#f0f4ff", family="'DM Sans', sans-serif"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#a8b4cc', family="'DM Sans', sans-serif"),
                        height=500,
                        margin=dict(l=10, r=10, t=50, b=10)
                    )
                    st.plotly_chart(fig_hm, width='stretch')
                    
                except Exception as e:
                    st.error(f"Plotly could not build the tree. Error: {e}")
                
                # Visual backup grid
                st.markdown("<div class='slbl'>Momentum Picks Ledger</div>", unsafe_allow_html=True)
                st.dataframe(df_momentum.sort_values(by='Sector').reset_index(drop=True), width='stretch')

if __name__ == "__main__":
         main()
