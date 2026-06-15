#!/usr/bin/env python3
"""
Veille stratégique Bourse
Sections : Scouting · Découvertes · S&R · Europe · ETFs · USA+Asie
"""
import warnings, os, smtplib, re, json
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.request
import yfinance as yf

# ═══════════════════════════════════════════════════════════════════════════════
#  UNIVERS
# ═══════════════════════════════════════════════════════════════════════════════
CAC40 = {
    "AI.PA":"Air Liquide","AIR.PA":"Airbus","ALO.PA":"Alstom","ATO.PA":"Atos",
    "BN.PA":"Danone","BNP.PA":"BNP Paribas","CA.PA":"Carrefour","CAP.PA":"Capgemini",
    "CS.PA":"AXA","DG.PA":"Vinci","DSY.PA":"Dassault Systèmes","EL.PA":"EssilorLuxottica",
    "ENGI.PA":"Engie","ERF.PA":"Eurofins Scientific","GLE.PA":"Société Générale",
    "HO.PA":"Thales","KER.PA":"Kering","LR.PA":"Legrand","MC.PA":"LVMH",
    "ML.PA":"Michelin","ORA.PA":"Orange","PUB.PA":"Publicis Groupe","RI.PA":"Pernod Ricard",
    "RMS.PA":"Hermès","RNO.PA":"Renault","SAF.PA":"Safran","SAN.PA":"Sanofi",
    "SGO.PA":"Saint-Gobain","STLAP.PA":"Stellantis","STMPA.PA":"STMicroelectronics",
    "SU.PA":"Schneider Electric","TTE.PA":"TotalEnergies","URW.PA":"Unibail-Rodamco",
    "VIE.PA":"Veolia","ACA.PA":"Crédit Agricole","BVI.PA":"Bureau Veritas",
    "RCO.PA":"Remy Cointreau","NK.PA":"Imerys","SOP.PA":"Sopra Steria",
}
DAX = {
    "ADS.DE":"Adidas","ALV.DE":"Allianz","BAYN.DE":"Bayer","BMW.DE":"BMW",
    "BAS.DE":"BASF","DB1.DE":"Deutsche Börse","DBK.DE":"Deutsche Bank",
    "DHL.DE":"DHL Group","DTE.DE":"Deutsche Telekom","EOAN.DE":"E.ON",
    "FRE.DE":"Fresenius","HEI.DE":"HeidelbergCement","HEN3.DE":"Henkel",
    "IFX.DE":"Infineon Technologies","LIN.DE":"Linde","MRK.DE":"Merck KGaA",
    "MUV2.DE":"Munich Re","RWE.DE":"RWE","SAP.DE":"SAP","SIE.DE":"Siemens",
    "SRT3.DE":"Sartorius","VOW3.DE":"Volkswagen","ZAL.DE":"Zalando",
}
OTHER_EU = {
    "ASML.AS":"ASML","INGA.AS":"ING Group","MT.AS":"ArcelorMittal","PHIA.AS":"Philips",
    "REN.AS":"RELX","UNA.AS":"Unilever","WKL.AS":"Wolters Kluwer",
    "NOVO-B.CO":"Novo Nordisk (DK)","ITX.MC":"Inditex (ES)","SAN.MC":"Banco Santander (ES)",
    "IBE.MC":"Iberdrola (ES)","ENI.MI":"ENI (IT)","RACE.MI":"Ferrari (IT)",
}
# DCAM.PA = Amundi MSCI Europe → exposition européenne → rangé avec les actions EU
EU_STOCKS_MAP = {**CAC40, **DAX, **OTHER_EU, "DCAM.PA": "Amundi MSCI Europe"}

