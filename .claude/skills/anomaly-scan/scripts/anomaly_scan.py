#!/usr/bin/env python3
"""Deterministic pass for /anomaly-scan.

Three detectors, all numeric or file-based, no judgement:
  1. Price/volume anomalies for every watchlist ticker (Yahoo chart endpoint,
     falls back to the dashboard's cached closes when offline).
  2. Document pairs: for each watchlist entity, the newest and previous Source
     Note that mention it, so the agent can diff their language.
  3. Social attention: mentions per ticker in 01-Raw/social/ this window vs the
     previous window of the same length (only if that folder exists).

The agent explains; this script only measures. Thresholds are flags for
"look here", not trading signals.

Usage:
  py .agents/skills/anomaly-scan/scripts/anomaly_scan.py
  py .agents/skills/anomaly-scan/scripts/anomaly_scan.py --offline --json
  py .agents/skills/anomaly-scan/scripts/anomaly_scan.py --tickers KCE DELTA --z 2 --vol 2.5
"""
import argparse
import datetime as dt
import json
import re
import statistics as st
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
UA = "llm-wiki-anomaly-scan/0.1 (personal research)"


def find_vault(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "02-Wiki").is_dir() and (p / "01-Raw").is_dir():
            return p
    sys.exit("Could not find the vault root (a folder containing 02-Wiki and 01-Raw).")


