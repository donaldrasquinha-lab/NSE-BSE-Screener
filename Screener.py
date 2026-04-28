# -*- coding: utf-8 -*-
"""
NSE + BSE Multibagger Screener v6.0 -- Streamlit Edition
Downloads full Upstox instrument CSV | Live scan after filter | Database tab

INSTALL:  pip install streamlit plotly requests numpy pandas
RUN:      streamlit run screener_st.py
"""

import io, csv, gzip, json, math, time, datetime, sqlite3, threading, traceback
from pathlib import Path
from typing   import Optional

import requests
import numpy  as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===========================================================================
#  CONFIG
# ===========================================================================
UPSTOX_BASE  = "https://api.upstox.com/v2"
DB_PATH      = Path("universe.db")
FUND_PATH    = Path("fundamentals.json")

# Upstox CDN instrument master URLs (tries each in order)
INST_URLS = [
    "https://assets.upstox.com/market-assets/instruments/exchange/complete.csv.gz",
    "https://assets.upstox.com/market-assets/instruments/v2/NSE.csv.gz",
]

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

st.set_page_config(page_title="NSE+BSE Screener",page_icon="🚀",layout="wide",
                   initial_sidebar_state="expanded")

# ===========================================================================
#  CSS
# ===========================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');
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
.stButton>button:disabled{opacity:.4!important;transform:none!important;}
.stTextInput>div>div>input,.stNumberInput>div>div>input{
  background:#131928!important;border:1px solid #253050!important;color:var(--t1)!important;
  border-radius:7px!important;font-family:var(--mono)!important;}
