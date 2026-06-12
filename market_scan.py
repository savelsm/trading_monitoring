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
PEA_ETFS = {
    "PAASI.PA":"Amundi PEA Emerging Asia ESG","PAEEM.PA":"Amundi PEA Emerging Markets",
    "PINR.PA":"Amundi PEA MSCI India","PAEJ.PA":"Amundi PEA Japan",
    "PTPXE.PA":"Amundi PEA Topix","DCAM.PA":"Amundi MSCI Europe",
    "ESE.PA":"BNP Paribas S&P 500 (PEA)","WPEA.PA":"iShares MSCI World Swap PEA",
    "ANX.PA":"Amundi Nasdaq-100 (PEA)","RS2K.PA":"Amundi Russell 2000 (PEA)",
}
NON_PEA = {
    # USA
    "NVDA":"NVIDIA","AAPL":"Apple","MSFT":"Microsoft","AMZN":"Amazon",
    "META":"Meta","GOOGL":"Alphabet","AVGO":"Broadcom",
    "BRK-B":"Berkshire Hathaway","XOM":"ExxonMobil","JPM":"JPMorgan Chase",
    # Japon
    "7203.T":"Toyota","6758.T":"Sony","9984.T":"SoftBank",
    "6861.T":"Keyence","6954.T":"Fanuc","4063.T":"Shin-Etsu Chemical",
    "8306.T":"MUFG","9432.T":"NTT","6501.T":"Hitachi","6902.T":"Denso",
    # Corée du Sud
    "005930.KS":"Samsung Electronics","000660.KS":"SK Hynix",
    "035420.KS":"NAVER","051910.KS":"LG Chem","006400.KS":"Samsung SDI",
    "035720.KS":"Kakao","000270.KS":"Kia Motors",
    # Taiwan
    "TSM":"TSMC","2454.TW":"MediaTek","2317.TW":"Hon Hai (Foxconn)",
    "2308.TW":"Delta Electronics",
    # Chine (cotées Hong Kong)
    "0700.HK":"Tencent","9988.HK":"Alibaba","3690.HK":"Meituan",
    "1810.HK":"Xiaomi","1211.HK":"BYD","9618.HK":"JD.com",
    "2318.HK":"Ping An","0941.HK":"China Mobile",
}
INDICES = {
    "^FCHI":"CAC 40","^STOXX50E":"Euro Stoxx 50","^GDAXI":"DAX 40",
    "^AEX":"AEX (Amsterdam)","^GSPC":"S&P 500","^IXIC":"NASDAQ",
    "^N225":"Nikkei 225","^HSI":"Hang Seng","^KS11":"KOSPI (Corée)",
    "^TWII":"TAIEX (Taiwan)","000001.SS":"Shanghai Composite",
}