# ETFs à exposition mondiale/US/Asie → section dédiée
EU_ETFS = {
    "PAASI.PA":"Amundi PEA Emerging Asia","PAEEM.PA":"Amundi PEA Emerging Markets",
    "PINR.PA":"Amundi PEA MSCI India","PAEJ.PA":"Amundi PEA Japan",
    "PTPXE.PA":"Amundi PEA Topix","ESE.PA":"BNP S&P 500 (PEA)",
    "WPEA.PA":"iShares MSCI World Swap PEA","ANX.PA":"Amundi Nasdaq-100 (PEA)",
    "RS2K.PA":"Amundi Russell 2000 (PEA)",
}
ETF_INDEX = {
    "PAASI.PA":"Emerging Asia","PAEEM.PA":"Emerging Markets","PINR.PA":"MSCI India",
    "PAEJ.PA":"Japon","PTPXE.PA":"Topix","DCAM.PA":"MSCI Europe",
    "ESE.PA":"S&P 500","WPEA.PA":"MSCI World","ANX.PA":"Nasdaq-100","RS2K.PA":"Russell 2000",
}
NON_PEA = {
    # USA
    "NVDA":"NVIDIA","AAPL":"Apple","MSFT":"Microsoft","AMZN":"Amazon",
    "META":"Meta","GOOGL":"Alphabet","AVGO":"Broadcom",
    "BRK-B":"Berkshire Hathaway","XOM":"ExxonMobil","JPM":"JPMorgan Chase",
    # Japon
    "7203.T":"Toyota","6758.T":"Sony","9984.T":"SoftBank","6861.T":"Keyence",
    "6954.T":"Fanuc","4063.T":"Shin-Etsu Chemical","8306.T":"MUFG",
    "9432.T":"NTT","6501.T":"Hitachi","6902.T":"Denso",
    # Corée
    "005930.KS":"Samsung Electronics","000660.KS":"SK Hynix","035420.KS":"NAVER",
    "051910.KS":"LG Chem","006400.KS":"Samsung SDI","035720.KS":"Kakao","000270.KS":"Kia Motors",
    # Taiwan
    "TSM":"TSMC","2454.TW":"MediaTek","2317.TW":"Hon Hai (Foxconn)","2308.TW":"Delta Electronics",
    # HK/Chine
    "0700.HK":"Tencent","9988.HK":"Alibaba","3690.HK":"Meituan","1810.HK":"Xiaomi",
    "1211.HK":"BYD","9618.HK":"JD.com","2318.HK":"Ping An","0941.HK":"China Mobile",
}
INDICES = {
    "^FCHI":"CAC 40","^STOXX50E":"Euro Stoxx 50","^GDAXI":"DAX 40",
    "^AEX":"AEX (Amsterdam)","^GSPC":"S&P 500","^IXIC":"NASDAQ",
    "^N225":"Nikkei 225","^HSI":"Hang Seng","^KS11":"KOSPI (Corée)",
    "^TWII":"TAIEX (Taiwan)","000001.SS":"Shanghai Composite",
}
MACRO = {
    "^VIX":"VIX","EURUSD=X":"EUR/USD","GC=F":"Or ($/oz)","BZ=F":"Brent ($/b)",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  NLP / SENTIMENT
# ═══════════════════════════════════════════════════════════════════════════════
STOP_WORDS = {
    "le","la","les","de","du","des","un","une","en","et","à","au","aux","par","sur",
    "pour","avec","dans","que","qui","se","sa","son","ses","ce","cet","cette","ces",
    "il","elle","ils","elles","on","je","tu","nous","vous","plus","the","of","in",
    "a","an","to","for","on","at","by","is","are","was","its","be","as","has","have",
    "it","this","that","with","from","will","after","but","or","new","said","says",
    "may","can","also","than","into","been","about","over","up","out","their",
}
FINANCIAL_TERMS = {
    "résultats","bénéfice","dividende","acquisition","fusion","rachat","chiffre",
    "croissance","perte","dette","restructuration","guidance","trimestre","annuel",
    "hausse","baisse","progression","recul","record","objectif","prévision",
    "investissement","contrat","partenariat","cession","introduction","offre",
    "earnings","profit","revenue","dividend","buyback","merger","outlook","downgrade",
    "upgrade","target","beat","miss","rally","surge","quarterly","annual","growth",
    "loss","debt","restructuring","contract","deal",
}
POSITIVE_WORDS = {
    "hausse","progression","record","croissance","beat","surge","rally","strong",
    "profit","dividend","upgrade","gains","rise","growth","positive","exceeded",
}
NEGATIVE_WORDS = {
    "baisse","perte","avertissement","miss","downgrade","restructuration","dette",
    "chute","loss","decline","warning","cut","disappoints","below","weak","risk",
}

def sentiment_icon(title):
    words = {w.lower() for w in re.findall(r'\b\w+\b', title)}
    pos = len(words & POSITIVE_WORDS); neg = len(words & NEGATIVE_WORDS)
    if pos > neg: return "🟢"
    if neg > pos: return "🔴"
    return "⚪"

def extract_keywords(text, n=5):
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', text)
    filtered = [w for w in words if w.lower() not in STOP_WORDS]
    freq = {}
    for w in filtered:
        wl = w.lower()
        freq[wl] = freq.get(wl, 0) + (3 if wl in FINANCIAL_TERMS else 1)
    return sorted(freq, key=freq.get, reverse=True)[:n]

# ═══════════════════════════════════════════════════════════════════════════════
#  NEWS & GROQ
# ═══════════════════════════════════════════════════════════════════════════════
def _finnhub_news(ticker, finnhub_key, days=5):
    from datetime import timedelta
    now_dt = datetime.now(timezone.utc)
    date_from = (now_dt - timedelta(days=days)).strftime("%Y-%m-%d")
    date_to   = now_dt.strftime("%Y-%m-%d")
    candidates = [ticker] + ([ticker.split(".")[0]] if "." in ticker else [])
    for sym in candidates:
        try:
            url = (f"https://finnhub.io/api/v1/company-news?symbol={sym}"
                   f"&from={date_from}&to={date_to}&token={finnhub_key}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            if isinstance(data, list) and data:
                return data
        except: pass
    return []

def _parse_yf_news_item(item):
    content = item.get("content", {})
    if content:
        title     = content.get("title", "")
        provider  = content.get("provider", {})
        publisher = provider.get("displayName", "") if isinstance(provider, dict) else ""
    else:
        title     = item.get("title", "")
        publisher = item.get("publisher", "")
    return title.strip(), publisher.strip()

def groq_synthesize(ticker_name, articles, groq_key, prompt_override=None):
    try:
        from groq import Groq
    except ImportError:
        return None
    texts = []
    for item in articles[:3]:
        h = item.get("headline", ""); su = item.get("summary", "")
        if h: texts.append(f"- {h}" + (f" : {su[:200]}" if su else ""))
    if not texts: return None
    prompt = prompt_override or (
        f"Tu es analyste financier. Voici des articles récents sur {ticker_name} :\n\n"
        + "\n".join(texts)
        + "\n\nEn 2 phrases maximum, explique la tendance actuelle et pourquoi ce titre "
        "est potentiellement intéressant. Sois factuel et concis. Réponds en français."
    )
    try:
        client = Groq(api_key=groq_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f" [groq ERR: {e}]", end="", flush=True)
        return None

def get_ticker_news(tickers, max_per_ticker=3):
    finnhub_key = os.environ.get("FINNHUB_KEY", "")
    groq_key    = os.environ.get("GROQ_KEY", "")
    sources = []
    if finnhub_key: sources.append("Finnhub")
    if groq_key:    sources.append("Groq")
    if not finnhub_key: sources.append("yfinance")
    print(f"    [news] Sources : {', '.join(sources)}", end=" ", flush=True)
    news_map = {}
    for t in tickers:
        entries = []; raw_finnhub = []
        if finnhub_key:
            raw_finnhub = _finnhub_news(t, finnhub_key)
            for item in raw_finnhub[:max_per_ticker]:
                h = item.get("headline",""); src = item.get("source","Finnhub")
                su = item.get("summary",""); url = item.get("url","")
                if h:
                    entries.append((f"{sentiment_icon(h)} {src}", h[:95],
                                    extract_keywords(h+" "+su), url))
        if not entries:
            try:
                for item in (yf.Ticker(t).news or [])[:max_per_ticker]:
                    title, pub = _parse_yf_news_item(item)
                    if title:
                        entries.append((f"{sentiment_icon(title)} {pub}",
                                        title[:95], extract_keywords(title), ""))
            except: pass
        synthesis = None
        if groq_key and (raw_finnhub or entries):
            src = raw_finnhub if raw_finnhub else [{"headline":e[1],"summary":""} for e in entries]
            synthesis = groq_synthesize(t, src, groq_key)
        if entries or synthesis:
            news_map[t] = {"articles": entries, "synthesis": synthesis}
    return news_map

# ═══════════════════════════════════════════════════════════════════════════════
#  DONNÉES MARCHÉ
# ═══════════════════════════════════════════════════════════════════════════════
def get_all_indices(indices_dict):
    results = {}
    tickers = list(indices_dict.keys())
    try:
        raw = yf.download(tickers, period="5d", auto_adjust=True,
                          group_by="ticker", threads=True, progress=False)
        for t in tickers:
            try:
                df = raw if len(tickers)==1 else (raw[t] if t in raw.columns.get_level_values(0) else None)
                if df is not None and not df.empty:
                    close = df["Close"].dropna()
                    if len(close) >= 2:
                        results[t] = (float(close.iloc[-1]),
                                      float((close.iloc[-1]/close.iloc[-2]-1)*100))
            except: pass
    except Exception as e:
        print(f"  [indices] ERR: {e}")
    return results

def get_yahoo_trending():
    tickers = set()
    EU_SUFFIXES   = (".PA",".DE",".AS",".MC",".MI",".CO",".L",".BR",".LS",".SW")
    ASIA_SUFFIXES = (".T",".KS",".TW",".HK",".SS",".SZ")
    US_LARGECAP   = {"NVDA","AAPL","MSFT","AMZN","META","GOOGL","TSM","AVGO","JPM","XOM","BRK-B"}
    for market in ["FR","DE","GB","JP","KR","TW","HK"]:
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/trending/{market}"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            result = data.get("finance",{}).get("result") or []
            if not result: continue
            for q in result[0].get("quotes",[]):
                sym = q.get("symbol","")
                if any(sym.endswith(s) for s in EU_SUFFIXES+ASIA_SUFFIXES):
                    tickers.add(sym)
                elif "." not in sym and sym in US_LARGECAP:
                    tickers.add(sym)
        except Exception as e:
            print(f"  [trending {market}] {e}")
    return tickers

def dl(tickers, period="14mo", label=""):
    if not tickers: return {}
    print(f"  {label} ({len(tickers)})...", end=" ", flush=True)
    try:
        raw = yf.download(list(tickers), period=period, auto_adjust=True,
                          group_by="ticker", threads=True, progress=False)
    except Exception as e:
        print(f"ERR:{e}"); return {}
    result = {}
    for t in tickers:
        try:
            df = raw if len(tickers)==1 else (raw[t] if t in raw.columns.get_level_values(0) else None)
            if df is not None and not df.empty and len(df)>=30: result[t]=df
        except: pass
    print(f"{len(result)}/{len(tickers)} OK")
    return result

# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYSE TECHNIQUE + SUPPORTS / RÉSISTANCES
# ═══════════════════════════════════════════════════════════════════════════════
def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    al = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    return 100 - (100 / (1 + ag/al.replace(0, np.nan)))

def macd(close, fast=12, slow=26, sig=9):
    ef = close.ewm(span=fast, adjust=False).mean()
    es = close.ewm(span=slow, adjust=False).mean()
    line = ef - es; signal = line.ewm(span=sig, adjust=False).mean()
    return line, signal, line - signal

def bollinger(close, period=20, nb=2):
    mid = close.rolling(period).mean(); std = close.rolling(period).std()
    upper = mid + nb*std; lower = mid - nb*std
    bw = (upper - lower) / mid
    pct_b = (close - lower) / (upper - lower).replace(0, np.nan)
    return upper, lower, mid, bw, pct_b

def sma(close, p): return close.rolling(p).mean()

def find_sr_levels(close, window=10, cluster_pct=0.025, lookback=130):
    """
    Détecte les niveaux de support et résistance par pivots locaux (~6 mois).
    - Résistance : pic local (max sur fenêtre ±window bougies)
    - Support    : creux local (min sur fenêtre ±window bougies)
    - Clustering : regroupe les niveaux à moins de cluster_pct les uns des autres
    """
    data    = close.iloc[-lookback:] if len(close) > lookback else close
    current = float(close.iloc[-1])
    prev    = float(close.iloc[-2]) if len(close) >= 2 else current

    highs, lows = [], []
    for i in range(window, len(data) - window):
        v   = float(data.iloc[i])
        win = data.iloc[max(0, i-window):i+window+1]
        if v >= float(win.max()) * 0.9985: highs.append(v)
        if v <= float(win.min()) * 1.0015: lows.append(v)

    def cluster(lvls):
        if not lvls: return []
        lvls = sorted(set(lvls)); grps = [[lvls[0]]]
        for l in lvls[1:]:
            if l <= grps[-1][-1] * (1 + cluster_pct): grps[-1].append(l)
            else: grps.append([l])
        return [sum(g)/len(g) for g in grps]

    res = cluster(highs); sup = cluster(lows)

    res_above = [r for r in res if r > current * 1.005]
    sup_below = [s for s in sup if s < current * 0.995]
    nearest_res = min(res_above, key=lambda x: x-current) if res_above else None
    nearest_sup = max(sup_below) if sup_below else None

    # Cassure de résistance : hier sous le niveau, aujourd'hui au-dessus (max +4%)
    breakout = None
    for r in sorted(res):
        if prev < r <= current * 1.04:
            breakout = r; break

    # Rebond sur support : prix à ≤2.5% au-dessus d'un support
    at_support = None
    if nearest_sup:
        pct = (current - nearest_sup) / nearest_sup * 100
        if 0 <= pct <= 2.5: at_support = nearest_sup

    return {
        "nearest_res": nearest_res,
        "nearest_sup": nearest_sup,
        "breakout":    breakout,
        "at_support":  at_support,
        "pct_to_res":  ((nearest_res/current)-1)*100 if nearest_res else None,
        "pct_to_sup":  ((current/nearest_sup)-1)*100 if nearest_sup else None,
    }

def analyze(ticker, df, min_periods=60):
    if df is None or len(df) < min_periods: return None
    close  = df["Close"].dropna()
    volume = df["Volume"].dropna() if "Volume" in df.columns else None
    if len(close) < min_periods: return None
    try:
        r  = rsi(close); ml, ms, mh = macd(close)
        _, _, _, bw, pct_b = bollinger(close)
        s20, s50, s200 = sma(close,20), sma(close,50), sma(close,200)
        cr = float(r.iloc[-1])
        ch = float(mh.iloc[-1]); ph = float(mh.iloc[-2]) if len(mh)>1 else 0
        cp = float(close.iloc[-1])
        cs20  = float(s20.iloc[-1])  if not np.isnan(s20.iloc[-1])  else None
        cs50  = float(s50.iloc[-1])  if not np.isnan(s50.iloc[-1])  else None
        cs200 = float(s200.iloc[-1]) if not np.isnan(s200.iloc[-1]) else None
        cbw = float(bw.iloc[-1]); pbw = float(bw.iloc[-5]) if len(bw)>5 else cbw
        squeeze = cbw < pbw*0.85
        cpb = float(pct_b.iloc[-1]) if not np.isnan(pct_b.iloc[-1]) else 0.5
        vr = None
        if volume is not None and len(volume)>=20:
            v5 = float(volume.iloc[-5:].mean()); v20 = float(volume.iloc[-20:].mean())
            if v20>0: vr = v5/v20
        bc   = ch>0 and ph<=0
        a20  = cp>cs20  if cs20  else None
        a50  = cp>cs50  if cs50  else None
        a200 = cp>cs200 if cs200 else None
        c1d  = float((close.iloc[-1]/close.iloc[-2]-1)*100)  if len(close)>=2  else 0
        c5d  = float((close.iloc[-1]/close.iloc[-6]-1)*100)  if len(close)>=6  else c1d
        c1m  = float((close.iloc[-1]/close.iloc[-22]-1)*100) if len(close)>=22 else 0
        # Pente RSI sur 3 jours : hausse = dynamique en cours, baisse = essoufflement
        rsi_slope = float(r.iloc[-1] - r.iloc[-4]) if len(r)>=4 else 0.0
        # 52 semaines high/low
        w52 = close.iloc[-252:] if len(close)>=252 else close
        h52 = float(w52.max()); l52 = float(w52.min())
        pct_from_h52 = (cp/h52 - 1)*100   # négatif : distance au plus haut annuel
        pct_from_l52 = (cp/l52 - 1)*100   # positif  : distance au plus bas annuel
        os = 0
        if cr<25: os+=3
        elif cr<35: os+=2
        elif cr<45: os+=1
        if bc: os+=2
        if a200: os+=1
        if vr and vr>=1.5: os+=1
        if cpb<0.2: os+=1
        ts = 0
        if a20: ts+=1
        if a50: ts+=1
        if a200: ts+=2
        if float(ml.iloc[-1])>float(ms.iloc[-1]): ts+=1
        if 45<=cr<=68: ts+=1
        sr = find_sr_levels(close)
        # Score de confiance /10 : agrège les signaux techniques indépendants
        conf = 0
        if bc: conf += 2
        elif float(ml.iloc[-1])>float(ms.iloc[-1]): conf += 1
        if a200 is True: conf += 2
        if vr and vr>=1.5: conf += 2
        elif vr and vr>=1.2: conf += 1
        if rsi_slope > 0: conf += 1
        if cpb < 0.3: conf += 1
        if sr.get("breakout"): conf += 1
        conf_score = min(conf, 10)
        return {"rsi":cr,"macd":float(ml.iloc[-1]),"signal":float(ms.iloc[-1]),"hist":ch,
                "bull_cross":bc,"above_sma20":a20,"above_sma50":a50,"above_sma200":a200,
                "vol_ratio":vr,"squeeze":squeeze,"pct_b":cpb,
                "oversold_score":os,"trend_score":ts,"overbought":cr>72,
                "price":cp,"change_1d":c1d,"change_5d":c5d,"change_1mo":c1m,
                "rsi_slope":rsi_slope,"conf_score":conf_score,
                "pct_from_h52":pct_from_h52,"pct_from_l52":pct_from_l52,
                **sr}
    except: return None

# ═══════════════════════════════════════════════════════════════════════════════
#  DÉCOUVERTES — Presse Finnhub + Yahoo Trending (fusionnés)
# ═══════════════════════════════════════════════════════════════════════════════
def decouverte_scan(finnhub_key, groq_key, known_tickers, top_n=5):
    """Détecte les tickers hors univers connu via Finnhub General News + Yahoo Trending."""
    candidates = {}  # sym → {"count": int, "articles": [], "source": str}

    # ── Presse Finnhub ───────────────────────────────────────────────────────
    if finnhub_key:
        print(f"  [Découvertes] Presse Finnhub...", end=" ", flush=True)
        for category in ["general", "merger"]:
            try:
                url = f"https://finnhub.io/api/v1/news?category={category}&token={finnhub_key}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    arts = json.loads(r.read())
                for art in arts[:80]:
                    for sym in art.get("related","").split(","):
                        sym = sym.strip().upper()
                        if (not sym or len(sym)>10 or sym in known_tickers
                                or not re.match(r'^[A-Z0-9]{1,6}(-[A-Z])?(\.[A-Z]{1,2})?$', sym)):
                            continue
                        if sym not in candidates:
                            candidates[sym] = {"count":0,"articles":[],"source":"📰 Presse"}
                        candidates[sym]["count"] += 1
                        candidates[sym]["articles"].append(art)
            except Exception as e:
                print(f"ERR {category}: {e}", end=" ", flush=True)
        print(f"{len(candidates)} via presse", end=" | ", flush=True)

    # ── Yahoo Trending ───────────────────────────────────────────────────────
    print(f"Yahoo Trending...", end=" ", flush=True)
    trending = get_yahoo_trending()
    for sym in trending - known_tickers - set(candidates.keys()):
        candidates[sym] = {"count":1,"articles":[],"source":"📡 Trending"}
    print(f"{len(trending)} trending")

    # ── Analyse des candidats ────────────────────────────────────────────────
    # Trie par nombre de mentions, puis enrichit les tickers avec yfinance
    sorted_cands = sorted(candidates.items(), key=lambda x: x[1]["count"], reverse=True)
    results = []; scanned = 0
    for sym, meta in sorted_cands:
        if len(results) >= top_n: break
        if scanned >= top_n * 4: break  # Evite de scanner trop de tickers lents
        scanned += 1
        try:
            df_raw = yf.download(sym, period="2y", auto_adjust=True,
                                 progress=False, threads=False)
            if df_raw is None or len(df_raw) < 30: continue
            s = analyze(sym, df_raw, min_periods=30)
            if not s: continue
            raw_arts = meta["articles"][:3]
            if not raw_arts and finnhub_key:
                raw_arts = _finnhub_news(sym, finnhub_key, days=5)[:3]
            arts = [{"headline":a.get("headline",""),"summary":a.get("summary",""),
                     "source":a.get("source",""),"url":a.get("url","")}
                    for a in raw_arts if a.get("headline")]
            synthesis = groq_synthesize(sym, arts, groq_key) if groq_key and arts else None
            results.append({"ticker":sym,"name":sym,"source":meta["source"],
                            "mentions":meta["count"],"s":s,
                            "articles":arts[:2],"synthesis":synthesis})
        except: continue
    return results

# ═══════════════════════════════════════════════════════════════════════════════
#  SCOUTING
# ═══════════════════════════════════════════════════════════════════════════════
def build_scouting(all_sig, finnhub_key, groq_key, top_n=3):
    """Top mouvements achat/vente sur l'ensemble de l'univers (effet mouton)."""
    def score_2d(s): return s.get("change_1d",0) + s.get("change_5d",0)
    top_buy  = sorted(all_sig.items(), key=lambda x: score_2d(x[1]), reverse=True)[:top_n]
    top_sell = sorted(all_sig.items(), key=lambda x: score_2d(x[1]))[:top_n]

    def enrich(entries):
        result = []
        for t, s in entries:
            articles = _finnhub_news(t, finnhub_key, days=3) if finnhub_key else []
            if not articles:
                try:
                    for item in (yf.Ticker(t).news or [])[:3]:
                        title, pub = _parse_yf_news_item(item)
                        if title:
                            content = item.get("content",{})
                            cp_link = content.get("canonicalUrl",{}) if content else {}
                            url = cp_link.get("url","") if isinstance(cp_link,dict) else ""
                            articles.append({"headline":title,"summary":"","source":pub,"url":url})
                except: pass
            synthesis = None
            if groq_key and articles:
                texts = [f"- {a.get('headline','')}" + (f" : {a.get('summary','')[:150]}" if a.get('summary') else "")
                         for a in articles[:3] if a.get('headline')]
                if texts:
                    c2d = s.get("change_2d", s["change_1d"])
                    direction = "hausse" if s["change_1d"]>0 else "baisse"
                    c5d = s.get("change_5d", s["change_1d"])
                    trend_conf = "confirmée 5j" if (s["change_1d"]>0)==(c5d>0) else "non confirmée (5j inverse)"
                    vol_txt = f" (Vol×{s['vol_ratio']:.1f})" if s.get("vol_ratio") and s["vol_ratio"]>1 else ""
                    rsi_sl = s.get("rsi_slope", 0)
                    rsi_txt = f", RSI en {'hausse' if rsi_sl>0 else 'baisse'} ({rsi_sl:+.1f} sur 3j)"
                    prompt = (
                        f"Tu es analyste financier. {s['name']} ({t}) : {s['change_1d']:+.1f}% aujourd'hui, "
                        f"{c5d:+.1f}% sur 5j ({trend_conf}){vol_txt}{rsi_txt}. RSI {s['rsi']:.0f}.\n"
                        f"Actualités :\n" + "\n".join(texts) +
                        f"\nEn 2 phrases max, explique cette {direction} : effet mouton ou mouvement fondamental ? Réponds en français."
                    )
                    try:
                        from groq import Groq
                        resp = Groq(api_key=groq_key).chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role":"user","content":prompt}], max_tokens=130)
                        synthesis = resp.choices[0].message.content.strip()
                    except Exception as e:
                        print(f" [scout groq ERR: {e}]", end="", flush=True)
            result.append({"ticker":t,"name":s["name"],"s":s,
                           "articles":articles[:2],"synthesis":synthesis})
        return result

    print(f"\n  [Scouting] Analyse top mouvements...", end=" ", flush=True)
    buys  = enrich(top_buy)
    sells = enrich(top_sell)
    print("OK")
    return buys, sells

# ═══════════════════════════════════════════════════════════════════════════════
#  RENDU HTML — utilitaires
# ═══════════════════════════════════════════════════════════════════════════════
def ticker_url(ticker):
    return f"https://finance.yahoo.com/quote/{ticker}"

def ticker_link(ticker, label=None):
    txt = label or ticker
    return f'<a href="{ticker_url(ticker)}" style="color:#1d4ed8;text-decoration:none" target="_blank">{txt}</a>'

def color_pct(v):
    if v > 0: return f'<span style="color:#16a34a">▲{v:.1f}%</span>'
    if v < 0: return f'<span style="color:#dc2626">▼{abs(v):.1f}%</span>'
    return f'{v:.1f}%'

def sr_hint_html(s):
    """Affiche la distance au prochain support/résistance + ratio R/R."""
    parts = []
    if s.get("pct_to_res"):
        parts.append(f'<span style="color:#7c3aed;font-size:10px">Résist.&nbsp;+{s["pct_to_res"]:.1f}%</span>')
    if s.get("pct_to_sup"):
        parts.append(f'<span style="color:#0369a1;font-size:10px">Support&nbsp;-{s["pct_to_sup"]:.1f}%</span>')
    if s.get("pct_to_res") and s.get("pct_to_sup") and s["pct_to_sup"] > 0:
        rr = s["pct_to_res"] / s["pct_to_sup"]
        col = "#16a34a" if rr >= 2 else ("#d97706" if rr >= 1 else "#dc2626")
        parts.append(f'<span style="color:{col};font-size:10px;font-weight:bold">R/R&nbsp;{rr:.1f}×</span>')
    return (' &nbsp;·&nbsp; '.join(parts)) if parts else ""

def news_html(news_entry):
    if not news_entry: return ""
    html = ""
    synthesis = news_entry.get("synthesis") if isinstance(news_entry, dict) else None
    articles  = news_entry.get("articles", []) if isinstance(news_entry, dict) else news_entry
    if synthesis:
        html += (f'<div style="margin-top:6px;padding:6px 8px;background:#f0fdf4;'
                 f'border-left:3px solid #16a34a;border-radius:3px;font-size:11px;color:#166534">'
                 f'🤖 {synthesis}</div>')
    seen = set()
    for item in articles[:2]:
        src = item[0]; title = item[1]
        keywords = item[2] if len(item)>2 else []
        url = item[3] if len(item)>3 else ""
        if title in seen: continue
        seen.add(title)
        kw_html = " ".join(
            f'<span style="background:#e0f2fe;color:#0369a1;border:1px solid #bae6fd;'
            f'padding:1px 5px;border-radius:3px;font-size:10px">{k}</span>'
            for k in keywords[:4])
        title_html = (f'<a href="{url}" style="color:#1d4ed8;text-decoration:none" target="_blank">{title}</a>'
                      if url else title)
        html += f'<div style="margin-top:4px;font-size:11px;color:#4b5563">📰 <em>[{src}]</em> {title_html}</div>'
        if kw_html: html += f'<div style="margin-top:2px">{kw_html}</div>'
    return html

def conf_badge_html(s):
    """Badge score de confiance /10."""
    c = s.get("conf_score", 0)
    col = "#16a34a" if c>=7 else ("#d97706" if c>=4 else "#6b7280")
    return f'<span style="color:{col};font-size:11px;font-weight:bold">⬤{c}/10</span>'

def w52_hint_html(s):
    """Contexte 52 semaines : proximité du plus haut / plus bas annuel."""
    parts = []
    h = s.get("pct_from_h52"); l = s.get("pct_from_l52")
    if h is not None and h > -5:
        parts.append(f'<span style="color:#7c3aed;font-size:10px">▲52sem&nbsp;{h:.1f}%</span>')
    elif h is not None and h < -30:
        parts.append(f'<span style="color:#6b7280;font-size:10px">▽52sem&nbsp;{h:.1f}%</span>')
    if l is not None and l < 10:
        parts.append(f'<span style="color:#dc2626;font-size:10px">↗52bas&nbsp;+{l:.1f}%</span>')
    return (' &nbsp;·&nbsp; '.join(parts)) if parts else ""

def html_row(name, ticker, s, badge="", news_map=None):
    ind = [f'RSI {s["rsi"]:.0f}']
    if s["bull_cross"]: ind.append("MACD↑")
    elif s["macd"]>s["signal"]: ind.append("MACD+")
    else: ind.append("MACD-")
    if s["above_sma200"] is True:  ind.append("▲SMA200")
    if s.get("vol_ratio") and s["vol_ratio"]>=1.5: ind.append(f'Vol×{s["vol_ratio"]:.1f}')
    if s.get("squeeze"): ind.append("BB squeeze")
    ind_html   = " · ".join(ind)
    badge_html = f' <span style="color:#6b7280;font-size:12px">{badge}</span>' if badge else ""
    sr_h  = sr_hint_html(s); w52_h = w52_hint_html(s)
    meta_parts = [p for p in [sr_h, w52_h] if p]
    meta_line  = (f'<div style="margin-top:2px;font-size:11px">' + ' &nbsp;·&nbsp; '.join(meta_parts) + '</div>') if meta_parts else ""
    articles   = (news_map or {}).get(ticker, [])
    return f"""
    <tr>
      <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">
        <strong>{name}</strong> <span style="color:#6b7280;font-size:12px">({ticker_link(ticker)})</span>
        &nbsp;{conf_badge_html(s)}{badge_html}<br>
        <span style="font-size:12px;color:#555">{ind_html}</span>{meta_line}
        {news_html(articles)}
      </td>
      <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap">
        {color_pct(s["change_1d"])}/j<br>
        <span style="font-size:12px">{color_pct(s["change_1mo"])}/mois</span>
      </td>
    </tr>"""

def section_html(title, color, rows_html, empty_msg="Aucun signal détecté."):
    content = rows_html or f'<tr><td colspan="2" style="padding:8px 12px;color:#6b7280">{empty_msg}</td></tr>'
    return f"""
    <div style="margin-bottom:24px">
      <div style="background:{color};color:#fff;padding:8px 14px;border-radius:6px 6px 0 0;font-weight:bold">{title}</div>
      <table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 6px 6px">
        {content}
      </table>
    </div>"""

# ═══════════════════════════════════════════════════════════════════════════════
#  RENDU HTML — sections spécifiques
# ═══════════════════════════════════════════════════════════════════════════════
def scouting_html(buys, sells):
    def card(item, side):
        s = item["s"]; t = item["ticker"]; name = item["name"]
        col_bg  = "#f0fdf4" if side=="buy" else "#fef2f2"
        col_bdr = "#16a34a" if side=="buy" else "#dc2626"
        col_txt = "#166534" if side=="buy" else "#991b1b"
        arrow   = "▲" if side=="buy" else "▼"
        pct1d = s["change_1d"]; pct5d = s.get("change_5d", pct1d)
        rsi_slope = s.get("rsi_slope", 0)
        vol_ok = s.get("vol_ratio") and s["vol_ratio"] >= 1.2
        # Confirmation forte : tendance 5j cohérente + volume + RSI en hausse
        n_confirm = sum([
            (pct1d>0)==(pct5d>0),   # 5j dans le même sens
            bool(vol_ok),           # volume au-dessus de la moyenne
            (pct1d>0)==(rsi_slope>0),  # RSI en phase
        ])
        if n_confirm == 3:
            confirm_tag = f'<span style="color:#16a34a;font-size:11px;font-weight:bold">✔✔&nbsp;5j</span>&nbsp;'
        elif n_confirm == 2:
            confirm_tag = f'<span style="color:#16a34a;font-size:11px;font-weight:bold">✔&nbsp;5j</span>&nbsp;'
        else:
            confirm_tag = f'<span style="color:#d97706;font-size:11px;font-weight:bold">⚠&nbsp;5j</span>&nbsp;'
        vol_tag = (f'<span style="color:#854d0e;font-size:11px">Vol×{s["vol_ratio"]:.1f}</span>&nbsp;'
                   if vol_ok else "")
        rsi_dir = "↑" if rsi_slope > 0 else ("↓" if rsi_slope < 0 else "→")
        rsi_tag = f'<span style="font-size:11px;color:#6b7280">RSI {s["rsi"]:.0f}{rsi_dir}</span>'
        arts_html = ""
        for a in item["articles"][:2]:
            h = a.get("headline","")[:90]; url = a.get("url",""); src = a.get("source","")
            kw = extract_keywords(h)
            kw_html = " ".join(
                f'<span style="background:#e0f2fe;color:#0369a1;border:1px solid #bae6fd;'
                f'padding:1px 4px;border-radius:3px;font-size:10px">{k}</span>' for k in kw[:4])
            lnk = f'<a href="{url}" style="color:#1d4ed8;text-decoration:none" target="_blank">{h}</a>' if url else h
            arts_html += f'<div style="margin-top:3px;font-size:11px;color:#4b5563">📰 [{src}] {lnk}</div>'
            if kw_html: arts_html += f'<div style="margin-top:2px">{kw_html}</div>'
        synth_html = (
            f'<div style="margin-top:6px;padding:5px 8px;background:{col_bg};'
            f'border-left:3px solid {col_bdr};border-radius:3px;font-size:11px;color:{col_txt}">'
            f'🤖 {item["synthesis"]}</div>' if item["synthesis"] else ""
        )
        return f"""
        <tr><td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">
          <div>
            <span style="font-size:18px;font-weight:bold;color:{col_bdr}">{arrow}{abs(pct1d):.1f}%</span>
            &nbsp;<strong style="font-size:13px">{ticker_link(t, name)}</strong>
            &nbsp;<span style="color:#6b7280;font-size:12px">({ticker_link(t)})</span>
          </div>
          <div style="margin-top:3px;font-size:11px">
            <span style="color:#6b7280">5j&nbsp;:&nbsp;{pct5d:+.1f}%</span>
            &nbsp;&nbsp;{confirm_tag}&nbsp;&nbsp;{vol_tag}&nbsp;{rsi_tag}
          </div>
          {arts_html}{synth_html}
        </td></tr>"""

    buys_rows  = "".join(card(i,"buy")  for i in buys)
    sells_rows = "".join(card(i,"sell") for i in sells)
    return f"""
    <div style="margin-bottom:24px;border:2px solid #1e3a5f;border-radius:8px;overflow:hidden">
      <div style="background:#1e3a5f;color:#fff;padding:10px 16px">
        <span style="font-size:15px;font-weight:bold">🔭 Scouting — Achat / Vente · Effet mouton</span>
        <span style="font-size:11px;opacity:0.7;margin-left:8px">Top mouvements · recoupés avec l'actualité</span>
      </div>
      <table style="width:100%;border-collapse:collapse">
        <tr>
          <td style="width:50%;vertical-align:top;border-right:1px solid #e5e7eb">
            <div style="background:#dcfce7;padding:6px 12px;font-weight:bold;font-size:12px;color:#166534">
              🟢 TOP ACHATS — momentum haussier</div>
            <table style="width:100%;border-collapse:collapse">{buys_rows}</table>
          </td>
          <td style="width:50%;vertical-align:top">
            <div style="background:#fee2e2;padding:6px 12px;font-weight:bold;font-size:12px;color:#991b1b">
              🔴 TOP VENTES — pression baissière</div>
            <table style="width:100%;border-collapse:collapse">{sells_rows}</table>
          </td>
        </tr>
      </table>
    </div>"""

def decouverte_html(decouvertes):
    if not decouvertes: return ""
    rows = ""
    for item in decouvertes:
        t = item["ticker"]; s = item["s"]; src = item["source"]
        cnt = item["mentions"]; arts = item["articles"]; synth = item["synthesis"]
        ind = (f'RSI {s["rsi"]:.0f} · '
               + ("MACD↑" if s["bull_cross"] else ("MACD+" if s["macd"]>s["signal"] else "MACD-"))
               + (f' · ▲SMA200' if s.get("above_sma200") else ""))
        src_tag = (f'<span style="color:#7c3aed;font-size:11px;font-weight:bold">{src}'
                   + (f'&nbsp;×{cnt}' if cnt>1 else '') + '</span>')
        arts_html = ""
        for a in arts:
            h = a.get("headline","")[:90]; url = a.get("url",""); sc = a.get("source","")
            kw = extract_keywords(h)
            kw_html = " ".join(
                f'<span style="background:#e0f2fe;color:#0369a1;border:1px solid #bae6fd;'
                f'padding:1px 4px;border-radius:3px;font-size:10px">{k}</span>' for k in kw[:4])
            lnk = f'<a href="{url}" style="color:#1d4ed8;text-decoration:none" target="_blank">{h}</a>' if url else h
            arts_html += f'<div style="margin-top:3px;font-size:11px;color:#4b5563">📰 [{sc}] {lnk}</div>'
            if kw_html: arts_html += f'<div style="margin-top:2px">{kw_html}</div>'
        synth_html = (
            f'<div style="margin-top:5px;padding:5px 8px;background:#f5f3ff;'
            f'border-left:3px solid #7c3aed;border-radius:3px;font-size:11px;color:#5b21b6">'
            f'🤖 {synth}</div>' if synth else ""
        )
        sr_h = sr_hint_html(s)
        sr_line = f'<div style="margin-top:2px;font-size:11px">{sr_h}</div>' if sr_h else ""
        rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">
            <strong>{ticker_link(t)}</strong>&nbsp;{src_tag}<br>
            <span style="font-size:12px;color:#555">{ind}</span>{sr_line}
            {arts_html}{synth_html}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap">
            {color_pct(s["change_1d"])}/j<br>
            <span style="font-size:12px">{color_pct(s["change_1mo"])}/mois</span>
          </td>
        </tr>"""
    return section_html("🔍 Découvertes — Presse & Trending", "#6d28d9", rows,
                        "Aucune nouvelle valeur détectée aujourd'hui.")

def etf_rows_html(sig_etf, news_map=None):
    rows = ""; nm = news_map or {}
    for t, s in sorted(sig_etf.items(), key=lambda x: x[1].get("change_1d",0), reverse=True):
        idx = ETF_INDEX.get(t,"")
        idx_badge = (f'<span style="background:#e0f2fe;color:#0369a1;border:1px solid #bae6fd;'
                     f'padding:1px 6px;border-radius:3px;font-size:10px">{idx}</span>' if idx else "")
        ind = [f'RSI {s["rsi"]:.0f}']
        if s["bull_cross"]: ind.append("MACD↑")
        elif s["macd"]>s["signal"]: ind.append("MACD+")
        else: ind.append("MACD-")
        if s.get("above_sma200"): ind.append("▲SMA200")
        ind_html = " · ".join(ind)
        rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">
            <strong>{s["name"]}</strong> <span style="color:#6b7280;font-size:12px">({ticker_link(t)})</span>
            &nbsp;{idx_badge}<br>
            <span style="font-size:12px;color:#555">{ind_html}</span>
            {news_html(nm.get(t,[]))}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap">
            {color_pct(s["change_1d"])}/j<br>
            <span style="font-size:12px">{color_pct(s["change_1mo"])}/mois</span>
          </td>
        </tr>"""
    return rows

# ═══════════════════════════════════════════════════════════════════════════════
#  RÉSUMÉ EXÉCUTIF (Groq)
# ═══════════════════════════════════════════════════════════════════════════════
def build_groq_summary(indices_data, sr_break, eu_buy_all, snp_buy, macro_data, groq_key):
    if not groq_key: return None
    idx_txt = ", ".join(
        f"{n}: {'+' if v[1]>=0 else ''}{v[1]:.1f}%"
        for n,v in indices_data[:6] if v
    )
    # Macro
    macro_txt = ", ".join(
        f"{n}: {v[0]:,.1f} ({'+' if v[1]>=0 else ''}{v[1]:.1f}%)"
        for n,v in macro_data.items() if v
    ) if macro_data else ""
    # Top cassures
    top_br = ", ".join(
        f"{s['name']} (+{s.get('change_1d',0):.1f}%)"
        for t,s in list(sr_break.items())[:4]
    ) or "aucune"
    # Top achats
    top_buy = ", ".join(
        f"{s['name']} (score {s.get('conf_score',0)}/10)"
        for t,s in list(eu_buy_all.items())[:3]
    ) or "aucun"
    prompt = (
        f"Tu es analyste financier senior. Contexte de marché du jour :\n"
        f"Indices : {idx_txt}\n"
        + (f"Macro : {macro_txt}\n" if macro_txt else "")
        + f"Cassures de résistance : {top_br}\n"
        f"Signaux d'achat Europe : {top_buy}\n\n"
        f"En 3-4 phrases concises, rédige un résumé exécutif du contexte de marché "
        f"et des points d'attention du jour. Identifie si le contexte est favorable ou défavorable "
        f"pour les signaux détectés. Réponds en français, sans titre, directement le texte."
    )
    try:
        from groq import Groq
        resp = Groq(api_key=groq_key).chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}], max_tokens=200)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f" [résumé Groq ERR: {e}]", end="", flush=True)
        return None

# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD HTML PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
def build_html(now, indices_data, sig_eu, sig_etf, snp, scouting, decouvertes, news_map, macro_data=None, groq_key="", groq_summary=None):
    nm = news_map or {}

    # ── Indices ──────────────────────────────────────────────────────────────
    idx_rows = ""
    for name, val in indices_data:
        if val:
            p, c = val; col = "#16a34a" if c>=0 else "#dc2626"; arrow = "▲" if c>=0 else "▼"
            idx_rows += (f'<td style="padding:6px 14px;text-align:center">'
                         f'<div style="font-size:12px;color:#6b7280">{name}</div>'
                         f'<div style="font-weight:bold">{p:,.2f}</div>'
                         f'<div style="color:{col};font-size:12px">{arrow}{abs(c):.2f}%</div></td>')
        else:
            idx_rows += (f'<td style="padding:6px 14px;text-align:center">'
                         f'<div style="font-size:12px;color:#6b7280">{name}</div>'
                         f'<div style="color:#9ca3af">n/d</div></td>')

    # ── S&R : Cassures + Supports ─────────────────────────────────────────────
    all_sig = {**sig_eu, **sig_etf, **snp}
    def _cassure_qualite(s):
        vol_ok  = s.get("vol_ratio") and s["vol_ratio"] >= 1.2
        move_ok = s.get("change_1d", 0) >= 2.0 and s.get("rsi", 100) < 70 and s.get("above_sma200")
        return vol_ok or move_ok
    sr_break_all = {t:s for t,s in all_sig.items() if s.get("breakout")}
    sr_break = dict(sorted(
        {t:s for t,s in sr_break_all.items() if _cassure_qualite(s)}.items(),
        key=lambda x: (bool(x[1].get("vol_ratio") and x[1]["vol_ratio"]>=1.2),
                       x[1].get("change_1d", 0)),
        reverse=True
    )[:10])
    sr_supp  = {t:s for t,s in all_sig.items() if s.get("at_support")}

    # ── Déduplication : un ticker n'apparaît que dans sa section prioritaire ──
    used = set(sr_break.keys())
    sr_supp_d = {t:s for t,s in sr_supp.items() if t not in used}
    used |= set(sr_supp_d.keys())

    sr_break_rows = ""
    for t,s in sr_break.items():
        res_lvl = s["breakout"]
        badge = f'🚀 +{((s["price"]/res_lvl)-1)*100:.1f}% au-dessus de {res_lvl:.2f}'
        sr_break_rows += html_row(s["name"], t, s, badge, nm)

    sr_supp_rows = ""
    for t,s in sorted(sr_supp_d.items(), key=lambda x: x[1].get("pct_to_sup",999)):
        sup_lvl = s["at_support"]
        badge = f'🛡️ à {s["pct_to_sup"]:.1f}% du support {sup_lvl:.2f}'
        sr_supp_rows += html_row(s["name"], t, s, badge, nm)

    # ── Europe — signaux (déduplication) ─────────────────────────────────────
    eu_buy_s = {t:s for t,s in sig_eu.items()
                if t not in used and s["oversold_score"]>=4
                and s["above_sma200"] is not False and not s["overbought"]}
    eu_buy_m = {t:s for t,s in sig_eu.items()
                if t not in used and 2<=s["oversold_score"]<4
                and s["above_sma200"] is not False and not s["overbought"] and t not in eu_buy_s}
    eu_buy_all = (dict(sorted(eu_buy_s.items(), key=lambda x:x[1]["oversold_score"], reverse=True))
                | dict(sorted(eu_buy_m.items(), key=lambda x:x[1]["oversold_score"], reverse=True)[:8]))
    used |= set(eu_buy_all.keys())
    eu_buy_rows = "".join(
        html_row(s["name"], t, s,
                 ("⭐⭐ Fort" if s["oversold_score"]>=4 else "⭐ Modéré") + f' [{s["oversold_score"]}/8]', nm)
        for t,s in eu_buy_all.items()
    )

    eu_mom = {t:s for t,s in sig_eu.items()
              if t not in used and s["trend_score"]>=5 and s["oversold_score"]<=2 and not s["overbought"]}
    eu_mom = dict(sorted(eu_mom.items(), key=lambda x:x[1]["trend_score"], reverse=True)[:8])
    used |= set(eu_mom.keys())
    eu_mom_rows = "".join(html_row(s["name"],t,s,f'Trend {s["trend_score"]}/6',nm) for t,s in eu_mom.items())

    eu_ob = dict(sorted({t:s for t,s in sig_eu.items() if s["overbought"]}.items(),
                        key=lambda x:x[1]["rsi"], reverse=True)[:8])
    eu_ob_rows = "".join(html_row(s["name"],t,s,"",nm) for t,s in eu_ob.items())

    # ── Compressions BB (toutes géographies) ─────────────────────────────────
    sq = {t:s for t,s in all_sig.items() if s.get("squeeze") and not s["overbought"]}
    sq_rows = "".join(
        f'<tr><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0">'
        f'<strong>{s["name"]}</strong> ({ticker_link(t)}) · RSI {s["rsi"]:.0f} · {color_pct(s["change_1d"])}/j'
        f'</td></tr>'
        for t,s in list(sq.items())[:8]
    ) if sq else ""

    # ── USA + Asie ───────────────────────────────────────────────────────────
    snp_buy = {t:s for t,s in snp.items() if s["oversold_score"]>=3 and not s["overbought"]}
    snp_mom = {t:s for t,s in snp.items() if s["trend_score"]>=4 and not s["overbought"] and t not in snp_buy}
    snp_ob  = dict(sorted({t:s for t,s in snp.items() if s["overbought"]}.items(),
                           key=lambda x:x[1]["rsi"], reverse=True)[:5])

    def sub_block(label, rows):
        return (f'<div style="margin:8px 0 4px;font-size:13px;color:#6b7280;padding:0 12px">{label}</div>'
                f'<table style="width:100%;border-collapse:collapse">{rows}</table>') if rows else ""

    snp_buy_rows = "".join(html_row(s["name"],t,s,"",nm) for t,s in sorted(snp_buy.items(),key=lambda x:x[1]["oversold_score"],reverse=True))
    snp_mom_rows = "".join(html_row(s["name"],t,s,"",nm) for t,s in sorted(snp_mom.items(),key=lambda x:x[1]["trend_score"],reverse=True))
    snp_ob_rows  = "".join(html_row(s["name"],t,s,"",nm) for t,s in snp_ob.items())
    snp_content  = (sub_block("▶ Signaux achat / rebond", snp_buy_rows)
                  + sub_block("▶ Momentum haussier", snp_mom_rows)
                  + sub_block("▶ Surachat", snp_ob_rows))
    if not snp_content:
        snp_content = '<div style="padding:8px 12px;color:#6b7280;font-size:13px">Aucun signal notable.</div>'

    n_eu = len(sig_eu); n_etf = len(sig_etf); n_snp = len(snp)

    # ── Macro rows ───────────────────────────────────────────────────────────
    macro_rows = ""
    for mname, mval in (macro_data or {}).items():
        if mval:
            mp, mc = mval; mcol = "#16a34a" if mc>=0 else "#dc2626"; marrow = "▲" if mc>=0 else "▼"
            macro_rows += (f'<td style="padding:6px 14px;text-align:center">'
                           f'<div style="font-size:11px;color:#6b7280">{mname}</div>'
                           f'<div style="font-weight:bold;font-size:13px">{mp:,.2f}</div>'
                           f'<div style="color:{mcol};font-size:11px">{marrow}{abs(mc):.2f}%</div></td>')

    # ── Résumé exécutif Groq ─────────────────────────────────────────────────
    summary_txt = groq_summary  # pre-computed in main() before news fetching
    summary_html = (
        f'<div style="background:#eff6ff;border-left:4px solid #2563eb;border-radius:6px;'
        f'padding:12px 16px;margin-bottom:20px;font-size:13px;color:#1e3a5f;line-height:1.6">'
        f'🤖 <strong>Contexte du jour</strong><br>{summary_txt}</div>'
    ) if summary_txt else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;background:#f9fafb;padding:20px">

  <div style="background:#1e3a5f;color:#fff;padding:18px 24px;border-radius:8px;margin-bottom:20px">
    <div style="font-size:20px;font-weight:bold">📊 Veille stratégique — Bourse</div>
    <div style="font-size:13px;opacity:0.8;margin-top:4px">
      {now.strftime("%A %d/%m/%Y — %H:%M UTC")}
      &nbsp;·&nbsp;{n_eu} Europe · {n_etf} ETFs · {n_snp} USA+Asie
    </div>
  </div>

  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:12px;overflow-x:auto">
    <div style="font-weight:bold;margin-bottom:8px;color:#374151">Indices</div>
    <table style="border-collapse:collapse;width:100%"><tr>{idx_rows}</tr></table>
  </div>
  {f'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;margin-bottom:20px;overflow-x:auto"><div style="font-size:11px;color:#6b7280;margin-bottom:4px">Macro</div><table style="border-collapse:collapse"><tr>{macro_rows}</tr></table></div>' if macro_rows else ""}
  {summary_html}

  {scouting_html(scouting[0], scouting[1]) if scouting else ""}
  {decouverte_html(decouvertes)}
  {section_html("🚀 Cassures de résistance — signal achat", "#0f766e", sr_break_rows, "Aucune cassure détectée aujourd'hui.") if sr_break_rows else ""}
  {section_html("🛡️ Rebonds sur support — à surveiller", "#0369a1", sr_supp_rows, "Aucun rebond sur support détecté.") if sr_supp_rows else ""}
  {section_html("🟢 Europe — Signaux d'achat &nbsp;<span style='font-size:12px;font-weight:normal'>(⭐⭐ Fort · ⭐ Modéré)</span>", "#16a34a", eu_buy_rows, "Aucun signal d'achat détecté aujourd'hui.")}
  {section_html("📈 Europe — Momentum haussier confirmé", "#2563eb", eu_mom_rows, "Aucune tendance forte.")}
  {section_html("🔴 Europe — Surachat — prudence", "#dc2626", eu_ob_rows, "Aucune valeur en surachat.") if eu_ob_rows else ""}
  {section_html("⚡ Compressions Bollinger — rupture imminente", "#7c3aed", sq_rows, "Aucune compression détectée.") if sq_rows else ""}

  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px;margin-bottom:20px">
    <div style="font-weight:bold;margin-bottom:6px;color:#374151">🌍 USA + Asie</div>
    {snp_content}
  </div>

  {section_html("📦 ETFs — Exposition mondiale", "#0891b2", etf_rows_html(sig_etf, nm), "Aucune donnée ETF.")}

  <div style="text-align:center;font-size:11px;color:#9ca3af;margin-top:16px">
    Généré automatiquement · données Yahoo Finance &amp; Finnhub · Usage personnel uniquement
  </div>
