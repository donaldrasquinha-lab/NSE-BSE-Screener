"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NSE + BSE Multibagger Screener  ·  Streamlit Edition                       ║
║  ~5000 Stocks · EPS Acceleration · RS Resilience · 21MA Buy Zone            ║
║                                                                              ║
║  INSTALL:  pip install streamlit plotly requests numpy pandas                ║
║  RUN:      streamlit run screener_st.py                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ── stdlib ──────────────────────────────────────────────────────────────────
import gzip, io, csv, json, math, time, datetime, logging, sqlite3, threading
from typing import Optional
from pathlib import Path

# ── third-party ──────────────────────────────────────────────────────────────
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="NSE+BSE Multibagger Screener",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GLOBAL CSS  — warm deep-navy, eye-comfort palette
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPSTOX_BASE    = "https://api.upstox.com/v2"
INSTRUMENT_URL = "https://assets.upstox.com/market-assets/instruments/exchange/complete.csv.gz"
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION STATE INITIALISATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UPSTOX HELPERS  (sync — Streamlit is synchronous)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUILT-IN UNIVERSE  — 400+ curated NSE + BSE stocks, works without internet
#  Format: [name, sym, instrument_key, sector_index, exch]
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_BUILTIN = [
 # NSE IT
 ["TCS","TCS","NSE_EQ|INE467B01029","NSE_INDEX|Nifty IT","NSE"],
 ["Infosys","INFY","NSE_EQ|INE009A01021","NSE_INDEX|Nifty IT","NSE"],
 ["Wipro","WIPRO","NSE_EQ|INE075A01022","NSE_INDEX|Nifty IT","NSE"],
 ["HCL Technologies","HCLTECH","NSE_EQ|INE860A01027","NSE_INDEX|Nifty IT","NSE"],
 ["Tech Mahindra","TECHM","NSE_EQ|INE669C01036","NSE_INDEX|Nifty IT","NSE"],
 ["LTIMindtree","LTIM","NSE_EQ|INE214T01019","NSE_INDEX|Nifty IT","NSE"],
 ["Mphasis","MPHASIS","NSE_EQ|INE356A01018","NSE_INDEX|Nifty IT","NSE"],
 ["Coforge","COFORGE","NSE_EQ|INE591G01017","NSE_INDEX|Nifty IT","NSE"],
 ["Persistent Sys","PERSISTENT","NSE_EQ|INE262H01021","NSE_INDEX|Nifty IT","NSE"],
 ["KPIT Tech","KPIT","NSE_EQ|INE04I401036","NSE_INDEX|Nifty IT","NSE"],
 ["LT Technology Svc","LTTS","NSE_EQ|INE010V01017","NSE_INDEX|Nifty IT","NSE"],
 ["Oracle Fin Svc","OFSS","NSE_EQ|INE881D01027","NSE_INDEX|Nifty IT","NSE"],
 ["Tata Elxsi","TATAELXSI","NSE_EQ|INE670A01012","NSE_INDEX|Nifty IT","NSE"],
 ["Cyient","CYIENT","NSE_EQ|INE136B01020","NSE_INDEX|Nifty IT","NSE"],
 ["Birlasoft","BIRLASOFT","NSE_EQ|INE836A01035","NSE_INDEX|Nifty IT","NSE"],
 ["Zensar Tech","ZENSARTECH","NSE_EQ|INE520A01027","NSE_INDEX|Nifty IT","NSE"],
 ["Intellect Design","INTELLECT","NSE_EQ|INE306R01017","NSE_INDEX|Nifty IT","NSE"],
 # NSE BANK
 ["HDFC Bank","HDFCBANK","NSE_EQ|INE040A01034","NSE_INDEX|Nifty Bank","NSE"],
 ["ICICI Bank","ICICIBANK","NSE_EQ|INE090A01021","NSE_INDEX|Nifty Bank","NSE"],
 ["Kotak Mah Bank","KOTAKBANK","NSE_EQ|INE237A01028","NSE_INDEX|Nifty Bank","NSE"],
 ["Axis Bank","AXISBANK","NSE_EQ|INE238A01034","NSE_INDEX|Nifty Bank","NSE"],
 ["State Bank India","SBIN","NSE_EQ|INE062A01020","NSE_INDEX|Nifty Bank","NSE"],
 ["IndusInd Bank","INDUSINDBK","NSE_EQ|INE095A01012","NSE_INDEX|Nifty Bank","NSE"],
 ["Bandhan Bank","BANDHANBNK","NSE_EQ|INE545U01014","NSE_INDEX|Nifty Bank","NSE"],
 ["Federal Bank","FEDERALBNK","NSE_EQ|INE171A01029","NSE_INDEX|Nifty Bank","NSE"],
 ["IDFC First Bank","IDFCFIRSTB","NSE_EQ|INE092T01019","NSE_INDEX|Nifty Bank","NSE"],
 ["AU Small Finance","AUBANK","NSE_EQ|INE949L01017","NSE_INDEX|Nifty Bank","NSE"],
 ["RBL Bank","RBLBANK","NSE_EQ|INE976G01028","NSE_INDEX|Nifty Bank","NSE"],
 ["Yes Bank","YESBANK","NSE_EQ|INE528G01035","NSE_INDEX|Nifty Bank","NSE"],
 ["Canara Bank","CANBK","NSE_EQ|INE476A01014","NSE_INDEX|Nifty Bank","NSE"],
 ["Bank of Baroda","BANKBARODA","NSE_EQ|INE028A01039","NSE_INDEX|Nifty Bank","NSE"],
 ["Punjab Natl Bank","PNB","NSE_EQ|INE160A01022","NSE_INDEX|Nifty Bank","NSE"],
 ["Union Bank","UNIONBANK","NSE_EQ|INE692A01016","NSE_INDEX|Nifty Bank","NSE"],
 ["Indian Bank","INDIANB","NSE_EQ|INE562A01011","NSE_INDEX|Nifty Bank","NSE"],
 ["Karur Vysya Bk","KARURVYSYA","NSE_EQ|INE036D01028","NSE_INDEX|Nifty Bank","NSE"],
 # NSE FMCG
 ["HUL","HINDUNILVR","NSE_EQ|INE030A01027","NSE_INDEX|Nifty FMCG","NSE"],
 ["ITC","ITC","NSE_EQ|INE154A01025","NSE_INDEX|Nifty FMCG","NSE"],
 ["Nestle India","NESTLEIND","NSE_EQ|INE239A01016","NSE_INDEX|Nifty FMCG","NSE"],
 ["Britannia","BRITANNIA","NSE_EQ|INE216A01030","NSE_INDEX|Nifty FMCG","NSE"],
 ["Dabur India","DABUR","NSE_EQ|INE016A01026","NSE_INDEX|Nifty FMCG","NSE"],
 ["Marico","MARICO","NSE_EQ|INE196A01026","NSE_INDEX|Nifty FMCG","NSE"],
 ["Godrej Consumer","GODREJCP","NSE_EQ|INE102D01028","NSE_INDEX|Nifty FMCG","NSE"],
 ["Colgate","COLPAL","NSE_EQ|INE259A01022","NSE_INDEX|Nifty FMCG","NSE"],
 ["Emami","EMAMILTD","NSE_EQ|INE548C01032","NSE_INDEX|Nifty FMCG","NSE"],
 ["Tata Consumer","TATACONSUM","NSE_EQ|INE192A01025","NSE_INDEX|Nifty FMCG","NSE"],
 ["Jubilant Foods","JUBLFOODS","NSE_EQ|INE797F01012","NSE_INDEX|Nifty FMCG","NSE"],
 ["Varun Beverages","VBL","NSE_EQ|INE200M01013","NSE_INDEX|Nifty FMCG","NSE"],
 ["Radico Khaitan","RADICO","NSE_EQ|INE944F01028","NSE_INDEX|Nifty FMCG","NSE"],
 # NSE AUTO
 ["Maruti Suzuki","MARUTI","NSE_EQ|INE585B01010","NSE_INDEX|Nifty Auto","NSE"],
 ["Tata Motors","TATAMOTORS","NSE_EQ|INE155L01022","NSE_INDEX|Nifty Auto","NSE"],
 ["M&M","M&M","NSE_EQ|INE101A01026","NSE_INDEX|Nifty Auto","NSE"],
 ["Bajaj Auto","BAJAJ-AUTO","NSE_EQ|INE917I01010","NSE_INDEX|Nifty Auto","NSE"],
 ["Eicher Motors","EICHERMOT","NSE_EQ|INE066A01021","NSE_INDEX|Nifty Auto","NSE"],
 ["Hero MotoCorp","HEROMOTOCO","NSE_EQ|INE158A01026","NSE_INDEX|Nifty Auto","NSE"],
 ["Ashok Leyland","ASHOKLEY","NSE_EQ|INE208A01029","NSE_INDEX|Nifty Auto","NSE"],
 ["Motherson Sum","MOTHERSON","NSE_EQ|INE775I01017","NSE_INDEX|Nifty Auto","NSE"],
 ["TVS Motor","TVSMOTOR","NSE_EQ|INE494B01023","NSE_INDEX|Nifty Auto","NSE"],
 ["Bharat Forge","BHARATFORG","NSE_EQ|INE465A01025","NSE_INDEX|Nifty Auto","NSE"],
 ["Balkrishna Ind","BALKRISIND","NSE_EQ|INE787D01026","NSE_INDEX|Nifty Auto","NSE"],
 ["Bosch","BOSCHLTD","NSE_EQ|INE323A01026","NSE_INDEX|Nifty Auto","NSE"],
 ["Exide Industries","EXIDEIND","NSE_EQ|INE302A01020","NSE_INDEX|Nifty Auto","NSE"],
 ["CEAT","CEATLTD","NSE_EQ|INE482A01020","NSE_INDEX|Nifty Auto","NSE"],
 # NSE PHARMA
 ["Sun Pharma","SUNPHARMA","NSE_EQ|INE044A01036","NSE_INDEX|Nifty Pharma","NSE"],
 ["Dr Reddy's","DRREDDY","NSE_EQ|INE089A01023","NSE_INDEX|Nifty Pharma","NSE"],
 ["Cipla","CIPLA","NSE_EQ|INE059A01026","NSE_INDEX|Nifty Pharma","NSE"],
 ["Divi's Labs","DIVISLAB","NSE_EQ|INE361B01024","NSE_INDEX|Nifty Pharma","NSE"],
 ["Aurobindo","AUROPHARMA","NSE_EQ|INE406A01037","NSE_INDEX|Nifty Pharma","NSE"],
 ["Torrent Pharma","TORNTPHARM","NSE_EQ|INE685A01028","NSE_INDEX|Nifty Pharma","NSE"],
 ["Lupin","LUPIN","NSE_EQ|INE326A01037","NSE_INDEX|Nifty Pharma","NSE"],
 ["Biocon","BIOCON","NSE_EQ|INE376G01013","NSE_INDEX|Nifty Pharma","NSE"],
 ["Abbott India","ABBOTINDIA","NSE_EQ|INE358A01014","NSE_INDEX|Nifty Pharma","NSE"],
 ["Alkem Labs","ALKEM","NSE_EQ|INE540L01014","NSE_INDEX|Nifty Pharma","NSE"],
 ["IPCA Labs","IPCALAB","NSE_EQ|INE571A01020","NSE_INDEX|Nifty Pharma","NSE"],
 ["Dr Lal PathLabs","LALPATHLAB","NSE_EQ|INE600L01024","NSE_INDEX|Nifty Pharma","NSE"],
 ["Apollo Hospitals","APOLLOHOSP","NSE_EQ|INE437A01024","NSE_INDEX|Nifty Pharma","NSE"],
 ["Max Healthcare","MAXHEALTH","NSE_EQ|INE027H01010","NSE_INDEX|Nifty Pharma","NSE"],
 ["Fortis HC","FORTIS","NSE_EQ|INE061F01013","NSE_INDEX|Nifty Pharma","NSE"],
 ["Syngene Intl","SYNGENE","NSE_EQ|INE398R01022","NSE_INDEX|Nifty Pharma","NSE"],
 # NSE ENERGY
 ["Reliance Ind","RELIANCE","NSE_EQ|INE002A01018","NSE_INDEX|Nifty Energy","NSE"],
 ["ONGC","ONGC","NSE_EQ|INE213A01029","NSE_INDEX|Nifty Energy","NSE"],
 ["Indian Oil Corp","IOC","NSE_EQ|INE242A01010","NSE_INDEX|Nifty Energy","NSE"],
 ["BPCL","BPCL","NSE_EQ|INE029A01011","NSE_INDEX|Nifty Energy","NSE"],
 ["Power Grid","POWERGRID","NSE_EQ|INE752E01010","NSE_INDEX|Nifty Energy","NSE"],
 ["NTPC","NTPC","NSE_EQ|INE733E01010","NSE_INDEX|Nifty Energy","NSE"],
 ["GAIL India","GAIL","NSE_EQ|INE129A01019","NSE_INDEX|Nifty Energy","NSE"],
 ["Petronet LNG","PETRONET","NSE_EQ|INE347G01014","NSE_INDEX|Nifty Energy","NSE"],
 ["HPCL","HINDPETRO","NSE_EQ|INE094A01015","NSE_INDEX|Nifty Energy","NSE"],
 ["Gujarat Gas","GUJARATGAS","NSE_EQ|INE844O01030","NSE_INDEX|Nifty Energy","NSE"],
 ["IGL","IGL","NSE_EQ|INE203G01027","NSE_INDEX|Nifty Energy","NSE"],
 ["Adani Ports","ADANIPORTS","NSE_EQ|INE742F01042","NSE_INDEX|Nifty Energy","NSE"],
 ["Tata Power","TATAPOWER","NSE_EQ|INE245A01021","NSE_INDEX|Nifty Energy","NSE"],
 ["Torrent Power","TORNTPOWER","NSE_EQ|INE813H01021","NSE_INDEX|Nifty Energy","NSE"],
 ["NHPC","NHPC","NSE_EQ|INE848E01016","NSE_INDEX|Nifty Energy","NSE"],
 ["Adani Green","ADANIGREEN","NSE_EQ|INE364U01010","NSE_INDEX|Nifty Energy","NSE"],
 # NSE METAL
 ["Tata Steel","TATASTEEL","NSE_EQ|INE081A01020","NSE_INDEX|Nifty Metal","NSE"],
 ["Hindalco","HINDALCO","NSE_EQ|INE038A01020","NSE_INDEX|Nifty Metal","NSE"],
 ["JSW Steel","JSWSTEEL","NSE_EQ|INE019A01038","NSE_INDEX|Nifty Metal","NSE"],
 ["SAIL","SAIL","NSE_EQ|INE114A01011","NSE_INDEX|Nifty Metal","NSE"],
 ["NMDC","NMDC","NSE_EQ|INE584A01023","NSE_INDEX|Nifty Metal","NSE"],
 ["Vedanta","VEDL","NSE_EQ|INE205A01025","NSE_INDEX|Nifty Metal","NSE"],
 ["Natl Aluminium","NATIONALUM","NSE_EQ|INE139A01034","NSE_INDEX|Nifty Metal","NSE"],
 ["APL Apollo","APLAPOLLO","NSE_EQ|INE702C01027","NSE_INDEX|Nifty Metal","NSE"],
 ["Jindal Steel","JINDALSTEL","NSE_EQ|INE749A01030","NSE_INDEX|Nifty Metal","NSE"],
 # NSE FINANCE / NBFC
 ["Bajaj Finance","BAJFINANCE","NSE_EQ|INE296A01024","NSE_INDEX|Nifty Financial Services","NSE"],
 ["Bajaj Finserv","BAJAJFINSV","NSE_EQ|INE918I01026","NSE_INDEX|Nifty Financial Services","NSE"],
 ["Cholamandalam","CHOLAFIN","NSE_EQ|INE121A01024","NSE_INDEX|Nifty Financial Services","NSE"],
 ["Muthoot Finance","MUTHOOTFIN","NSE_EQ|INE414G01012","NSE_INDEX|Nifty Financial Services","NSE"],
 ["Manappuram","MANAPPURAM","NSE_EQ|INE522D01027","NSE_INDEX|Nifty Financial Services","NSE"],
 ["LIC Housing","LICHOUSING","NSE_EQ|INE115A01026","NSE_INDEX|Nifty Financial Services","NSE"],
 ["Shriram Finance","SHRIRAMFIN","NSE_EQ|INE721A01047","NSE_INDEX|Nifty Financial Services","NSE"],
 ["M&M Financial","M&MFIN","NSE_EQ|INE774D01024","NSE_INDEX|Nifty Financial Services","NSE"],
 ["HDFC Life","HDFCLIFE","NSE_EQ|INE795G01014","NSE_INDEX|Nifty Financial Services","NSE"],
 ["SBI Life","SBILIFE","NSE_EQ|INE123W01016","NSE_INDEX|Nifty Financial Services","NSE"],
 ["ICICI Lombard","ICICIGI","NSE_EQ|INE765G01017","NSE_INDEX|Nifty Financial Services","NSE"],
 ["ICICI Pru Life","ICICIPRU","NSE_EQ|INE726G01019","NSE_INDEX|Nifty Financial Services","NSE"],
 # NSE TELECOM / CEMENT / CAPGOODS
 ["Bharti Airtel","BHARTIARTL","NSE_EQ|INE397D01024","NSE_INDEX|Nifty 50","NSE"],
 ["UltraTech Cement","ULTRACEMCO","NSE_EQ|INE481G01011","NSE_INDEX|Nifty 50","NSE"],
 ["Shree Cement","SHREECEM","NSE_EQ|INE070A01015","NSE_INDEX|Nifty 50","NSE"],
 ["Ambuja Cements","AMBUJACEM","NSE_EQ|INE079A01024","NSE_INDEX|Nifty 50","NSE"],
 ["ACC","ACCLTD","NSE_EQ|INE012A01025","NSE_INDEX|Nifty 50","NSE"],
 ["Dalmia Bharat","DALMIACEM","NSE_EQ|INE120A01034","NSE_INDEX|Nifty 50","NSE"],
 ["Siemens","SIEMENS","NSE_EQ|INE003A01024","NSE_INDEX|Nifty 50","NSE"],
 ["ABB India","ABB","NSE_EQ|INE117A01022","NSE_INDEX|Nifty 50","NSE"],
 ["BHEL","BHEL","NSE_EQ|INE257A01026","NSE_INDEX|Nifty 50","NSE"],
 ["Havells India","HAVELLS","NSE_EQ|INE176B01034","NSE_INDEX|Nifty 50","NSE"],
 ["Voltas","VOLTAS","NSE_EQ|INE226A01021","NSE_INDEX|Nifty 50","NSE"],
 ["Dixon Technologies","DIXON","NSE_EQ|INE935N01020","NSE_INDEX|Nifty 50","NSE"],
 ["Titan Company","TITAN","NSE_EQ|INE280A01028","NSE_INDEX|Nifty 50","NSE"],
 ["Asian Paints","ASIANPAINT","NSE_EQ|INE021A01026","NSE_INDEX|Nifty 50","NSE"],
 ["Berger Paints","BERGEPAINT","NSE_EQ|INE463A01038","NSE_INDEX|Nifty 50","NSE"],
 ["Pidilite Ind","PIDILITIND","NSE_EQ|INE318A01026","NSE_INDEX|Nifty 50","NSE"],
 ["SRF","SRF","NSE_EQ|INE647A01010","NSE_INDEX|Nifty 50","NSE"],
 ["Deepak Nitrite","DEEPAKNTR","NSE_EQ|INE288B01029","NSE_INDEX|Nifty 50","NSE"],
 ["Coromandel Intl","COROMANDEL","NSE_EQ|INE169A01031","NSE_INDEX|Nifty 50","NSE"],
 ["PI Industries","PIIND","NSE_EQ|INE603J01030","NSE_INDEX|Nifty 50","NSE"],
 # NSE REALTY / DEFENCE / LOGISTICS
 ["DLF","DLF","NSE_EQ|INE271C01023","NSE_INDEX|Nifty Realty","NSE"],
 ["Lodha Dev","LODHA","NSE_EQ|INE752H01022","NSE_INDEX|Nifty Realty","NSE"],
 ["Godrej Prop","GODREJPROP","NSE_EQ|INE484J01027","NSE_INDEX|Nifty Realty","NSE"],
 ["Prestige Estates","PRESTIGE","NSE_EQ|INE811K01011","NSE_INDEX|Nifty Realty","NSE"],
 ["HAL","HAL","NSE_EQ|INE066F01020","NSE_INDEX|Nifty 50","NSE"],
 ["BEL","BEL","NSE_EQ|INE263A01024","NSE_INDEX|Nifty 50","NSE"],
 ["Cochin Shipyard","COCHINSHIP","NSE_EQ|INE704P01017","NSE_INDEX|Nifty 50","NSE"],
 ["Mazagon Dock","MAZDOCK","NSE_EQ|INE249M01031","NSE_INDEX|Nifty 50","NSE"],
 ["IndiGo","INDIGO","NSE_EQ|INE646L01027","NSE_INDEX|Nifty 50","NSE"],
 ["Avenue Supermarts","DMART","NSE_EQ|INE192R01011","NSE_INDEX|Nifty 50","NSE"],
 ["Trent","TRENTLTD","NSE_EQ|INE372A01015","NSE_INDEX|Nifty 50","NSE"],
 ["Zomato","ZOMATO","NSE_EQ|INE758T01015","NSE_INDEX|Nifty 50","NSE"],
 ["IRCTC","IRCTC","NSE_EQ|INE335Y01020","NSE_INDEX|Nifty 50","NSE"],
 ["Page Industries","PAGEIND","NSE_EQ|INE827B01014","NSE_INDEX|Nifty 50","NSE"],
 # BSE IT
 ["TCS","TCS","BSE_EQ|532540","BSE_INDEX|S&P BSE IT","BSE"],
 ["Infosys","INFY","BSE_EQ|500209","BSE_INDEX|S&P BSE IT","BSE"],
 ["Wipro","WIPRO","BSE_EQ|507685","BSE_INDEX|S&P BSE IT","BSE"],
 ["HCL Technologies","HCLTECH","BSE_EQ|532281","BSE_INDEX|S&P BSE IT","BSE"],
 ["Tech Mahindra","TECHM","BSE_EQ|532755","BSE_INDEX|S&P BSE IT","BSE"],
 ["LTIMindtree","LTIM","BSE_EQ|540005","BSE_INDEX|S&P BSE IT","BSE"],
 ["Mphasis","MPHASIS","BSE_EQ|526299","BSE_INDEX|S&P BSE IT","BSE"],
 ["Coforge","COFORGE","BSE_EQ|532541","BSE_INDEX|S&P BSE IT","BSE"],
 ["Persistent Sys","PERSISTENT","BSE_EQ|533179","BSE_INDEX|S&P BSE IT","BSE"],
 ["KPIT Tech","KPIT","BSE_EQ|542651","BSE_INDEX|S&P BSE IT","BSE"],
 ["Tata Elxsi","TATAELXSI","BSE_EQ|500408","BSE_INDEX|S&P BSE IT","BSE"],
 # BSE BANK
 ["HDFC Bank","HDFCBANK","BSE_EQ|500180","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["ICICI Bank","ICICIBANK","BSE_EQ|532174","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["Kotak Mah Bank","KOTAKBANK","BSE_EQ|500247","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["Axis Bank","AXISBANK","BSE_EQ|532215","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["State Bank India","SBIN","BSE_EQ|500112","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["IndusInd Bank","INDUSINDBK","BSE_EQ|532187","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["Bandhan Bank","BANDHANBNK","BSE_EQ|541153","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["Federal Bank","FEDERALBNK","BSE_EQ|500469","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["IDFC First Bank","IDFCFIRSTB","BSE_EQ|539437","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["AU Small Finance","AUBANK","BSE_EQ|540611","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["Canara Bank","CANBK","BSE_EQ|532483","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["Bank of Baroda","BANKBARODA","BSE_EQ|532134","BSE_INDEX|S&P BSE Bankex","BSE"],
 ["Punjab Natl Bank","PNB","BSE_EQ|532461","BSE_INDEX|S&P BSE Bankex","BSE"],
 # BSE FMCG
 ["HUL","HINDUNILVR","BSE_EQ|500696","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["ITC","ITC","BSE_EQ|500875","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["Nestle India","NESTLEIND","BSE_EQ|500790","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["Britannia","BRITANNIA","BSE_EQ|500825","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["Dabur India","DABUR","BSE_EQ|500096","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["Marico","MARICO","BSE_EQ|531642","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["Godrej Consumer","GODREJCP","BSE_EQ|532424","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["Tata Consumer","TATACONSUM","BSE_EQ|500800","BSE_INDEX|S&P BSE FMCG","BSE"],
 ["Varun Beverages","VBL","BSE_EQ|540180","BSE_INDEX|S&P BSE FMCG","BSE"],
 # BSE AUTO
 ["Maruti Suzuki","MARUTI","BSE_EQ|532500","BSE_INDEX|S&P BSE Auto","BSE"],
 ["Tata Motors","TATAMOTORS","BSE_EQ|500570","BSE_INDEX|S&P BSE Auto","BSE"],
 ["M&M","M&M","BSE_EQ|500520","BSE_INDEX|S&P BSE Auto","BSE"],
 ["Bajaj Auto","BAJAJ-AUTO","BSE_EQ|532977","BSE_INDEX|S&P BSE Auto","BSE"],
 ["Eicher Motors","EICHERMOT","BSE_EQ|505200","BSE_INDEX|S&P BSE Auto","BSE"],
 ["Hero MotoCorp","HEROMOTOCO","BSE_EQ|500182","BSE_INDEX|S&P BSE Auto","BSE"],
 ["Ashok Leyland","ASHOKLEY","BSE_EQ|500477","BSE_INDEX|S&P BSE Auto","BSE"],
 ["TVS Motor","TVSMOTOR","BSE_EQ|532343","BSE_INDEX|S&P BSE Auto","BSE"],
 ["Bharat Forge","BHARATFORG","BSE_EQ|500493","BSE_INDEX|S&P BSE Auto","BSE"],
 ["Bosch","BOSCHLTD","BSE_EQ|500530","BSE_INDEX|S&P BSE Auto","BSE"],
 # BSE PHARMA
 ["Sun Pharma","SUNPHARMA","BSE_EQ|524715","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Dr Reddy's","DRREDDY","BSE_EQ|500124","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Cipla","CIPLA","BSE_EQ|500087","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Divi's Labs","DIVISLAB","BSE_EQ|532488","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Aurobindo","AUROPHARMA","BSE_EQ|524804","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Torrent Pharma","TORNTPHARM","BSE_EQ|500420","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Lupin","LUPIN","BSE_EQ|500257","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Apollo Hospitals","APOLLOHOSP","BSE_EQ|508869","BSE_INDEX|S&P BSE Healthcare","BSE"],
 ["Max Healthcare","MAXHEALTH","BSE_EQ|543220","BSE_INDEX|S&P BSE Healthcare","BSE"],
 # BSE ENERGY / METAL
 ["Reliance Ind","RELIANCE","BSE_EQ|500325","BSE_INDEX|S&P BSE Energy","BSE"],
 ["ONGC","ONGC","BSE_EQ|500312","BSE_INDEX|S&P BSE Energy","BSE"],
 ["NTPC","NTPC","BSE_EQ|532555","BSE_INDEX|S&P BSE Energy","BSE"],
 ["Power Grid","POWERGRID","BSE_EQ|532898","BSE_INDEX|S&P BSE Energy","BSE"],
 ["GAIL India","GAIL","BSE_EQ|532155","BSE_INDEX|S&P BSE Energy","BSE"],
 ["Adani Ports","ADANIPORTS","BSE_EQ|532921","BSE_INDEX|S&P BSE Energy","BSE"],
 ["Tata Power","TATAPOWER","BSE_EQ|500400","BSE_INDEX|S&P BSE Energy","BSE"],
 ["Tata Steel","TATASTEEL","BSE_EQ|500470","BSE_INDEX|S&P BSE Metal","BSE"],
 ["Hindalco","HINDALCO","BSE_EQ|500440","BSE_INDEX|S&P BSE Metal","BSE"],
 ["JSW Steel","JSWSTEEL","BSE_EQ|500228","BSE_INDEX|S&P BSE Metal","BSE"],
 ["Vedanta","VEDL","BSE_EQ|500295","BSE_INDEX|S&P BSE Metal","BSE"],
 ["SAIL","SAIL","BSE_EQ|500113","BSE_INDEX|S&P BSE Metal","BSE"],
 ["Jindal Steel","JINDALSTEL","BSE_EQ|532286","BSE_INDEX|S&P BSE Metal","BSE"],
 # BSE FINANCE / MISC
 ["Bajaj Finance","BAJFINANCE","BSE_EQ|500034","BSE_INDEX|S&P BSE Finance","BSE"],
 ["Bajaj Finserv","BAJAJFINSV","BSE_EQ|532978","BSE_INDEX|S&P BSE Finance","BSE"],
 ["Cholamandalam","CHOLAFIN","BSE_EQ|511243","BSE_INDEX|S&P BSE Finance","BSE"],
 ["Muthoot Finance","MUTHOOTFIN","BSE_EQ|533398","BSE_INDEX|S&P BSE Finance","BSE"],
 ["Shriram Finance","SHRIRAMFIN","BSE_EQ|511218","BSE_INDEX|S&P BSE Finance","BSE"],
 ["HDFC Life","HDFCLIFE","BSE_EQ|540777","BSE_INDEX|S&P BSE Finance","BSE"],
 ["SBI Life","SBILIFE","BSE_EQ|540719","BSE_INDEX|S&P BSE Finance","BSE"],
 ["Bharti Airtel","BHARTIARTL","BSE_EQ|532454","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Asian Paints","ASIANPAINT","BSE_EQ|500820","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["UltraTech Cement","ULTRACEMCO","BSE_EQ|532538","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Titan Company","TITAN","BSE_EQ|500114","BSE_INDEX|S&P BSE Consumer Durables","BSE"],
 ["Pidilite","PIDILITIND","BSE_EQ|500331","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["HAL","HAL","BSE_EQ|541154","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["BEL","BEL","BSE_EQ|500049","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Lodha Dev","LODHA","BSE_EQ|543321","BSE_INDEX|S&P BSE Realty","BSE"],
 ["DLF","DLF","BSE_EQ|532868","BSE_INDEX|S&P BSE Realty","BSE"],
 ["IndiGo","INDIGO","BSE_EQ|521228","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Avenue Supermarts","DMART","BSE_EQ|540376","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Zomato","ZOMATO","BSE_EQ|543320","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Siemens","SIEMENS","BSE_EQ|500550","BSE_INDEX|S&P BSE Capital Goods","BSE"],
 ["ABB India","ABB","BSE_EQ|500002","BSE_INDEX|S&P BSE Capital Goods","BSE"],
 ["Havells","HAVELLS","BSE_EQ|517354","BSE_INDEX|S&P BSE Capital Goods","BSE"],
 ["Dixon Tech","DIXON","BSE_EQ|541987","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["SRF","SRF","BSE_EQ|503806","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["PI Industries","PIIND","BSE_EQ|523642","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["IRCTC","IRCTC","BSE_EQ|542830","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Trent","TRENTLTD","BSE_EQ|500251","BSE_INDEX|S&P BSE Sensex","BSE"],
 ["Berger Paints","BERGEPAINT","BSE_EQ|509480","BSE_INDEX|S&P BSE Sensex","BSE"],
]

def _builtin_to_dict(row):
    return {"name": row[0], "sym": row[1], "ikey": row[2],
            "sector": row[3], "exch": row[4], "isin": ""}

BUILTIN_UNIVERSE = [_builtin_to_dict(r) for r in _BUILTIN]

# Batch download store — lives on disk, one JSON per batch of 500
BATCH_DIR = Path("universe_batches")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UNIVERSE MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=3600, show_spinner=False)
def load_universe_cache() -> list:
    """Load from merged cache file, falling back to built-in universe."""
    # Try merged cache first
    if UNIVERSE_CACHE.exists():
        try:
            data = json.loads(UNIVERSE_CACHE.read_text())
            uni  = data.get("universe", [])
            if uni:
                return uni
        except Exception:
            pass
    # Try assembled batches
    assembled = _assemble_batches()
    if assembled:
        return assembled
    # Always-available fallback
    return BUILTIN_UNIVERSE


def _assemble_batches() -> list:
    """Merge all downloaded batch files into a single universe list."""
    if not BATCH_DIR.exists():
        return []
    all_stocks, seen = [], set()
    for f in sorted(BATCH_DIR.glob("batch_*.json")):
        try:
            batch = json.loads(f.read_text())
            for stk in batch:
                k = stk.get("ikey", "")
                if k and k not in seen:
                    seen.add(k)
                    all_stocks.append(stk)
        except Exception:
            pass
    return all_stocks


def _save_merged_cache(uni: list):
    nse_c = sum(1 for u in uni if u.get("exch") == "NSE")
    bse_c = len(uni) - nse_c
    cache = {"generated": datetime.datetime.now().isoformat(),
             "total": len(uni), "nse": nse_c, "bse": bse_c, "universe": uni}
    UNIVERSE_CACHE.write_text(json.dumps(cache, separators=(",", ":")))


def build_universe_sync(progress_cb=None) -> list:
    """
    Download Upstox instrument master in 500-row batches and store each
    batch to disk immediately.  If the download fails mid-way, completed
    batches are preserved and the app still works with partial data.
    Falls back to BUILTIN_UNIVERSE if the download cannot start at all.
    """
    BATCH_DIR.mkdir(exist_ok=True)

    # ── Step 1: Sector maps ──────────────────────────────────────────────
    isin_sector: dict = {}
    hdrs = {"User-Agent": "Mozilla/5.0 (compatible; Screener/5.0)"}
    total_sectors = len(NSE_SECTOR_URLS)
    for i, (idx_key, url) in enumerate(NSE_SECTOR_URLS.items()):
        if progress_cb:
            progress_cb(i / (total_sectors * 4),
                        f"Fetching sector map {i+1}/{total_sectors}: {idx_key.split('|')[1]}…")
        try:
            r = requests.get(url, headers=hdrs, timeout=12)
            if r.status_code == 200:
                for row in csv.DictReader(io.StringIO(r.text)):
                    isin = (row.get("ISIN Code") or row.get("ISIN") or "").strip()
                    if isin:
                        isin_sector[isin] = idx_key
        except Exception:
            pass
        time.sleep(0.3)

    if progress_cb:
        progress_cb(0.25, f"✅ Sector maps: {len(isin_sector):,} ISINs  →  downloading instrument master in batches…")

    # ── Step 2: Download gzip in chunks ──────────────────────────────────
    raw_chunks = []
    try:
        with requests.get(INSTRUMENT_URL, timeout=90, stream=True) as resp:
            resp.raise_for_status()
            total_bytes = int(resp.headers.get("Content-Length", 0))
            downloaded  = 0
            for chunk in resp.iter_content(chunk_size=65536):   # 64 KB chunks
                if chunk:
                    raw_chunks.append(chunk)
                    downloaded += len(chunk)
                    if total_bytes > 0 and progress_cb:
                        pct = 0.25 + (downloaded / total_bytes) * 0.40
                        progress_cb(pct,
                            f"Downloading… {downloaded//1024:,} KB / {total_bytes//1024:,} KB")
    except Exception as e:
        if progress_cb:
            progress_cb(0.25, f"⚠️  Download failed ({e}) — using built-in universe of {len(BUILTIN_UNIVERSE)} stocks")
        # Return whatever we assembled from previous batches (or built-in)
        assembled = _assemble_batches()
        return assembled if assembled else BUILTIN_UNIVERSE

    if progress_cb:
        progress_cb(0.65, "Parsing instrument master and storing batches…")

    # ── Step 3: Parse and store in 500-row batches ───────────────────────
    raw = b"".join(raw_chunks)
    try:
        with gzip.open(io.BytesIO(raw), "rt", encoding="utf-8") as f:
            all_rows = list(csv.DictReader(f))
    except Exception as e:
        if progress_cb:
            progress_cb(0.65, f"⚠️  Parse error ({e}) — using built-in universe")
        return BUILTIN_UNIVERSE

    BATCH_SIZE = 500
    uni, seen, batch_num = [], set(), 0
    current_batch: list = []

    for row in all_rows:
        seg  = row.get("segment", "")
        inst = row.get("instrument_type", "")
        ikey = row.get("instrument_key", "")
        isin = row.get("isin", "")
        sym  = row.get("trading_symbol", row.get("tradingsymbol", "")).upper().strip()
        name = row.get("name", sym).strip()

        if seg not in ("NSE_EQ", "BSE_EQ") or inst != "EQUITY":
            continue
        if not ikey or ikey in seen:
            continue
        seen.add(ikey)

        exch    = "NSE" if seg == "NSE_EQ" else "BSE"
        nse_sec = isin_sector.get(isin, "NSE_INDEX|Nifty 500")
        bse_sec = nse_sec.replace("NSE_INDEX|Nifty", "BSE_INDEX|S&P BSE")
        stock   = {"name": name[:32], "sym": sym, "ikey": ikey,
                   "sector": nse_sec if exch == "NSE" else bse_sec,
                   "exch": exch, "isin": isin}

        current_batch.append(stock)
        uni.append(stock)

        if len(current_batch) >= BATCH_SIZE:
            batch_path = BATCH_DIR / f"batch_{batch_num:04d}.json"
            batch_path.write_text(json.dumps(current_batch, separators=(",", ":")))
            batch_num    += 1
            current_batch = []

            if progress_cb:
                pct = 0.65 + min(batch_num / 12, 1.0) * 0.30
                progress_cb(pct, f"Stored batch {batch_num} — {len(uni):,} stocks so far…")

    # Save final partial batch
    if current_batch:
        batch_path = BATCH_DIR / f"batch_{batch_num:04d}.json"
        batch_path.write_text(json.dumps(current_batch, separators=(",", ":")))

    # ── Step 4: Merge + save combined cache ──────────────────────────────
    _save_merged_cache(uni)

    nse_c = sum(1 for u in uni if u["exch"] == "NSE")
    bse_c = len(uni) - nse_c
    if progress_cb:
        progress_cb(1.0,
            f"✅ Complete: {len(uni):,} stocks ({nse_c:,} NSE + {bse_c:,} BSE) "
            f"in {batch_num+1} batches stored to disk")
    return uni


def get_fundamentals() -> dict:
    return json.loads(FUND_DATA_PATH.read_text()) if FUND_DATA_PATH.exists() else {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EPS INTELLIGENCE ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TECHNICAL INDICATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCAN ENGINE  (runs in background thread)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def run_scan_thread(token: str, cfg: dict, uni: list, fd: dict):
    """Runs in a daemon thread; writes progress to session_state via shared dict."""
    total   = len(uni)
    results = []
    stats   = st.session_state.scan_stats

    stats.update({"total": total, "processed": 0, "passed": 0, "perfect": 0})
    st.session_state.scan_running = True
    st.session_state.scan_done    = False

    # Phase 1: Batch LTP
    st.session_state.scan_msg = "Phase 1/3: Fetching live prices (batch)…"
    ltp_map = fetch_batch_ltp([u["ikey"] for u in uni], token)

    # Phase 2: Sector indices
    st.session_state.scan_msg = "Phase 2/3: Caching sector index candles…"
    sec_keys  = list({u["sector"] for u in uni})
    sec_cache = {}
    for sk in sec_keys:
        sec_cache[sk] = fetch_hist(sk, token)
        time.sleep(0.1)

    # Phase 3: Per-stock
    for i, stk in enumerate(uni):
        if not st.session_state.get("scan_running", False):
            break  # cancelled

        sym  = stk["sym"]
        ikey = stk["ikey"]
        skey = stk["sector"]

        stats["processed"] = i + 1
        pct = (i + 1) / total
        st.session_state.scan_progress = pct
        st.session_state.scan_msg = (
            f"Phase 3/3: [{i+1}/{total}]  {sym}  — "
            f"{stats['passed']} passed  {stats['perfect']} perfect"
        )

        df = fetch_hist(ikey, token)
        if df is None or len(df) < 30:
            continue

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
            "name":    stk["name"],  "sym":     sym,
            "sector":  skey.replace("NSE_INDEX|Nifty ","").replace("BSE_INDEX|S&P BSE ",""),
            "exch":    stk["exch"],  "price":   round(price, 2),
            "high":    round(h52_, 2), "dH":   round(dH, 2),
            "sp":      round(sp, 2),  "xp":    round(xp, 2),
            "rs_leader": rs_leader,   "sma":   round(sm, 2),
            "dS":      round(dS, 2),  "in_bz": in_bz,
            "rsi":     None if math.isnan(rsi_v) else rsi_v,
            "eps":     fund.get("eps", []),   "sales": fund.get("sales", []),
            "ttm":     fund.get("ttm"),        "pe":    pe,
            "yoy":     yoy,                    "g":     fund.get("g", []),
            "ac":      fund.get("ac", {}),     "sr":    fund.get("sr", {}),
            "sq":      fund.get("sq", {}),
            "eps_ok":  ttm >= cfg["min_eps"],
            "yoy_ok":  bool(yoy and yoy >= cfg["min_yoy"]),
            "ac_ok":   ac_ok, "sr_ok": sr_ok, "sq_ok": sq_ok,
            "fs":      fs,    "perfect": is_perfect,
        })
        time.sleep(0.05)

    st.session_state.results       = sorted(results, key=lambda x: x.get("fs", 0), reverse=True)
    st.session_state.scan_running  = False
    st.session_state.scan_done     = True
    st.session_state.scan_progress = 1.0
    st.session_state.last_scan_time = datetime.datetime.now().strftime("%d %b %Y  %H:%M IST")
    st.session_state.scan_msg      = (
        f"✅ Scan complete — {stats['passed']} passed / {total} total "
        f"({stats['perfect']} perfect)"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHART HELPERS  (Plotly dark theme)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HTML COMPONENT HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RENDER STOCK CARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN UI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="screener-header">
  <h1>🚀 NSE + BSE Multibagger Screener</h1>
  <div class="sub">
    ~5000 Stocks · EPS Acceleration · Surprise Factor · RS Resilience · 21MA Buy Zone · Upstox V2
  </div>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("### 🚀 Multibagger Screener")
    st.caption("NSE + BSE · v5.0 · Upstox V2")
    st.divider()

    # ── Universe ──────────────────────────────────────────────────────────
    st.markdown('<div class="sec-lbl">🌐 Universe</div>', unsafe_allow_html=True)

    uni = load_universe_cache()
    if not uni and UNIVERSE_CACHE.exists():
        uni = load_universe_cache()
    uni_size = len(uni)
    nse_c = sum(1 for u in uni if u.get("exch") == "NSE")
    bse_c = uni_size - nse_c

    col1, col2, col3 = st.columns(3)
    col1.metric("NSE", f"{nse_c:,}")
    col2.metric("BSE", f"{bse_c:,}")
    batch_count = len(list(BATCH_DIR.glob("batch_*.json"))) if BATCH_DIR.exists() else 0
    col3.metric("Batches", f"{batch_count}")

    if st.button("🔄 Download Universe (~5000 stocks)", use_container_width=True):
        bar_ph  = st.progress(0.0)
        prog_ph = st.empty()
        def _prog(pct, msg):
            bar_ph.progress(min(float(pct), 1.0))
            prog_ph.caption(msg)
        # Download runs synchronously with live progress
        new_uni = build_universe_sync(_prog)
        load_universe_cache.clear()
        if new_uni and new_uni is not BUILTIN_UNIVERSE:
            st.success(f"✅ {len(new_uni):,} stocks downloaded & stored in batches")
        elif new_uni:
            st.warning(
                f"⚠️ Download failed — using built-in universe of "
                f"{len(new_uni):,} stocks. "
                f"Check your internet connection and try again."
            )
        st.rerun()

    if UNIVERSE_CACHE.exists():
        info = json.loads(UNIVERSE_CACHE.read_text())
        st.caption(f"Generated: {info.get('generated','—')[:16]}")

    st.divider()

    # ── Token ─────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-lbl">🔑 Upstox Token</div>', unsafe_allow_html=True)
    token = st.text_input("Access Token", type="password",
                          placeholder="Paste bearer token…", key="token_input")
    st.caption("① upstox.com/developer → Your App\n② OAuth2 flow → copy access_token\n③ Valid for 1 trading day")

    st.divider()

    # ── EPS Filters ───────────────────────────────────────────────────────
    st.markdown('<div class="sec-lbl">📊 EPS Filters</div>', unsafe_allow_html=True)
    min_eps  = st.slider("Min TTM EPS (₹)",      0, 120,  10, 2)
    min_yoy  = st.slider("Min YoY EPS Growth %", 0, 100,  20, 5)
    req_accel = st.checkbox("EPS Accelerating (Staircase)", value=True)
    req_surp  = st.checkbox("Analyst Beat Required",         value=False)
    req_qual  = st.checkbox("Sales + EPS Quality",           value=True)

    st.divider()

    # ── Technical Filters ─────────────────────────────────────────────────
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

    # ── Run / Stop ────────────────────────────────────────────────────────
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
    # ── Utility ───────────────────────────────────────────────────────────
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LAUNCH SCAN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if run_btn:
    if not token:
        st.error("⚠️ Please enter your Upstox Access Token in the sidebar.")
        st.stop()
    uni_now = load_universe_cache()  # always returns at least BUILTIN_UNIVERSE
    if not uni_now:
        uni_now = BUILTIN_UNIVERSE
    st.session_state.results       = []
    st.session_state.scan_running  = True
    st.session_state.scan_done     = False
    st.session_state.scan_progress = 0.0
    fd = get_fundamentals()
    t  = threading.Thread(
        target=run_scan_thread,
        args=(token, cfg, uni_now, fd),
        daemon=True,
    )
    t.start()
    st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROGRESS BAR  (auto-refreshes while scanning)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.scan_running:
    stats = st.session_state.scan_stats
    pct   = st.session_state.scan_progress
    st.markdown("""<div class="prog-box">
      <div class="plbl">● SCANNING</div></div>""", unsafe_allow_html=True)
    st.progress(min(pct, 1.0))
    st.caption(st.session_state.scan_msg)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total",     stats.get("total", 0))
    c2.metric("Processed", stats.get("processed", 0))
    c3.metric("Passed",    stats.get("passed", 0))
    c4.metric("⭐ Perfect", stats.get("perfect", 0))
    time.sleep(2)
    st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
results = st.session_state.results

if not results and not st.session_state.scan_running:
    # ── Welcome screen ────────────────────────────────────────────────────
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

    st.info(
        "**Ready to scan right away!** A built-in universe of "
        f"**{len(BUILTIN_UNIVERSE):,} NSE+BSE stocks** is pre-loaded.\n\n"
        "**Step 1:** Paste your Upstox token in the sidebar  \n"
        "**Step 2:** Click **🔍 RUN FULL SCAN**  \n\n"
        "👉 Optionally click **🔄 Download Universe** to expand to ~5,000 stocks "
        "(stored in 500-stock batches so partial downloads still work)."
    )
    st.stop()

# ── Exchange filter ───────────────────────────────────────────────────────────
exch_opts  = ["All", "NSE", "BSE"]
exch_sel   = st.radio("Exchange Filter:", exch_opts, horizontal=True,
                       index=exch_opts.index(st.session_state.exch_filter))
st.session_state.exch_filter = exch_sel

def filtered(rows: list) -> list:
    if exch_sel == "All":
        return rows
    return [r for r in rows if r.get("exch","") == exch_sel]

frows = filtered(results)

# ── KPI strip ─────────────────────────────────────────────────────────────────
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab_perf, tab_eps, tab_all, tab_charts, tab_exp = st.tabs([
    "⭐ Perfect Setups", "🔬 EPS Deep Dive",
    "📋 Full Results",   "📊 Charts", "💾 Export"
])

# ── TAB 1: Perfect Setups ─────────────────────────────────────────────────────
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

# ── TAB 2: EPS Deep Dive ──────────────────────────────────────────────────────
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

# ── TAB 3: Full Results ───────────────────────────────────────────────────────
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

# ── TAB 4: Charts ─────────────────────────────────────────────────────────────
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

# ── TAB 5: Export ─────────────────────────────────────────────────────────────
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

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<p style="font-family:JetBrains Mono,monospace;font-size:.58rem;color:#252a3a;'
    f'text-align:right;margin-top:32px;">'
    f'NSE+BSE Multibagger Screener · Upstox V2 · Streamlit v5.0 · '
    f'{datetime.date.today()}</p>',
    unsafe_allow_html=True
)