.stSelectbox>div>div{background:#131928!important;border-color:#253050!important;}
.stTabs [role="tablist"]{background:#0f1320;border:1px solid #1e2740;border-radius:10px;padding:3px;}
.stTabs [role="tab"]{color:#5c6a88!important;border-radius:7px!important;font-family:var(--sans)!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{background:#131928!important;color:var(--sky)!important;}
.stDataFrame{border-radius:10px!important;overflow:hidden;}
div[data-testid="stInfo"]{background:rgba(56,189,248,.07)!important;border:1px solid rgba(56,189,248,.2)!important;}
div[data-testid="stSuccess"]{background:rgba(52,211,153,.07)!important;border:1px solid rgba(52,211,153,.2)!important;}
div[data-testid="stWarning"]{background:rgba(251,191,36,.07)!important;border:1px solid rgba(251,191,36,.2)!important;}
div[data-testid="stError"]{background:rgba(248,113,113,.07)!important;border:1px solid rgba(248,113,113,.2)!important;}
.stProgress>div>div{background:linear-gradient(90deg,var(--sky),var(--sage))!important;}
#MainMenu,footer,header{visibility:hidden!important;}
div[data-baseweb="slider"]>div{background:#253050!important;}
div[data-baseweb="slider"]>div>div{background:var(--sky)!important;}

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
.clav{color:var(--lav);}.ctang{color:var(--tang);}
.sig{display:inline-flex;align-items:center;padding:2px 8px;border-radius:4px;
  font-family:var(--mono);font-size:.57rem;font-weight:500;margin:2px;}
.sig-rs{background:rgba(56,189,248,.1);color:var(--sky);border:1px solid rgba(56,189,248,.25);}
.sig-bz{background:rgba(251,146,60,.1);color:var(--tang);border:1px solid rgba(251,146,60,.25);}
.sig-ac{background:rgba(251,191,36,.1);color:var(--amber);border:1px solid rgba(251,191,36,.25);}
.sig-sr{background:rgba(167,139,250,.1);color:var(--lav);border:1px solid rgba(167,139,250,.25);}
.sig-ok{background:rgba(52,211,153,.12);color:var(--sage);border:1px solid rgba(52,211,153,.3);font-weight:700;}
.scard{background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:14px 16px;margin-bottom:8px;}
.scard.hit{background:linear-gradient(160deg,#0f1d14,var(--card));border-color:rgba(52,211,153,.3);}
.scard .ch{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;}
.scard .sym{font-weight:700;font-size:1rem;color:var(--t1);}
.scard .nm{font-size:.7rem;color:var(--t3);flex:1;}
.scard .live-px{font-family:var(--mono);font-weight:700;font-size:1.05rem;color:var(--sage);margin-left:auto;}
.scard .live-chg{font-family:var(--mono);font-size:.72rem;text-align:right;}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:5px;margin:10px 0;}
.met{background:var(--card2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;}
.met .ml{font-size:.55rem;color:var(--t4);text-transform:uppercase;letter-spacing:.8px;}
.met .mv{font-size:.84rem;font-weight:600;color:var(--t1);margin-top:2px;font-family:var(--mono);}
.igrid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px;}
.ip{background:#0a0e1a;border:1px solid var(--border);border-radius:7px;padding:10px 12px;}
.ip .il{font-family:var(--mono);font-size:.55rem;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;}
.ip .iv{font-size:.78rem;font-weight:600;color:var(--t1);}
.ip .is{font-family:var(--mono);font-size:.6rem;color:var(--t4);margin-top:3px;}
.stair{display:flex;align-items:flex-end;gap:4px;height:70px;padding:5px 6px 0;
  background:#0a0e1a;border:1px solid var(--border);border-radius:7px;margin:10px 0;}
.scol{display:flex;flex-direction:column;align-items:center;flex:1;height:100%;justify-content:flex-end;}
.sarr{font-size:.56rem;margin-bottom:2px;font-family:var(--mono);}
.sbar{width:100%;border-radius:3px 3px 0 0;min-height:6px;display:flex;align-items:center;
  justify-content:center;font-size:.56rem;font-weight:600;color:rgba(0,0,0,.9);}
.slb{font-family:var(--mono);font-size:.52rem;color:var(--t4);margin-top:2px;}
.prog-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:14px;}
.scanning{animation:blink 1.2s ease infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.4;}}
</style>
""", unsafe_allow_html=True)

# ===========================================================================
#  THREAD-SAFE SCAN STATE
# ===========================================================================
import threading as _th
_SCAN: dict = {"running":False,"progress":0.0,"msg":"","done":False,
               "error":"","results":[],"log":[],
               "stats":{"total":0,"processed":0,"passed":0,"perfect":0}}
_LOCK = _th.Lock()

def _su(**kw):
    with _LOCK:
        for k,v in kw.items(): _SCAN[k]=v

def _sl(m):
    with _LOCK:
        _SCAN["log"].append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}")

# ===========================================================================
#  SESSION STATE
# ===========================================================================
def _init():
    for k,v in {
        "results":[],"scan_running":False,"scan_done":False,"scan_error":"",
        "last_scan_time":None,"exch_filter":"All",
        "token_status":"unknown","token_user":"",
        "dl_running":False,"dl_msg":"","dl_error":"",
        "live_prices":{},"live_updated":None,
    }.items():
        if k not in st.session_state: st.session_state[k]=v
_init()

# ===========================================================================
#  DATABASE
# ===========================================================================
def _db():
    c = sqlite3.connect(str(DB_PATH),check_same_thread=False)
    c.execute("""CREATE TABLE IF NOT EXISTS instruments(
        ikey TEXT PRIMARY KEY, sym TEXT NOT NULL, name TEXT,
        exch TEXT NOT NULL, segment TEXT, inst_type TEXT,
        lot_size INTEGER DEFAULT 1, tick_size REAL DEFAULT 0.05,
        isin TEXT, sector TEXT, expiry TEXT, added TEXT, updated TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_e ON instruments(exch)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_s ON instruments(sym)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_t ON instruments(inst_type)")
    for col in ["segment TEXT","inst_type TEXT","lot_size INTEGER DEFAULT 1",
                "tick_size REAL DEFAULT 0.05","isin TEXT","sector TEXT",
                "expiry TEXT","updated TEXT"]:
        try: c.execute(f"ALTER TABLE instruments ADD COLUMN {col}")
        except: pass
    c.commit(); return c

def db_count():
    try:
        c=_db()
        t=c.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
        n=c.execute("SELECT COUNT(*) FROM instruments WHERE exch='NSE'").fetchone()[0]
        b=c.execute("SELECT COUNT(*) FROM instruments WHERE exch='BSE'").fetchone()[0]
        c.close(); return {"total":t,"nse":n,"bse":b}
    except: return {"total":0,"nse":0,"bse":0}

def db_load_all(exch=None,page=1,per=500):
    try:
        c=_db()
        off=(page-1)*per
        w=" WHERE exch=?" if exch else ""
        p=[exch] if exch else []
        rows=c.execute(f"SELECT ikey,sym,name,exch,segment,inst_type,lot_size,tick_size,isin,sector FROM instruments{w} ORDER BY sym LIMIT {per} OFFSET {off}",p).fetchall()
        c.close()
        return [{"ikey":r[0],"sym":r[1],"name":r[2],"exch":r[3],"segment":r[4],
                 "inst_type":r[5],"lot_size":r[6],"tick_size":r[7],"isin":r[8],
                 "sector":r[9] or ""} for r in rows]
    except: return []

def db_load_equity():
    try:
        c=_db()
        rows=c.execute("""SELECT ikey,sym,name,exch,sector FROM instruments
            WHERE (inst_type IN ('EQUITY','EQ') OR inst_type IS NULL OR inst_type='')
            AND (expiry IS NULL OR expiry='')""").fetchall()
        c.close()
        return [{"ikey":r[0],"sym":r[1],"name":r[2],"exch":r[3],
                 "sector":r[4] or "NSE_INDEX|Nifty 500"} for r in rows]
    except: return []

def db_total_count():
    try:
        c=_db(); t=c.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]; c.close(); return t
    except: return 0

def db_save_many(rows):
    if not rows: return
    now=datetime.datetime.now().isoformat()
    c=_db()
    c.executemany(
        "INSERT OR REPLACE INTO instruments(ikey,sym,name,exch,segment,inst_type,"
        "lot_size,tick_size,isin,sector,expiry,added,updated)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,"
        "COALESCE((SELECT added FROM instruments WHERE ikey=?),?),?)",
        [(r["ikey"],r.get("sym",""),r.get("name",""),r.get("exch",""),
          r.get("segment",""),r.get("inst_type",""),
          int(r.get("lot_size") or 1), float(r.get("tick_size") or 0.05),
          r.get("isin",""), r.get("sector",""), r.get("expiry",""),
          r["ikey"], now, now) for r in rows])
    c.commit(); c.close()

def db_get_keys():
    try:
        c=_db(); k={r[0] for r in c.execute("SELECT ikey FROM instruments").fetchall()}
        c.close(); return k
    except: return set()

# ===========================================================================
#  INSTRUMENT DOWNLOAD — full CSV from Upstox developer portal
# ===========================================================================
def _fetch_sector_maps(token):
    imap={}
    hdrs={"User-Agent":"Mozilla/5.0"}
    if token: hdrs["Authorization"]=f"Bearer {token}"
    for idx_key,url in NSE_SECTOR_URLS.items():
        try:
            r=requests.get(url,headers=hdrs,timeout=10)
            if r.status_code==200:
                for row in csv.DictReader(io.StringIO(r.text)):
                    isin=(row.get("ISIN Code") or row.get("ISIN") or "").strip()
                    if isin: imap[isin]=idx_key
        except: pass
        time.sleep(0.2)
    return imap

def _parse_csv_gz(raw_bytes, isin_sector):
    """Parse gzipped CSV instrument master. Returns list of dicts."""
    instruments=[]; seen=set()
    try:
        with gzip.open(io.BytesIO(raw_bytes),"rt",encoding="utf-8",errors="replace") as f:
            reader=csv.DictReader(f)
            for row in reader:
                seg  =row.get("segment","")
                itype=row.get("instrument_type","")
                ikey =row.get("instrument_key","")
                if not ikey or ikey in seen: continue
                seen.add(ikey)
                isin =row.get("isin","")
                sym  =row.get("trading_symbol",row.get("tradingsymbol","")).upper().strip()
                name =row.get("name","").strip() or sym
                exch =row.get("exchange","")
                if "NSE" in seg: exch="NSE"
                elif "BSE" in seg: exch="BSE"
                sector=isin_sector.get(isin,
                    "NSE_INDEX|Nifty 500" if exch=="NSE" else "BSE_INDEX|S&P BSE 500")
                instruments.append({
                    "ikey":ikey,"sym":sym,"name":name[:40],"exch":exch,
                    "segment":seg,"inst_type":itype,
                    "lot_size":row.get("lot_size","1"),
                    "tick_size":row.get("tick_size","0.05"),
                    "isin":isin,"sector":sector,
                    "expiry":row.get("expiry",""),
                })
    except Exception as e:
        _sl(f"CSV parse error: {e}")
    return instruments

def _download_via_api(token, progress_cb=None):
    """Fallback: use Upstox API /instruments endpoint."""
    all_rows=[]
    hdrs={"Authorization":f"Bearer {token}","Accept":"application/json"}
    for exch_seg in ["NSE_EQ","BSE_EQ"]:
        if progress_cb: progress_cb(0.3+0.1*(exch_seg=="BSE_EQ"),
                                    f"API: fetching {exch_seg}...")
        try:
            r=requests.get(f"{UPSTOX_BASE}/instruments",headers=hdrs,
                           params={"exchange":exch_seg},timeout=60)
            if r.status_code==200:
                data=r.json()
                rows=(data.get("data") or data) if isinstance(data,dict) else data
                if isinstance(rows,list):
                    all_rows.extend(rows)
                    if progress_cb: progress_cb(0.5,f"API: {len(all_rows):,} rows so far")
            else:
                _sl(f"API {exch_seg}: HTTP {r.status_code}")
        except Exception as e:
            _sl(f"API {exch_seg}: {e}")
        time.sleep(0.3)
    return all_rows

def download_instruments_full(token, progress_cb=None):
    """
    Download the complete NSE+BSE instrument list from Upstox.
    Strategy:
      1. Fetch sector maps from NSE for ISIN->sector mapping
      2. Try Upstox CDN gzip CSV (with and without token)
      3. Fall back to Upstox V2 API /instruments endpoint
      4. Parse and store ALL instruments (not just equity) to SQLite
    """
    # Step 1: Sector maps
    if progress_cb: progress_cb(0.02,"Fetching NSE sector maps...")
    isin_sector=_fetch_sector_maps(token)
    if progress_cb: progress_cb(0.12,f"Sector maps: {len(isin_sector):,} ISINs")

    # Step 2: Try CDN download
    raw_bytes=None
    for i,url in enumerate(INST_URLS):
        if progress_cb: progress_cb(0.14+i*0.03,f"Trying CDN: {url.split('/')[-1]}...")
        hdrs={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept":"application/octet-stream,*/*",
            "Referer":"https://upstox.com/",
        }
        if token: hdrs["Authorization"]=f"Bearer {token}"
        try:
            chunks,downloaded,total=[],0,0
            with requests.get(url,headers=hdrs,stream=True,timeout=120) as resp:
                if resp.status_code in (401,403,404):
                    _sl(f"CDN {url}: HTTP {resp.status_code}"); continue
                resp.raise_for_status()
                total=int(resp.headers.get("Content-Length",0))
                for chunk in resp.iter_content(65536):
                    if chunk:
                        chunks.append(chunk); downloaded+=len(chunk)
                        if progress_cb and total>0:
                            progress_cb(0.20+(downloaded/total)*0.45,
                                f"Downloading {url.split('/')[-1]}: "
                                f"{downloaded//1024:,} / {total//1024:,} KB")
            if chunks:
                raw_bytes=b"".join(chunks)
                _sl(f"CDN success: {len(raw_bytes)//1024:,} KB from {url}")
                break
        except Exception as e:
            _sl(f"CDN {url}: {e}"); continue

    # Step 3: Parse or API fallback
    instruments=[]
    if raw_bytes:
        if progress_cb: progress_cb(0.68,"Parsing instrument CSV...")
        instruments=_parse_csv_gz(raw_bytes, isin_sector)
        _sl(f"Parsed {len(instruments):,} instruments from CSV")
    elif token:
        if progress_cb: progress_cb(0.25,"CDN unavailable — using Upstox API /instruments...")
        api_rows=_download_via_api(token, progress_cb)
        if api_rows:
            existing_keys=db_get_keys()
            for row in api_rows:
                ikey=(row.get("instrument_key") or row.get("key",""))
                if not ikey or ikey in existing_keys: continue
                seg=row.get("segment",""); exch=row.get("exchange","")
                if "NSE" in seg or exch=="NSE": exch="NSE"
                elif "BSE" in seg or exch=="BSE": exch="BSE"
                isin=row.get("isin","")
                sym=(row.get("trading_symbol") or row.get("tradingsymbol") or "").upper().strip()
                name=row.get("name","") or sym
                sector=isin_sector.get(isin,
                    "NSE_INDEX|Nifty 500" if exch=="NSE" else "BSE_INDEX|S&P BSE 500")
                instruments.append({
                    "ikey":ikey,"sym":sym,"name":name[:40],"exch":exch,
                    "segment":seg,"inst_type":row.get("instrument_type","EQ"),
                    "lot_size":row.get("lot_size","1"),
                    "tick_size":row.get("tick_size","0.05"),
                    "isin":isin,"sector":sector,"expiry":row.get("expiry",""),
                })

    if not instruments:
        return {"ok":False,"error":"All download methods failed. Check token and network.",
                "total":db_total_count(),"new":0}

    # Step 4: Save to DB in batches of 500
    existing_keys=db_get_keys()
    new_rows=[r for r in instruments if r["ikey"] not in existing_keys]
    if progress_cb: progress_cb(0.70,f"Saving {len(new_rows):,} new instruments to DB...")

    BATCH=500
    for i in range(0,len(new_rows),BATCH):
        db_save_many(new_rows[i:i+BATCH])
        if progress_cb:
            pct=0.70+(i/max(len(new_rows),1))*0.28
            progress_cb(pct,f"Saved {min(i+BATCH,len(new_rows)):,} / {len(new_rows):,}...")

    c=db_count()
    if progress_cb:
        progress_cb(1.0,
            f"Done! {c['total']:,} total ({c['nse']:,} NSE + {c['bse']:,} BSE) | "
            f"{len(new_rows):,} new this run")
    return {"ok":True,"total":c["total"],"nse":c["nse"],"bse":c["bse"],
            "new":len(new_rows),"error":""}

# ===========================================================================
#  UPSTOX LIVE DATA
# ===========================================================================
def _hdr(token): return {"Authorization":f"Bearer {token}","Accept":"application/json"}

def fetch_ltp_batch(keys, token):
    out={}
    for i in range(0,len(keys),200):
        batch=keys[i:i+200]
        try:
            r=requests.get(f"{UPSTOX_BASE}/market-quote/ltp",headers=_hdr(token),
                params={"instrument_key":",".join(batch)},timeout=15)
            if r.status_code==200:
                for ikey,v in r.json().get("data",{}).items():
                    ltp=v.get("last_price") or v.get("ltp")
                    if ltp: out[ikey]=float(ltp)
        except: pass
        time.sleep(0.15)
    return out

def fetch_full_quotes(keys, token):
    """Returns {ikey: {ltp, chg, pct, prev}}."""
    out={}
    for i in range(0,len(keys),100):
        batch=keys[i:i+100]
        try:
            r=requests.get(f"{UPSTOX_BASE}/market-quote/quotes",headers=_hdr(token),
                params={"instrument_key":",".join(batch)},timeout=15)
            if r.status_code==200:
                for ikey,v in r.json().get("data",{}).items():
                    ltp=float(v.get("last_price") or 0)
                    prev=float(v.get("ohlc",{}).get("close") or v.get("prev_close_price") or ltp)
                    chg=ltp-prev; pct=(chg/prev*100) if prev else 0
                    out[ikey]={"ltp":ltp,"chg":round(chg,2),"pct":round(pct,2),"prev":prev}
        except: pass
        time.sleep(0.2)
    return out

def fetch_hist(ikey, token, days=430):
    td=datetime.date.today(); fd=td-datetime.timedelta(days=days)
    try:
        r=requests.get(f"{UPSTOX_BASE}/historical-candle/{ikey}/day/{td}/{fd}",
            headers=_hdr(token),timeout=15)
        if r.status_code!=200: return None
        candles=r.json().get("data",{}).get("candles",[])
        if not candles or len(candles)<25: return None
        df=pd.DataFrame(candles,columns=["ts","O","H","L","C","V","OI"])
        df["ts"]=pd.to_datetime(df["ts"])
        return df.sort_values("ts").reset_index(drop=True)
    except: return None

def verify_token(token):
    try:
        r=requests.get(f"{UPSTOX_BASE}/user/profile",headers=_hdr(token),timeout=8)
        if r.status_code==200:
            d=r.json().get("data",{})
            return {"ok":True,"name":d.get("name",d.get("user_name","User")),
                    "email":d.get("email","")}
        return {"ok":False,"error":f"HTTP {r.status_code}: {r.text[:80]}"}
    except Exception as e: return {"ok":False,"error":str(e)}

# ===========================================================================
#  TECHNICAL INDICATORS
# ===========================================================================
def perf_n(df,n):
    if len(df)<n+1: return None
    s,e=df["C"].iloc[-(n+1)],df["C"].iloc[-1]
    return (e-s)/s*100 if s else None

def sma_n(df,n):
    return float(df["C"].tail(n).mean()) if len(df)>=n else float(df["C"].mean())

def rsi14(df):
    if len(df)<16: return float("nan")
    cl=df["C"].tail(28).values; d=np.diff(cl)
    g=np.where(d>0,d,0); ls=np.where(d<0,-d,0)
    ag,al=g[:14].mean(),ls[:14].mean()
    for i in range(14,len(d)): ag=(ag*13+g[i])/14; al=(al*13+ls[i])/14
    return round(100-100/(1+ag/al),1) if al else 100.0

def avg_vol(df,n=20): return float(df["V"].tail(n).mean())
def high52(df): return float(df["H"].tail(252).max())
def low52(df):  return float(df["L"].tail(252).min())
def atr14(df):
    if len(df)<15: return 0.0
    h=df["H"].tail(15).values; l=df["L"].tail(15).values; c=df["C"].tail(15).values
    tr=[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,15)]
    return round(sum(tr)/len(tr),2)

# ===========================================================================
#  EPS INTELLIGENCE ENGINE  (reworked — 3 clear rules)
# ===========================================================================
def eps_qoq(eps):
    return [(eps[i]-eps[i-1])/abs(eps[i-1])*100 if eps[i-1]!=0 else 0
            for i in range(1,len(eps))]

def eps_yoy(eps):
    if len(eps)<4 or eps[0]==0: return None
    return (eps[-1]-eps[0])/abs(eps[0])*100

def rule_accel(eps):
    """Rule 1 — EPS Acceleration: each quarter grows faster than the last."""
    if len(eps)<3:
        return {"ok":False,"score":0,"grade":"F","verdict":"Insufficient data","qoq":[]}
    g=eps_qoq(eps)
    if not g:
        return {"ok":False,"score":0,"grade":"F","verdict":"No data","qoq":[]}
    pos   =sum(1 for x in g if x>0)
    steps =sum(1 for i in range(1,len(g)) if g[i]>g[i-1])
    latest_best=len(g)>0 and g[-1]==max(g)
    score =round(steps/max(len(g)-1,1)*100)
    ok    =(score>=50 and all(x>0 for x in g) and latest_best)
    if ok and score==100: grd,v="A+","Parabolic staircase"
    elif ok:              grd,v="A","Accelerating QoQ"
    elif pos==len(g):     grd,v="B","Consistent positive"
    elif pos>0:           grd,v="C","Mixed quarters"
    else:                 grd,v="D","Decelerating"
    return {"ok":ok,"score":score,"grade":grd,"verdict":v,"qoq":g}

def rule_surprise(latest_eps, est):
    """Rule 2 — Surprise Factor: actual EPS vs analyst estimate."""
    if not est or est==0:
        return {"ok":False,"beat":None,"grade":"N/A","verdict":"No estimate"}
    beat=(latest_eps-est)/abs(est)*100
    if   beat>=20: ok,grd,v=True, "A+","Massive beat >20%"
    elif beat>=10: ok,grd,v=True, "A", "Strong beat >10%"
    elif beat>= 3: ok,grd,v=True, "B", "Beat >3%"
    elif beat>=-3: ok,grd,v=False,"C", "In line"
    else:          ok,grd,v=False,"D", "Miss"
    return {"ok":ok,"beat":round(beat,1),"grade":grd,"verdict":v}

def rule_sales_quality(eps, sales):
    """Rule 3 — Sales Quality: organic growth needs both EPS and Revenue rising."""
    if len(eps)<2 or len(sales)<2 or eps[0]==0 or sales[0]==0:
        return {"ok":False,"grade":"N/A","verdict":"Insufficient data","eps_g":0,"sal_g":0}
    eg=(eps[-1]-eps[0])/abs(eps[0])*100
    sg=(sales[-1]-sales[0])/abs(sales[0])*100
    if   eg>=25 and sg>=20: ok,grd,v=True, "A+","Organic: EPS+Revenue accelerating"
    elif eg>=15 and sg>=10: ok,grd,v=True, "A", "Strong organic growth"
    elif eg>=10 and sg>= 5: ok,grd,v=True, "B", "Decent quality growth"
    elif eg>=10 and sg<  3: ok,grd,v=False,"C", "Cost-cutting — revenue flat"
    elif eg<0:              ok,grd,v=False,"D", "EPS declining"
    else:                   ok,grd,v=False,"B-","Moderate — watch revenue"
    return {"ok":ok,"grade":grd,"verdict":v,"eps_g":round(eg,1),"sal_g":round(sg,1)}

def analyse_fund(sym, price, fd):
    d=fd.get(sym)
    if not d: return {"av":False}
    eps,sales,est=d["eps"],d.get("sales",[]),d.get("est")
    if not eps or len(eps)<2: return {"av":False}
    ttm=sum(eps[-4:]) if len(eps)>=4 else sum(eps)
    pe=round(price/ttm,1) if ttm>0 else None
    yoy=eps_yoy(eps)
    ac=rule_accel(eps); sr=rule_surprise(eps[-1],est)
    sqr=rule_sales_quality(eps,sales)
    fs=0
    if yoy is not None:
        fs+=30 if yoy>=30 else 22 if yoy>=20 else 12 if yoy>=10 else 0
    if ac["ok"]:  fs+=25
    elif ac["grade"] in ("B","C"): fs+=8
    if sr["ok"]:  fs+=20
    if sqr["ok"]: fs+=25
    elif sqr["grade"]=="B": fs+=10
    return {"av":True,"eps":eps,"sales":sales,"ttm":round(ttm,2),"pe":pe,
            "yoy":round(yoy,1) if yoy is not None else None,
            "g":ac["qoq"],"ac":ac,"sr":sr,"sq":sqr,"est":est,"fs":min(fs,100)}

# ===========================================================================
#  SCAN ENGINE  (background thread — only writes to _SCAN)
# ===========================================================================
def run_scan_thread(token, cfg, uni, fd):
    """
    4-filter scan pipeline:
    F1: Within X% of 52-Week High
    F2: RS Resilience (sector drops, stock holds)
    F3: 21MA Buy Zone (price within 0-N% above 21-day SMA)
    F4: EPS Intelligence (3 rules: Accel / Surprise / Sales Quality)

    ALL stocks that PASS the selected filters are returned.
    Stocks are sorted: perfect (all 4) first, then by fundamental score.
    """
    try:
        total=len(uni)
        stats={"total":total,"processed":0,"passed":0,"perfect":0}
        _su(running=True,done=False,error="",progress=0.0,results=[],log=[],stats=dict(stats))
        _sl(f"Scan: {total} stocks")

        results=[]

        # Phase 1: Batch LTP
        _su(msg="[1/3] Batch LTP fetch...")
        try:
            ltp_map=fetch_ltp_batch([u["ikey"] for u in uni],token)
            _sl(f"LTP: {len(ltp_map)}/{total}")
        except Exception as e:
            _sl(f"LTP error: {e}"); ltp_map={}

        # Phase 2: Sector index candles
        _su(msg="[2/3] Caching sector indices...")
        sec_keys=list({u["sector"] for u in uni if u.get("sector")})
        sec_cache={}
        for sk in sec_keys:
            try: sec_cache[sk]=fetch_hist(sk,token)
            except: sec_cache[sk]=None
            time.sleep(0.08)
        _sl(f"Sectors: {sum(1 for v in sec_cache.values() if v is not None)}/{len(sec_keys)} OK")

        # Phase 3: Per-stock
        for i,stk in enumerate(uni):
            with _LOCK:
                if not _SCAN["running"]: _sl("Stopped"); break

            sym=stk["sym"]; ikey=stk["ikey"]; skey=stk.get("sector","")
            stats["processed"]=i+1
            _su(progress=(i+1)/total, stats=dict(stats),
                msg=f"[3/3] {i+1}/{total} {sym} | passed:{stats['passed']} perfect:{stats['perfect']}")

            try:
                df=fetch_hist(ikey,token)
                if df is None or len(df)<30: continue

                price=ltp_map.get(ikey) or float(df["C"].iloc[-1])
                if avg_vol(df)<cfg["min_vol"]: continue

                # F1: 52-Week High proximity
                h52_=high52(df); l52_=low52(df)
                dH=(price-h52_)/h52_*100
                if dH < -cfg["high_prox"]: continue

                # F2: RS Resilience
                sd=sec_cache.get(skey)
                rs_leader=False; sp=None; xp=None
                if sd is not None and len(sd)>=cfg["rs_days"]+2:
                    sp=perf_n(df,cfg["rs_days"]); xp=perf_n(sd,cfg["rs_days"])
                    if sp is not None and xp is not None:
                        rs_leader=(xp<=cfg["sec_drop"] and sp>=cfg.get("stk_min",0.0))
                if cfg.get("req_rs") and not rs_leader: continue

                # F3: 21MA Buy Zone
                sma21=sma_n(df,21); sma50=sma_n(df,50)
                dS=(price-sma21)/sma21*100
                in_bz=cfg["bz_lo"]<=dS<=cfg["bz_hi"]
                if cfg.get("req_bz") and not in_bz: continue

                # Indicators
                rsi_v=rsi14(df); atr_v=atr14(df); av=avg_vol(df)

                # F4: EPS Intelligence
                fund=analyse_fund(sym,price,fd)
                ttm=fund.get("ttm") or 0; pe=fund.get("pe")
                yoy=fund.get("yoy"); fs=fund.get("fs",0)
                ac_ok=fund.get("ac",{}).get("ok",False) if fund["av"] else False
                sr_ok=fund.get("sr",{}).get("ok",False) if fund["av"] else False
                sq_ok=fund.get("sq",{}).get("ok",False) if fund["av"] else False
                eps_ok=ttm>=cfg["min_eps"]; yoy_ok=(yoy is not None and yoy>=cfg["min_yoy"])

                if cfg.get("req_eps") and not eps_ok: continue
                if cfg.get("req_yoy") and not yoy_ok: continue
                if cfg.get("req_accel") and not ac_ok: continue
                if cfg.get("req_surp")  and not sr_ok: continue
                if cfg.get("req_qual")  and not sq_ok: continue

                # Perfect = all 4 filters satisfied simultaneously
                is_perfect=(rs_leader and in_bz and eps_ok and yoy_ok and ac_ok)

                stats["passed"]+=1; stats["perfect"]+=int(is_perfect)
                results.append({
                    "name":stk["name"],"sym":sym,"ikey":ikey,
                    "sector":skey.replace("NSE_INDEX|Nifty ","").replace("BSE_INDEX|S&P BSE ",""),
                    "exch":stk["exch"],"price":round(price,2),
                    "high52":round(h52_,2),"low52":round(l52_,2),"dH":round(dH,2),
                    "sp":round(sp,2) if sp is not None else None,
                    "xp":round(xp,2) if xp is not None else None,
                    "rs_leader":rs_leader,"sma21":round(sma21,2),"sma50":round(sma50,2),
                    "dS":round(dS,2),"in_bz":in_bz,
                    "rsi":None if math.isnan(rsi_v) else rsi_v,
                    "atr":atr_v,"avg_vol":int(av),
                    "eps":fund.get("eps",[]),"sales":fund.get("sales",[]),
                    "ttm":fund.get("ttm"),"pe":pe,"yoy":yoy,"g":fund.get("g",[]),
                    "ac":fund.get("ac",{}),"sr":fund.get("sr",{}),"sq":fund.get("sq",{}),
                    "eps_ok":eps_ok,"yoy_ok":yoy_ok,
                    "ac_ok":ac_ok,"sr_ok":sr_ok,"sq_ok":sq_ok,
                    "fs":fs,"perfect":is_perfect,
                    "live_ltp":price,"live_chg":0.0,"live_pct":0.0,
                })
            except Exception as e:
                _sl(f"  {sym}: {e}"); continue

            time.sleep(0.04)

        sorted_r=sorted(results,key=lambda x:(not x["perfect"],-x.get("fs",0)))
        msg=f"Done: {stats['passed']} passed / {total} | {stats['perfect']} perfect setups"
        _su(running=False,done=True,progress=1.0,results=sorted_r,stats=dict(stats),msg=msg)
        _sl(msg)

    except Exception as e:
        err=f"Crash: {e}\n{traceback.format_exc()}"
        _su(running=False,done=True,error=err,msg=f"CRASH: {e}"); _sl(err)

# ===========================================================================
#  FUNDAMENTALS
# ===========================================================================
@st.cache_data(ttl=300,show_spinner=False)
def get_fundamentals():
    return json.loads(FUND_PATH.read_text()) if FUND_PATH.exists() else {}

@st.cache_data(ttl=120,show_spinner=False)
def load_universe():
    return db_load_equity()

# ===========================================================================
#  CHART HELPERS
# ===========================================================================
_PBG="#0f1320";_BG="#0a0d14";_GR="rgba(30,39,64,.6)"
_SKY="rgba(56,189,248,.8)";_SAGE="rgba(52,211,153,.8)"
_AMB="rgba(251,191,36,.8)";_COR="rgba(248,113,113,.8)";_MU="#2e3a52"
QL=["Q1","Q2","Q3","Q4 Latest"]

def _lay(title="",h=320):
    return dict(title=dict(text=title,font=dict(color="#a8b4cc",size=12,family="JetBrains Mono")),
                paper_bgcolor=_PBG,plot_bgcolor=_BG,
                font=dict(color="#5c6a88",family="JetBrains Mono"),
                height=h,margin=dict(l=40,r=12,t=44,b=36),
                xaxis=dict(gridcolor=_GR,linecolor=_GR,tickfont=dict(size=9)),
                yaxis=dict(gridcolor=_GR,linecolor=_GR,tickfont=dict(size=9)))

def chart_eps(r):
    eps=r.get("eps",[]); sales=r.get("sales",[]); g=r.get("g",[])
    if not eps: return go.Figure()
    ql=QL[:len(eps)]
    fig=make_subplots(rows=1,cols=2,subplot_titles=["EPS (Rs/share)","Revenue (Rs Cr)"],
                      horizontal_spacing=0.12)
    clr=[_SAGE if i==len(eps)-1 else _SKY for i in range(len(eps))]
    fig.add_trace(go.Bar(x=ql,y=eps,marker_color=clr,marker_line_color="transparent",
        text=[f"Rs{e:.1f}" for e in eps],textposition="outside",
        textfont=dict(size=9,color="#a8b4cc"),name="EPS"),row=1,col=1)
    if sales:
        sc=[f"rgba(251,191,36,{0.4+0.15*i})" for i in range(len(sales))]
        fig.add_trace(go.Bar(x=ql[:len(sales)],y=sales,marker_color=sc,
            marker_line_color="transparent",
            text=[f"{v/1000:.0f}K" if v>10000 else str(int(v)) for v in sales],
            textposition="outside",textfont=dict(size=9,color="#a8b4cc"),name="Sales"),row=1,col=2)
    lay=_lay(f"{r.get('name',r.get('sym',''))} - EPS & Revenue",h=260)
    lay["showlegend"]=False
    for ax in ["xaxis","xaxis2","yaxis","yaxis2"]:
        lay[ax]=dict(gridcolor=_GR,linecolor=_GR,tickfont=dict(size=9))
    fig.update_layout(**lay); return fig

def chart_rs(results,rs_days):
    if not results: return go.Figure()
    fig=go.Figure()
    fig.add_vline(x=0,line=dict(color=_GR,dash="dot",width=1))
    fig.add_hline(y=-3,line=dict(color=_COR,dash="dot",width=1))
    clrs=[_AMB if r.get("perfect") else _SAGE if r.get("rs_leader") else _MU for r in results]
    sizes=[10 if r.get("perfect") else 8 if r.get("rs_leader") else 5 for r in results]
    fig.add_trace(go.Scatter(
        x=[r.get("sp") or 0 for r in results],
        y=[r.get("xp") or 0 for r in results],
        mode="markers+text",
        marker=dict(size=sizes,color=clrs,line=dict(color="rgba(0,0,0,.4)",width=.5)),
        text=[r.get("sym","") for r in results],
        textposition="top center",textfont=dict(size=8,color="#5c6a88"),
        hovertemplate="<b>%{text}</b><br>Stock: %{x:.1f}%<br>Sector: %{y:.1f}%<extra></extra>"))
    lay=_lay(f"RS Map - Stock vs Sector ({rs_days}d)",h=380)
    lay["xaxis"]["title"]=dict(text=f"Stock {rs_days}d %",font=dict(size=10))
    lay["yaxis"]["title"]=dict(text=f"Sector {rs_days}d %",font=dict(size=10))
    fig.update_layout(**lay); return fig

# ===========================================================================
#  HTML CARD COMPONENTS
# ===========================================================================
def sig_badges(r):
    exch=r.get("exch","NSE")
    ec="var(--sky)" if exch=="NSE" else "var(--amber)"
    out=f'<span class="sig" style="color:{ec};border:1px solid {ec}33;font-size:.52rem">{exch}</span>'
    if r.get("rs_leader"): out+='<span class="sig sig-rs">RS LEADER</span>'
    if r.get("in_bz"):     out+='<span class="sig sig-bz">BUY ZONE</span>'
    if r.get("ac_ok"):     out+='<span class="sig sig-ac">EPS ACCEL</span>'
    if r.get("sr_ok"):     out+='<span class="sig sig-sr">BEAT EST</span>'
    if r.get("sq_ok"):     out+='<span class="sig sig-ok">SALES+EPS</span>'
    if r.get("perfect"):   out+='<span class="sig sig-ok" style="font-weight:700">PERFECT</span>'
    return out

def staircase_html(r):
    eps=r.get("eps",[]); g=r.get("g",[])
    if not eps: return ""
    maxe=max(eps) if max(eps)>0 else 1
    bars=""
    for i,e in enumerate(eps):
        pct=max(int(e/maxe*100),6)
        col="#34d399" if i==len(eps)-1 else "#38bdf8"
        arr=""
        if i>0 and i-1<len(g):
            gv=g[i-1]
            arr=f'<span style="color:{"#34d399" if gv>0 else "#f87171"}">{gv:+.0f}%</span>'
        lbl=QL[i] if i<len(QL) else f"Q{i+1}"
        bars+=(f'<div class="scol">'
               f'<div class="sarr">{arr}</div>'
               f'<div class="sbar" style="height:{pct}%;background:{col}">Rs{e:.1f}</div>'
               f'<div class="slb">{lbl}</div></div>')
    return f'<div class="stair">{bars}</div>'

def render_card(r, live, rs_days):
    li=live.get(r.get("ikey",""),{})
    ltp=li.get("ltp") or r.get("price",0)
    chg=li.get("chg",0); pct=li.get("pct",0)
    chg_col="var(--sage)" if chg>=0 else "var(--coral)"
    sign="+" if chg>=0 else ""
    ac=r.get("ac",{}); sr=r.get("sr",{}); sqr=r.get("sq",{})
    yoy=r.get("yoy"); pe=r.get("pe"); fs=r.get("fs",0)
    fc="var(--sage)" if fs>=60 else "var(--amber)" if fs>=40 else "var(--coral)"
    qoq_str=" -> ".join([
        f'<span style="color:{"#34d399" if x>0 else "#f87171"}">{x:+.0f}%</span>'
        for x in r.get("g",[])])
    cls="scard hit" if r.get("perfect") else "scard"
    st.markdown(f"""
<div class="{cls}">
  <div class="ch">
    <div class="sym">{r.get('sym','')}</div>
    <div class="nm">{r.get('name','')}</div>
    <div style="background:var(--card2);border:1px solid var(--border);border-radius:4px;
                padding:2px 7px;font-family:var(--mono);font-size:.55rem;color:var(--t3)">
      {r.get('sector','')}</div>
    <div style="margin-left:auto;text-align:right">
      <div class="live-px">Rs{ltp:,.2f}</div>
      <div class="live-chg" style="color:{chg_col}">{sign}{chg:.2f} ({sign}{pct:.2f}%)</div>
    </div>
  </div>
  <div style="margin:6px 0">{sig_badges(r)}</div>
  <div class="mgrid">
    <div class="met"><div class="ml">52W High</div><div class="mv">Rs{r.get('high52',0):,.0f}</div></div>
    <div class="met"><div class="ml">Dist 52W%</div>
      <div class="mv" style="color:{'var(--sage)' if (r.get('dH',0) or 0)>=-2 else 'var(--t2)'}">{r.get('dH',0):.2f}%</div></div>
    <div class="met"><div class="ml">Stk {rs_days}d%</div>
      <div class="mv" style="color:{'var(--sage)' if (r.get('sp') or 0)>=0 else 'var(--coral)'}">{f"{r.get('sp',0):+.1f}%" if r.get('sp') is not None else "n/a"}</div></div>
    <div class="met"><div class="ml">Sec {rs_days}d%</div>
      <div class="mv" style="color:{'var(--sage)' if (r.get('xp') or 0)>=0 else 'var(--coral)'}">{f"{r.get('xp',0):+.1f}%" if r.get('xp') is not None else "n/a"}</div></div>
    <div class="met"><div class="ml">21MA Dist</div><div class="mv" style="color:var(--tang)">{r.get('dS',0):.2f}%</div></div>
    <div class="met"><div class="ml">RSI 14</div>
      <div class="mv" style="color:{'var(--coral)' if (r.get('rsi') or 50)>70 else 'var(--sage)' if (r.get('rsi') or 50)<30 else 'var(--t1)'}">{r.get('rsi') or 'n/a'}</div></div>
    <div class="met"><div class="ml">EPS TTM</div><div class="mv" style="color:var(--amber)">Rs{r.get('ttm') or 'n/a'}</div></div>
    <div class="met"><div class="ml">P/E</div><div class="mv">{f"{pe}x" if pe else 'n/a'}</div></div>
    <div class="met"><div class="ml">YoY EPS%</div>
      <div class="mv" style="color:{'var(--sage)' if (yoy or 0)>=20 else 'var(--amber)' if (yoy or 0)>=10 else 'var(--coral)'}">{f"{yoy:+.1f}%" if yoy is not None else 'n/a'}</div></div>
    <div class="met"><div class="ml">Fund Score</div><div class="mv" style="color:{fc}">{fs}/100</div></div>
  </div>
  {staircase_html(r)}
  <div class="igrid">
    <div class="ip"><div class="il" style="color:var(--amber)">Rule 1 — EPS Acceleration</div>
      <div class="iv">{ac.get('grade','n/a')} | {ac.get('verdict','n/a')}</div>
      <div class="is">Score:{ac.get('score',0)}/100  QoQ: {qoq_str or 'n/a'}</div></div>
    <div class="ip"><div class="il" style="color:var(--lav)">Rule 2 — Surprise Factor</div>
      <div class="iv">{sr.get('grade','n/a')} | {sr.get('verdict','n/a')}</div>
      <div class="is">{f"Beat: +{sr.get('beat',0)}% vs estimate" if sr.get('beat') is not None else 'No analyst estimate'}</div></div>
    <div class="ip"><div class="il" style="color:var(--sage)">Rule 3 — Sales Quality</div>
      <div class="iv">{sqr.get('grade','n/a')} | {sqr.get('verdict','n/a')}</div>
      <div class="is">EPS +{sqr.get('eps_g',0):.1f}%  Revenue +{sqr.get('sal_g',0):.1f}%</div></div>
    <div class="ip"><div class="il" style="color:var(--sky)">Live Quote</div>
      <div class="iv" style="color:var(--sage)">Rs{ltp:,.2f}</div>
      <div class="is">Chg: {sign}{chg:.2f} ({sign}{pct:.2f}%)  ATR:{r.get('atr',0):.1f}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ===========================================================================
#  MAIN UI
# ===========================================================================
st.markdown("""
<div class="hdr">
  <h1>NSE + BSE Multibagger Screener</h1>
  <div class="sub">Upstox Instrument CSV | EPS Accel + RS Resilience + 21MA Buy Zone | Live Prices for Results Only</div>
</div>""", unsafe_allow_html=True)

# ===========================================================================
#  SIDEBAR
# ===========================================================================
with st.sidebar:
    st.markdown("**Screener v6.0**")
    st.caption("Upstox V2 API | SQLite | Live Prices")
    st.divider()

    # Universe
    st.markdown('<div class="sec-lbl">Universe</div>', unsafe_allow_html=True)
    _dc=db_count()
    sc1,sc2,sc3=st.columns(3)
    sc1.metric("NSE",  f"{_dc['nse']:,}")
    sc2.metric("BSE",  f"{_dc['bse']:,}")
    sc3.metric("Total",f"{_dc['total']:,}")
    if _dc["total"]>0:
        st.progress(min(_dc["total"]/8000,1.0))
        st.caption(f"{_dc['total']:,} / ~8,000 instruments ({_dc['total']/80:.0f}%)")

    if st.session_state.get("dl_running"):
        st.info(st.session_state.get("dl_msg","Downloading...")[:80])

    if st.button("Download Full Instrument List",use_container_width=True,
                 disabled=st.session_state.get("dl_running",False)):
        st.session_state.dl_running=True; st.session_state.dl_msg="Starting..."
        st.session_state.dl_error=""; st.rerun()

    if st.button("Clear DB",use_container_width=True,key="sb_clr"):
        if DB_PATH.exists(): DB_PATH.unlink()
        load_universe.clear(); st.rerun()

    if st.session_state.get("dl_error"):
        st.error(st.session_state.dl_error[:160])

    st.divider()

    # Token
    st.markdown('<div class="sec-lbl">Token</div>', unsafe_allow_html=True)
    ts=st.session_state.token_status
    if ts=="valid":
        st.markdown(
            f'<div style="background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.3);'
            f'border-radius:7px;padding:6px 10px;font-size:.68rem;color:var(--sage)">'
            f'Connected: {st.session_state.token_user}</div>',unsafe_allow_html=True)
    elif ts=="invalid":
        st.markdown(
            '<div style="background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.3);'
            'border-radius:7px;padding:6px 10px;font-size:.68rem;color:var(--coral)">Invalid token</div>',
            unsafe_allow_html=True)

    token=st.text_input("Access Token",type="password",placeholder="Paste bearer token...",
                         key="token_input")
    if st.button("Verify Token",use_container_width=True):
        if token.strip():
            with st.spinner("Verifying..."): vr=verify_token(token.strip())
            if vr["ok"]:
                st.session_state.token_status="valid"; st.session_state.token_user=vr["name"]
                st.success(f"Connected as {vr['name']}")
            else:
                st.session_state.token_status="invalid"
                st.error(vr.get("error","Invalid"))
            st.rerun()
        else: st.warning("Paste token first")

    st.divider()

    # EPS Filters
    st.markdown('<div class="sec-lbl">EPS Filters</div>', unsafe_allow_html=True)
    min_eps   = st.slider("Min TTM EPS (Rs)",      0,120, 10,2)
    min_yoy   = st.slider("Min YoY EPS Growth %",  0,100, 20,5)
    req_eps   = st.checkbox("Apply EPS filter",   value=True)
    req_yoy   = st.checkbox("Apply YoY filter",   value=True)
    req_accel = st.checkbox("Require Accel",       value=False)
    req_surp  = st.checkbox("Require Beat Est",    value=False)
    req_qual  = st.checkbox("Require Sales+EPS",   value=False)

    st.divider()

    # Technical Filters
    st.markdown('<div class="sec-lbl">Technical Filters</div>', unsafe_allow_html=True)
    rs_days   = st.slider("RS Lookback Days",        5, 30, 20)
    high_prox = st.slider("Max Dist 52W High %",   1.0,10.0,5.0,0.5)
    sec_drop  = st.slider("Sector Drop %",        -15.0,-1.0,-3.0,0.5)
    bz_hi     = st.slider("21MA BuyZone Upper %",  0.5, 8.0, 3.0,0.5)
    req_rs    = st.checkbox("Require RS Leader",   value=False)
    req_bz    = st.checkbox("Require BuyZone",     value=False)
    min_vol   = st.number_input("Min Avg Volume",  min_value=0,value=50000,step=25000)

    st.divider()

    cfg=dict(rs_days=rs_days,high_prox=high_prox,sec_drop=sec_drop,stk_min=0.0,
             bz_lo=0.0,bz_hi=bz_hi,min_eps=float(min_eps),min_yoy=float(min_yoy),
             req_eps=req_eps,req_yoy=req_yoy,req_accel=req_accel,
             req_surp=req_surp,req_qual=req_qual,req_rs=req_rs,req_bz=req_bz,
             min_vol=int(min_vol))

    rc1,rc2=st.columns([3,1])
    with rc1: run_btn=st.button("RUN FULL SCAN",use_container_width=True,
                                 disabled=st.session_state.scan_running)
    with rc2:
        if st.button("Stop",disabled=not st.session_state.scan_running):
            _su(running=False); st.session_state.scan_running=False

    if st.session_state.last_scan_time:
        st.caption(f"Last: {st.session_state.last_scan_time}")

    st.divider()
    st.markdown('<div class="sec-lbl">Live Prices</div>', unsafe_allow_html=True)
    if st.button("Refresh Live Prices",use_container_width=True,
                 disabled=not bool(st.session_state.results)):
        if token and st.session_state.results:
            with st.spinner("Fetching live prices for results..."):
                lp=fetch_full_quotes([r["ikey"] for r in st.session_state.results],token)
            st.session_state.live_prices=lp
            st.session_state.live_updated=datetime.datetime.now().strftime("%H:%M:%S")
            st.rerun()
    if st.session_state.live_updated:
        st.caption(f"Updated: {st.session_state.live_updated}")

    st.divider()
    if st.button("Refresh EPS Data",use_container_width=True):
        with st.spinner("Fetching NSE quarterly results..."):
            try:
                hdrs={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com","Accept":"application/json"}
                s=requests.Session()
                s.get("https://www.nseindia.com",headers=hdrs,timeout=10)
                r=s.get("https://www.nseindia.com/api/corporates-financial-results",
                    headers=hdrs,params={"index":"equities","period":"Quarterly"},timeout=20)
                if r.status_code==200:
                    fd=get_fundamentals()
                    for rec in r.json():
                        sym=rec.get("symbol","").upper(); ev=rec.get("eps"); rv=rec.get("reIncome")
                        if sym and ev:
                            if sym not in fd: fd[sym]={"eps":[],"sales":[],"est":None}
                            fd[sym]["eps"]=(fd[sym]["eps"]+[float(ev)])[-4:]
                            if rv: fd[sym]["sales"]=(fd[sym]["sales"]+[float(rv)])[-4:]
                    FUND_PATH.write_text(json.dumps(fd,separators=(",",":")))
                    get_fundamentals.clear()
                    st.success(f"Updated {len(fd)} symbols")
                else: st.warning(f"NSE HTTP {r.status_code}")
            except Exception as e: st.error(str(e))

# ===========================================================================
#  DOWNLOAD RUNNER
# ===========================================================================
if st.session_state.get("dl_running"):
    tok_dl=st.session_state.get("token_input","")
    if not tok_dl:
        st.session_state.dl_running=False
        st.error("Paste and verify token before downloading.")
    else:
        st.markdown("### Downloading Full Instrument List from Upstox...")
        _bar=st.progress(0.0); _msg=st.empty(); _stat=st.empty()
        def _dlcb(pct,msg):
            _bar.progress(min(float(pct),1.0)); _msg.markdown(f"**{msg}**")
            st.session_state.dl_msg=msg
            c=db_count()
            _stat.markdown(f"**DB:** {c['total']:,} instruments  ({c['nse']:,} NSE + {c['bse']:,} BSE)")
        res=download_instruments_full(tok_dl,_dlcb)
        load_universe.clear()
        st.session_state.dl_running=False
        if res["ok"]:
            st.session_state.dl_error=""
            st.success(f"{res['total']:,} instruments downloaded  ({res['nse']:,} NSE + {res['bse']:,} BSE)  |  {res.get('new',0):,} new")
        else:
            st.session_state.dl_error=res["error"]
            st.error(f"Download failed: {res['error'][:300]}")
        st.rerun()

# ===========================================================================
#  LAUNCH SCAN
# ===========================================================================
if run_btn:
    if not token:
        st.error("Paste and verify your Upstox token first."); st.stop()
    uni_now=load_universe(); load_universe.clear()
    if not uni_now:
        st.error("DB is empty. Download instrument list first."); st.stop()
    fd=get_fundamentals()
    _su(running=True,done=False,error="",progress=0.0,results=[],log=[],
        stats={"total":len(uni_now),"processed":0,"passed":0,"perfect":0})
    st.session_state.results=[]; st.session_state.scan_running=True
    st.session_state.scan_done=False; st.session_state.live_prices={}
    _th.Thread(target=run_scan_thread,args=(token,cfg,uni_now,fd),daemon=True).start()
    st.rerun()

# ===========================================================================
#  SCAN PROGRESS
# ===========================================================================
if st.session_state.scan_running:
    with _LOCK: snap=dict(_SCAN)
    if snap["done"]:
        st.session_state.scan_running=False; st.session_state.scan_done=True
        st.session_state.results=snap["results"]
        st.session_state.last_scan_time=datetime.datetime.now().strftime("%d %b %Y  %H:%M IST")
        if snap["error"]: st.session_state.scan_error=snap["error"]
        # Auto-fetch live prices for results immediately
        if snap["results"] and token:
            with st.spinner(f"Fetching live prices for {len(snap['results'])} results..."):
                lp=fetch_full_quotes([r["ikey"] for r in snap["results"]],token)
            st.session_state.live_prices=lp
            st.session_state.live_updated=datetime.datetime.now().strftime("%H:%M:%S")
        st.rerun()
    else:
        pct=snap["progress"]; stats=snap["stats"]; msg=snap["msg"]
        st.markdown('<div class="prog-box"><div class="plbl scanning">SCANNING...</div></div>',
                    unsafe_allow_html=True)
        st.progress(min(float(pct),1.0)); st.caption(msg)
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Total",stats.get("total",0)); c2.metric("Processed",stats.get("processed",0))
        c3.metric("Passed",stats.get("passed",0)); c4.metric("Perfect",stats.get("perfect",0))
        with _LOCK: log_lines=list(_SCAN.get("log",[]))
        if log_lines:
            with st.expander(f"Scan Log ({len(log_lines)})"):
                st.code("\n".join(log_lines[-40:]))
        time.sleep(2); st.rerun()

# ===========================================================================
#  TABS
# ===========================================================================
results=st.session_state.results
live=st.session_state.live_prices

if st.session_state.get("scan_error"):
    with st.expander("Scan Error",expanded=True): st.code(st.session_state.scan_error)
    if st.button("Clear"): st.session_state.scan_error=""; st.rerun()

tab_res, tab_live, tab_charts, tab_inst, tab_exp = st.tabs([
    "Scan Results", "Live Watchlist", "Charts", "Instrument DB", "Export"
])

# ---- TAB 1: Scan Results ----
with tab_res:
    if not results and not st.session_state.scan_running:
        st.markdown('<div class="sec-lbl">Screener Logic</div>', unsafe_allow_html=True)
        c1,c2,c3,c4=st.columns(4)
        for col_ctx,title,color,body in [
            (c1,"52-Week High","var(--amber)",
             "Stock must be within X% of its 52W high — near highs shows institutional accumulation, not dead money."),
            (c2,"RS Resilience","var(--sky)",
             "When sector drops 3-5%, stock stays flat or rises. Relative strength signals smart money buying."),
            (c3,"21MA Buy Zone","var(--tang)",
             "Price 0-3% above 21-day SMA = low-risk entry. Tight to moving average = uptrend intact."),
            (c4,"EPS Rules (3)","var(--sage)",
             "Acceleration (staircase growth), Surprise (beat estimate), Sales Quality (organic not cost-cuts).")
        ]:
            with col_ctx:
                st.markdown(f"""<div style="background:var(--card);border:1px solid var(--border);
border-radius:10px;padding:14px">
<div style="font-family:var(--mono);font-size:.57rem;color:{color};letter-spacing:2px;
margin-bottom:6px;text-transform:uppercase">{title}</div>
<div style="font-size:.72rem;color:var(--t2);line-height:1.6">{body}</div>
</div>""",unsafe_allow_html=True)
        st.info("Step 1: Download instruments  |  Step 2: Verify token  |  Step 3: RUN FULL SCAN")
    else:
        # KPIs
        perf_c=[r for r in results if r.get("perfect")]
        rs_c=[r for r in results if r.get("rs_leader")]
        bz_c=[r for r in results if r.get("in_bz")]
        ac_c=[r for r in results if r.get("ac_ok")]
        st.markdown(
            f'<div class="kpis">'
            f'<div class="kpi"><div class="v csky">{len(results)}</div><div class="l">Passed</div></div>'
            f'<div class="kpi"><div class="v csage">{len(rs_c)}</div><div class="l">RS Leaders</div></div>'
            f'<div class="kpi"><div class="v ctang">{len(bz_c)}</div><div class="l">Buy Zone</div></div>'
            f'<div class="kpi"><div class="v camb">{len(ac_c)}</div><div class="l">EPS Accel</div></div>'
            f'<div class="kpi"><div class="v csage">{len(perf_c)}</div><div class="l">Perfect</div></div>'
            f'</div>',unsafe_allow_html=True)

        exch_sel=st.radio("Exchange:",["All","NSE","BSE"],horizontal=True,key="res_exch")
        frows=results if exch_sel=="All" else [r for r in results if r.get("exch")==exch_sel]

        if perf_c:
            st.markdown('<div class="sec-lbl">PERFECT SETUPS — All 4 Signals Green</div>',
                        unsafe_allow_html=True)
            for r in [x for x in perf_c if exch_sel=="All" or x.get("exch")==exch_sel]:
                with st.expander(
                    f"{r.get('sym','')}  |  {r.get('name','')}  |  "
                    f"Rs{live.get(r.get('ikey',''),{}).get('ltp') or r.get('price',0):,.2f}  |  "
                    f"Score:{r.get('fs',0)}/100",expanded=True):
                    render_card(r,live,rs_days)
                    fig=chart_eps(r)
                    if fig.data: st.plotly_chart(fig,use_container_width=True,
                                                 key=f"c_{r['sym']}_{r.get('exch','')}")

        non_p=[r for r in frows if not r.get("perfect")]
        if non_p:
            st.markdown(f'<div class="sec-lbl">ALL PASSING STOCKS ({len(non_p)})</div>',
                        unsafe_allow_html=True)
            for r in non_p:
                with st.expander(
                    f"{r.get('sym','')} [{r.get('exch','')}]  |  {r.get('name','')}  |  "
                    f"Rs{live.get(r.get('ikey',''),{}).get('ltp') or r.get('price',0):,.2f}  |  "
                    f"Score:{r.get('fs',0)}/100",expanded=False):
                    render_card(r,live,rs_days)

# ---- TAB 2: Live Watchlist ----
with tab_live:
    st.markdown('<div class="sec-lbl">Live Watchlist — Scan Results Only</div>',
                unsafe_allow_html=True)
    if not results:
        st.info("Run a scan first. Live prices are fetched only for stocks that pass the filters.")
    else:
        lc1,lc2=st.columns([4,1])
        with lc2:
            if st.button("Refresh Now",use_container_width=True):
                if token:
                    with st.spinner("Fetching..."):
                        lp=fetch_full_quotes([r["ikey"] for r in results],token)
                    st.session_state.live_prices=lp
                    st.session_state.live_updated=datetime.datetime.now().strftime("%H:%M:%S")
                    live=lp; st.rerun()
        with lc1:
            st.caption(f"{len(results)} stocks in watchlist" +
                       (f"  |  Last updated: {st.session_state.live_updated}"
                        if st.session_state.live_updated else "  |  Not yet fetched"))

        rows=[]
        for r in results:
            li=live.get(r.get("ikey",""),{})
            ltp=li.get("ltp") or r.get("price",0)
            rows.append({
                "Symbol":  r.get("sym",""),    "Name":    r.get("name","")[:20],
                "Exch":    r.get("exch",""),   "Sector":  r.get("sector","")[:16],
                "LTP":     round(ltp,2),        "Chg":     li.get("chg",0),
                "Chg%":    li.get("pct",0),
                "52W%":    r.get("dH",0),       "21MA%":   r.get("dS",0),
                "RS":      "Y" if r.get("rs_leader") else "",
                "BZ":      "Y" if r.get("in_bz")     else "",
                "YoY%":    r.get("yoy"),         "F.Score": r.get("fs",0),
                "Perfect": "Y" if r.get("perfect") else "",
            })
        df_live=pd.DataFrame(rows)
        st.dataframe(df_live,use_container_width=True,hide_index=True,
            column_config={
                "LTP":    st.column_config.NumberColumn("LTP",    format="Rs%.2f"),
                "Chg":    st.column_config.NumberColumn("Chg",    format="%.2f"),
                "Chg%":   st.column_config.NumberColumn("Chg%",   format="%.2f%%"),
                "52W%":   st.column_config.NumberColumn("52W%",   format="%.1f%%"),
                "21MA%":  st.column_config.NumberColumn("21MA%",  format="%.1f%%"),
                "YoY%":   st.column_config.NumberColumn("YoY%",   format="%.1f%%"),
                "F.Score":st.column_config.ProgressColumn("Score",min_value=0,max_value=100),
            })

# ---- TAB 3: Charts ----
with tab_charts:
    if not results:
        st.info("Run a scan to see charts.")
    else:
        cc1,cc2=st.columns(2)
        with cc1: st.plotly_chart(chart_rs(results,rs_days),use_container_width=True,key="ch_rs")
        with cc2:
            top20=sorted(results,key=lambda x:x.get("fs",0))[-20:]
            ff=go.Figure(go.Bar(
                y=[f"{r['sym']}[{r.get('exch','?')[0]}]" for r in top20],
                x=[r.get("fs",0) for r in top20],orientation="h",
                marker_color=[_AMB if r.get("perfect") else _SAGE if r.get("fs",0)>=60 else _SKY for r in top20],
                marker_line_color="transparent"))
            lf=_lay("Fund Score Top 20",h=380); lf["xaxis"]["range"]=[0,112]
            ff.update_layout(**lf)
            st.plotly_chart(ff,use_container_width=True,key="ch_fund")

# ---- TAB 4: Instrument DB ----
with tab_inst:
    st.markdown('<div class="sec-lbl">Full Instrument Database</div>',unsafe_allow_html=True)
    _dc2=db_count()
    ia,ib,ic,id_=st.columns(4)
    ia.metric("Total",  f"{_dc2['total']:,}")
    ib.metric("NSE",    f"{_dc2['nse']:,}")
    ic.metric("BSE",    f"{_dc2['bse']:,}")
    id_.metric("Target","~8,000")
    if _dc2["total"]>0:
        st.progress(min(_dc2["total"]/8000,1.0))
        st.caption(f"{_dc2['total']:,} instruments stored  |  {_dc2['total']/80:.1f}% of ~8K target")

    st.divider()
    idc1,idc2,idc3=st.columns([2,2,1])
    with idc1:
        if st.button("Download Full List",use_container_width=True,key="inst_dl",
                     disabled=st.session_state.get("dl_running",False)):
            if not st.session_state.get("token_input",""):
                st.error("Verify token first")
            else:
                st.session_state.dl_running=True; st.session_state.dl_msg="Starting..."
                st.session_state.dl_error=""; st.rerun()
    with idc2:
        if st.button("Sync / Update DB",use_container_width=True,key="inst_sync",
                     disabled=st.session_state.get("dl_running",False)):
            if st.session_state.get("token_input",""):
                st.session_state.dl_running=True; st.rerun()
    with idc3:
        if st.button("Clear DB",use_container_width=True,key="inst_clr"):
            if DB_PATH.exists(): DB_PATH.unlink()
            load_universe.clear(); st.rerun()

    if st.session_state.get("dl_error"):
        with st.expander("Download Errors",expanded=True):
            st.code(st.session_state.dl_error)

    st.divider()

    if _dc2["total"]==0:
        st.warning("Database empty. Click 'Download Full List' above (requires valid token).")
    else:
        fi1,fi2,fi3,fi4=st.columns([3,2,2,1])
        with fi1: q_i=st.text_input("Search",key="inst_q",placeholder="INFY or Infosys")
        with fi2: ex_i=st.selectbox("Exchange",["All","NSE","BSE"],key="inst_ex")
        with fi3: tp_i=st.selectbox("Type",["All","EQUITY","EQ","FUT","OPT","ETF","INDEX"],key="inst_tp")
        with fi4: pg_i=st.number_input("Page",min_value=1,value=1,key="inst_pg")

        all_i=db_load_all(exch=None if ex_i=="All" else ex_i,limit=None,page=1,per=100000)
        if q_i:
            q2=q_i.upper()
            all_i=[r for r in all_i if q2 in r.get("sym","").upper() or q2 in r.get("name","").upper()]
        if tp_i!="All":
            all_i=[r for r in all_i if (r.get("inst_type","") or "").upper()==tp_i]

        total_f=len(all_i); PER=500
        page_items=all_i[(pg_i-1)*PER:pg_i*PER]
        st.caption(f"Showing {len(page_items):,} of {total_f:,}  |  Page {pg_i}/{max(1,(total_f+PER-1)//PER)}")

        df_i=pd.DataFrame([{
            "Symbol":  r.get("sym",""),      "Name":    r.get("name",""),
            "Exchange":r.get("exch",""),     "Segment": r.get("segment",""),
            "Type":    r.get("inst_type",""),"Lot":     r.get("lot_size",""),
            "Tick":    r.get("tick_size",""),"ISIN":    r.get("isin",""),
            "Sector":  r.get("sector","").replace("NSE_INDEX|Nifty ","").replace("BSE_INDEX|S&P BSE ",""),
            "Key":     r.get("ikey",""),
        } for r in page_items])

        st.dataframe(df_i,use_container_width=True,hide_index=True,
            column_config={
                "Symbol":  st.column_config.TextColumn(width="small"),
                "Name":    st.column_config.TextColumn(width="medium"),
                "Exchange":st.column_config.TextColumn(width="small"),
                "Type":    st.column_config.TextColumn(width="small"),
                "Sector":  st.column_config.TextColumn(width="medium"),
                "Key":     st.column_config.TextColumn(width="large"),
            })

        if st.button("Save Snapshot to JSON",key="inst_snap"):
            snap={"saved":datetime.datetime.now().isoformat(),"total":total_f,"instruments":all_i}
            Path("universe_snapshot.json").write_text(json.dumps(snap,separators=(",",":"),ensure_ascii=False))
            st.success(f"Saved {total_f:,} instruments")

# ---- TAB 5: Export ----
with tab_exp:
    st.markdown('<div class="sec-lbl">Export</div>',unsafe_allow_html=True)
    if not results:
        st.info("Run a scan first.")
    else:
        def _csv(rows):
            cols=["sym","name","exch","sector","price","high52","dH","sp","xp",
                  "rs_leader","sma21","dS","in_bz","rsi","atr","ttm","pe","yoy",
                  "eps_ok","yoy_ok","ac_ok","sr_ok","sq_ok","fs","perfect"]
            return pd.DataFrame([{c:r.get(c) for c in cols} for r in rows]).to_csv(index=False).encode()
        ec1,ec2,ec3,ec4=st.columns(4)
        with ec1: st.download_button("All Results",_csv(results),f"scan_{datetime.date.today()}.csv","text/csv")
        with ec2:
            pf=[r for r in results if r.get("perfect")]
            st.download_button("Perfect Only",_csv(pf),f"perfect_{datetime.date.today()}.csv","text/csv",disabled=not pf)
        with ec3:
            nr=[r for r in results if r.get("exch")=="NSE"]
            st.download_button("NSE Only",_csv(nr),f"nse_{datetime.date.today()}.csv","text/csv",disabled=not nr)
        with ec4:
            br=[r for r in results if r.get("exch")=="BSE"]
            st.download_button("BSE Only",_csv(br),f"bse_{datetime.date.today()}.csv","text/csv",disabled=not br)
        st.divider()
        st.markdown('<div class="sec-lbl">Scan Config</div>',unsafe_allow_html=True)
        st.json(cfg)
