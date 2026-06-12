#!/usr/bin/env python3
import sys, warnings, os, smtplib, io, re, json
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.request
import yfinance as yf
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

CAC40 = {
    "AI.PA":"Air Liquide","AIR.PA":"Airbus","ALO.PA":"Alstom","ATO.PA":"Atos",
    "BN.PA":"Danone","BNP.PA":"BNP Paribas","CA.PA":"Carrefour","CAP.PA":"Capgemini",
    "CS.PA":"AXA","DG.PA":"Vinci","DSY.PA":"Dassault Systèmes","EL.PA":"EssilorLuxottica",
    "ENGI.PA":"Engie","ERF.PA":"Eurofins Scientific","GLE.PA":"Société Générale",
    "HO.PA":"Thales","KER.PA":"Kering","LR.PA":"Legrand","MC.PA":"LVMH",
    "ML.PA":"Michelin","ORA.PA":"Orange","PUB.PA":"Publicis Groupe","RI.PA":"Pernod Ricard",
    "RMS.PA":"Hermès","RNO.PA":"Renault","SAF.PA":"Safran","SAN.PA":"Sanofi",
    "SGO.PA":"Saint-Gobain","STLAP.PA":"Stellantis","STM.PA":"STMicroelectronics",
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
PEA_ETFS = {
    "PAASI.PA":"Amundi PEA Emerging Asia ESG","PAEEM.PA":"Amundi PEA Emerging Markets",
    "PINR.PA":"Amundi PEA MSCI India","PAEJ.PA":"Amundi PEA Japan",
    "PTPXE.PA":"Amundi PEA Topix","DCAM.PA":"Amundi MSCI Europe",
    "ESE.PA":"BNP Paribas S&P 500 (PEA)","WPEA.PA":"iShares MSCI World Swap PEA",
    "ANX.PA":"Amundi Nasdaq-100 (PEA)","RS2K.PA":"Amundi Russell 2000 (PEA)",
}
NON_PEA = {
    "NVDA":"NVIDIA","AAPL":"Apple","MSFT":"Microsoft","AMZN":"Amazon",
    "META":"Meta","GOOGL":"Alphabet","TSM":"TSMC (Taiwan)","AVGO":"Broadcom",
    "005930.KS":"Samsung (Corée)","7203.T":"Toyota (Japon)","6758.T":"Sony (Japon)",
    "9984.T":"SoftBank (Japon)","BRK-B":"Berkshire Hathaway","XOM":"ExxonMobil",
    "JPM":"JPMorgan Chase",
}
INDICES = {
    "^FCHI":"CAC 40","^STOXX50E":"Euro Stoxx 50","^GDAXI":"DAX 40",
    "^AEX":"AEX (Amsterdam)","^GSPC":"S&P 500","^IXIC":"NASDAQ",
    "^N225":"Nikkei 225","^HSI":"Hang Seng",
}

# Lookup nom de société → ticker (pour extraction depuis articles RSS)
COMPANY_TO_TICKER = {
    # CAC 40
    "air liquide":"AI.PA","airbus":"AIR.PA","alstom":"ALO.PA","atos":"ATO.PA",
    "danone":"BN.PA","bnp paribas":"BNP.PA","bnp":"BNP.PA","carrefour":"CA.PA",
    "capgemini":"CAP.PA","axa":"CS.PA","vinci":"DG.PA","dassault":"DSY.PA",
    "essilor":"EL.PA","luxottica":"EL.PA","essilorluxottica":"EL.PA",
    "engie":"ENGI.PA","eurofins":"ERF.PA","société générale":"GLE.PA",
    "societe generale":"GLE.PA","thales":"HO.PA","kering":"KER.PA",
    "legrand":"LR.PA","lvmh":"MC.PA","moët":"MC.PA","louis vuitton":"MC.PA",
    "michelin":"ML.PA","orange":"ORA.PA","publicis":"PUB.PA",
    "pernod ricard":"RI.PA","pernod":"RI.PA","hermès":"RMS.PA","hermes":"RMS.PA",
    "renault":"RNO.PA","safran":"SAF.PA","sanofi":"SAN.PA",
    "saint-gobain":"SGO.PA","saint gobain":"SGO.PA","stellantis":"STLAP.PA",
    "stmicroelectronics":"STM.PA","stm":"STM.PA","schneider":"SU.PA",
    "totalenergies":"TTE.PA","total":"TTE.PA","unibail":"URW.PA",
    "veolia":"VIE.PA","crédit agricole":"ACA.PA","credit agricole":"ACA.PA",
    "bureau veritas":"BVI.PA","rémy cointreau":"RCO.PA","imerys":"NK.PA",
    "sopra":"SOP.PA",
    # DAX
    "adidas":"ADS.DE","allianz":"ALV.DE","bayer":"BAYN.DE","bmw":"BMW.DE",
    "basf":"BAS.DE","deutsche börse":"DB1.DE","deutsche boerse":"DB1.DE",
    "deutsche bank":"DBK.DE","dhl":"DHL.DE","deutsche post":"DHL.DE",
    "deutsche telekom":"DTE.DE","telekom":"DTE.DE","e.on":"EOAN.DE","eon":"EOAN.DE",
    "fresenius":"FRE.DE","heidelberg":"HEI.DE","henkel":"HEN3.DE",
    "infineon":"IFX.DE","linde":"LIN.DE","merck":"MRK.DE","munich re":"MUV2.DE",
    "münchener rück":"MUV2.DE","rwe":"RWE.DE","sap":"SAP.DE","siemens":"SIE.DE",
    "sartorius":"SRT3.DE","volkswagen":"VOW3.DE","vw":"VOW3.DE","zalando":"ZAL.DE",
    # Autres EU
    "asml":"ASML.AS","ing":"INGA.AS","arcelor":"MT.AS","arcelormittal":"MT.AS",
    "philips":"PHIA.AS","relx":"REN.AS","unilever":"UNA.AS","wolters":"WKL.AS",
    "novo nordisk":"NOVO-B.CO","novo":"NOVO-B.CO","inditex":"ITX.MC","zara":"ITX.MC",
    "santander":"SAN.MC","iberdrola":"IBE.MC","eni":"ENI.MI","ferrari":"RACE.MI",
    # Hors PEA (utile pour détecter aussi)
    "nvidia":"NVDA","apple":"AAPL","microsoft":"MSFT","amazon":"AMZN",
    "meta":"META","alphabet":"GOOGL","google":"GOOGL","tsmc":"TSM",
    "broadcom":"AVGO","samsung":"005930.KS","toyota":"7203.T","sony":"6758.T",
    "softbank":"9984.T","berkshire":"BRK-B","exxon":"XOM","jpmorgan":"JPM",
}

RSS_FEEDS = [
    ("Les Echos",    "https://feeds.lesechos.fr/rss/rss_finance.xml"),
    ("Reuters",      "https://feeds.reuters.com/reuters/businessNews"),
    ("Boursorama",   "https://www.boursorama.com/actualites/rss/"),
    ("Reuters FR",   "https://fr.reuters.com/rssFeed/businessNews"),
]

def get_yahoo_trending():
    """Tickers trending sur Yahoo Finance pour FR et DE."""
    tickers = set()
    for market in ["FR", "DE", "US"]:
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/trending/{market}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            quotes = data["finance"]["result"][0]["quotes"]
            for q in quotes:
                sym = q.get("symbol","")
                # Garder seulement actions européennes éligibles PEA ou connues
                if sym.endswith((".PA",".DE",".AS",".MC",".MI",".CO")):
                    tickers.add(sym)
                elif market == "US" and "." not in sym and len(sym) <= 5:
                    tickers.add(sym)
        except Exception as e:
            print(f"  [trending {market}] {e}")
    return tickers

STOP_WORDS = {
    "le","la","les","de","du","des","un","une","en","et","à","au","aux","par","sur",
    "pour","avec","dans","que","qui","se","sa","son","ses","ce","cet","cette","ces",
    "il","elle","ils","elles","on","je","tu","nous","vous","plus","the","of","in",
    "a","an","to","for","on","at","by","is","are","was","its","be","as","has","have",
    "it","this","that","with","from","will","after","but","or","new","new","said",
    "says","may","can","also","than","into","been","about","over","up","out","their",
}

def extract_keywords(text, n=5):
    """Extrait les n mots-clés les plus significatifs d'un texte."""
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', text)
    filtered = [w for w in words if w.lower() not in STOP_WORDS]
    # Compte la fréquence et retourne les plus fréquents
    freq = {}
    for w in filtered:
        freq[w.lower()] = freq.get(w.lower(), 0) + 1
    top = sorted(freq, key=freq.get, reverse=True)[:n]
    return top

def scan_rss_for_tickers():
    """Parse les flux RSS et extrait les tickers + mots-clés des articles mentionnés."""
    if not HAS_FEEDPARSER:
        return {}
    found = {}  # ticker → [(source, titre, mots_clés)]
    text_lower_map = {k.lower(): v for k, v in COMPANY_TO_TICKER.items()}
    for source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                full_text = title + " " + summary
                text_lower = full_text.lower()
                for name, ticker in text_lower_map.items():
                    if name in text_lower:
                        keywords = extract_keywords(full_text)
                        if ticker not in found:
                            found[ticker] = []
                        found[ticker].append((source, title[:90], keywords))
        except Exception as e:
            print(f"  [rss {source}] {e}")
    return found

def radar_scan(static_universe: set, rss_hits: dict = None):
    """
    Combine Yahoo trending + RSS, analyse les tickers non encore dans l'univers statique.
    Retourne dict ticker → {name, signals, sources, articles}
    """
    print("\n  [Radar] Trending Yahoo Finance...", end=" ", flush=True)
    trending = get_yahoo_trending()
    print(f"{len(trending)} tickers")

    if rss_hits is None:
        print("  [Radar] Scan RSS...", end=" ", flush=True)
        rss_hits = scan_rss_for_tickers()
        print(f"{len(rss_hits)} tickers mentionnés")
    else:
        print(f"  [Radar] RSS déjà scanné — {len(rss_hits)} tickers")

    # Union des deux sources, hors univers statique
    candidates = (trending | set(rss_hits.keys())) - static_universe
    candidates = {t for t in candidates if not t.startswith("^")}

    if not candidates:
        print("  [Radar] Aucun nouveau ticker à analyser.")
        return {}

    print(f"  [Radar] Analyse de {len(candidates)} nouveaux tickers...", end=" ", flush=True)
    results = {}
    try:
        raw = yf.download(list(candidates), period="14mo", auto_adjust=True,
                          group_by="ticker", threads=True, progress=False)
    except Exception as e:
        print(f"ERR:{e}")
        return {}

    ok = 0
    for t in candidates:
        try:
            df = raw if len(candidates)==1 else (raw[t] if t in raw.columns.get_level_values(0) else None)
            if df is None or df.empty or len(df) < 60:
                continue
            s = analyze(t, df)
            if s:
                # Sources ayant mentionné ce ticker
                sources_list = rss_hits.get(t, [])
                is_trending = t in trending
                results[t] = {
                    "name": COMPANY_TO_TICKER.get(t.split(".")[0].lower(), t),
                    "trending": is_trending,
                    "articles": sources_list,
                    **s
                }
                ok += 1
        except:
            pass
    print(f"{ok} analysés")
    return results

def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    al = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = ag / al.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(close, fast=12, slow=26, sig=9):
    ef = close.ewm(span=fast, adjust=False).mean()
    es = close.ewm(span=slow, adjust=False).mean()
    line = ef - es
    signal = line.ewm(span=sig, adjust=False).mean()
    return line, signal, line - signal

def bollinger(close, period=20, nb=2):
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + nb*std; lower = mid - nb*std
    bw = (upper - lower) / mid
    pct_b = (close - lower) / (upper - lower).replace(0, np.nan)
    return upper, lower, mid, bw, pct_b

def sma(close, p): return close.rolling(p).mean()

def analyze(ticker, df):
    if df is None or len(df) < 60: return None
    close = df["Close"].dropna()
    volume = df["Volume"].dropna() if "Volume" in df.columns else None
    if len(close) < 60: return None
    try:
        r = rsi(close)
        ml, ms, mh = macd(close)
        _, _, _, bw, pct_b = bollinger(close)
        s20, s50, s200 = sma(close,20), sma(close,50), sma(close,200)
        cr = float(r.iloc[-1])
        ch = float(mh.iloc[-1]); ph = float(mh.iloc[-2]) if len(mh)>1 else 0
        cp = float(close.iloc[-1])
        cs20 = float(s20.iloc[-1]) if not np.isnan(s20.iloc[-1]) else None
        cs50 = float(s50.iloc[-1]) if not np.isnan(s50.iloc[-1]) else None
        cs200 = float(s200.iloc[-1]) if not np.isnan(s200.iloc[-1]) else None
        cbw = float(bw.iloc[-1]); pbw = float(bw.iloc[-5]) if len(bw)>5 else cbw
        squeeze = cbw < pbw*0.85
        cpb = float(pct_b.iloc[-1]) if not np.isnan(pct_b.iloc[-1]) else 0.5
        vr = None
        if volume is not None and len(volume)>=20:
            v5 = float(volume.iloc[-5:].mean()); v20 = float(volume.iloc[-20:].mean())
            if v20>0: vr = v5/v20
        bc = ch>0 and ph<=0
        a20 = cp>cs20 if cs20 else None
        a50 = cp>cs50 if cs50 else None
        a200 = cp>cs200 if cs200 else None
        c1d = float((close.iloc[-1]/close.iloc[-2]-1)*100) if len(close)>=2 else 0
        c1m = float((close.iloc[-1]/close.iloc[-22]-1)*100) if len(close)>=22 else 0
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
        return {"rsi":cr,"macd":float(ml.iloc[-1]),"signal":float(ms.iloc[-1]),"hist":ch,
                "bull_cross":bc,"above_sma20":a20,"above_sma50":a50,"above_sma200":a200,
                "vol_ratio":vr,"squeeze":squeeze,"pct_b":cpb,
                "oversold_score":os,"trend_score":ts,"overbought":cr>72,
                "price":cp,"change_1d":c1d,"change_1mo":c1m}
    except: return None

def dl(tickers, period="14mo", label=""):
    if not tickers: return {}
    print(f"  {label} ({len(tickers)})...", end=" ", flush=True)
    try:
        raw = yf.download(list(tickers), period=period, auto_adjust=True,
                          group_by="ticker", threads=True, progress=False)
    except Exception as e: print(f"ERR:{e}"); return {}
    result = {}
    for t in tickers:
        try:
            df = raw if len(tickers)==1 else (raw[t] if t in raw.columns.get_level_values(0) else None)
            if df is not None and not df.empty and len(df)>=30: result[t]=df
        except: pass
    print(f"{len(result)}/{len(tickers)} OK")
    return result

def get_idx(ticker):
    try:
        df = yf.download(ticker, period="5d", auto_adjust=True, progress=False)
        if df is not None and not df.empty:
            return float(df["Close"].iloc[-1]), float((df["Close"].iloc[-1]/df["Close"].iloc[-2]-1)*100)
    except: pass
    return None, None

def fmts(s):
    parts = [f"RSI {s['rsi']:.0f}"]
    if s["bull_cross"]: parts.append("MACD↑ croisement haussier")
    elif s["macd"]>s["signal"]: parts.append("MACD > signal")
    else: parts.append("MACD < signal")
    if s["above_sma200"] is True: parts.append("▲SMA200")
    elif s["above_sma200"] is False: parts.append("▼SMA200")
    if s["vol_ratio"] and s["vol_ratio"]>=1.5: parts.append(f"Vol×{s['vol_ratio']:.1f}")
    if s["squeeze"]: parts.append("BB squeeze")
    return " | ".join(parts)

def fmtp(s): return f"{s['change_1d']:+.1f}%/j  {s['change_1mo']:+.1f}%/mois"

W=70
def sec(title, c="─"): print(); print(c*W); print(f"  {title}"); print(c*W)
def row(name, ticker, s, extra=""):
    print(f"  {(name+' ('+ticker+')'):<44} {fmtp(s)}")
    print(f"    {fmts(s)}")
    if extra: print(f"    {extra}")

def main():
    now = datetime.now(timezone.utc)
    print("="*W)
    print(f"  SCAN OPPORTUNITÉS MARCHÉ — {now.strftime('%A %d/%m/%Y — %H:%M UTC')}")
    print(f"  Univers : CAC40 + DAX + EU + ETFs PEA + Hors-PEA ({sum(map(len,[CAC40,DAX,OTHER_EU,PEA_ETFS,NON_PEA]))} valeurs)")
    print("="*W)

    sec("CONTEXTE INDICES", "─")
    indices_data = []
    for t, n in INDICES.items():
        p, c = get_idx(t)
        indices_data.append((n, (p, c) if p else None))
        if p: print(f"  {n:<28} {p:>10,.2f}   {'▲' if c>=0 else '▼'}{abs(c):.2f}%")
        else: print(f"  {n:<28} {'n/d':>10}")

    print()
    all_pea = {**CAC40,**DAX,**OTHER_EU,**PEA_ETFS}
    dpea  = dl(list(CAC40.keys()),    label="CAC 40")
    ddax  = dl(list(DAX.keys()),      label="DAX")
    deu   = dl(list(OTHER_EU.keys()), label="Autres EU")
    detf  = dl(list(PEA_ETFS.keys()), label="ETFs PEA")
    dnpea = dl(list(NON_PEA.keys()),  label="Hors-PEA")
    all_data = {**dpea,**ddax,**deu,**detf}

    sig, snp = {}, {}
    for t, df in all_data.items():
        s = analyze(t, df)
        if s: sig[t] = {"name": all_pea.get(t,t), **s}
    for t, df in dnpea.items():
        s = analyze(t, df)
        if s: snp[t] = {"name": NON_PEA.get(t,t), **s}

    ca = {t:s for t,s in sig.items() if s["oversold_score"]>=4 and s["above_sma200"] is not False and not s["overbought"]}
    ca = dict(sorted(ca.items(), key=lambda x: x[1]["oversold_score"], reverse=True))
    sec("A. SIGNAUX D'ACHAT — convergence multi-indicateurs (éligibles PEA)","=")
    if ca:
        for t,s in ca.items(): row(s["name"],t,s,f"[Score: {s['oversold_score']}/8]")
    else: print("  Aucun signal fort détecté aujourd'hui.")

    cb = {t:s for t,s in sig.items() if 2<=s["oversold_score"]<4 and s["above_sma200"] is not False and not s["overbought"] and t not in ca}
    cb = dict(sorted(cb.items(), key=lambda x: x[1]["oversold_score"], reverse=True)[:12])
    sec("B. À SURVEILLER — RSI en zone de retournement ou MACD s'amorce","─")
    if cb:
        for t,s in cb.items(): row(s["name"],t,s)
    else: print("  Aucune valeur en zone de surveillance.")

    cc = {t:s for t,s in sig.items() if s["trend_score"]>=4 and s["oversold_score"]<=2 and not s["overbought"]}
    cc = dict(sorted(cc.items(), key=lambda x: x[1]["trend_score"], reverse=True)[:10])
    sec("C. TENDANCE HAUSSIÈRE CONFIRMÉE — momentum solide","─")
    if cc:
        for t,s in cc.items(): row(s["name"],t,s,f"[Trend: {s['trend_score']}/6]")
    else: print("  Aucune valeur en tendance forte.")

    cd = {t:s for t,s in sig.items() if s["overbought"]}
    cd = dict(sorted(cd.items(), key=lambda x: x[1]["rsi"], reverse=True)[:8])
    sec("D. SURACHAT — prudence / prise de bénéfices","─")
    if cd:
        for t,s in cd.items(): row(s["name"],t,s)
    else: print("  Aucune valeur en surachat significatif.")

    sq = {t:s for t,s in sig.items() if s.get("squeeze") and not s["overbought"]}
    if sq:
        sec("⚡ COMPRESSIONS BOLLINGER — rupture imminente","─")
        for t,s in list(sq.items())[:8]:
            print(f"  {s['name']:<38} ({t})  RSI {s['rsi']:.0f}  {fmtp(s)}")

    sec("HORS PEA — Compte-titres ordinaire uniquement","=")
    ha = {t:s for t,s in snp.items() if s["oversold_score"]>=3 and not s["overbought"]}
    hc = {t:s for t,s in snp.items() if s["trend_score"]>=4 and not s["overbought"] and t not in ha}
    if ha:
        print("\n  ▶ Signaux d'achat / rebond :")
        for t,s in sorted(ha.items(),key=lambda x:x[1]["oversold_score"],reverse=True): row(s["name"],t,s)
    if hc:
        print("\n  ▶ Tendances haussières :")
        for t,s in sorted(hc.items(),key=lambda x:x[1]["trend_score"],reverse=True): row(s["name"],t,s)
    if not ha and not hc: print("  Aucun signal notable hors-PEA.")

    sec("RÉSUMÉ","=")
    print(f"  Valeurs analysées (PEA) : {len(sig)}")
    print(f"  A (achat fort) : {len(ca)}  |  B (surveiller) : {len(cb)}  |  C (tendance) : {len(cc)}  |  D (surachat) : {len(cd)}")
    print(f"  Compressions BB : {len(sq)}  |  Hors-PEA : {len(snp)}")
    print("="*W)

    # Radar — nouvelles valeurs trending / presse
    static_universe = set({**CAC40,**DAX,**OTHER_EU,**PEA_ETFS,**NON_PEA}.keys())
    rss_hits = scan_rss_for_tickers()
    radar = radar_scan(static_universe, rss_hits)
    if radar:
        sec("🛰️ RADAR — Nouvelles valeurs détectées","─")
        for t, s in sorted(radar.items(), key=lambda x: x[1]["oversold_score"]+x[1]["trend_score"], reverse=True):
            tags = []
            if s["trending"]: tags.append("[Trending]")
            if s["articles"]: tags.append(f"[{', '.join(set(a[0] for a in s['articles'][:2]))}]")
            print(f"  {t:<16} RSI {s['rsi']:.0f}  {fmtp(s)}  {' '.join(tags)}")
            for src, title in s["articles"][:1]:
                print(f"    → {src}: {title}")

    # Envoi email HTML
    html = build_html(now, indices_data, ca, cb, cc, cd, sq, ha, hc, sig, snp, radar, rss_hits)
    send_email(html, now)

def color_pct(v):
    if v > 0: return f'<span style="color:#16a34a">▲{v:.1f}%</span>'
    if v < 0: return f'<span style="color:#dc2626">▼{abs(v):.1f}%</span>'
    return f'{v:.1f}%'

def badge(label, color):
    return f'<span style="background:{color};color:#fff;padding:2px 7px;border-radius:4px;font-size:12px;margin-right:4px">{label}</span>'

def html_row(name, ticker, s, score_label="", rss_hits=None):
    indicators = []
    indicators.append(f'RSI {s["rsi"]:.0f}')
    if s["bull_cross"]: indicators.append("MACD↑")
    elif s["macd"] > s["signal"]: indicators.append("MACD+")
    else: indicators.append("MACD-")
    if s["above_sma200"] is True: indicators.append("▲SMA200")
    if s["vol_ratio"] and s["vol_ratio"] >= 1.5: indicators.append(f'Vol×{s["vol_ratio"]:.1f}')
    if s["squeeze"]: indicators.append("BB squeeze")
    ind_html = " · ".join(indicators)
    score_html = f' <span style="color:#6b7280;font-size:12px">{score_label}</span>' if score_label else ""
    context = rss_context_html(rss_hits.get(ticker, [])) if rss_hits else ""
    return f"""
    <tr>
      <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">
        <strong>{name}</strong> <span style="color:#6b7280;font-size:12px">({ticker})</span>{score_html}<br>
        <span style="font-size:12px;color:#555">{ind_html}</span>
        {context}
      </td>
      <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap">
        {color_pct(s["change_1d"])}/j<br>
        <span style="font-size:12px">{color_pct(s["change_1mo"])}/mois</span>
      </td>
    </tr>"""

def section_html(title, color, rows_html, empty_msg="Aucun signal détecté."):
    content = rows_html if rows_html else f'<tr><td colspan="2" style="padding:8px 12px;color:#6b7280">{empty_msg}</td></tr>'
    return f"""
    <div style="margin-bottom:24px">
      <div style="background:{color};color:#fff;padding:8px 14px;border-radius:6px 6px 0 0;font-weight:bold">{title}</div>
      <table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 6px 6px">
        {content}
      </table>
    </div>"""

def rss_context_html(articles):
    """Génère le bloc HTML contexte RSS (titres + mots-clés) pour un ticker."""
    if not articles:
        return ""
    html = ""
    seen = set()
    for item in articles[:2]:
        src, title = item[0], item[1]
        keywords = item[2] if len(item) > 2 else []
        if title in seen:
            continue
        seen.add(title)
        kw_html = ""
        if keywords:
            kw_html = " ".join(
                f'<span style="background:#f0f9ff;color:#0369a1;border:1px solid #bae6fd;padding:1px 5px;border-radius:3px;font-size:10px">{k}</span>'
                for k in keywords[:5]
            )
        html += f'<div style="margin-top:4px;font-size:11px;color:#4b5563">📰 <em>[{src}]</em> {title}</div>'
        if kw_html:
            html += f'<div style="margin-top:2px">{kw_html}</div>'
    return html

def radar_html_rows(radar):
    rows = ""
    for t, s in sorted(radar.items(), key=lambda x: x[1]["oversold_score"]+x[1]["trend_score"], reverse=True):
        tags = []
        if s["trending"]: tags.append('<span style="background:#7c3aed;color:#fff;padding:1px 6px;border-radius:3px;font-size:11px">📡 Trending</span>')
        if s["articles"]:
            srcs = ", ".join(set(a[0] for a in s["articles"][:3]))
            tags.append(f'<span style="background:#0891b2;color:#fff;padding:1px 6px;border-radius:3px;font-size:11px">📰 {srcs}</span>')
        tag_html = " ".join(tags)
        rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">
            <strong>{t}</strong> {tag_html}<br>
            <span style="font-size:12px;color:#555">RSI {s['rsi']:.0f} · {'MACD↑' if s['bull_cross'] else ('MACD+' if s['macd']>s['signal'] else 'MACD-')} · {'▲SMA200' if s['above_sma200'] else ''}</span>
            {rss_context_html(s.get('articles',[]))}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap">
            {color_pct(s['change_1d'])}/j<br>
            <span style="font-size:12px">{color_pct(s['change_1mo'])}/mois</span>
          </td>
        </tr>"""
    return rows

def build_html(now, indices_data, ca, cb, cc, cd, sq, ha, hc, sig, snp, radar=None, rss_hits=None):
    idx_rows = ""
    for name, val in indices_data:
        if val:
            p, c = val
            arrow = "▲" if c >= 0 else "▼"
            col = "#16a34a" if c >= 0 else "#dc2626"
            idx_rows += f'<td style="padding:6px 14px;text-align:center"><div style="font-size:12px;color:#6b7280">{name}</div><div style="font-weight:bold">{p:,.2f}</div><div style="color:{col};font-size:12px">{arrow}{abs(c):.2f}%</div></td>'

    rh = rss_hits or {}
    ca_rows = "".join(html_row(s["name"],t,s,f'[Score {s["oversold_score"]}/8]',rh) for t,s in ca.items())
    cb_rows = "".join(html_row(s["name"],t,s,"",rh) for t,s in cb.items())
    cc_rows = "".join(html_row(s["name"],t,s,f'[Trend {s["trend_score"]}/6]',rh) for t,s in cc.items())
    cd_rows = "".join(html_row(s["name"],t,s,"",rh) for t,s in cd.items())
    ha_rows = "".join(html_row(s["name"],t,s,"",rh) for t,s in sorted(ha.items(),key=lambda x:x[1]["oversold_score"],reverse=True))
    hc_rows = "".join(html_row(s["name"],t,s,"",rh) for t,s in sorted(hc.items(),key=lambda x:x[1]["trend_score"],reverse=True))

    sq_html = ""
    if sq:
        sq_items = "".join(f'<tr><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0"><strong>{s["name"]}</strong> ({t}) · RSI {s["rsi"]:.0f} · {color_pct(s["change_1d"])}/j</td></tr>' for t,s in list(sq.items())[:8])
        sq_html = section_html("⚡ Compressions Bollinger — rupture imminente", "#7c3aed", sq_items)

    radar_html = ""
    if radar:
        r_rows = radar_html_rows(radar)
        radar_html = section_html("🛰️ Radar — Nouvelles valeurs détectées (trending / presse)", "#0f766e", r_rows,
                                  "Aucune nouvelle valeur détectée aujourd'hui.")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;background:#f9fafb;padding:20px">
  <div style="background:#1e3a5f;color:#fff;padding:18px 24px;border-radius:8px;margin-bottom:20px">
    <div style="font-size:20px;font-weight:bold">📈 Scan Marché PEA</div>
    <div style="font-size:13px;opacity:0.8;margin-top:4px">{now.strftime("%A %d/%m/%Y — %H:%M UTC")} · {len(sig)} valeurs PEA · {len(snp)} hors-PEA</div>
  </div>

  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:20px;overflow-x:auto">
    <div style="font-weight:bold;margin-bottom:8px;color:#374151">Indices</div>
    <table style="border-collapse:collapse;width:100%"><tr>{idx_rows}</tr></table>
  </div>

  {radar_html}
  {section_html("🟢 A — Signaux d'achat forts (PEA)", "#16a34a", ca_rows, "Aucun signal fort aujourd'hui.")}
  {section_html("🟡 B — À surveiller", "#d97706", cb_rows, "Aucune valeur en zone de surveillance.")}
  {section_html("🔵 C — Tendance haussière confirmée", "#2563eb", cc_rows, "Aucune tendance forte.")}
  {section_html("🔴 D — Surachat — prudence", "#dc2626", cd_rows, "Aucune valeur en surachat.")}
  {sq_html}

  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px;margin-bottom:20px">
    <div style="font-weight:bold;margin-bottom:10px;color:#374151">Hors PEA (CTO uniquement)</div>
    {'<div style="margin-bottom:6px;font-size:13px;color:#6b7280">▶ Signaux achat / rebond</div><table style="width:100%;border-collapse:collapse">' + ha_rows + '</table>' if ha_rows else ''}
    {'<div style="margin:10px 0 6px;font-size:13px;color:#6b7280">▶ Tendances haussières</div><table style="width:100%;border-collapse:collapse">' + hc_rows + '</table>' if hc_rows else ''}
    {'<div style="color:#6b7280;font-size:13px">Aucun signal notable hors-PEA.</div>' if not ha_rows and not hc_rows else ''}
  </div>

  <div style="text-align:center;font-size:11px;color:#9ca3af;margin-top:16px">
    Généré automatiquement — données Yahoo Finance · Usage personnel uniquement
  </div>
</body></html>"""

def send_email(html_body, now):
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pwd  = os.environ.get("GMAIL_APP_PASSWORD", "")
    recipient  = os.environ.get("RECIPIENT_EMAIL", gmail_user)
    if not gmail_user or not gmail_pwd:
        print("  [email] GMAIL_USER ou GMAIL_APP_PASSWORD non défini — email ignoré.")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 Scan PEA — {now.strftime('%d/%m/%Y')}"
    msg["From"]    = gmail_user
    msg["To"]      = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(gmail_user, gmail_pwd)
            srv.sendmail(gmail_user, recipient, msg.as_string())
        print(f"  [email] Envoyé à {recipient} ✓")
    except Exception as e:
        print(f"  [email] Erreur : {e}")

if __name__ == "__main__":
    main()
