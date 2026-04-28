# -*- coding: utf-8 -*-
"""
NSE + BSE Multibagger Screener -- Streamlit Edition
~5000 Stocks | EPS Acceleration | RS Resilience | 21MA Buy Zone

INSTALL:  pip install streamlit plotly requests numpy pandas
RUN:      streamlit run screener_st.py
"""

# -- stdlib ------------------------------------------------------------------
import gzip, io, csv, json, math, time, datetime, logging, sqlite3, threading
from typing import Optional
from pathlib import Path

# -- third-party --------------------------------------------------------------
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ===========================================================================
#  PAGE CONFIG
# ===========================================================================
st.set_page_config(
    page_title="NSE+BSE Multibagger Screener",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===========================================================================
#  GLOBAL CSS  — warm deep-navy, eye-comfort palette
# ===========================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg:     #0f1117; --surf:   #13161f; --card:  #181c28;
  --card2:  #1c2030; --border: #252a3a; --border2:#2e364d;
  --sky:    #5bc4f5; --sage:   #4ecf8f; --amber: #f0b429;
  --coral:  #f07070; --lav:    #a78bfa; --tang:  #f0834a;
  --t1: #e8ecf4; --t2: #b4bdce; --t3: #737e96; --t4: #454d63;
}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {
  background: var(--bg) !important; color: var(--t2) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Header */
.screener-header {
  background: linear-gradient(135deg, #0d1624 0%, #131e30 60%, #0a1118 100%);
  border: 1px solid var(--border2); border-radius: 12px;
  padding: 22px 28px 18px; margin-bottom: 20px; position: relative; overflow: hidden;
}
.screener-header::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--sky) 25%, var(--sage) 65%, var(--amber) 88%, transparent);
}
.screener-header h1 {
  font-weight: 800; font-size: 1.6rem; color: var(--t1);
  letter-spacing: -.5px; margin: 0; line-height: 1.1;
}
.screener-header .sub {
  font-family: 'JetBrains Mono', monospace; font-size: .62rem;
  color: var(--t3); margin-top: 6px; letter-spacing: .8px;
}

/* Section labels */
.sec-lbl {
  font-family: 'JetBrains Mono', monospace; font-size: .6rem;
  letter-spacing: 2px; text-transform: uppercase; color: var(--sky);
  border-left: 2px solid var(--sky); padding-left: 9px; margin: 16px 0 10px;
}

/* KPI cards */
.kpi-row { display: flex; gap: 10px; margin-bottom: 18px; flex-wrap: wrap; }
.kpi {
  flex: 1; min-width: 100px; background: var(--card);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; text-align: center;
}
.kpi .v { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.85rem; line-height: 1; }
.kpi .l { font-size: .58rem; color: var(--t3); text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
.c-sky   { color: var(--sky); }   .c-sage  { color: var(--sage); }
.c-amber { color: var(--amber); } .c-lav   { color: var(--lav); }
.c-tang  { color: var(--tang); }  .c-coral { color: var(--coral); }

/* Badges */
.badge {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 8px; border-radius: 4px;
  font-family: 'JetBrains Mono', monospace; font-size: .58rem; letter-spacing: .3px;
}
.b-rs   { background:rgba(91,196,245,.1);  color:var(--sky);   border:1px solid rgba(91,196,245,.25); }
.b-bz   { background:rgba(240,131,74,.1);  color:var(--tang);  border:1px solid rgba(240,131,74,.25); }
.b-acc  { background:rgba(240,180,41,.1);  color:var(--amber); border:1px solid rgba(240,180,41,.25); }
.b-srp  { background:rgba(167,139,250,.1); color:var(--lav);   border:1px solid rgba(167,139,250,.25); }
.b-sal  { background:rgba(78,207,143,.1);  color:var(--sage);  border:1px solid rgba(78,207,143,.25); }
.b-star { background:rgba(240,180,41,.15); color:#f5c842;       border:1px solid rgba(245,200,66,.35); font-weight:700; }
.b-nse  { background:rgba(91,196,245,.08); color:var(--sky);   border:1px solid rgba(91,196,245,.2); font-size:.52rem; }
.b-bse  { background:rgba(240,180,41,.08); color:var(--amber); border:1px solid rgba(240,180,41,.2); font-size:.52rem; }

/* Stock cards */
.scard {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px; margin-bottom: 10px;
}
.scard.perfect {
  background: linear-gradient(160deg, #141c18, var(--card));
  border-color: rgba(78,207,143,.28);
}
.star-tag {
  font-family: 'JetBrains Mono', monospace; font-size: .55rem;
  letter-spacing: 2px; color: var(--sage); margin-bottom: 10px;
  text-transform: uppercase;
}
.card-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;
}
.sym { font-weight: 800; font-size: 1.1rem; color: var(--t1); }
.nm  { font-size: .72rem; color: var(--t3); }
.sect {
  font-family: 'JetBrains Mono', monospace; font-size: .58rem;
  color: var(--t4); background: var(--card2); padding: 2px 7px; border-radius: 3px;
}
.px-val {
  margin-left: auto; font-family: 'JetBrains Mono', monospace;
  font-weight: 600; font-size: 1rem; color: var(--t1);
}

/* Metric grid inside cards */
.mgrid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 6px; margin: 12px 0;
}
.met {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: 6px; padding: 9px 11px;
}
.met .ml { font-size: .57rem; color: var(--t4); text-transform: uppercase; letter-spacing: .8px; }
.met .mv { font-size: .86rem; font-weight: 600; color: var(--t1); margin-top: 3px; font-family: 'JetBrains Mono', monospace; }

/* Intel panels */
.igrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px; }
.ip {
  background: #111520; border: 1px solid var(--border);
  border-radius: 7px; padding: 12px 13px;
}
.ip .il { font-family: 'JetBrains Mono', monospace; font-size: .57rem; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }
.ip .iv { font-size: .82rem; font-weight: 600; color: var(--t1); line-height: 1.3; }
.ip .is { font-family: 'JetBrains Mono', monospace; font-size: .61rem; color: var(--t4); margin-top: 4px; }

/* Staircase */
.stair {
  display: flex; align-items: flex-end; gap: 5px; height: 82px;
  padding: 6px 8px 0; background: #111520; border: 1px solid var(--border);
  border-radius: 7px; margin: 12px 0;
}
.scol { display:flex; flex-direction:column; align-items:center; flex:1; height:100%; justify-content:flex-end; }
.sarr { font-size:.58rem; margin-bottom:2px; line-height:1; font-family:'JetBrains Mono',monospace; }
.sbar {
  width:100%; border-radius:3px 3px 0 0; min-height:8px;
  display:flex; align-items:center; justify-content:center;
  font-size:.57rem; font-weight:600; color:rgba(0,0,0,.85);
}
.slb { font-family:'JetBrains Mono',monospace; font-size:.53rem; color:var(--t4); margin-top:3px; white-space:nowrap; }

/* Progress */
.prog-box {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 18px; margin-bottom: 16px;
}
.prog-box .plbl { font-size: .72rem; font-weight: 600; color: var(--sky); margin-bottom: 8px; }
.prog-box .pmsg { font-family: 'JetBrains Mono', monospace; font-size: .62rem; color: var(--t4); margin-top: 6px; }

/* Rules */
.rule-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px; height: 100%;
}
.rule-num { font-family: 'JetBrains Mono', monospace; font-size: .57rem; letter-spacing: 2px; margin-bottom: 7px; text-transform: uppercase; }
.rule-card h4 { font-size: .9rem; font-weight: 700; color: var(--t1); margin-bottom: 7px; }
.rule-card p  { font-size: .73rem; color: var(--t2); line-height: 1.65; }
.rule-ex { margin-top: 9px; padding: 7px 10px; background: rgba(0,0,0,.25); border-radius: 5px; font-family: 'JetBrains Mono', monospace; font-size: .63rem; }