</body></html>"""

# ═══════════════════════════════════════════════════════════════════════════════
#  EMAIL
# ═══════════════════════════════════════════════════════════════════════════════
def send_email(html_body, now):
    gmail_user = os.environ.get("GMAIL_USER","")
    gmail_pwd  = os.environ.get("GMAIL_APP_PASSWORD","")
    recipient  = os.environ.get("RECIPIENT_EMAIL", gmail_user)
    if not gmail_user or not gmail_pwd:
        print("  [email] GMAIL_USER ou GMAIL_APP_PASSWORD non défini — email ignoré.")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Veille stratégique Bourse — {now.strftime('%d/%m/%Y')}"
    msg["From"] = gmail_user; msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(gmail_user, gmail_pwd)
            srv.sendmail(gmail_user, recipient, msg.as_string())
        print(f"  [email] Envoyé à {recipient} ✓")
    except Exception as e:
        print(f"  [email] Erreur : {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSOLE
# ═══════════════════════════════════════════════════════════════════════════════
def fmts(s):
    parts = [f"RSI {s['rsi']:.0f}"]
    if s["bull_cross"]: parts.append("MACD↑")
    elif s["macd"]>s["signal"]: parts.append("MACD+")
    else: parts.append("MACD-")
    if s["above_sma200"] is True:  parts.append("▲SMA200")
    elif s["above_sma200"] is False: parts.append("▼SMA200")
    if s.get("vol_ratio") and s["vol_ratio"]>=1.5: parts.append(f"Vol×{s['vol_ratio']:.1f}")
    if s.get("squeeze"):    parts.append("BB squeeze")
    if s.get("breakout"):   parts.append(f"🚀 Cassure {s['breakout']:.2f}")
    if s.get("at_support"): parts.append(f"🛡️ Support {s['at_support']:.2f}")
    return " | ".join(parts)

def fmtp(s): return f"{s['change_1d']:+.1f}%/j  {s['change_1mo']:+.1f}%/mois"
W = 70
def sec(title, c="─"): print(); print(c*W); print(f"  {title}"); print(c*W)
def row_con(name, ticker, s, extra=""):
    print(f"  {(name+' ('+ticker+')'):<44} {fmtp(s)}")
    print(f"    {fmts(s)}")
    if extra: print(f"    {extra}")

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    now = datetime.now(timezone.utc)
    n_total = len(EU_STOCKS_MAP) + len(EU_ETFS) + len(NON_PEA)
    print("="*W)
    print(f"  VEILLE STRATÉGIQUE BOURSE — {now.strftime('%A %d/%m/%Y — %H:%M UTC')}")
    print(f"  Univers : {len(EU_STOCKS_MAP)} Europe · {len(EU_ETFS)} ETFs · {len(NON_PEA)} USA+Asie = {n_total} valeurs")
    print("="*W)

    sec("INDICES", "─")
    idx_values = get_all_indices(INDICES)
    indices_data = []
    for t, n in INDICES.items():
        val = idx_values.get(t)
        indices_data.append((n, val))
        if val:
            p, c = val
            print(f"  {n:<30} {p:>12,.2f}   {'▲' if c>=0 else '▼'}{abs(c):.2f}%")
        else:
            print(f"  {n:<30} {'n/d':>12}")

    macro_raw = get_all_indices(MACRO)
    macro_data = {MACRO[t]: macro_raw.get(t) for t in MACRO}
    print("  Macro :", " | ".join(
        f"{MACRO[t]}: {macro_raw[t][0]:,.2f} ({macro_raw[t][1]:+.2f}%)"
        for t in MACRO if macro_raw.get(t)) or "n/d"
    )

    print()
    deu  = dl(list(EU_STOCKS_MAP.keys()), label="Europe (actions)")
    detf = dl(list(EU_ETFS.keys()),       label="ETFs")
    dsnp = dl(list(NON_PEA.keys()),       label="USA + Asie")

    sig_eu, sig_etf, snp = {}, {}, {}
    for t, df in deu.items():
        s = analyze(t, df)
        if s: sig_eu[t]  = {"name": EU_STOCKS_MAP.get(t,t), **s}
    for t, df in detf.items():
        s = analyze(t, df)
        if s: sig_etf[t] = {"name": EU_ETFS.get(t,t), **s}
    for t, df in dsnp.items():
        s = analyze(t, df)
        if s: snp[t]     = {"name": NON_PEA.get(t,t), **s}

    all_sig = {**sig_eu, **sig_etf, **snp}

    # ── S&R ─────────────────────────────────────────────────────────────────
    def _cassure_qualite(s):
        vol_ok  = s.get("vol_ratio") and s["vol_ratio"] >= 1.2
        move_ok = s.get("change_1d", 0) >= 2.0 and s.get("rsi", 100) < 70 and s.get("above_sma200")
        return vol_ok or move_ok
    sr_break_all = {t:s for t,s in all_sig.items() if s.get("breakout")}
    sr_break = dict(sorted(
        {t:s for t,s in sr_break_all.items() if _cassure_qualite(s)}.items(),
        key=lambda x: (bool(x[1].get("vol_ratio") and x[1]["vol_ratio"]>=1.2),
                       x[1].get("change_1d", 0)),
        reverse=True
    )[:10])
    sr_supp  = {t:s for t,s in all_sig.items() if s.get("at_support")}
    if sr_break:
        sec(f"🚀 CASSURES DE RÉSISTANCE (top {len(sr_break)}/{len(sr_break_all)} filtrées)","=")
        for t,s in sr_break.items():
            row_con(s["name"],t,s,f"Cassure {s['breakout']:.2f}")
    if sr_supp:
        sec("🛡️ REBONDS SUR SUPPORT","─")
        for t,s in sorted(sr_supp.items(), key=lambda x:x[1].get("pct_to_sup",999)):
            row_con(s["name"],t,s,f"Support {s['at_support']:.2f} ({s['pct_to_sup']:.1f}% au-dessus)")

    # ── Europe ───────────────────────────────────────────────────────────────
    eu_buy = {t:s for t,s in sig_eu.items() if s["oversold_score"]>=2 and s["above_sma200"] is not False and not s["overbought"]}
    eu_buy = dict(sorted(eu_buy.items(), key=lambda x:x[1]["oversold_score"], reverse=True))
    sec("EUROPE — SIGNAUX D'ACHAT","=")
    if eu_buy:
        for t,s in eu_buy.items():
            row_con(s["name"],t,s,("⭐⭐ Fort" if s["oversold_score"]>=4 else "⭐  Modéré") + f" [{s['oversold_score']}/8]")
    else: print("  Aucun signal d'achat détecté.")

    eu_mom = {t:s for t,s in sig_eu.items() if s["trend_score"]>=5 and s["oversold_score"]<=2 and not s["overbought"]}
    sec("EUROPE — MOMENTUM HAUSSIER","─")
    if eu_mom:
        for t,s in dict(sorted(eu_mom.items(), key=lambda x:x[1]["trend_score"],reverse=True)[:8]).items():
            row_con(s["name"],t,s,f"Trend {s['trend_score']}/6 · conf {s.get('conf_score',0)}/10")
    else: print("  Aucune tendance forte.")

    # ── USA + Asie ───────────────────────────────────────────────────────────
    snp_buy = {t:s for t,s in snp.items() if s["oversold_score"]>=3 and not s["overbought"]}
    snp_mom = {t:s for t,s in snp.items() if s["trend_score"]>=4 and not s["overbought"] and t not in snp_buy}
    sec("USA + ASIE","=")
    if snp_buy:
        print("\n  ▶ Signaux achat / rebond :")
        for t,s in sorted(snp_buy.items(),key=lambda x:x[1]["oversold_score"],reverse=True): row_con(s["name"],t,s)
    if snp_mom:
        print("\n  ▶ Momentum haussier :")
        for t,s in sorted(snp_mom.items(),key=lambda x:x[1]["trend_score"],reverse=True): row_con(s["name"],t,s)
    if not snp_buy and not snp_mom: print("  Aucun signal notable.")

    # ── Résumé ───────────────────────────────────────────────────────────────
    sec("RÉSUMÉ","=")
    total_ok = len(sig_eu)+len(sig_etf)+len(snp)
    echecs = n_total - total_ok
    sq = {t:s for t,s in all_sig.items() if s.get("squeeze") and not s["overbought"]}
    eu_ob = {t:s for t,s in sig_eu.items() if s["overbought"]}
    print(f"  Analysées : {len(sig_eu)} Europe · {len(sig_etf)} ETFs · {len(snp)} USA+Asie = {total_ok}"
          + (f" ({echecs} échec(s))" if echecs else ""))
    print(f"  Achat EU : {len(eu_buy)} · Momentum EU : {len(eu_mom)} · Surachat EU : {len(eu_ob)}")
    print(f"  Cassures résistance : {len(sr_break)} · Rebonds support : {len(sr_supp)} · BB squeeze : {len(sq)}")
    print("="*W)

    # ── Résumé Groq (avant news pour éviter le rate limit) ───────────────────
    groq_key = os.environ.get("GROQ_KEY","")
    print(f"\n  [Résumé] Génération...", end=" ", flush=True)
    groq_summary = build_groq_summary(indices_data, sr_break, eu_buy, snp_buy, macro_data or {}, groq_key)
    print("OK" if groq_summary else "skipped")

    # ── News ─────────────────────────────────────────────────────────────────
    # Widen to trend_score>=4 for news fetching (display still uses >=5)
    eu_mom_news = {t for t,s in sig_eu.items() if s["trend_score"]>=4 and not s["overbought"]}
    signal_tickers = list(set(
        list(eu_buy) + list(eu_mom_news) + list(sr_break) + list(sr_supp)
        + list(snp_buy) + list(snp_mom)
    ))
    print(f"  [News] {len(signal_tickers)} valeurs...", end=" ", flush=True)
    news_map = get_ticker_news(signal_tickers)
    print(f"{len(news_map)} avec actualités")

    # ── Scouting ─────────────────────────────────────────────────────────────
    finnhub_key = os.environ.get("FINNHUB_KEY","")
    scouting = build_scouting(all_sig, finnhub_key, groq_key)

    # ── Découvertes ───────────────────────────────────────────────────────────
    known = set(EU_STOCKS_MAP) | set(EU_ETFS) | set(NON_PEA)
    decouvertes = decouverte_scan(finnhub_key, groq_key, known, top_n=5)
    print(f"  [Découvertes] {len(decouvertes)} valeurs retenues")

    # ── Email ─────────────────────────────────────────────────────────────────
    html = build_html(now, indices_data, sig_eu, sig_etf, snp, scouting, decouvertes, news_map,
                      macro_data=macro_data, groq_key=groq_key, groq_summary=groq_summary)
    send_email(html, now)

if __name__ == "__main__":
    main()