STOP_WORDS = {
    "le","la","les","de","du","des","un","une","en","et","à","au","aux","par","sur",
    "pour","avec","dans","que","qui","se","sa","son","ses","ce","cet","cette","ces",
    "il","elle","ils","elles","on","je","tu","nous","vous","plus","the","of","in",
    "a","an","to","for","on","at","by","is","are","was","its","be","as","has","have",
    "it","this","that","with","from","will","after","but","or","new","said","says",
    "may","can","also","than","into","been","about","over","up","out","their",
}
FINANCIAL_TERMS = {
    # Français
    "résultats","bénéfice","dividende","acquisition","fusion","rachat","chiffre",
    "croissance","perte","dette","restructuration","guidance","trimestre","annuel",
    "hausse","baisse","progression","recul","record","objectif","prévision",
    "investissement","contrat","partenariat","cession","introduction","offre",
    # Anglais
    "earnings","profit","revenue","dividend","buyback","merger","outlook","downgrade",
    "upgrade","target","beat","miss","rally","surge","guidance","acquisition",
    "quarterly","annual","growth","loss","debt","restructuring","contract","deal",
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
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg: return "🟢"
    if neg > pos: return "🔴"
    return "⚪"

def extract_keywords(text, n=5):
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', text)
    filtered = [w for w in words if w.lower() not in STOP_WORDS]
    freq = {}
    for w in filtered:
        w_lower = w.lower()
        score = 3 if w_lower in FINANCIAL_TERMS else 1
        freq[w_lower] = freq.get(w_lower, 0) + score
    return sorted(freq, key=freq.get, reverse=True)[:n]

def _finnhub_news(ticker, finnhub_key, days=5):
    """Récupère les actualités Finnhub. Essaie le symbole complet puis sans suffixe."""
    from datetime import timedelta
    now_dt = datetime.now(timezone.utc)
    date_from = (now_dt - timedelta(days=days)).strftime("%Y-%m-%d")
    date_to   = now_dt.strftime("%Y-%m-%d")
    candidates = [ticker]
    if "." in ticker:
        candidates.append(ticker.split(".")[0])
    for sym in candidates:
        try:
            url = (f"https://finnhub.io/api/v1/company-news?symbol={sym}"
                   f"&from={date_from}&to={date_to}&token={finnhub_key}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            if isinstance(data, list) and len(data) > 0:
                return data
        except:
            pass
    return []

def _parse_yf_news_item(item):
    """Parse un article yfinance — compatible ancien et nouveau format."""
    # Nouveau format yfinance >= 0.2.37 : imbriqué sous "content"
    content = item.get("content", {})
    if content:
        title     = content.get("title", "")
        provider  = content.get("provider", {})
        publisher = provider.get("displayName", "") if isinstance(provider, dict) else ""
    else:
        # Ancien format plat
        title     = item.get("title", "")
        publisher = item.get("publisher", "")
    return title.strip(), publisher.strip()

def groq_synthesize(ticker_name, articles, groq_key):
    """Appelle Groq (Llama 3.1 70B) pour synthétiser les articles d'un ticker en 2 phrases."""
    texts = []
    for item in articles[:3]:
        headline = item.get("headline", "")
        summary  = item.get("summary", "")
        if headline:
            texts.append(f"- {headline}" + (f" : {summary[:200]}" if summary else ""))
    if not texts:
        return None
    prompt = (
        f"Tu es analyste financier. Voici des articles récents sur {ticker_name} :\n\n"
        + "\n".join(texts)
        + "\n\nEn 2 phrases maximum, explique la tendance actuelle et pourquoi ce titre "
        "est potentiellement intéressant. Sois factuel et concis. Réponds en français."
    )
    payload = {
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 120,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {groq_key}",
                "content-type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:300]
        print(f" [groq {e.code}: {body}]", end="", flush=True)
        return None
    except Exception as e:
        print(f" [groq ERR: {e}]", end="", flush=True)
        return None

def get_ticker_news(tickers, max_per_ticker=3):
    finnhub_key = os.environ.get("FINNHUB_KEY", "")
    groq_key    = os.environ.get("GROQ_KEY", "")
    sources = []
    if finnhub_key: sources.append("Finnhub")
    if groq_key:    sources.append("Groq synthèse")
    if not finnhub_key: sources.append("yfinance")
    print(f"    [news] Sources : {', '.join(sources)}", end=" ", flush=True)

    news_map = {}
    for t in tickers:
        entries      = []
        raw_finnhub  = []

        # --- Source 1 : Finnhub ---
        if finnhub_key:
            raw_finnhub = _finnhub_news(t, finnhub_key)
            for item in raw_finnhub[:max_per_ticker]:
                headline = item.get("headline", "")
                source   = item.get("source", "Finnhub")
                summary  = item.get("summary", "")
                if headline:
                    icon = sentiment_icon(headline)
                    kw   = extract_keywords(headline + " " + summary)
                    entries.append((f"{icon} {source}", headline[:95], kw))

        # --- Source 2 : yfinance (fallback si Finnhub vide) ---
        if not entries:
            try:
                raw_items = yf.Ticker(t).news or []
                for item in raw_items[:max_per_ticker]:
                    title, publisher = _parse_yf_news_item(item)
                    if title:
                        icon = sentiment_icon(title)
                        kw   = extract_keywords(title)
                        entries.append((f"{icon} {publisher}", title[:95], kw))
            except Exception as e:
                print(f"\n    [news] yf ERR {t}: {e}", end=" ", flush=True)

        # --- Source 3 : Synthèse Groq (si articles disponibles) ---
        synthesis = None
        if groq_key and (raw_finnhub or entries):
            src = raw_finnhub if raw_finnhub else [
                {"headline": e[1], "summary": ""} for e in entries
            ]
            synthesis = groq_synthesize(t, src, groq_key)

        if entries or synthesis:
            news_map[t] = {"articles": entries, "synthesis": synthesis}

    return news_map

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
            except:
                pass
    except Exception as e:
        print(f"  [indices] ERR: {e}")
    return results

def get_yahoo_trending():
    tickers = set()
    EU_SUFFIXES = (".PA",".DE",".AS",".MC",".MI",".CO",".L",".BR",".LS",".SW")
    ASIA_SUFFIXES = (".T",".KS",".TW",".HK",".SS",".SZ")
    US_LARGECAP = {"NVDA","AAPL","MSFT","AMZN","META","GOOGL","TSM","AVGO","JPM","XOM","BRK-B"}
    for market in ["FR","DE","GB","JP","KR","TW","HK"]:
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/trending/{market}"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            result = data.get("finance", {}).get("result") or []
            if not result:
                continue
            quotes = result[0].get("quotes", [])
            for q in quotes:
                sym = q.get("symbol","")
                if any(sym.endswith(s) for s in EU_SUFFIXES+ASIA_SUFFIXES):
                    tickers.add(sym)
                elif "." not in sym and sym in US_LARGECAP:
                    tickers.add(sym)
        except Exception as e:
            print(f"  [trending {market}] {e}")
    return tickers

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

def radar_scan(static_universe):
    print("\n  [Radar] Trending Yahoo Finance...", end=" ", flush=True)
    trending = get_yahoo_trending()
    print(f"{len(trending)} tickers")
    candidates = trending - static_universe
    candidates = {t for t in candidates if not t.startswith("^")}
    if not candidates:
        print("  [Radar] Aucun nouveau ticker.")
        return {}
    print(f"  [Radar] Analyse de {len(candidates)} nouveaux tickers...", end=" ", flush=True)
    results = {}
    try:
        raw = yf.download(list(candidates), period="14mo", auto_adjust=True,
                          group_by="ticker", threads=True, progress=False)
    except Exception as e:
        print(f"ERR:{e}"); return {}
    ok = 0
    for t in candidates:
        try:
            df = raw if len(candidates)==1 else (raw[t] if t in raw.columns.get_level_values(0) else None)
            if df is None or df.empty or len(df) < 60: continue
            s = analyze(t, df)
            if s:
                results[t] = {"name":t, "trending":True, "articles":[], **s}
                ok += 1
        except: pass
    print(f"{ok} analysés")
    if results:
        print(f"  [Radar] News...", end=" ", flush=True)
        radar_news = get_ticker_news(list(results.keys()))
        for t in results:
            entry = radar_news.get(t, {})
            results[t]["articles"]  = entry.get("articles", []) if isinstance(entry, dict) else entry
            results[t]["synthesis"] = entry.get("synthesis") if isinstance(entry, dict) else None
        print(f"{len(radar_news)} avec actualités")
    return results

def color_pct(v):
    if v > 0: return f'<span style="color:#16a34a">▲{v:.1f}%</span>'
    if v < 0: return f'<span style="color:#dc2626">▼{abs(v):.1f}%</span>'
    return f'{v:.1f}%'

def news_html(news_entry):
    """news_entry : dict {"articles": [...], "synthesis": str|None} ou None."""
    if not news_entry: return ""
    html = ""
    synthesis = news_entry.get("synthesis") if isinstance(news_entry, dict) else None
    articles  = news_entry.get("articles", []) if isinstance(news_entry, dict) else news_entry

    # Synthèse Claude en premier
    if synthesis:
        html += (
            f'<div style="margin-top:6px;padding:6px 8px;background:#f0fdf4;border-left:3px solid #16a34a;'
            f'border-radius:3px;font-size:11px;color:#166534">'
            f'🤖 <strong>Synthèse :</strong> {synthesis}</div>'
        )

    # Articles sources
    seen = set()
    for item in articles[:2]:
        src, title = item[0], item[1]
        keywords = item[2] if len(item) > 2 else []
        if title in seen: continue
        seen.add(title)
        kw_html = " ".join(
            f'<span style="background:#e0f2fe;color:#0369a1;border:1px solid #bae6fd;'
            f'padding:1px 5px;border-radius:3px;font-size:10px">{k}</span>'
            for k in keywords[:4]
        )
        html += f'<div style="margin-top:4px;font-size:11px;color:#4b5563">📰 <em>[{src}]</em> {title}</div>'
        if kw_html: html += f'<div style="margin-top:2px">{kw_html}</div>'
    return html

def html_row(name, ticker, s, score_label="", news_map=None):
    indicators = [f'RSI {s["rsi"]:.0f}']
    if s["bull_cross"]: indicators.append("MACD↑")
    elif s["macd"] > s["signal"]: indicators.append("MACD+")
    else: indicators.append("MACD-")
    if s["above_sma200"] is True: indicators.append("▲SMA200")
    if s["vol_ratio"] and s["vol_ratio"] >= 1.5: indicators.append(f'Vol×{s["vol_ratio"]:.1f}')
    if s["squeeze"]: indicators.append("BB squeeze")
    ind_html = " · ".join(indicators)
    score_html = f' <span style="color:#6b7280;font-size:12px">{score_label}</span>' if score_label else ""
    articles = (news_map or {}).get(ticker, [])
    return f"""
    <tr>
      <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">
        <strong>{name}</strong> <span style="color:#6b7280;font-size:12px">({ticker})</span>{score_html}<br>
        <span style="font-size:12px;color:#555">{ind_html}</span>
        {news_html(articles)}
      </td>
      <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap">
        {color_pct(s["change_1d"])}/j<br>
        <span style="font-size:12px">{color_pct(s["change_1mo"])}/mois</span>
      </td>
    </tr>"""

def radar_rows(radar):
    rows = ""
    for t, s in sorted(radar.items(), key=lambda x: x[1]["oversold_score"]+x[1]["trend_score"], reverse=True):
        tags = '<span style="background:#7c3aed;color:#fff;padding:1px 6px;border-radius:3px;font-size:11px">📡 Trending</span>'
        rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">
            <strong>{t}</strong> {tags}<br>
            <span style="font-size:12px;color:#555">RSI {s['rsi']:.0f} · {'MACD↑' if s['bull_cross'] else ('MACD+' if s['macd']>s['signal'] else 'MACD-')} · {'▲SMA200' if s['above_sma200'] else ''}</span>
            {news_html(s.get('articles',[]))}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;white-space:nowrap">
            {color_pct(s['change_1d'])}/j<br>
            <span style="font-size:12px">{color_pct(s['change_1mo'])}/mois</span>
          </td>
        </tr>"""
    return rows

def section_html(title, color, rows_html, empty_msg="Aucun signal détecté."):
    content = rows_html if rows_html else f'<tr><td colspan="2" style="padding:8px 12px;color:#6b7280">{empty_msg}</td></tr>'
    return f"""
    <div style="margin-bottom:24px">
      <div style="background:{color};color:#fff;padding:8px 14px;border-radius:6px 6px 0 0;font-weight:bold">{title}</div>
      <table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 6px 6px">
        {content}
      </table>
    </div>"""

def build_html(now, indices_data, ca, cb, cc, cd, sq, ha, hc, sig, snp, radar, news_map):
    idx_rows = ""
    for name, val in indices_data:
        if val:
            p, c = val
            col = "#16a34a" if c >= 0 else "#dc2626"
            arrow = "▲" if c >= 0 else "▼"
            idx_rows += f'<td style="padding:6px 14px;text-align:center"><div style="font-size:12px;color:#6b7280">{name}</div><div style="font-weight:bold">{p:,.2f}</div><div style="color:{col};font-size:12px">{arrow}{abs(c):.2f}%</div></td>'
        else:
            idx_rows += f'<td style="padding:6px 14px;text-align:center"><div style="font-size:12px;color:#6b7280">{name}</div><div style="color:#9ca3af">n/d</div></td>'

    nm = news_map or {}
    ca_rows = "".join(html_row(s["name"],t,s,f'[Score {s["oversold_score"]}/8]',nm) for t,s in ca.items())
    cb_rows = "".join(html_row(s["name"],t,s,"",nm) for t,s in cb.items())
    cc_rows = "".join(html_row(s["name"],t,s,f'[Trend {s["trend_score"]}/6]',nm) for t,s in cc.items())
    cd_rows = "".join(html_row(s["name"],t,s,"",nm) for t,s in cd.items())
    ha_rows = "".join(html_row(s["name"],t,s,"",nm) for t,s in sorted(ha.items(),key=lambda x:x[1]["oversold_score"],reverse=True))
    hc_rows = "".join(html_row(s["name"],t,s,"",nm) for t,s in sorted(hc.items(),key=lambda x:x[1]["trend_score"],reverse=True))

    sq_html = ""
    if sq:
        sq_items = "".join(f'<tr><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0"><strong>{s["name"]}</strong> ({t}) · RSI {s["rsi"]:.0f} · {color_pct(s["change_1d"])}/j</td></tr>' for t,s in list(sq.items())[:8])
        sq_html = section_html("⚡ Compressions Bollinger — rupture imminente", "#7c3aed", sq_items)

    radar_html = ""
    if radar:
        r_rows = radar_rows(radar)
        radar_html = section_html("🛰️ Radar — Nouvelles valeurs détectées (trending)", "#0f766e", r_rows)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;background:#f9fafb;padding:20px">
  <div style="background:#1e3a5f;color:#fff;padding:18px 24px;border-radius:8px;margin-bottom:20px">
    <div style="font-size:20px;font-weight:bold">📈 Scan Marché PEA</div>
    <div style="font-size:13px;opacity:0.8;margin-top:4px">{now.strftime("%A %d/%m/%Y — %H:%M UTC")} · {len(sig)} valeurs PEA · {len(snp)} hors-PEA/Asie</div>
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
    <div style="font-weight:bold;margin-bottom:10px;color:#374151">Hors PEA — CTO (USA + Asie)</div>
    {'<div style="margin-bottom:6px;font-size:13px;color:#6b7280">▶ Signaux achat / rebond</div><table style="width:100%;border-collapse:collapse">' + ha_rows + '</table>' if ha_rows else ''}
    {'<div style="margin:10px 0 6px;font-size:13px;color:#6b7280">▶ Tendances haussières</div><table style="width:100%;border-collapse:collapse">' + hc_rows + '</table>' if hc_rows else ''}
    {'<div style="color:#6b7280;font-size:13px">Aucun signal notable hors-PEA.</div>' if not ha_rows and not hc_rows else ''}
  </div>

  <div style="text-align:center;font-size:11px;color:#9ca3af;margin-top:16px">
    Généré automatiquement — données Yahoo Finance · Usage personnel uniquement
  </div>
</body></html>"""

def send_email(html_body, now):
    gmail_user = os.environ.get("GMAIL_USER","")
    gmail_pwd  = os.environ.get("GMAIL_APP_PASSWORD","")
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
    print(f"  Univers : CAC40 + DAX + EU + ETFs PEA + Hors-PEA/Asie ({sum(map(len,[CAC40,DAX,OTHER_EU,PEA_ETFS,NON_PEA]))} valeurs)")
    print("="*W)

    sec("CONTEXTE INDICES", "─")
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

    print()
    all_pea = {**CAC40,**DAX,**OTHER_EU,**PEA_ETFS}
    dpea  = dl(list(CAC40.keys()),    label="CAC 40")
    ddax  = dl(list(DAX.keys()),      label="DAX")
    deu   = dl(list(OTHER_EU.keys()), label="Autres EU")
    detf  = dl(list(PEA_ETFS.keys()), label="ETFs PEA")
    dnpea = dl(list(NON_PEA.keys()),  label="Hors-PEA/Asie")
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
    total_ok = len(sig) + len(snp)
    total_uni = sum(map(len, [CAC40, DAX, OTHER_EU, PEA_ETFS, NON_PEA]))
    echecs = total_uni - total_ok
    print(f"  Valeurs analysées : {len(sig)} PEA + {len(snp)} hors-PEA/Asie = {total_ok}"
          + (f" ({echecs} échec(s) téléchargement)" if echecs else ""))
    print(f"  A (achat fort) : {len(ca)}  |  B (surveiller) : {len(cb)}  |  C (tendance) : {len(cc)}  |  D (surachat) : {len(cd)}")
    print(f"  Compressions BB : {len(sq)}")
    print("="*W)

    # News yfinance pour les valeurs signalées
    signal_tickers = list(set(list(ca)+list(cb)+list(cc)+list(ha)+list(hc)))
    print(f"\n  [News] Récupération pour {len(signal_tickers)} valeurs...", end=" ", flush=True)
    news_map = get_ticker_news(signal_tickers)
    print(f"{len(news_map)} avec actualités")

    # Radar trending
    static_universe = set({**CAC40,**DAX,**OTHER_EU,**PEA_ETFS,**NON_PEA}.keys())
    radar = radar_scan(static_universe)

    html = build_html(now, indices_data, ca, cb, cc, cd, sq, ha, hc, sig, snp, radar, news_map)
    send_email(html, now)

if __name__ == "__main__":
    main()