def read_note(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = FRONTMATTER.match(text)
    if not m:
        return {}, text
    try:
        return (yaml.safe_load(m.group(1)) or {}), text[m.end():]
    except yaml.YAMLError:
        return {}, text[m.end():]


def to_date(value):
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def file_date(path: Path, fm: dict):
    for key in ("published", "created", "date"):
        d = to_date(fm.get(key))
        if d:
            return d
    m = re.match(r"(\d{4})(\d{2})(\d{2})", path.name)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


# ---------- 1. price / volume ----------

def fetch_yahoo(symbol: str, rng: str):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
           f"?range={rng}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        payload = json.load(r)
    res = payload["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    rows = []
    for ts, c, v in zip(res.get("timestamp", []), q.get("close", []), q.get("volume", [])):
        if c is not None:
            rows.append({"date": dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat(), "close": c, "volume": v})
    return rows


def load_cache(vault: Path):
    path = vault / "dashboard" / "data" / "market-data.json"
    if not path.exists():
        return {}, None
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for ticker, q in (data.get("quotes") or {}).items():
        out[ticker] = [{"date": p["time"][:10], "close": p["close"], "volume": None} for p in q.get("points", [])]
    return out, data.get("fetchedAt")


def price_metrics(rows, lookback=60, vol_window=20, mom_window=20):
    closes = [r["close"] for r in rows]
    if len(closes) < 25:
        return None
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    hist = rets[-(lookback + 1):-1]
    sd = st.pstdev(hist) if len(hist) > 5 else None
    last_ret = rets[-1]
    vols = [r["volume"] for r in rows if r["volume"] is not None]
    vol_ratio = None
    if len(vols) > vol_window and vols[-1] is not None:
        base = [v for v in vols[-(vol_window + 1):-1] if v]
        if base:
            vol_ratio = vols[-1] / (sum(base) / len(base))
    mom = closes[-1] / closes[-(mom_window + 1)] - 1 if len(closes) > mom_window else None
    hi, lo = max(closes), min(closes)
    return {
        "last_date": rows[-1]["date"],
        "close": closes[-1],
        "ret_1d_pct": round(last_ret * 100, 2),
        "z_1d": round(last_ret / sd, 2) if sd else None,
        "vol_ratio_20d": round(vol_ratio, 2) if vol_ratio is not None else None,
        "ret_20d_pct": round(mom * 100, 2) if mom is not None else None,
        "from_high_pct": round((closes[-1] / hi - 1) * 100, 2),
        "from_low_pct": round((closes[-1] / lo - 1) * 100, 2),
        "is_new_high": closes[-1] >= hi,
        "is_new_low": closes[-1] <= lo,
        "points": len(closes),
    }


# ---------- 2. document pairs ----------

def doc_pairs(vault: Path, stocks, since: dt.date):
    sources = []
    for path in (vault / "02-Wiki" / "Sources").glob("*.md"):
        if path.name == "README.md":
            continue
        fm, body = read_note(path)
        if fm.get("type") != "source-note":
            continue
        links = {Path(t).stem for t in WIKILINK.findall(body)}
        sources.append({"path": path.relative_to(vault).as_posix(), "date": file_date(path, fm),
                        "created": to_date(fm.get("created")), "links": links, "body": body})
    pairs = []
    for s in stocks:
        ent = s.get("entity", "")
        names = {n for n in (ent, s.get("ticker", "")) if n and len(n) >= 3}
        hits = [x for x in sources if ent in x["links"]
                or any(re.search(rf"(?<!\w){re.escape(n)}(?!\w)", x["body"]) for n in names)]
        hits.sort(key=lambda x: (x["date"] or dt.date.min, x["path"]))
        newest = hits[-1] if hits else None
        prev = hits[-2] if len(hits) > 1 else None
        pairs.append({
            "ticker": s.get("ticker"), "entity": ent, "count": len(hits),
            "newest": newest["path"] if newest else None,
            "newest_date": newest["date"].isoformat() if newest and newest["date"] else None,
            "newest_in_window": bool(newest and newest["created"] and newest["created"] >= since),
            "previous": prev["path"] if prev else None,
            "previous_date": prev["date"].isoformat() if prev and prev["date"] else None,
        })
    return pairs


# ---------- 3. social attention ----------

def social_counts(vault: Path, stocks, until: dt.date, days: int):
    folder = vault / "01-Raw" / "social"
    if not folder.is_dir():
        return None
    cur_start = until - dt.timedelta(days=days)
    prev_start = cur_start - dt.timedelta(days=days)
    counts = {s["ticker"]: {"current": 0, "previous": 0} for s in stocks}
    for path in folder.rglob("*.md"):
        fm, body = read_note(path)
        d = file_date(path, fm)
        if not d:
            continue
        bucket = "current" if cur_start < d <= until else "previous" if prev_start < d <= cur_start else None
        if not bucket:
            continue
        for s in stocks:
            pats = [rf"\${re.escape(s['ticker'])}\b", rf"(?<!\w){re.escape(s['ticker'])}(?!\w)"]
            if s.get("entity"):
                pats.append(re.escape(s["entity"]))
            n = sum(len(re.findall(p, body)) for p in pats)
            counts[s["ticker"]][bucket] += n
    return {"window_days": days, "counts": counts}


def main():
    ap = argparse.ArgumentParser(description="Numeric + document anomaly pass for /anomaly-scan")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--tickers", nargs="*", help="Limit to these watchlist tickers")
    ap.add_argument("--offline", action="store_true", help="Use dashboard/data/market-data.json only")
    ap.add_argument("--range", default="6mo", help="Yahoo range (default 6mo)")
    ap.add_argument("--z", type=float, default=2.5, help="Flag |1-day return z-score| >= this")
    ap.add_argument("--vol", type=float, default=3.0, help="Flag volume >= this multiple of 20-day average")
    ap.add_argument("--rel", type=float, default=10.0, help="Flag 20-day return that differs from the watchlist median by >= this many points")
    ap.add_argument("--days", type=int, default=7, help="Window for 'new' documents and social counts")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).resolve() if args.vault else find_vault(Path(__file__).resolve())
    wl_path = vault / "dashboard" / "config" / "watchlist.json"
    if not wl_path.exists():
        sys.exit(f"Watchlist not found: {wl_path}")
    stocks = json.loads(wl_path.read_text(encoding="utf-8"))["stocks"]
    if args.tickers:
        wanted = {t.upper() for t in args.tickers}
        stocks = [s for s in stocks if s.get("ticker", "").upper() in wanted]
    today = dt.date.today()
    since = today - dt.timedelta(days=args.days)

    cache, cache_time = load_cache(vault)
    prices, data_source = {}, {}
    for s in stocks:
        sym, t = s.get("marketSymbol"), s.get("ticker")
        if not sym:
            data_source[t] = "no market symbol (private or unlisted)"
            continue
        rows = None
        if not args.offline:
            try:
                rows = fetch_yahoo(sym, args.range)
                data_source[t] = "Yahoo chart (with volume)"
            except Exception as e:  # network, rate limit, format change
                data_source[t] = f"Yahoo failed ({type(e).__name__}); "
        if rows is None:
            rows = cache.get(t)
            data_source[t] = data_source.get(t, "") + (f"dashboard cache {cache_time} (closes only)" if rows else "no data")
        m = price_metrics(rows) if rows else None
        if m:
            prices[t] = m

    moms = [m["ret_20d_pct"] for m in prices.values() if m.get("ret_20d_pct") is not None]
    median_mom = st.median(moms) if moms else None
    flags = []
    for t, m in prices.items():
        reasons = []
        if m["z_1d"] is not None and abs(m["z_1d"]) >= args.z:
            reasons.append(f"1-day move {m['ret_1d_pct']}% = {m['z_1d']}σ of last 60 days")
        if m["vol_ratio_20d"] is not None and m["vol_ratio_20d"] >= args.vol:
            reasons.append(f"volume {m['vol_ratio_20d']}× its 20-day average")
        if median_mom is not None and m["ret_20d_pct"] is not None and len(moms) >= 3:
            gap = m["ret_20d_pct"] - median_mom
            if abs(gap) >= args.rel:
                reasons.append(f"20-day return {m['ret_20d_pct']}% vs watchlist median {round(median_mom, 2)}% (gap {round(gap, 2)} pts)")
        if m["is_new_high"]:
            reasons.append(f"close at {args.range} high")
        if m["is_new_low"]:
            reasons.append(f"close at {args.range} low")
        m["flags"] = reasons
        if reasons:
            flags.append(t)

    pairs = doc_pairs(vault, stocks, since)
    social = social_counts(vault, stocks, today, args.days)

    result = {"vault": str(vault), "run_date": today.isoformat(), "thresholds": {"z": args.z, "vol": args.vol, "rel": args.rel},
              "data_source": data_source, "prices": prices, "median_ret_20d_pct": median_mom,
              "flagged_tickers": flags, "doc_pairs": pairs, "social": social}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"# Anomaly scan {today} (thresholds: |z|≥{args.z}, volume≥{args.vol}×, 20d gap≥{args.rel} pts)\n")
    print("## 1. Price and volume\n")
    print("| Ticker | Last | Close | 1d % | z | Vol ×20d | 20d % | From high % | Flags |")
    print("|---|---|---|---|---|---|---|---|---|")
    for s in stocks:
        t = s.get("ticker")
        m = prices.get(t)
        if not m:
            print(f"| {t} | - | - | - | - | - | - | - | {data_source.get(t, 'no data')} |")
            continue
        fl = "; ".join(m["flags"]) or "-"
        vr = m["vol_ratio_20d"] if m["vol_ratio_20d"] is not None else "n/a"
        print(f"| {t} | {m['last_date']} | {m['close']:.2f} | {m['ret_1d_pct']} | {m['z_1d']} | {vr} | {m['ret_20d_pct']} | {m['from_high_pct']} | {fl} |")
    print("\nData source per ticker: " + "; ".join(f"{k}: {v}" for k, v in data_source.items()))
    print("\n## 2. Document pairs to diff (newest vs previous Source Note per entity)\n")
    for p in pairs:
        if not p["newest"]:
            print(f"- {p['ticker']} ({p['entity']}): no Source Notes yet")
            continue
        tag = " · NEW in window" if p["newest_in_window"] else ""
        prev = f"`{p['previous']}` ({p['previous_date']})" if p["previous"] else "none (only one source; no diff possible)"
        print(f"- {p['ticker']}: newest `{p['newest']}` ({p['newest_date']}){tag} · previous {prev}")
    print("\n## 3. Social attention\n")
    if social is None:
        print("01-Raw/social/ does not exist yet; skipped.")
    else:
        print(f"Mentions in the last {social['window_days']} days vs the {social['window_days']} days before:")
        for t, c in social["counts"].items():
            print(f"- {t}: {c['current']} (previous {c['previous']})")


if __name__ == "__main__":
    main()