/* Perfect setup box */
.setup-box {
  position: relative; background: linear-gradient(135deg, #131c15, var(--card));
  border: 1px solid rgba(78,207,143,.22); border-radius: 10px;
  padding: 18px 20px; margin: 12px 0;
}
.setup-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.si { background: rgba(0,0,0,.25); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; flex: 1; min-width: 140px; }
.si .sil { font-family: 'JetBrains Mono', monospace; font-size: .56rem; color: var(--t4); text-transform: uppercase; letter-spacing: .8px; }
.si .siv { font-size: .78rem; font-weight: 600; color: var(--t1); margin-top: 3px; }

/* Table */
.tbl-wrap { overflow-x: auto; }

/* Streamlit overrides */
[data-testid="stSidebar"] { background: #13161f !important; border-right: 1px solid #252a3a !important; }
[data-testid="stSidebar"] * { color: var(--t2) !important; }
.stButton > button {
  background: linear-gradient(135deg, #1a4a8a, #0d3066) !important;
  color: var(--sky) !important; border: 1px solid rgba(91,196,245,.3) !important;
  border-radius: 8px !important; font-weight: 700 !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  transition: all .2s !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, #1e5599, #1040a0) !important;
  box-shadow: 0 4px 20px rgba(91,196,245,.18) !important;
  transform: translateY(-1px) !important;
}
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background: #181c28 !important; border: 1px solid #2e364d !important;
  color: #e8ecf4 !important; border-radius: 7px !important;
  font-family: 'JetBrains Mono', monospace !important;
}
.stSelectbox > div > div { background: #181c28 !important; border-color: #2e364d !important; }
.stSlider > div { color: var(--t2) !important; }
div[data-baseweb="slider"] > div { background: #2e364d !important; }
div[data-baseweb="slider"] > div > div { background: var(--sky) !important; }
.stTabs [role="tablist"] { background: #181c28; border: 1px solid #252a3a; border-radius: 10px; padding: 3px; }
.stTabs [role="tab"]          { color: var(--t3) !important; border-radius: 7px !important; font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { background: #1f2438 !important; color: var(--sky) !important; }
.stDataFrame { border-radius: 10px !important; overflow: hidden; }
div[data-testid="stInfo"]    { background: rgba(91,196,245,.07) !important; border: 1px solid rgba(91,196,245,.2) !important; }
div[data-testid="stSuccess"] { background: rgba(78,207,143,.07) !important; border: 1px solid rgba(78,207,143,.2) !important; }
div[data-testid="stWarning"] { background: rgba(240,180,41,.07) !important; border: 1px solid rgba(240,180,41,.2) !important; }
div[data-testid="stError"]   { background: rgba(240,112,112,.07) !important; border: 1px solid rgba(240,112,112,.2) !important; }
.stProgress > div > div { background: linear-gradient(90deg, var(--sky), var(--sage)) !important; }
#MainMenu, footer, header { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ===========================================================================
#  CONFIGURATION
# ===========================================================================
UPSTOX_BASE    = "https://api.upstox.com/v2"
# Upstox instrument master — multiple sources tried in order
INSTRUMENT_URLS = [
    # Source 1: Upstox CDN (requires Accept header, may need auth)
    "https://assets.upstox.com/market-assets/instruments/exchange/complete.csv.gz",
    # Source 2: Upstox alternate CDN path
    "https://assets.upstox.com/market-assets/instruments/v2/exchange/complete.json.gz",
]
INSTRUMENT_URL = INSTRUMENT_URLS[0]   # kept for backward compat
UNIVERSE_CACHE = Path("universe_cache.json")
FUND_DATA_PATH = Path("fundamentals.json")
QUOTE_BATCH    = 200
QL             = ["Q1", "Q2", "Q3", "Q4 Latest"]

NSE_SECTOR_URLS = {
    "NSE_INDEX|Nifty IT":     "https://www.nse-india.com/content/indices/ind_niftyit.csv",
    "NSE_INDEX|Nifty Bank":   "https://www.nse-india.com/content/indices/ind_niftybank.csv",
    "NSE_INDEX|Nifty Auto":   "https://www.nse-india.com/content/indices/ind_niftyauto.csv",
    "NSE_INDEX|Nifty FMCG":   "https://www.nse-india.com/content/indices/ind_niftyfmcg.csv",
    "NSE_INDEX|Nifty Pharma": "https://www.nse-india.com/content/indices/ind_niftypharma.csv",
    "NSE_INDEX|Nifty Energy": "https://www.nse-india.com/content/indices/ind_niftyenergy.csv",
    "NSE_INDEX|Nifty Metal":  "https://www.nse-india.com/content/indices/ind_niftymetal.csv",
    "NSE_INDEX|Nifty Realty": "https://www.nse-india.com/content/indices/ind_niftyrealty.csv",
    "NSE_INDEX|Nifty Financial Services":
        "https://www.nse-india.com/content/indices/ind_niftyfinservice.csv",
}

# ===========================================================================
#  SESSION STATE INITIALISATION
# ===========================================================================
# -- Thread-safe scan state ----------------------------------------------
# Background thread writes to _SCAN (a plain dict — safe to share).
# Main thread reads _SCAN and copies finished results to session_state.
import threading as _threading
_SCAN: dict = {
    "running":   False,
    "progress":  0.0,
    "msg":       "",
    "stats":     {"total": 0, "processed": 0, "passed": 0, "perfect": 0},
    "results":   [],
    "done":      False,
    "error":     "",
    "log":       [],          # full error/warning log visible in UI
}
_SCAN_LOCK = _threading.Lock()

def _scan_update(**kw):
    """Thread-safe write to _SCAN."""
    with _SCAN_LOCK:
        for k, v in kw.items():
            _SCAN[k] = v

def _scan_log(msg: str):
    with _SCAN_LOCK:
        _SCAN["log"].append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def init_state():
    defaults = {
        "results":        [],
        "scan_running":   False,
        "scan_progress":  0.0,
        "scan_msg":       "",
        "scan_stats":     {"total": 0, "processed": 0, "passed": 0, "perfect": 0},
        "universe":       [],
        "universe_stats": {},
        "scan_done":      False,
        "exch_filter":    "All",
        "last_scan_time": None,
        "token_status":   "unknown",
        "dl_running":     False,
        "dl_msg":         "",
        "dl_error":       "",   # "unknown" | "valid" | "invalid"
        "token_user":     "",
        "download_error": "",
        "download_log":   [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ===========================================================================
#  UPSTOX HELPERS  (sync — Streamlit is synchronous)
# ===========================================================================
def upstox_hdr(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

def fetch_hist(ikey: str, token: str, days: int = 430) -> Optional[pd.DataFrame]:
    to_d   = datetime.date.today()
    from_d = to_d - datetime.timedelta(days=days)
    url = (f"{UPSTOX_BASE}/historical-candle/{ikey}/day/"
           f"{to_d.isoformat()}/{from_d.isoformat()}")
    try:
        r = requests.get(url, headers=upstox_hdr(token), timeout=15)
        if r.status_code != 200:
            return None
        candles = r.json().get("data", {}).get("candles", [])
        if not candles or len(candles) < 30:
            return None
        df = pd.DataFrame(candles, columns=["ts","O","H","L","C","V","OI"])
        df["ts"] = pd.to_datetime(df["ts"])
        return df.sort_values("ts").reset_index(drop=True)
    except Exception:
        return None

def fetch_batch_ltp(keys: list, token: str) -> dict:
    out = {}
    for i in range(0, len(keys), QUOTE_BATCH):
        batch = keys[i:i+QUOTE_BATCH]
        try:
            r = requests.get(f"{UPSTOX_BASE}/market-quote/quotes",
                headers=upstox_hdr(token),
                params={"instrument_key": ",".join(batch)}, timeout=15)
            if r.status_code == 200:
                for v in r.json().get("data", {}).values():
                    ltp  = v.get("last_price") or v.get("ltp")
                    ikey = v.get("instrument_token") or v.get("instrument_key")
                    if ltp and ikey:
                        out[ikey] = float(ltp)
        except Exception:
            pass
        time.sleep(0.2)
    return out

# ===========================================================================
#  SYMBOL MASTER LISTS
#  500 NSE symbols + 500 BSE scrip codes shipped in the app.
#  These are resolved to full instrument details via Upstox API in batches of 50.
#  The database grows incrementally — each resolved batch is stored in SQLite.
# ===========================================================================

# -- 500 NSE trading symbols --------------------------------------------------
NSE_500 = [
"TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM","MPHASIS","COFORGE","PERSISTENT","KPIT",
"LTTS","OFSS","TATAELXSI","CYIENT","BIRLASOFT","ZENSARTECH","INTELLECT","HAPPSTMNDS",
"NEWGEN","TANLA","RATEGAIN","LATENTVIEW","ECLERX","MASTECH","SASKEN","RAMCOSYS",
"HDFCBANK","ICICIBANK","KOTAKBANK","AXISBANK","SBIN","INDUSINDBK","BANDHANBNK",
"FEDERALBNK","IDFCFIRSTB","AUBANK","RBLBANK","YESBANK","CANBK","BANKBARODA","PNB",
"UNIONBANK","INDIANB","KARURVYSYA","DCBBANK","CSBBANK","SOUTHBANK","EQUITASBNK",
"UJJIVANSFB","KARNATAKABK","TMKANSASBNK","LAKSHVILAS","JANDKBANK","CITYUNIONBK",
"HINDUNILVR","ITC","NESTLEIND","BRITANNIA","DABUR","MARICO","GODREJCP","COLPAL",
"EMAMILTD","TATACONSUM","JUBLFOODS","VBL","MCDOWELL-N","RADICO","PGHH","CCL",
"BIKAJI","PATANJALI","PRATAAP","KRBL","HATSUN","DODLA","HERITAGE","UBL","UNITDSPR",
"MARUTI","TATAMOTORS","M&M","BAJAJ-AUTO","EICHERMOT","HEROMOTOCO","ASHOKLEY",
"MOTHERSON","TVSMOTOR","BHARATFORG","BALKRISIND","BOSCHLTD","EXIDEIND","CEATLTD",
"SCHAEFFLER","SKFINDIA","WABCOINDIA","MINDAIND","SUPRAJIT","MRF","APOLLOTYRE",
"JKTYRE","TIINDIA","ENDURANCE","CRAFTSMAN","LUMAXTECH","VARROC","ESCORTS","FORCE",
"SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","AUROPHARMA","TORNTPHARM","LUPIN","BIOCON",
"ABBOTINDIA","ALKEM","IPCALAB","LALPATHLAB","METROPOLIS","MAXHEALTH","FORTIS",
"APOLLOHOSP","SYNGENE","GLENMARK","AJANTPHARM","GRANULES","NATCOPHARM","PFIZER",
"GLAXO","LAURUSLABS","ERIS","JUBLPHARMA","CAPLIPOINT","STRIDES","GLAND","FDC",
"STAR","SUVENPHARM","DIVIS","SHILPAMED","MARKSANS","WINDLAS","WOCKPHARMA","IPCA",
"RELIANCE","ONGC","IOC","BPCL","POWERGRID","NTPC","GAIL","PETRONET","HINDPETRO",
"MRPL","GUJARATGAS","IGL","MGL","ADANIPORTS","TATAPOWER","TORNTPOWER","NHPC",
"SJVN","SUZLON","INOXWIND","ADANIGREEN","ADANIPOWER","CESC","RECLTD","PFC","IREDA",
"TATASTEEL","HINDALCO","JSWSTEEL","SAIL","NMDC","VEDL","NATIONALUM","APLAPOLLO",
"WELSPUNIND","JINDALSTEL","RATNAMANI","MOIL","COALINDIA","HINDCOPPER","MANDHATU",
"BAJFINANCE","BAJAJFINSV","CHOLAFIN","MUTHOOTFIN","MANAPPURAM","LICHOUSING",
"PNBHOUSING","CANFINHOME","REPCO","M&MFIN","SHRIRAMFIN","IIFL","CREDITACC",
"HDFCLIFE","SBILIFE","ICICIGI","ICICILOPRU","STARHEALTH","NIACL","ICICIGI",
"BHARTIARTL","IDEA","TATACOMM","HFCL","STLTECH","VINDHYATEL","TEJAS",
"ULTRACEMCO","SHREECEM","AMBUJACEM","ACCLTD","DALMIACEM","JKCEMENT","RAMCOCEM",
"HEIDELBERG","BIRLACORPN","INDIACEM","KESORAMIND","NCLTIND","PRICOL","PRISMJOHS",
"SIEMENS","ABB","BHEL","CUMMINS","THERMAX","KEC","KALPATPOWR","GRINDWELL",
"CGPOWER","ELECON","AIA","TIMKEN","KAYNES","DIXON","AMBER","HAVELLS","VOLTAS",
"BLUESTAR","CROMPTON","VGUARD","ORIENTELEC","WHIRLPOOL","SYMPHONY","TTKHLTCR",
"DLF","LODHA","GODREJPROP","PRESTIGE","OBEROIRLTY","PHOENIXLTD","BRIGADE",
"SOBHA","KOLTEPATIL","PURVA","SUNTECK","ELDECO","NESCO","MAHINDCIE",
"HAL","BEL","COCHINSHIP","MAZDOCK","DATAPATTNS","MTAR","PARAS","BEML","GRSE",
"MIDHANI","WALCHNDNAGR","DYNAMATECH","BDL","BHARAT",
"DMART","TRENTLTD","NYKAA","ZOMATO","PAGEIND","KAJARIACER","CENTURYPLY",
"TITAN","KALYANKJIL","RAJESHEXPO","ABFRL","MANYAVAR","VEDANT","CAMPUS",
"INDIGO","LEMONTRE","CHALET","EIH","TAJGVK","ORIENTHOTEL","WONDERLA",
"PVR","INOXLEISUR","SUNTV","ZEEL","NDTV","DISHTV",
"IRCTC","IRFC","RVNL","RITES","IRCON","NBCC","HUDCO",
"SRF","DEEPAKNTR","NAVINFLUOR","AARTIIND","VINATIORGA","TATACHEM","CHAMBLFERT",
"COROMANDEL","PIIND","GHCL","DEEPAKFERT","GNFC","GSFC","NFL","RCF","NEOGEN",
"ALKYL","SUDARSCHEM","FINEORG","NOCIL","GALAXY","ANUPAM","VALIANT","CAMS",
"PIDILITIND","ASIANPAINT","BERGEPAINT","KANSAINER","LAXMIMETAL","PRINCEPIPE",
"APOLLOPIPE","FINOLEX","ASTRAL","SUPREMEIND","NILKAMAL","KAPLAM","TIME",
"CONCOR","DELHIVERY","BLUEDART","GATI","TCI","ALLCARGO","MAHINDLOG",
"BIOCON","GLAND","DIVIS","SUNPHARMA","DRREDDY",
"ADANIENT","ADANIPORTS","ADANIGREEN","ADANIPOWER","ADANIGAS","ADANITRANS",
"LT","LARSENTOUBRO","LTFIN","LTTECHNO","LTTS","LTIM",
"TATAMOTORS","TATACONSUM","TATACHEM","TATASTEEL","TATAPOWER","TATAELXSI",
"RELIANCE","JSWSTEEL","JSWENERGY","JSWAL","JSWINFRA",
]

# -- 500 BSE scrip codes -------------------------------------------------------
BSE_500 = [
532540,500209,507685,532281,532755,540005,526299,532541,533179,542651,
540115,532466,500408,532175,532400,543227,540900,532790,543320,543321,
500180,532174,500247,532215,500112,532187,541153,500469,539437,540611,
532648,532483,532134,532461,532477,532814,540065,532772,543354,532679,
500696,500875,500790,500825,500096,531642,532424,500830,531162,500800,
540180,532532,532497,517214,519570,532054,500696,519152,500215,500790,
532500,500570,500520,532977,505200,500182,500477,532343,500493,500530,
500086,500878,532539,500048,533520,519600,500533,505200,532343,
524715,500124,500087,532488,524804,500420,500257,532523,500488,539523,
508869,543220,532296,542650,526235,506194,542532,500359,507180,524745,
500325,500312,532555,532898,532155,532921,500400,530965,500547,500104,
541450,500280,500166,533519,509040,530101,500299,523467,504028,
500470,500440,500228,500295,500113,526371,532234,500498,532286,532285,
542652,519126,590073,513023,500108,532325,
500034,532978,511243,533398,511218,540777,540719,540716,532532,532978,
532454,500820,532538,500114,500331,541154,500049,543321,532868,521228,
540376,543320,500550,500002,517354,541987,503806,523642,542830,500251,
509480,532747,535801,532827,506395,506401,543181,543237,
500002,500003,500008,500010,500012,500014,500017,500020,500022,500023,
500025,500027,500031,500032,500038,500040,500043,500045,500047,500048,
500049,500052,500055,500057,500059,500061,500063,500065,500067,500071,
500073,500075,500079,500082,500084,500086,500087,500088,500092,500093,
500095,500096,500097,500101,500103,500104,500106,500109,500110,500112,
500113,500114,500116,500120,500123,500124,500125,500126,500127,500128,
500129,500130,500133,500135,500136,500137,500138,500143,500145,500146,
500147,500148,500150,500152,500153,500154,500155,500157,500158,500163,
500164,500166,500168,500171,500172,500174,500176,500178,500180,500182,
500183,500185,500186,500187,500188,500189,500190,500191,500193,500194,
500196,500197,500199,500200,500201,500202,500205,500208,500209,500215,
500217,500218,500219,500220,500222,500223,500224,500227,500228,500229,
500230,500232,500233,500234,500237,500238,500239,500241,500242,500243,
500244,500245,500247,500248,500251,500252,500253,500255,500257,500258,
500261,500262,500263,500264,500267,500269,500271,500275,500276,500277,
500278,500279,500280,500283,500284,500285,500287,500289,500290,500292,
500295,500296,500297,500298,500299,500300,500302,500303,500304,500305,
500306,500307,500308,500310,500311,500312,500313,500315,500316,500317,
500318,500319,500320,500321,500322,500323,500325,500327,500328,500329,
500330,500331,500332,500333,500335,500336,500337,500338,500339,500340,
]

# -- SQLite database for universe ----------------------------------------------
DB_PATH = Path("universe.db")

def _db_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            ikey    TEXT PRIMARY KEY,
            sym     TEXT NOT NULL,
            name    TEXT,
            exch    TEXT NOT NULL,
            sector  TEXT,
            isin    TEXT,
            added   TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_exch ON instruments(exch)")
    conn.commit()
    return conn

def db_count() -> dict:
    """Return {total, nse, bse} counts from DB."""
    try:
        conn = _db_conn()
        total = conn.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
        nse   = conn.execute("SELECT COUNT(*) FROM instruments WHERE exch='NSE'").fetchone()[0]
        bse   = conn.execute("SELECT COUNT(*) FROM instruments WHERE exch='BSE'").fetchone()[0]
        conn.close()
        return {"total": total, "nse": nse, "bse": bse}
    except Exception:
        return {"total": 0, "nse": 0, "bse": 0}

def db_load_all() -> list:
    """Load all instruments from DB as list of dicts."""
    try:
        conn  = _db_conn()
        rows  = conn.execute(
            "SELECT ikey,sym,name,exch,sector,isin FROM instruments"
        ).fetchall()
        conn.close()
        return [{"ikey":r[0],"sym":r[1],"name":r[2],"exch":r[3],
                 "sector":r[4],"isin":r[5]} for r in rows]
    except Exception:
        return []

def db_save_batch(stocks: list):
    """Insert/replace a batch of stocks into DB."""
    if not stocks:
        return
    conn = _db_conn()
    now  = datetime.datetime.now().isoformat()
    conn.executemany(
        "INSERT OR REPLACE INTO instruments(ikey,sym,name,exch,sector,isin,added)"
        " VALUES(?,?,?,?,?,?,?)",
        [(s["ikey"], s["sym"], s["name"], s["exch"],
          s.get("sector",""), s.get("isin",""), now) for s in stocks]
    )
    conn.commit()
    conn.close()

def db_get_existing_keys() -> set:
    """Return set of all ikeys already in DB."""
    try:
        conn  = _db_conn()
        keys  = {r[0] for r in conn.execute("SELECT ikey FROM instruments").fetchall()}
        conn.close()
        return keys
    except Exception:
        return set()

# -- Default universe (shown before any DB data) ----------------------------
DEFAULT_UNIVERSE = [
 {"name":"TCS",         "sym":"TCS",        "ikey":"NSE_EQ|INE467B01029","sector":"NSE_INDEX|Nifty IT",    "exch":"NSE","isin":"INE467B01029"},
 {"name":"Infosys",     "sym":"INFY",       "ikey":"NSE_EQ|INE009A01021","sector":"NSE_INDEX|Nifty IT",    "exch":"NSE","isin":"INE009A01021"},
 {"name":"HDFC Bank",   "sym":"HDFCBANK",   "ikey":"NSE_EQ|INE040A01034","sector":"NSE_INDEX|Nifty Bank",  "exch":"NSE","isin":"INE040A01034"},
 {"name":"ICICI Bank",  "sym":"ICICIBANK",  "ikey":"NSE_EQ|INE090A01021","sector":"NSE_INDEX|Nifty Bank",  "exch":"NSE","isin":"INE090A01021"},
 {"name":"Reliance",    "sym":"RELIANCE",   "ikey":"NSE_EQ|INE002A01018","sector":"NSE_INDEX|Nifty Energy", "exch":"NSE","isin":"INE002A01018"},
 {"name":"Kotak Bank",  "sym":"KOTAKBANK",  "ikey":"NSE_EQ|INE237A01028","sector":"NSE_INDEX|Nifty Bank",  "exch":"NSE","isin":"INE237A01028"},
 {"name":"Axis Bank",   "sym":"AXISBANK",   "ikey":"NSE_EQ|INE238A01034","sector":"NSE_INDEX|Nifty Bank",  "exch":"NSE","isin":"INE238A01034"},
 {"name":"SBI",         "sym":"SBIN",       "ikey":"NSE_EQ|INE062A01020","sector":"NSE_INDEX|Nifty Bank",  "exch":"NSE","isin":"INE062A01020"},
 {"name":"Wipro",       "sym":"WIPRO",      "ikey":"NSE_EQ|INE075A01022","sector":"NSE_INDEX|Nifty IT",    "exch":"NSE","isin":"INE075A01022"},
 {"name":"HCL Tech",    "sym":"HCLTECH",    "ikey":"NSE_EQ|INE860A01027","sector":"NSE_INDEX|Nifty IT",    "exch":"NSE","isin":"INE860A01027"},
 {"name":"Sun Pharma",  "sym":"SUNPHARMA",  "ikey":"NSE_EQ|INE044A01036","sector":"NSE_INDEX|Nifty Pharma","exch":"NSE","isin":"INE044A01036"},
 {"name":"Bajaj Finance","sym":"BAJFINANCE","ikey":"NSE_EQ|INE296A01024","sector":"NSE_INDEX|Nifty Financial Services","exch":"NSE","isin":"INE296A01024"},
 {"name":"Maruti",      "sym":"MARUTI",     "ikey":"NSE_EQ|INE585B01010","sector":"NSE_INDEX|Nifty Auto",  "exch":"NSE","isin":"INE585B01010"},
 {"name":"Tata Motors", "sym":"TATAMOTORS", "ikey":"NSE_EQ|INE155L01022","sector":"NSE_INDEX|Nifty Auto",  "exch":"NSE","isin":"INE155L01022"},
 {"name":"NTPC",        "sym":"NTPC",       "ikey":"NSE_EQ|INE733E01010","sector":"NSE_INDEX|Nifty Energy", "exch":"NSE","isin":"INE733E01010"},
 {"name":"ONGC",        "sym":"ONGC",       "ikey":"NSE_EQ|INE213A01029","sector":"NSE_INDEX|Nifty Energy", "exch":"NSE","isin":"INE213A01029"},
 {"name":"Tata Steel",  "sym":"TATASTEEL",  "ikey":"NSE_EQ|INE081A01020","sector":"NSE_INDEX|Nifty Metal",  "exch":"NSE","isin":"INE081A01020"},
 {"name":"ITC",         "sym":"ITC",        "ikey":"NSE_EQ|INE154A01025","sector":"NSE_INDEX|Nifty FMCG",  "exch":"NSE","isin":"INE154A01025"},
 {"name":"HUL",         "sym":"HINDUNILVR", "ikey":"NSE_EQ|INE030A01027","sector":"NSE_INDEX|Nifty FMCG",  "exch":"NSE","isin":"INE030A01027"},
 {"name":"Bharti Airtel","sym":"BHARTIARTL","ikey":"NSE_EQ|INE397D01024","sector":"NSE_INDEX|Nifty 50",    "exch":"NSE","isin":"INE397D01024"},
]

# Sector heuristic for NSE symbols without ISIN lookup
_SECTOR_MAP = {
    "IT": ("NSE_INDEX|Nifty IT", ["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM","MPHASIS",
           "COFORGE","PERSISTENT","KPIT","LTTS","OFSS","TATAELXSI","CYIENT","BIRLASOFT",
           "ZENSARTECH","INTELLECT","HAPPSTMNDS","NEWGEN","TANLA","RATEGAIN","LATENTVIEW"]),
    "BANK": ("NSE_INDEX|Nifty Bank", ["HDFCBANK","ICICIBANK","KOTAKBANK","AXISBANK","SBIN",
             "INDUSINDBK","BANDHANBNK","FEDERALBNK","IDFCFIRSTB","AUBANK","RBLBANK","YESBANK",
             "CANBK","BANKBARODA","PNB","UNIONBANK","INDIANB","KARURVYSYA","DCBBANK","CSBBANK"]),
    "FMCG": ("NSE_INDEX|Nifty FMCG", ["HINDUNILVR","ITC","NESTLEIND","BRITANNIA","DABUR",
              "MARICO","GODREJCP","COLPAL","EMAMILTD","TATACONSUM","JUBLFOODS","VBL"]),
    "AUTO": ("NSE_INDEX|Nifty Auto", ["MARUTI","TATAMOTORS","M&M","BAJAJ-AUTO","EICHERMOT",
              "HEROMOTOCO","ASHOKLEY","MOTHERSON","TVSMOTOR","BHARATFORG","BALKRISIND",
              "BOSCHLTD","EXIDEIND","CEATLTD","MRF","APOLLOTYRE","JKTYRE"]),
    "PHARMA": ("NSE_INDEX|Nifty Pharma", ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","AUROPHARMA",
               "TORNTPHARM","LUPIN","BIOCON","ABBOTINDIA","ALKEM","IPCALAB","LALPATHLAB",
               "METROPOLIS","MAXHEALTH","APOLLOHOSP","GLENMARK","AJANTPHARM","GRANULES"]),
    "ENERGY": ("NSE_INDEX|Nifty Energy", ["RELIANCE","ONGC","IOC","BPCL","POWERGRID","NTPC",
               "GAIL","PETRONET","HINDPETRO","MRPL","GUJARATGAS","IGL","MGL","ADANIGREEN",
               "TATAPOWER","TORNTPOWER","NHPC","SJVN","ADANIPOWER","CESC"]),
    "METAL": ("NSE_INDEX|Nifty Metal", ["TATASTEEL","HINDALCO","JSWSTEEL","SAIL","NMDC",
              "VEDL","NATIONALUM","APLAPOLLO","JINDALSTEL","RATNAMANI","MOIL","COALINDIA"]),
    "FIN": ("NSE_INDEX|Nifty Financial Services", ["BAJFINANCE","BAJAJFINSV","CHOLAFIN",
            "MUTHOOTFIN","MANAPPURAM","LICHOUSING","SHRIRAMFIN","M&MFIN","HDFCLIFE",
            "SBILIFE","ICICIGI","ICICILOPRU"]),
    "REALTY": ("NSE_INDEX|Nifty Realty", ["DLF","LODHA","GODREJPROP","PRESTIGE","OBEROIRLTY",
               "PHOENIXLTD","BRIGADE","SOBHA","KOLTEPATIL"]),
    "CAPGOODS": ("NSE_INDEX|Nifty 50", ["SIEMENS","ABB","BHEL","CUMMINS","THERMAX","KEC",
                 "CGPOWER","DIXON","AMBER","KAYNES","HAVELLS","VOLTAS","BLUESTAR"]),
}
_SYM_SECTOR = {}
for sec_key, (idx, syms) in _SECTOR_MAP.items():
    for s in syms:
        _SYM_SECTOR[s] = idx

def _guess_sector_nse(sym: str) -> str:
    return _SYM_SECTOR.get(sym, "NSE_INDEX|Nifty 500")

def _guess_sector_bse(sym: str) -> str:
    nse_sec = _SYM_SECTOR.get(sym, "NSE_INDEX|Nifty 500")
    return nse_sec.replace("NSE_INDEX|Nifty", "BSE_INDEX|S&P BSE")


# ===========================================================================
#  UNIVERSE LOADING
# ===========================================================================
@st.cache_data(ttl=120, show_spinner=False)
def load_universe_cache() -> list:
    """Load from DB if available, else DEFAULT_UNIVERSE."""
    db_stocks = db_load_all()
    if db_stocks:
        return db_stocks
    return DEFAULT_UNIVERSE

def _db_progress() -> str:
    c = db_count()
    if c["total"] == 0:
        return "DB empty — click Download to build"
    return (f"DB: {c['total']:,} stocks  "
            f"({c['nse']:,} NSE + {c['bse']:,} BSE)")


# ===========================================================================
#  BATCH DOWNLOADER  — 50 NSE + 50 BSE per round, stored to SQLite
# ===========================================================================

def _resolve_nse_batch(syms: list[str], token: str) -> list[dict]:
    """
    Resolve a batch of NSE trading symbols to full instrument records
    via Upstox GET /v2/market-quote/quotes.
    We call it with instrument_key = NSE_EQ|<SYM> — Upstox accepts symbol-based keys.
    """
    keys    = [f"NSE_EQ|{s}" for s in syms]
    results = []
    hdrs    = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        r = requests.get(
            f"{UPSTOX_BASE}/market-quote/quotes",
            headers=hdrs,
            params={"instrument_key": ",".join(keys)},
            timeout=15,
        )
        if r.status_code != 200:
            return []
        data = r.json().get("data", {})
        for ikey, info in data.items():
            sym = ikey.replace("NSE_EQ|","").split("|")[0]
            results.append({
                "ikey":   ikey,
                "sym":    sym,
                "name":   info.get("company_name") or info.get("symbol") or sym,
                "exch":   "NSE",
                "sector": _guess_sector_nse(sym),
                "isin":   info.get("isin",""),
            })
    except Exception:
        pass
    return results


def _resolve_bse_batch(codes: list[int], token: str) -> list[dict]:
    """
    Resolve BSE scrip codes → instrument records.
    Upstox BSE key format: BSE_EQ|<scrip_code>
    """
    keys    = [f"BSE_EQ|{c}" for c in codes]
    results = []
    hdrs    = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        r = requests.get(
            f"{UPSTOX_BASE}/market-quote/quotes",
            headers=hdrs,
            params={"instrument_key": ",".join(keys)},
            timeout=15,
        )
        if r.status_code != 200:
            return []
        data = r.json().get("data", {})
        for ikey, info in data.items():
            sym = info.get("symbol") or ikey.replace("BSE_EQ|","")
            results.append({
                "ikey":   ikey,
                "sym":    sym,
                "name":   info.get("company_name") or sym,
                "exch":   "BSE",
                "sector": _guess_sector_bse(sym),
                "isin":   info.get("isin",""),
            })
    except Exception:
        pass
    return results


def download_universe_batches(token: str, progress_cb=None) -> dict:
    """
    Download stocks 50 NSE + 50 BSE at a time, store each batch to SQLite.

    Algorithm:
    -----------------------------------------------------------------
    1. Load NSE_500 symbols and BSE_500 scrip codes
    2. Skip any already in DB (resume-safe)
    3. Walk both lists simultaneously in BATCH_SIZE=50 chunks
    4. For each chunk: resolve via Upstox market-quote/quotes API
    5. Save resolved stocks to DB immediately after each chunk
    6. Report progress after each batch
    -----------------------------------------------------------------
    Returns {ok, nse_added, bse_added, total_in_db, errors}
    """
    BATCH = 50
    existing = db_get_existing_keys()

    # Build pending lists (skip already resolved)
    nse_pending = [s for s in NSE_500  if f"NSE_EQ|{s}" not in existing]
    bse_pending = [c for c in BSE_500  if f"BSE_EQ|{c}" not in existing]

    total_pending = len(nse_pending) + len(bse_pending)
    if total_pending == 0:
        msg = f"✅ All stocks already in DB — {db_count()['total']:,} total"
        if progress_cb:
            progress_cb(1.0, msg)
        return {"ok": True, "nse_added": 0, "bse_added": 0,
                "total_in_db": db_count()["total"], "errors": []}

    nse_added = bse_added = 0
    done      = 0
    errors    = []

    # NSE batches
    nse_batches = [nse_pending[i:i+BATCH] for i in range(0, len(nse_pending), BATCH)]
    bse_batches = [bse_pending[i:i+BATCH] for i in range(0, len(bse_pending), BATCH)]
    total_batches = len(nse_batches) + len(bse_batches)
    batch_num     = 0

    # Process NSE
    for batch in nse_batches:
        batch_num += 1
        pct = done / total_pending
        if progress_cb:
            progress_cb(pct,
                f"NSE batch {batch_num}/{len(nse_batches)} "
                f"({batch[0]}…{batch[-1]})  —  "
                f"{nse_added} NSE + {bse_added} BSE added so far")

        try:
            stocks = _resolve_nse_batch(batch, token)
            if stocks:
                db_save_batch(stocks)
                nse_added += len(stocks)
                done      += len(batch)
            else:
                errors.append(f"NSE batch {batch}: empty response (market closed?)")
                done += len(batch)
        except Exception as e:
            errors.append(f"NSE batch {batch[0]}: {e}")
            done += len(batch)

        time.sleep(0.3)   # respect rate limit

    # Process BSE
    for batch in bse_batches:
        batch_num += 1
        pct = done / total_pending
        if progress_cb:
            progress_cb(pct,
                f"BSE batch {batch_num - len(nse_batches)}/{len(bse_batches)} "
                f"({batch[0]}…{batch[-1]})  —  "
                f"{nse_added} NSE + {bse_added} BSE added so far")

        try:
            stocks = _resolve_bse_batch(batch, token)
            if stocks:
                db_save_batch(stocks)
                bse_added += len(stocks)
                done      += len(batch)
            else:
                errors.append(f"BSE batch {batch}: empty response")
                done += len(batch)
        except Exception as e:
            errors.append(f"BSE batch {batch[0]}: {e}")
            done += len(batch)

        time.sleep(0.3)

    counts = db_count()
    final_msg = (
        f"✅ Done! Added {nse_added} NSE + {bse_added} BSE stocks.  "
        f"DB total: {counts['total']:,}  "
        f"({counts['nse']:,} NSE + {counts['bse']:,} BSE)"
    )
    if errors:
        final_msg += f"  |  {len(errors)} batch errors (see log)"
    if progress_cb:
        progress_cb(1.0, final_msg)

    return {
        "ok":         True,
        "nse_added":  nse_added,
        "bse_added":  bse_added,
        "total_in_db":counts["total"],
        "errors":     errors,
    }



def get_fundamentals() -> dict:
    return json.loads(FUND_DATA_PATH.read_text()) if FUND_DATA_PATH.exists() else {}

# ===========================================================================
#  EPS INTELLIGENCE ENGINE
# ===========================================================================
def eps_qoq(eps: list) -> list:
    return [(eps[i]-eps[i-1])/eps[i-1]*100 if eps[i-1] > 0 else 0 for i in range(1, len(eps))]

def eps_yoy(eps: list) -> Optional[float]:
    return (eps[-1]-eps[0])/eps[0]*100 if len(eps) >= 4 and eps[0] > 0 else None

def calc_accel(g: list) -> dict:
    if len(g) < 2:
        return {"score": 0, "verdict": "N/A", "ok": False}
    steps = sum(1 for i in range(1, len(g)) if g[i] > g[i-1])
    score = round(steps / (len(g)-1) * 100)
    peak  = g[-1] == max(g)
    pos   = all(x > 0 for x in g)
    ok    = score >= 50 and peak and pos
    if ok and score == 100: v = "🚀 Perfect Staircase — Parabolic Risk!"
    elif ok:                 v = "📈 Accelerating EPS"
    elif pos:                v = "✅ Consistent Growth"
    elif steps > 0:          v = "⚠️ Mixed Acceleration"
    else:                    v = "❌ Decelerating"
    return {"score": score, "verdict": v, "ok": ok}

def calc_surprise(actual: float, est: Optional[float]) -> dict:
    if not est or est <= 0:
        return {"beat": None, "verdict": "No Estimate", "ok": False}
    b = (actual - est) / abs(est) * 100
    v = ("🎯 Massive Beat (>20%)" if b >= 20 else "✅ Strong Beat (>10%)" if b >= 10
         else "👍 Beat (>3%)" if b >= 3 else "≈ In Line" if b >= -3 else "❌ Miss")
    return {"beat": round(b, 1), "verdict": v, "ok": b >= 3}

def calc_sq(eps: list, sales: list) -> dict:
    eg = (eps[-1]-eps[0])/abs(eps[0])*100 if eps[0] else 0
    sg = (sales[-1]-sales[0])/abs(sales[0])*100 if sales[0] else 0
    if eg >= 20 and sg >= 15:  g,v,ok = "A+","🏆 Organic Growth — EPS + Sales expanding",True
    elif eg >= 15 and sg >= 8: g,v,ok = "A","✅ Strong Organic Growth",True
    elif eg >= 10 and sg >= 5: g,v,ok = "B","👍 Decent Growth Quality",True
    elif eg >= 10 and sg < 3:  g,v,ok = "C","⚠️ Cost Cutting — Sales flat",False
    elif eg < 0:               g,v,ok = "D","❌ EPS Declining",False
    else:                      g,v,ok = "B-","↗ Moderate — monitor revenue",False
    return {"grade": g, "verdict": v, "ok": ok, "eps_g": round(eg,1), "sal_g": round(sg,1)}

def analyse_fund(sym: str, price: float, fd: dict) -> dict:
    d = fd.get(sym)
    if not d:
        return {"av": False}
    eps_l, sal_l, est = d["eps"], d["sales"], d.get("est")
    ttm = sum(eps_l)
    pe  = round(price/ttm, 1) if ttm > 0 else None
    g   = eps_qoq(eps_l)
    yoy = eps_yoy(eps_l)
    ac  = calc_accel(g)
    sr  = calc_surprise(eps_l[-1], est)
    sqr = calc_sq(eps_l, sal_l)
    fs  = min((35 if yoy and yoy >= 20 else 20 if yoy and yoy >= 10 else 0) +
              (25 if ac["ok"] else 0) + (20 if sr["ok"] else 0) + (20 if sqr["ok"] else 0), 100)
    return {"av": True, "eps": eps_l, "sales": sal_l, "ttm": round(ttm,2),
            "pe": pe, "g": [round(x,1) for x in g],
            "yoy": round(yoy,1) if yoy is not None else None,
            "ac": ac, "sr": sr, "sq": sqr, "est": est, "fs": fs}

# ===========================================================================
#  TECHNICAL INDICATORS
# ===========================================================================
def perf_n(df: pd.DataFrame, n: int) -> Optional[float]:
    if len(df) < n+1:
        return None
    s, e = df["C"].iloc[-(n+1)], df["C"].iloc[-1]
    return (e-s)/s*100 if s else None

def sma21(df: pd.DataFrame) -> float:
    return float(df["C"].tail(21).mean())

def rsi14(df: pd.DataFrame) -> float:
    if len(df) < 16:
        return float("nan")
    cl = df["C"].tail(28).values
    d  = np.diff(cl)
    g  = np.where(d > 0, d, 0)
    ls = np.where(d < 0, -d, 0)
    ag, al = g[:14].mean(), ls[:14].mean()
    for i in range(14, len(d)):
        ag = (ag*13+g[i])/14
        al = (al*13+ls[i])/14
    return round(100-100/(1+ag/al), 1) if al else 100.0

def avg_vol(df: pd.DataFrame, n: int = 20) -> float:
    return float(df["V"].tail(n).mean())

def high52(df: pd.DataFrame) -> float:
    return float(df["H"].tail(252).max())

# ===========================================================================
#  SCAN ENGINE  (runs in background thread)
# ===========================================================================
def run_scan_thread(token: str, cfg: dict, uni: list, fd: dict):
    """
    Runs in a daemon thread.
    Writes ONLY to the module-level _SCAN dict (thread-safe).
    Never touches st.session_state — that is NOT thread-safe in Streamlit.
    """
    import traceback
    try:
        total = len(uni)
        _scan_update(running=True, done=False, error="", progress=0.0,
                     results=[], log=[],
                     stats={"total": total, "processed": 0, "passed": 0, "perfect": 0})
        _scan_log(f"Scan started: {total} stocks")

        results = []
        stats   = {"total": total, "processed": 0, "passed": 0, "perfect": 0}

        # Phase 1: Batch LTP
        _scan_update(msg="Phase 1/3: Fetching live prices (batch)…")
        _scan_log("Phase 1: batch LTP fetch")
        try:
            ltp_map = fetch_batch_ltp([u["ikey"] for u in uni], token)
            _scan_log(f"Phase 1 done: {len(ltp_map)} LTPs fetched")
        except Exception as e:
            _scan_log(f"Phase 1 warning (LTP batch): {e} — will use last-close prices")
            ltp_map = {}

        # Phase 2: Sector indices
        _scan_update(msg="Phase 2/3: Caching sector index candles…")
        _scan_log("Phase 2: sector index candles")
        sec_keys  = list({u["sector"] for u in uni})
        sec_cache = {}
        for sk in sec_keys:
            try:
                sec_cache[sk] = fetch_hist(sk, token)
            except Exception as e:
                _scan_log(f"  sector {sk}: {e}")
                sec_cache[sk] = None
            time.sleep(0.1)
        valid_sectors = sum(1 for v in sec_cache.values() if v is not None)
        _scan_log(f"Phase 2 done: {valid_sectors}/{len(sec_keys)} sector indices OK")

        # Phase 3: Per-stock scan
        _scan_log("Phase 3: per-stock scan starting")
        for i, stk in enumerate(uni):
            # Check stop flag
            with _SCAN_LOCK:
                if not _SCAN["running"]:
                    _scan_log("Scan stopped by user")
                    break

            sym  = stk["sym"]
            ikey = stk["ikey"]
            skey = stk["sector"]

            stats["processed"] = i + 1
            pct = (i + 1) / total
            _scan_update(
                progress=pct,
                stats=dict(stats),
                msg=f"Phase 3/3: [{i+1}/{total}]  {sym}  — "
                    f"{stats['passed']} passed  {stats['perfect']} perfect"
            )

            try:
                df = fetch_hist(ikey, token)
            except Exception as e:
                _scan_log(f"  {sym}: hist fetch error: {e}")
                continue

            if df is None or len(df) < 30:
                continue

            try:
                price = ltp_map.get(ikey) or float(df["C"].iloc[-1])
                if avg_vol(df) < cfg["min_vol"]:
                    continue

                h52_ = high52(df)
                dH   = (price - h52_) / h52_ * 100
                if dH < -cfg["high_prox"]:
                    continue

                sd = sec_cache.get(skey)
                if sd is None or len(sd) < cfg["rs_days"] + 2:
                    continue

                sp = perf_n(df, cfg["rs_days"])
                xp = perf_n(sd, cfg["rs_days"])
                if sp is None or xp is None:
                    continue

                rs_leader = xp < cfg["sec_drop"] and sp >= cfg.get("stk_min", 0)
                sm        = sma21(df)
                dS        = (price - sm) / sm * 100
                in_bz     = cfg["bz_lo"] <= dS <= cfg["bz_hi"]
                rsi_v     = rsi14(df)

                fund  = analyse_fund(sym, price, fd)
                ttm   = fund.get("ttm") or 0
                pe    = fund.get("pe")
                yoy   = fund.get("yoy")
                fs    = fund.get("fs", 0)
                ac_ok = fund.get("ac", {}).get("ok", False) if fund["av"] else False
                sr_ok = fund.get("sr", {}).get("ok", False) if fund["av"] else False
                sq_ok = fund.get("sq", {}).get("ok", False) if fund["av"] else False

                is_perfect = (rs_leader and in_bz
                              and ttm >= cfg["min_eps"]
                              and yoy is not None and yoy >= cfg["min_yoy"]
                              and ac_ok)

                stats["passed"]  += 1
                stats["perfect"] += int(is_perfect)

                results.append({
                    "name":     stk["name"],    "sym":    sym,
                    "sector":   skey.replace("NSE_INDEX|Nifty ","").replace("BSE_INDEX|S&P BSE ",""),
                    "exch":     stk["exch"],    "price":  round(price, 2),
                    "high":     round(h52_, 2), "dH":     round(dH, 2),
                    "sp":       round(sp, 2),   "xp":     round(xp, 2),
                    "rs_leader":rs_leader,      "sma":    round(sm, 2),
                    "dS":       round(dS, 2),   "in_bz":  in_bz,
                    "rsi":      None if math.isnan(rsi_v) else rsi_v,
                    "eps":      fund.get("eps",[]),   "sales": fund.get("sales",[]),
                    "ttm":      fund.get("ttm"),       "pe":   pe,
                    "yoy":      yoy,                   "g":    fund.get("g",[]),
                    "ac":       fund.get("ac",{}),     "sr":   fund.get("sr",{}),
                    "sq":       fund.get("sq",{}),
                    "eps_ok":   ttm >= cfg["min_eps"],
                    "yoy_ok":   bool(yoy and yoy >= cfg["min_yoy"]),
                    "ac_ok":    ac_ok, "sr_ok": sr_ok, "sq_ok": sq_ok,
                    "fs":       fs,    "perfect": is_perfect,
                })
            except Exception as e:
                _scan_log(f"  {sym}: processing error: {e}")
                continue

            time.sleep(0.05)

        # Sort and finalise
        sorted_results = sorted(results, key=lambda x: x.get("fs", 0), reverse=True)
        done_msg = (f"✅ Scan complete — {stats['passed']} passed / {total} total "
                    f"({stats['perfect']} perfect)")
        _scan_update(
            running=False, done=True, progress=1.0,
            results=sorted_results, stats=dict(stats), msg=done_msg
        )
        _scan_log(done_msg)

    except Exception as e:
        err = f"Scan crashed: {e}\n{traceback.format_exc()}"
        _scan_update(running=False, done=True, error=err, msg=f"❌ {e}")
        _scan_log(err)


# ===========================================================================
#  TOKEN VERIFICATION
# ===========================================================================
def verify_token(token: str) -> dict:
    """
    Hit Upstox /v2/user/profile to confirm token is valid.
    Returns {ok, name, email, error}
    """
    try:
        r = requests.get(
            f"{UPSTOX_BASE}/user/profile",
            headers=upstox_hdr(token),
            timeout=8,
        )
        if r.status_code == 200:
            d = r.json().get("data", {})
            return {
                "ok":    True,
                "name":  d.get("name", d.get("user_name", "User")),
                "email": d.get("email", ""),
                "error": "",
            }
        else:
            return {"ok": False, "name": "", "email": "",
                    "error": f"HTTP {r.status_code}: {r.text[:120]}"}
    except Exception as e:
        return {"ok": False, "name": "", "email": "", "error": str(e)}


# ===========================================================================
#  CHART HELPERS  (Plotly dark theme)
# ===========================================================================
BG   = "#0f1117"
PBG  = "#13161f"
GRID = "rgba(37,42,58,.7)"
MUT  = "#454d63"
SKY  = "rgba(91,196,245,.8)"
SAGE = "rgba(78,207,143,.8)"
AMB  = "rgba(240,180,41,.8)"
CORAL= "rgba(240,112,112,.8)"

def base_layout(title: str = "", h: int = 340) -> dict:
    return dict(
        title=dict(text=title, font=dict(color="#b4bdce", size=13, family="JetBrains Mono")),
        paper_bgcolor=PBG, plot_bgcolor=BG,
        font=dict(color="#737e96", family="JetBrains Mono"),
        height=h, margin=dict(l=44, r=16, t=50, b=40),
        xaxis=dict(gridcolor=GRID, tickcolor=MUT, linecolor=GRID, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, tickcolor=MUT, linecolor=GRID, tickfont=dict(size=10)),
    )

def pt(r: dict) -> str:
    return AMB if r.get("perfect") else SAGE if r.get("rs_leader") else MUT

def chart_rs_scatter(df: list, rs_days: int) -> go.Figure:
    fig = go.Figure()
    fig.add_vline(x=0, line=dict(color=GRID, dash="dot", width=1))
    fig.add_hline(y=-3, line=dict(color=CORAL, dash="dot", width=1))
    fig.add_shape(type="rect", x0=0, x1=max((r.get("sp",0) for r in df), default=10)+5,
                  y0=-50, y1=-3, fillcolor="rgba(78,207,143,.03)", line_width=0)
    fig.add_trace(go.Scatter(
        x=[r.get("sp",0) for r in df], y=[r.get("xp",0) for r in df],
        mode="markers+text",
        marker=dict(size=[9 if r.get("perfect") else 7 if r.get("rs_leader") else 5 for r in df],
                    color=[pt(r) for r in df],
                    symbol=["star" if r.get("perfect") else "diamond" if r.get("rs_leader") else "circle" for r in df],
                    line=dict(color="rgba(0,0,0,.4)", width=.5)),
        text=[r.get("sym","") for r in df],
        textposition="top center",
        textfont=dict(size=8, color="#737e96"),
        hovertemplate="<b>%{text}</b><br>Stock: %{x:.1f}%<br>Sector: %{y:.1f}%<extra></extra>",
    ))
    lay = base_layout(f"RS Map — Stock vs Sector ({rs_days}d)", h=380)
    lay["xaxis"]["title"] = dict(text=f"Stock {rs_days}d %", font=dict(size=11))
    lay["yaxis"]["title"] = dict(text=f"Sector {rs_days}d %", font=dict(size=11))
    fig.update_layout(**lay)
    return fig

def chart_fund_bar(df: list) -> go.Figure:
    top = sorted(df, key=lambda x: x.get("fs",0))[-20:]
    colors = [AMB if r.get("perfect") else SAGE if (r.get("fs",0) >= 60) else SKY for r in top]
    fig = go.Figure(go.Bar(
        y=[f"{r['sym']}[{(r.get('exch','?') or '?')[0]}]" for r in top],
        x=[r.get("fs",0) for r in top],
        orientation="h",
        marker_color=colors, marker_line_color="transparent",
        customdata=[[r.get("sym",""), r.get("name",""), r.get("fs",0)] for r in top],
        hovertemplate="<b>%{customdata[0]}</b><br>Fund Score: %{x}/100<extra></extra>",
    ))
    fig.add_vline(x=60, line=dict(color=SAGE, dash="dot", width=1))
    lay = base_layout("Fundamental Quality Score (Top 20)", h=380)
    lay["xaxis"]["range"] = [0, 112]
    fig.update_layout(**lay)
    return fig

def chart_pe_scatter(df: list) -> go.Figure:
    valid = [r for r in df if r.get("pe") and r.get("yoy") is not None]
    fig   = go.Figure(go.Scatter(
        x=[r.get("yoy",0) for r in valid], y=[r.get("pe",0) for r in valid],
        mode="markers+text",
        marker=dict(size=[9 if r.get("perfect") else 6 for r in valid],
                    color=[pt(r) for r in valid],
                    line=dict(color="rgba(0,0,0,.4)", width=.5)),
        text=[r.get("sym","") for r in valid],
        textposition="top center", textfont=dict(size=8, color="#737e96"),
        hovertemplate="<b>%{text}</b><br>YoY: %{x:.1f}%<br>P/E: %{y:.1f}x<extra></extra>",
    ))
    lay = base_layout("P/E vs YoY EPS Growth", h=340)
    lay["xaxis"]["title"] = dict(text="YoY EPS Growth %", font=dict(size=11))
    lay["yaxis"]["title"] = dict(text="P/E Ratio", font=dict(size=11))
    fig.update_layout(**lay)
    return fig

def chart_52w_bar(df: list) -> go.Figure:
    s = sorted(df, key=lambda x: x.get("dH",0), reverse=True)
    colors = [AMB if r.get("perfect") else SAGE if (r.get("dH",0) >= -1) else SKY for r in s]
    fig = go.Figure(go.Bar(
        x=[r.get("sym","") for r in s], y=[r.get("dH",0) for r in s],
        marker_color=colors, marker_line_color="transparent",
        hovertemplate="<b>%{x}</b><br>Dist 52W High: %{y:.2f}%<extra></extra>",
    ))
    fig.add_hline(y=-2, line=dict(color=CORAL, dash="dash", width=1))
    lay = base_layout("Distance from 52-Week High (%)", h=340)
    lay["xaxis"]["tickfont"] = {"size": 8}
    lay["xaxis"]["tickangle"] = 45
    lay["yaxis"]["range"] = [min((r.get("dH",0) for r in s), default=-5)-1, 3]
    fig.update_layout(**lay)
    return fig

def chart_eps_staircase(r: dict) -> go.Figure:
    eps   = r.get("eps", [])
    sales = r.get("sales", [])
    qoq   = r.get("g", [])
    if not eps:
        return go.Figure()

    fig = make_subplots(rows=1, cols=2, subplot_titles=["EPS Staircase (₹/share)", "Sales (₹ Cr)"],
                        horizontal_spacing=0.12)
    colors = [SAGE if i == len(eps)-1 else SKY for i in range(len(eps))]
    fig.add_trace(go.Bar(
        x=QL[:len(eps)], y=eps, marker_color=colors, marker_line_color="transparent",
        text=[f"₹{e:.1f}" for e in eps], textposition="outside", textfont=dict(size=10, color="#b4bdce"),
        name="EPS",
    ), row=1, col=1)
    for i, g in enumerate(qoq):
        color = SAGE if g > 0 else CORAL
        arrow = "↑" if g > 0 else "↓"
        fig.add_annotation(
            x=QL[i+1] if i+1 < len(QL) else QL[-1], y=eps[i+1] if i+1 < len(eps) else 0,
            text=f"{arrow}{abs(g):.0f}%", showarrow=False, yshift=22,
            font=dict(size=9, color=color, family="JetBrains Mono"), row=1, col=1,
        )
    if sales:
        s_clr = [f"rgba(240,180,41,{0.4+0.15*i})" for i in range(len(sales))]
        fig.add_trace(go.Bar(
            x=QL[:len(sales)], y=sales, marker_color=s_clr, marker_line_color="transparent",
            text=[f"₹{v/1000:.0f}K" if v > 10000 else f"₹{v:.0f}" for v in sales],
            textposition="outside", textfont=dict(size=9, color="#b4bdce"),
            name="Sales",
        ), row=1, col=2)

    lay = base_layout(f"{r.get('name',r.get('sym',''))} — EPS & Sales Trend", h=280)
    lay["showlegend"] = False
    for i in [1, 2]:
        lay[f"xaxis{'2' if i==2 else ''}"] = dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=9))
        lay[f"yaxis{'2' if i==2 else ''}"] = dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=9))
    fig.update_layout(**lay)
    return fig

# ===========================================================================
#  HTML COMPONENT HELPERS
# ===========================================================================
def badge(label: str, cls: str) -> str:
    return f'<span class="badge {cls}">{label}</span> '

def badge_row(r: dict) -> str:
    html  = badge(r.get("exch","NSE"), f"b-{'nse' if r.get('exch','NSE')=='NSE' else 'bse'}")
    if r.get("rs_leader"): html += badge("RS LEADER", "b-rs")
    if r.get("in_bz"):     html += badge("BUY ZONE",  "b-bz")
    if r.get("ac_ok"):     html += badge("EPS ACCEL", "b-acc")
    if r.get("sr_ok"):     html += badge("BEAT EST",  "b-srp")
    if r.get("sq_ok"):     html += badge("SALES+EPS", "b-sal")
    if r.get("perfect"):   html += badge("⭐ PERFECT", "b-star")
    return html

def staircase_html(r: dict) -> str:
    eps = r.get("eps", [])
    qoq = r.get("g", [])
    if not eps:
        return ""
    max_e = max(eps) if max(eps) > 0 else 1
    bars  = ""
    for i, e in enumerate(eps):
        pct   = max(int(e / max_e * 100), 8)
        isL   = i == len(eps) - 1
        col   = "#4ecf8f" if isL else "#5bc4f5"
        arrow = ""
        if i > 0 and i-1 < len(qoq):
            g = qoq[i-1]
            arrow = f'<span style="color:{"#4ecf8f" if g>0 else "#f07070"}">{"▲" if g>0 else "▼"}{abs(g):.0f}%</span>'
        label = QL[i] if i < len(QL) else f"Q{i+1}"
        bars += f"""<div class="scol">
          <div class="sarr">{arrow}</div>
          <div class="sbar" style="height:{pct}%;background:{col}">₹{e:.1f}</div>
          <div class="slb">{label}</div>
        </div>"""
    return f'<div class="stair">{bars}</div>'

def met(label: str, value: str, color: str = "var(--t1)") -> str:
    return (f'<div class="met"><div class="ml">{label}</div>'
            f'<div class="mv" style="color:{color}">{value}</div></div>')

def kpi(value, label: str, color: str = "c-sky") -> str:
    return (f'<div class="kpi"><div class="v {color}">{value}</div>'
            f'<div class="l">{label}</div></div>')

def intel_panel(icon: str, label: str, color: str, verdict: str, sub: str) -> str:
    return (f'<div class="ip"><div class="il" style="color:{color}">{icon} {label}</div>'
            f'<div class="iv">{verdict}</div><div class="is">{sub}</div></div>')

def color_val(v: float, pos: str = "var(--sage)", neg: str = "var(--coral)") -> str:
    return pos if v >= 0 else neg

def fmt_pct(v: Optional[float], sign: bool = True) -> str:
    if v is None:
        return "—"
    return f"{'+' if sign and v > 0 else ''}{v:.2f}%"

# ===========================================================================
#  RENDER STOCK CARD
# ===========================================================================
def render_stock_card(r: dict, rs_days: int, expanded: bool = True):
    is_perfect = r.get("perfect", False)
    card_class = "scard perfect" if is_perfect else "scard"

    ac  = r.get("ac", {})
    sr  = r.get("sr", {})
    sqr = r.get("sq", {})
    yoy = r.get("yoy")
    rsi = r.get("rsi")
    ttm = r.get("ttm")
    pe  = r.get("pe")
    dH  = r.get("dH", 0)
    dS  = r.get("dS", 0)
    sp  = r.get("sp", 0)
    xp  = r.get("xp", 0)
    fs  = r.get("fs", 0)

    beat_str = f"+{sr.get('beat')}% vs estimate" if sr.get("beat") is not None else "No estimate"
    qoq_str  = " → ".join([
        f'<span style="color:{"#4ecf8f" if g>0 else "#f07070"}">{"↑" if g>0 else "↓"}{abs(g):.0f}%</span>'
        for g in r.get("g", [])
    ])

    star_html = '<div class="star-tag">⭐ PERFECT SETUP — All Signals Green</div>' if is_perfect else ""

    metrics_html = f"""
    <div class="mgrid">
      {met("52W High",     f"₹{r.get('high',0):,.0f}")}
      {met("Dist 52W%",    fmt_pct(dH),                color_val(dH+2))}
      {met(f"Stock {rs_days}d%", fmt_pct(sp),          color_val(sp))}
      {met(f"Sector {rs_days}d%", fmt_pct(xp),         color_val(xp))}
      {met("21MA Dist%",   fmt_pct(dS),                "var(--tang)")}
      {met("RSI (14)",     str(rsi) if rsi else "—",   "var(--coral)" if rsi and rsi>70 else "var(--sage)" if rsi and rsi<30 else "var(--t1)")}
      {met("EPS TTM ₹",   f"₹{ttm}" if ttm else "—",  "var(--amber)")}
      {met("P/E Ratio",    f"{pe}x" if pe else "—")}
      {met("YoY EPS%",     fmt_pct(yoy),               "var(--sage)" if yoy and yoy>=20 else "var(--amber)" if yoy and yoy>=10 else "var(--coral)")}
      {met("Fund Score",   f"{fs}/100",                 "var(--sage)" if fs>=60 else "var(--amber)" if fs>=40 else "var(--t2)")}
    </div>"""

    intel_html = f"""
    <div class="igrid">
      {intel_panel("📈", "EPS Acceleration", "var(--amber)",
                   ac.get("verdict","—"),
                   f"Score: {ac.get('score',0)}/100" + (f" · QoQ: {qoq_str}" if qoq_str else ""))}
      {intel_panel("🎯", "Surprise Factor", "var(--lav)",
                   sr.get("verdict","—"), beat_str)}
      {intel_panel("🏆", "Sales vs EPS Quality", "var(--sage)",
                   sqr.get("verdict","—"),
                   f"Grade: {sqr.get('grade','—')} · EPS +{sqr.get('eps_g',0)}% · Sales +{sqr.get('sal_g',0)}%")}
    </div>"""

    full_html = f"""
    <div class="{card_class}">
      {star_html}
      <div class="card-header">
        <div class="sym">{r.get('sym','')}</div>
        <div class="nm">{r.get('name','')}</div>
        <div class="sect">{r.get('sector','').replace('NSE_INDEX|Nifty ','').replace('BSE_INDEX|S&P BSE ','')}</div>
        <div class="px-val">₹{r.get('price',0):,.2f}</div>
      </div>
      <div class="badges">{badge_row(r)}</div>
      {metrics_html}
      {staircase_html(r)}
      {intel_html}
    </div>"""

    st.markdown(full_html, unsafe_allow_html=True)

    # Plotly EPS chart inside expander
    if r.get("eps") and expanded:
        fig = chart_eps_staircase(r)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True, key=f"eps_{r['sym']}_{r.get('exch','')}")

# ===========================================================================
#  MAIN UI
# ===========================================================================
# -- Header -------------------------------------------------------------------
st.markdown("""
<div class="screener-header">
  <h1>🚀 NSE + BSE Multibagger Screener</h1>
  <div class="sub">
    ~5000 Stocks · EPS Acceleration · Surprise Factor · RS Resilience · 21MA Buy Zone · Upstox V2
  </div>
</div>
""", unsafe_allow_html=True)

# ===========================================================================
#  SIDEBAR
# ===========================================================================
with st.sidebar:
    st.markdown("### 🚀 Multibagger Screener")
    st.caption("NSE + BSE · v5.0 · Upstox V2")
    st.divider()

    # -- Universe ----------------------------------------------------------
    st.markdown('<div class="sec-lbl">🌐 Universe</div>', unsafe_allow_html=True)

    db_c = db_count()
    col1, col2, col3 = st.columns(3)
    col1.metric("NSE",  f"{db_c['nse']:,}")
    col2.metric("BSE",  f"{db_c['bse']:,}")
    col3.metric("Total",f"{db_c['total']:,}")
    _sym_total = len(NSE_500) + len(BSE_500)
    if db_c["total"] > 0:
        pct_done = min(db_c["total"] / _sym_total * 100, 100)
        st.progress(min(pct_done/100, 1.0))
        st.caption(f"{'✅' if pct_done>=90 else '📥'} {db_c['total']:,} / {_sym_total:,} ({pct_done:.0f}%)")
    else:
        st.caption("📭 DB empty — click Download to build")

    if st.session_state.get("dl_running"):
        st.info(f"⏳ {st.session_state.get('dl_msg','Downloading…')}")

    dc1, dc2 = st.columns(2)
    with dc1:
        if st.button("⬇️ Download Stocks", use_container_width=True,
                     disabled=st.session_state.get("dl_running", False),
                     help="50 NSE + 50 BSE per batch via Upstox API. Token required."):
            tok_val = st.session_state.get("token_input","")
            if not tok_val:
                st.error("⚠️ Verify token first")
            else:
                st.session_state.dl_running = True
                st.session_state.dl_msg     = "Starting…"
                st.session_state.dl_error   = ""
                st.rerun()
    with dc2:
        if st.button("🗑 Clear DB", use_container_width=True):
            try:
                if DB_PATH.exists(): DB_PATH.unlink()
                load_universe_cache.clear()
                st.rerun()
            except Exception as _e:
                st.error(str(_e))

    if st.session_state.get("dl_error"):
        st.warning(st.session_state.dl_error)
        if st.button("Clear error", key="clr_dl"):
            st.session_state.dl_error=""
            st.rerun()





    st.divider()

    # -- Token -------------------------------------------------------------
    st.markdown('<div class="sec-lbl">🔑 Upstox Token</div>', unsafe_allow_html=True)

    # Connection status indicator
    ts = st.session_state.token_status
    if ts == "valid":
        st.markdown(
            f'<div style="background:rgba(78,207,143,.12);border:1px solid rgba(78,207,143,.3);'
            f'border-radius:7px;padding:8px 12px;font-size:.72rem;color:var(--sage);margin-bottom:8px">'
            f'● Connected · {st.session_state.token_user}</div>',
            unsafe_allow_html=True
        )
    elif ts == "invalid":
        st.markdown(
            '<div style="background:rgba(240,112,112,.1);border:1px solid rgba(240,112,112,.3);'
            'border-radius:7px;padding:8px 12px;font-size:.72rem;color:var(--coral);margin-bottom:8px">'
            f'● Invalid token: {st.session_state.get("token_error","")[:60]}</div>',
            unsafe_allow_html=True
        )

    token = st.text_input("Access Token", type="password",
                          placeholder="Paste bearer token…", key="token_input")

    if st.button("🔌 Verify Token", use_container_width=True):
        if token.strip():
            with st.spinner("Connecting to Upstox…"):
                vr = verify_token(token.strip())
            if vr["ok"]:
                st.session_state.token_status = "valid"
                st.session_state.token_user   = vr["name"]
                st.session_state.token_error  = ""
                st.success(f"✅ Connected as {vr['name']} ({vr['email']})")
            else:
                st.session_state.token_status = "invalid"
                st.session_state.token_user   = ""
                st.session_state.token_error  = vr["error"]
                st.error(f"❌ {vr['error']}")
            st.rerun()
        else:
            st.warning("Paste your token first.")

    st.caption("① upstox.com/developer → Your App\n② OAuth2 flow → copy access_token\n③ Valid for 1 trading day")

    with st.expander("📥 Manual instruments.json (if download fails)"):
        st.markdown("""
**If automatic download fails (403/401 error):**

1. Log into [Upstox Developer Console](https://developer.upstox.com)
2. Go to **API Docs** → **Instruments** → Download CSV/JSON
3. Or run in terminal with your token:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.upstox.com/v2/instruments?exchange=NSE_EQ" \
  -o instruments.json
```
4. Place `instruments.json` in the **same folder** as `screener_st.py`
5. Click **⬇️ Download All ~8000 Stocks** — it will pick up the file automatically
        """)

    st.divider()

    # -- EPS Filters -------------------------------------------------------
    st.markdown('<div class="sec-lbl">📊 EPS Filters</div>', unsafe_allow_html=True)
    min_eps  = st.slider("Min TTM EPS (₹)",      0, 120,  10, 2)
    min_yoy  = st.slider("Min YoY EPS Growth %", 0, 100,  20, 5)
    req_accel = st.checkbox("EPS Accelerating (Staircase)", value=True)
    req_surp  = st.checkbox("Analyst Beat Required",         value=False)
    req_qual  = st.checkbox("Sales + EPS Quality",           value=True)

    st.divider()

    # -- Technical Filters -------------------------------------------------
    st.markdown('<div class="sec-lbl">📈 Technical Filters</div>', unsafe_allow_html=True)
    rs_days   = st.slider("RS Lookback Days",           5,   30,   20)
    high_prox = st.slider("Max Dist 52W High %",        1.0,  8.0,  2.0, 0.5)
    sec_drop  = st.slider("Sector Drop Threshold %",  -10.0, -1.0, -3.0, 0.5)
    bz_hi     = st.slider("21MA BuyZone Upper %",       0.5,  5.0,  1.5, 0.5)
    min_vol   = st.number_input("Min Avg Daily Volume",
                                min_value=10_000, value=100_000, step=50_000)

    st.divider()

    cfg = dict(
        rs_days=rs_days, high_prox=high_prox, sec_drop=sec_drop,
        stk_min=0.0, bz_lo=0.0, bz_hi=bz_hi,
        min_eps=float(min_eps), min_yoy=float(min_yoy),
        req_accel=req_accel, req_surp=req_surp, req_qual=req_qual,
        min_vol=int(min_vol),
    )

    # -- Run / Stop --------------------------------------------------------
    run_col, stop_col = st.columns([3, 1])
    with run_col:
        run_btn = st.button("🔍 RUN FULL SCAN", use_container_width=True,
                            disabled=st.session_state.scan_running)
    with stop_col:
        if st.button("⏹", disabled=not st.session_state.scan_running,
                     help="Stop scan"):
            st.session_state.scan_running = False

    if st.session_state.last_scan_time:
        st.caption(f"Last: {st.session_state.last_scan_time}")

    st.divider()
    # -- Utility -----------------------------------------------------------
    st.markdown('<div class="sec-lbl">🛠 Utilities</div>', unsafe_allow_html=True)
    if st.button("📊 Refresh EPS Data (NSE)", use_container_width=True):
        with st.spinner("Fetching NSE quarterly results…"):
            try:
                hdrs = {"User-Agent":"Mozilla/5.0","Accept":"application/json",
                        "Referer":"https://www.nseindia.com"}
                sess = requests.Session()
                sess.get("https://www.nseindia.com", headers=hdrs, timeout=10)
                r = sess.get("https://www.nseindia.com/api/corporates-financial-results",
                             headers=hdrs, params={"index":"equities","period":"Quarterly"}, timeout=20)
                if r.status_code == 200:
                    fd = get_fundamentals()
                    for rec in r.json():
                        sym = rec.get("symbol","").upper()
                        eps = rec.get("eps")
                        rev = rec.get("reIncome")
                        if sym and eps:
                            if sym not in fd:
                                fd[sym] = {"eps":[], "sales":[], "est":None}
                            fd[sym]["eps"] = (fd[sym]["eps"] + [float(eps)])[-4:]
                            if rev:
                                fd[sym]["sales"] = (fd[sym]["sales"] + [float(rev)])[-4:]
                    FUND_DATA_PATH.write_text(json.dumps(fd, separators=(",",":")))
                    st.success(f"✅ Updated {len(fd)} symbols")
                else:
                    st.warning("NSE returned non-200; try again after market hours.")
            except Exception as e:
                st.error(f"Failed: {e}")

# ===========================================================================
#  BACKGROUND DOWNLOAD RUNNER
# ===========================================================================
if st.session_state.get("dl_running"):
    tok_dl = st.session_state.get("token_input","")
    if tok_dl:
        st.markdown("### ⬇️ Building Stock Database…")
        _dl_bar = st.progress(0.0)
        _dl_msg = st.empty()
        _dl_stat = st.empty()

        def _dl_cb(pct, msg):
            _dl_bar.progress(min(float(pct), 1.0))
            _dl_msg.caption(msg)
            st.session_state.dl_msg = msg
            _c = db_count()
            _dl_stat.caption(
                f"Live DB: {_c['total']:,}  ({_c['nse']:,} NSE + {_c['bse']:,} BSE)"
            )

        _res = download_universe_batches(tok_dl, _dl_cb)
        load_universe_cache.clear()
        st.session_state.dl_running = False
        if _res["errors"]:
            st.session_state.dl_error = (
                f"⚠️ {len(_res['errors'])} batch errors.\n"
                + "\n".join(_res["errors"][:8])
            )
        _cf = db_count()
        st.success(
            f"✅ Added {_res['nse_added']} NSE + {_res['bse_added']} BSE.  "
            f"DB total: {_cf['total']:,}"
        )
        st.rerun()
    else:
        st.session_state.dl_running = False

# ===========================================================================
#  LAUNCH SCAN
# ===========================================================================
if run_btn:
    if not token:
        st.error("⚠️ Please enter your Upstox Access Token in the sidebar.")
        st.stop()
    uni_now = load_universe_cache()
    load_universe_cache.clear()
    fd      = get_fundamentals()
    # Reset shared scan state
    _scan_update(running=True, done=False, error="", progress=0.0,
                 results=[], log=[], msg="Starting…",
                 stats={"total": len(uni_now), "processed": 0, "passed": 0, "perfect": 0})
    # Reset session state flags
    st.session_state.results       = []
    st.session_state.scan_running  = True
    st.session_state.scan_done     = False
    st.session_state.scan_progress = 0.0
    t = threading.Thread(
        target=run_scan_thread,
        args=(token, cfg, uni_now, fd),
        daemon=True,
    )
    t.start()
    st.rerun()

# ===========================================================================
#  PROGRESS BAR  (auto-refreshes while scanning)
# ===========================================================================
# -- Sync _SCAN → session_state (safe: main thread only) ------------------
if st.session_state.scan_running:
    with _SCAN_LOCK:
        snap = dict(_SCAN)          # read snapshot under lock

    pct   = snap["progress"]
    stats = snap["stats"]
    msg   = snap["msg"]
    done  = snap["done"]
    err   = snap["error"]

    if done:
        # Scan finished (or crashed) — copy results to session_state
        st.session_state.scan_running   = False
        st.session_state.scan_done      = True
        st.session_state.results        = snap["results"]
        st.session_state.scan_progress  = 1.0
        st.session_state.last_scan_time = datetime.datetime.now().strftime("%d %b %Y  %H:%M IST")
        if err:
            st.session_state.scan_error = err
        st.rerun()
    else:
        # Still running — show live progress
        st.markdown('<div class="prog-box"><div class="plbl scanning">● SCANNING</div></div>',
                    unsafe_allow_html=True)
        st.progress(min(float(pct), 1.0))
        st.caption(msg)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total",     stats.get("total", 0))
        c2.metric("Processed", stats.get("processed", 0))
        c3.metric("Passed",    stats.get("passed", 0))
        c4.metric("⭐ Perfect", stats.get("perfect", 0))

        # Show scan log in expander (live debugging)
        log_lines = snap.get("log", [])
        if log_lines:
            with st.expander(f"📋 Scan Log ({len(log_lines)} entries)", expanded=False):
                st.code("\n".join(log_lines[-30:]), language=None)

        time.sleep(2)
        st.rerun()

# ===========================================================================
#  RESULTS
# ===========================================================================
results = st.session_state.results

# Show any scan error that occurred
if st.session_state.get("scan_error"):
    with st.expander("❌ Scan Error Log", expanded=True):
        st.code(st.session_state.scan_error, language=None)
    if st.button("Clear Error"):
        st.session_state.scan_error = ""
        st.rerun()

# Show scan log from _SCAN after completion
if st.session_state.scan_done and not st.session_state.scan_running:
    with _SCAN_LOCK:
        log_snap = list(_SCAN.get("log", []))
    if log_snap:
        with st.expander(f"📋 Last Scan Log ({len(log_snap)} entries)", expanded=False):
            st.code("\n".join(log_snap), language=None)

if not results and not st.session_state.scan_running:
    # -- Welcome screen ----------------------------------------------------
    st.markdown('<div class="sec-lbl">📖 The Three EPS Rules for Multibaggers</div>',
                unsafe_allow_html=True)
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.markdown("""<div class="rule-card">
          <div class="rule-num" style="color:var(--amber)">Rule 01 — Acceleration</div>
          <h4>📈 The Staircase Pattern</h4>
          <p>Each quarter's growth must be <strong style="color:var(--t1)">higher than the last</strong>.
             Q1 +10% → Q2 +20% → Q3 +40% signals a <strong style="color:var(--sage)">parabolic run</strong>.</p>
          <div class="rule-ex" style="color:var(--sage)">+10% → +20% → +40% = 🚀 Parabolic Signal</div>
        </div>""", unsafe_allow_html=True)
    with rc2:
        st.markdown("""<div class="rule-card">
          <div class="rule-num" style="color:var(--lav)">Rule 02 — Surprise Factor</div>
          <h4>🎯 Beat the Estimate</h4>
          <p>The biggest multibaggers occur when EPS is <strong style="color:var(--t1)">much higher than
             analysts expected</strong>. A 20%+ beat forces rapid institutional re-rating.</p>
          <div class="rule-ex" style="color:var(--lav)">Actual > Estimate by 20% = 🎯 Re-rating Catalyst</div>
        </div>""", unsafe_allow_html=True)
    with rc3:
        st.markdown("""<div class="rule-card">
          <div class="rule-num" style="color:var(--sage)">Rule 03 — Sales Quality</div>
          <h4>🏆 Sales + EPS Together</h4>
          <p>EPS up while <strong style="color:var(--coral)">Sales are flat</strong> = cost cutting only.
             True multibaggers have <strong style="color:var(--sage)">both Revenue and EPS expanding</strong>.</p>
          <div class="rule-ex" style="color:var(--sage)">Revenue ↑ + EPS ↑ = 🏆 Grade A+ Organic Growth</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-lbl">⭐ The Perfect Setup</div>', unsafe_allow_html=True)
    st.markdown("""<div class="setup-box">
      <div style="font-family:'JetBrains Mono',monospace;font-size:.6rem;letter-spacing:2px;
                  color:var(--sage);margin-bottom:10px">★ PERFECT SETUP CHECKLIST</div>
      <div class="setup-row">
        <div class="si"><div class="sil">Sector</div><div class="siv">Falling 4–5%</div></div>
        <div class="si"><div class="sil">Stock Price</div><div class="siv">Near 52W High, hugging 21MA</div></div>
        <div class="si"><div class="sil">EPS Growth</div><div class="siv">&gt;20% YoY + Accelerating QoQ</div></div>
        <div class="si"><div class="sil">Sales Quality</div><div class="siv">Revenue expanding with EPS</div></div>
        <div class="si"><div class="sil">Action</div><div class="siv" style="color:var(--sage)">Sector turns up → Buy breakout</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    _wdb = db_count()
    if _wdb["total"] > 0:
        st.info(
            f"**{_wdb['total']:,} stocks in database**  "
            f"({_wdb['nse']:,} NSE + {_wdb['bse']:,} BSE)\n\n"
            "**Step 1:** Paste & verify Upstox token  \n"
            "**Step 2:** Click **🔍 RUN FULL SCAN**"
        )
    else:
        st.info(
            f"**{len(DEFAULT_UNIVERSE)} default stocks ready** — scan works immediately.\n\n"
            "**Step 1:** Paste & verify token → **Step 2:** RUN FULL SCAN  \n\n"
            "📥 Click **⬇️ Download Stocks** to build your full database "
            "(50 NSE + 50 BSE per batch, stored in universe.db)."
        )
    st.stop()

# -- Exchange filter -----------------------------------------------------------
exch_opts  = ["All", "NSE", "BSE"]
exch_sel   = st.radio("Exchange Filter:", exch_opts, horizontal=True,
                       index=exch_opts.index(st.session_state.exch_filter))
st.session_state.exch_filter = exch_sel

def filtered(rows: list) -> list:
    if exch_sel == "All":
        return rows
    return [r for r in rows if r.get("exch","") == exch_sel]

frows = filtered(results)

# -- KPI strip -----------------------------------------------------------------
perfects   = [r for r in frows if r.get("perfect")]
rs_leaders = [r for r in frows if r.get("rs_leader")]
bz_stocks  = [r for r in frows if r.get("in_bz")]
accel_rows = [r for r in frows if r.get("ac_ok")]
surp_rows  = [r for r in frows if r.get("sr_ok")]

st.markdown(
    f'<div class="kpi-row">'
    f'{kpi(len(frows),    "Screened",     "c-sky")}'
    f'{kpi(len(rs_leaders),"RS Leaders",  "c-sage")}'
    f'{kpi(len(bz_stocks), "Buy Zone",    "c-sky")}'
    f'{kpi(len(accel_rows),"EPS Accel",   "c-amber")}'
    f'{kpi(len(surp_rows), "Analyst Beat","c-lav")}'
    f'{kpi(len(perfects),  "⭐ Perfect",  "c-tang")}'
    f'</div>',
    unsafe_allow_html=True
)

# ===========================================================================
#  TABS
# ===========================================================================
tab_perf, tab_eps, tab_all, tab_charts, tab_exp = st.tabs([
    "⭐ Perfect Setups", "🔬 EPS Deep Dive",
    "📋 Full Results",   "📊 Charts", "💾 Export"
])

# -- TAB 1: Perfect Setups -----------------------------------------------------
with tab_perf:
    show_rows = perfects if perfects else frows[:6]
    if perfects:
        st.markdown(
            f'<div class="sec-lbl">⭐ {len(perfects)} Perfect Setup{"s" if len(perfects)>1 else ""} — All 5 Signals Green</div>',
            unsafe_allow_html=True)
    else:
        st.markdown('<div class="sec-lbl">📌 Top Candidates (no Perfect Setups — try relaxing thresholds)</div>',
                    unsafe_allow_html=True)

    for i, r in enumerate(show_rows):
        label = f"{'⭐ ' if r.get('perfect') else '📌 '}{r.get('sym','')}  ·  {r.get('name','')}  ·  ₹{r.get('price',0):,.2f}  ·  Fund Score: {r.get('fs',0)}/100"
        with st.expander(label, expanded=r.get("perfect", False)):
            render_stock_card(r, rs_days, expanded=True)

    # RS Leaders (not perfect)
    rs_not_perfect = [r for r in rs_leaders if not r.get("perfect")]
    if rs_not_perfect:
        st.markdown('<div class="sec-lbl">✅ RS Leaders (not yet in buy zone)</div>',
                    unsafe_allow_html=True)
        for r in rs_not_perfect[:10]:
            with st.expander(f"✅ {r.get('sym','')}  ·  {r.get('name','')}  ·  ₹{r.get('price',0):,.2f}"):
                render_stock_card(r, rs_days, expanded=False)

# -- TAB 2: EPS Deep Dive ------------------------------------------------------
with tab_eps:
    st.markdown('<div class="sec-lbl">🔬 EPS Deep Dive — All Screened Stocks</div>',
                unsafe_allow_html=True)
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1: f_accel = st.checkbox("📈 EPS Accel Only", key="f_accel")
    with f_col2: f_beat  = st.checkbox("🎯 Beat Only",      key="f_beat")
    with f_col3: f_qual  = st.checkbox("🏆 Sales+EPS Only", key="f_qual")
    with f_col4: f_perf  = st.checkbox("⭐ Perfect Only",   key="f_perf")

    eps_rows = [r for r in frows if r.get("eps")]
    if f_accel: eps_rows = [r for r in eps_rows if r.get("ac_ok")]
    if f_beat:  eps_rows = [r for r in eps_rows if r.get("sr_ok")]
    if f_qual:  eps_rows = [r for r in eps_rows if r.get("sq_ok")]
    if f_perf:  eps_rows = [r for r in eps_rows if r.get("perfect")]

    if not eps_rows:
        st.info("No stocks match the selected filters.")
    else:
        for r in eps_rows:
            yoy_str = fmt_pct(r.get("yoy"))
            label   = f"{r.get('sym','')} [{r.get('exch','?')}]  ·  YoY: {yoy_str}  ·  Fund: {r.get('fs',0)}/100  ·  {r.get('ac',{}).get('verdict','')}"
            with st.expander(label):
                st.plotly_chart(chart_eps_staircase(r), use_container_width=True,
                                key=f"eps_dive_{r['sym']}_{r.get('exch','')}")
                ac  = r.get("ac",{})
                sr  = r.get("sr",{})
                sqr = r.get("sq",{})
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("TTM EPS",     f"₹{r.get('ttm','—')}")
                c2.metric("P/E",         f"{r.get('pe','—')}x" if r.get("pe") else "—")
                c3.metric("Accel Score", f"{ac.get('score',0)}/100")
                c4.metric("Sales Growth",f"+{sqr.get('sal_g',0):.1f}%")

                beat_str = f"+{sr.get('beat')}% vs estimate" if sr.get("beat") else "No estimate"
                st.markdown(
                    f'<div style="font-size:.72rem;color:var(--t3);margin-top:8px">'
                    f'<strong style="color:var(--t2)">EPS Accel:</strong> {ac.get("verdict","—")}  ·  '
                    f'<strong style="color:var(--t2)">Surprise:</strong> {sr.get("verdict","—")} ({beat_str})  ·  '
                    f'<strong style="color:var(--t2)">Sales Quality:</strong> {sqr.get("verdict","—")}'
                    f'</div>', unsafe_allow_html=True
                )

# -- TAB 3: Full Results -------------------------------------------------------
with tab_all:
    st.markdown('<div class="sec-lbl">📋 Complete Scan Results</div>', unsafe_allow_html=True)

    sort_opts = {
        "Fund Score ↓":      ("fs",      True),
        "YoY EPS% ↓":        ("yoy",     True),
        "Dist 52W High ↓":   ("dH",      True),
        "RS Leader first":   ("rs_leader",True),
        "⭐ Perfect first":  ("perfect", True),
        "Price ↓":           ("price",   True),
        "Symbol A→Z":        ("sym",     False),
    }
    sort_sel = st.selectbox("Sort by:", list(sort_opts.keys()), index=0)
    sort_key, sort_rev = sort_opts[sort_sel]

    display = sorted(frows, key=lambda x: (x.get(sort_key) or 0), reverse=sort_rev)

    # Build display DataFrame
    df_disp = pd.DataFrame([{
        "Symbol":       r.get("sym",""),
        "Exchange":     r.get("exch",""),
        "Sector":       r.get("sector",""),
        "Price ₹":      r.get("price",0),
        f"Stk{rs_days}d%": r.get("sp",0),
        f"Sec{rs_days}d%": r.get("xp",0),
        "Dist 52W%":    r.get("dH",0),
        "21MA Dist%":   r.get("dS",0),
        "RSI":          r.get("rsi","—"),
        "EPS TTM ₹":    r.get("ttm","—"),
        "P/E":          r.get("pe","—"),
        "YoY EPS%":     r.get("yoy","—"),
        "RS Leader":    "✅" if r.get("rs_leader") else "—",
        "Buy Zone":     "🎯" if r.get("in_bz")     else "—",
        "EPS Accel":    "📈" if r.get("ac_ok")     else "—",
        "Beat Est":     "🎯" if r.get("sr_ok")     else "—",
        "Sales+EPS":    "🏆" if r.get("sq_ok")     else "—",
        "Fund Score":   r.get("fs",0),
        "⭐ Perfect":   "⭐" if r.get("perfect")   else "—",
    } for r in display])

    st.dataframe(
        df_disp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price ₹":    st.column_config.NumberColumn(format="₹%.2f"),
            "EPS TTM ₹":  st.column_config.NumberColumn(format="₹%.1f"),
            "Fund Score":  st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            f"Stk{rs_days}d%": st.column_config.NumberColumn(format="%.2f%%"),
            f"Sec{rs_days}d%": st.column_config.NumberColumn(format="%.2f%%"),
            "Dist 52W%":  st.column_config.NumberColumn(format="%.2f%%"),
            "21MA Dist%": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )

# -- TAB 4: Charts -------------------------------------------------------------
with tab_charts:
    if not frows:
        st.info("Run a scan to see charts.")
    else:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.plotly_chart(chart_rs_scatter(frows, rs_days),
                            use_container_width=True, key="ch_rs")
        with cc2:
            st.plotly_chart(chart_fund_bar(frows),
                            use_container_width=True, key="ch_fund")

        cc3, cc4 = st.columns(2)
        with cc3:
            st.plotly_chart(chart_pe_scatter(frows),
                            use_container_width=True, key="ch_pe")
        with cc4:
            st.plotly_chart(chart_52w_bar(frows),
                            use_container_width=True, key="ch_52w")

# -- TAB 5: Export -------------------------------------------------------------
with tab_exp:
    st.markdown('<div class="sec-lbl">💾 Export Results</div>', unsafe_allow_html=True)

    def make_csv(rows: list) -> bytes:
        cols = ["sym","name","exch","sector","price","high","dH","sp","xp",
                "rs_leader","sma","dS","in_bz","rsi","ttm","pe","yoy",
                "eps_ok","yoy_ok","ac_ok","sr_ok","sq_ok","fs","perfect"]
        df = pd.DataFrame([{c: r.get(c) for c in cols} for r in rows])
        return df.to_csv(index=False).encode("utf-8")

    ec1, ec2, ec3, ec4, ec5 = st.columns(5)
    with ec1:
        st.download_button("⬇️ Full CSV",       make_csv(frows),
                           f"full_{datetime.date.today()}.csv", "text/csv")
    with ec2:
        st.download_button("⭐ Perfect CSV",    make_csv(perfects),
                           f"perfect_{datetime.date.today()}.csv", "text/csv",
                           disabled=not perfects)
    with ec3:
        st.download_button("✅ RS Leaders CSV", make_csv(rs_leaders),
                           f"rs_{datetime.date.today()}.csv", "text/csv",
                           disabled=not rs_leaders)
    with ec4:
        nse_rows = [r for r in frows if r.get("exch") == "NSE"]
        st.download_button("NSE Only CSV",     make_csv(nse_rows),
                           f"nse_{datetime.date.today()}.csv", "text/csv",
                           disabled=not nse_rows)
    with ec5:
        bse_rows = [r for r in frows if r.get("exch") == "BSE"]
        st.download_button("BSE Only CSV",     make_csv(bse_rows),
                           f"bse_{datetime.date.today()}.csv", "text/csv",
                           disabled=not bse_rows)

    st.markdown('<div class="sec-lbl">⚙️ Scan Config Used</div>', unsafe_allow_html=True)
    st.json(cfg)

# -- Footer --------------------------------------------------------------------
st.markdown(
    f'<p style="font-family:JetBrains Mono,monospace;font-size:.58rem;color:#252a3a;'
    f'text-align:right;margin-top:32px;">'
    f'NSE+BSE Multibagger Screener · Upstox V2 · Streamlit v5.0 · '
    f'{datetime.date.today()}</p>',
    unsafe_allow_html=True
)
