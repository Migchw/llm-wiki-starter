#!/usr/bin/env python3
"""Deterministic pass for /earnings-scorecard.

Pulls earnings data from yfinance for every watchlist ticker (or --tickers),
computes beat/miss, surprise, YoY and the price reaction around each report,
and writes dashboard/data/earnings-data.json for the dashboard.

yfinance gives EPS actual-vs-consensus history, current/next-quarter consensus
for EPS and revenue (with analyst count and range) and quarterly statements.
It does NOT keep revenue-consensus history, so every run snapshots the
consensus into dashboard/data/consensus-history.json. After a report, revenue
surprise is computed against the last snapshot taken before the report date.
Segment figures and non-GAAP items (gross billings, EBITDA consensus) are not
available here; they come from the press release via /ingest.

Usage:
  py .agents/skills/earnings-scorecard/scripts/earnings_scorecard.py
  py .agents/skills/earnings-scorecard/scripts/earnings_scorecard.py --tickers SNX KCE
  py .agents/skills/earnings-scorecard/scripts/earnings_scorecard.py --actual "SNX:2026-09-24:revenue=21.56e9"
"""
import argparse
import datetime as dt
import json
import math
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

try:
    import yfinance as yf
except ImportError:
    sys.exit("yfinance is not installed. Run: py -m pip install yfinance")


def find_vault(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "02-Wiki").is_dir() and (p / "dashboard").is_dir():
            return p
    sys.exit("Could not find the vault root (a folder containing 02-Wiki and dashboard).")


def num(v):
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def pct(a, b):
    a, b = num(a), num(b)
    if a is None or b is None or b == 0:
        return None
    return round((a / abs(b) - 1) * 100 if b > 0 else (a - b) / abs(b) * 100, 2)


def row(df, name, col):
    try:
        return num(df.loc[name, col])
    except Exception:
        return None


def period_table(df):
    """Consensus tables (earnings_estimate / revenue_estimate) -> dict keyed by period."""
    out = {}
    if df is None or getattr(df, "empty", True):
        return out
    for period, r in df.iterrows():
        out[str(period)] = {k: num(r.get(k)) for k in ("avg", "low", "high", "numberOfAnalysts", "yearAgoEps", "yearAgoRevenue", "growth")}
    return out


def reaction(prices, report_ts):
    """Return % change on the reaction day and 5 trading days later vs the last close before the report."""
    if prices is None or prices.empty:
        return None
    closes = prices["Close"].dropna()
    idx = closes.index
    local = report_ts.tz_convert(idx.tz) if getattr(report_ts, "tzinfo", None) and idx.tz is not None else report_ts
    after_close = local.hour >= 16
    day = local.normalize()
    pre = closes[idx < day + dt.timedelta(days=1)] if after_close else closes[idx < day]
    post = closes[idx >= day + dt.timedelta(days=1)] if after_close else closes[idx >= day]
    if pre.empty or post.empty:
        return None
    base = pre.iloc[-1]
    d0 = post.iloc[0]
    d5 = post.iloc[5] if len(post) > 5 else None
    return {
        "intraday": post.index[0].date() == dt.date.today(),
        "reaction_day": str(post.index[0].date()),
        "d0_pct": round((d0 / base - 1) * 100, 2),
        "d5_pct": round((d5 / base - 1) * 100, 2) if d5 is not None else None,
    }


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default


def parse_actuals(items):
    """'SNX:2026-09-24:revenue=21.56e9,eps=5.68' -> {('SNX','2026-09-24'): {...}}"""
    out = {}
    for item in items or []:
        try:
            ticker, date, pairs = item.split(":", 2)
            vals = {}
            for pair in pairs.split(","):
                k, v = pair.split("=")
                vals[k.strip()] = float(v)
            out[(ticker.upper(), date)] = vals
        except ValueError:
            sys.exit(f"Bad --actual value: {item!r}. Use TICKER:YYYY-MM-DD:revenue=21.56e9,eps=5.68")
    return out


def parse_guidance(items):
    """'SNX:2026-09-24:revenue=21.8e9-22.6e9,eps=5.65-6.15' -> {('SNX','2026-09-24'): {...}}"""
    out = {}
    for item in items or []:
        try:
            ticker, date, pairs = item.split(":", 2)
            vals = {"source": "manual (press release outlook)"}
            for pair in pairs.split(","):
                k, rng = pair.split("=")
                lo, hi = (float(x) for x in rng.split("~" if "~" in rng else "-", 1)) if ("-" in rng.lstrip("-") or "~" in rng) else (float(rng), float(rng))
                vals[k.strip()] = {"low": lo, "high": hi, "mid": round((lo + hi) / 2, 6)}
            out[(ticker.upper(), date)] = vals
        except ValueError:
            sys.exit(f"Bad --guidance value: {item!r}. Use TICKER:YYYY-MM-DD:revenue=21.8e9-22.6e9,eps=5.65-6.15")
    return out


def scorecard(stock, history, manual, guidance, today):
    ticker, symbol = stock["ticker"], stock["marketSymbol"]
    t = yf.Ticker(symbol)
    flags, errors = [], []

    def safe(fn, label):
        try:
            return fn()
        except Exception as e:  # yfinance raises many kinds when Yahoo changes a field
            errors.append(f"{label}: {type(e).__name__}")
            return None

    dates = safe(lambda: t.get_earnings_dates(limit=12), "earnings_dates")
    eps_est = period_table(safe(lambda: t.earnings_estimate, "earnings_estimate"))
    rev_est = period_table(safe(lambda: t.revenue_estimate, "revenue_estimate"))
    stmt = safe(lambda: t.quarterly_income_stmt, "quarterly_income_stmt")
    prices = safe(lambda: t.history(period="3y", interval="1d", auto_adjust=False), "history")

    # --- EPS history with price reaction
    eps_hist = []
    if dates is not None and not dates.empty:
        for ts, r in dates.sort_index().iterrows():
            est, act = num(r.get("EPS Estimate")), num(r.get("Reported EPS"))
            entry = {"date": str(ts.date()), "eps_estimate": est, "eps_actual": act,
                     "surprise_pct": num(r.get("Surprise(%)")), "upcoming": act is None}
            if act is not None:
                sp = entry["surprise_pct"]
                if sp is not None:
                    entry["beat"] = "beat" if sp > 0.5 else "miss" if sp < -0.5 else "in line"
                else:
                    entry["beat"] = None if est is None else ("beat" if act > est else "miss" if act < est else "in line")
                entry["reaction"] = reaction(prices, ts)
            eps_hist.append(entry)
    reported = [e for e in eps_hist if not e["upcoming"]]
    upcoming = [e for e in eps_hist if e["upcoming"]]
    window = reported[-8:]
    beats = [e for e in window if e.get("beat") == "beat"]
    surprises = [e["surprise_pct"] for e in window if e["surprise_pct"] is not None]
    reactions = [e["reaction"]["d0_pct"] for e in window if e.get("reaction")]
    stats = {
        "quarters": len(window),
        "beats": len(beats),
        "beat_rate_pct": round(len(beats) / len(window) * 100, 1) if window else None,
        "avg_surprise_pct": round(sum(surprises) / len(surprises), 2) if surprises else None,
        "avg_reaction_pct": round(sum(reactions) / len(reactions), 2) if reactions else None,
    }

    # --- statements (latest 5 quarters)
    quarters = []
    if stmt is not None and not stmt.empty:
        cols = list(stmt.columns)[:5]
        for c in cols:
            rev, op, gp, ni = (row(stmt, n, c) for n in ("Total Revenue", "Operating Income", "Gross Profit", "Net Income"))
            quarters.append({
                "period_end": str(c.date()), "revenue": rev, "net_income": ni,
                "eps_diluted": row(stmt, "Diluted EPS", c), "ebitda": row(stmt, "EBITDA", c),
                "gross_margin_pct": round(gp / rev * 100, 2) if gp and rev else None,
                "operating_margin_pct": round(op / rev * 100, 2) if op and rev else None,
            })
        # YoY needs the same quarter a year earlier; pull it from the full table when available
        allcols = list(stmt.columns)
        for q in quarters:
            end = dt.date.fromisoformat(q["period_end"])
            prior = [c for c in allcols if abs((end - c.date()).days - 365) <= 20]
            if prior:
                q["revenue_yoy_pct"] = pct(q["revenue"], row(stmt, "Total Revenue", prior[0]))
                q["net_income_yoy_pct"] = pct(q["net_income"], row(stmt, "Net Income", prior[0]))
                q["eps_yoy_pct"] = pct(q["eps_diluted"], row(stmt, "Diluted EPS", prior[0]))

    # --- consensus snapshot (so revenue surprise can be computed after the report)
    snap = {
        "date": today.isoformat(),
        "q0": {"eps": eps_est.get("0q", {}).get("avg"), "revenue": rev_est.get("0q", {}).get("avg"),
               "year_ago_revenue": rev_est.get("0q", {}).get("yearAgoRevenue"), "year_ago_eps": eps_est.get("0q", {}).get("yearAgoEps")},
        "q1": {"eps": eps_est.get("+1q", {}).get("avg"), "revenue": rev_est.get("+1q", {}).get("avg")},
    }
    h = history.setdefault(ticker, {"snapshots": [], "actuals": {}})
    h["snapshots"] = [s for s in h["snapshots"] if s["date"] != snap["date"]] + [snap]
    h["snapshots"] = h["snapshots"][-120:]

    # --- latest report: EPS from earnings_dates; revenue from statements, manual actuals, or pending
    latest = None
    if reported:
        last = reported[-1]
        rdate = dt.date.fromisoformat(last["date"])
        before = [s for s in h["snapshots"] if dt.date.fromisoformat(s["date"]) < rdate]
        # If no snapshot predates the report, the current 0q still refers to the reported quarter
        # when its year-ago revenue matches the statement quarter one year before the report.
        rev_consensus, rev_consensus_src = None, None
        if before:
            rev_consensus, rev_consensus_src = before[-1]["q0"]["revenue"], f"snapshot {before[-1]['date']}"
        elif (today - rdate).days <= 10 and rev_est.get("0q", {}).get("avg"):
            rev_consensus, rev_consensus_src = rev_est["0q"]["avg"], f"yfinance 0q on {today} (quarter just reported, not yet rolled)"
        man = manual.get((ticker, last["date"])) or h["actuals"].get(last["date"])
        if manual.get((ticker, last["date"])):
            h["actuals"][last["date"]] = dict(manual[(ticker, last["date"])], source="manual (press release)")
        stmt_q = quarters[0] if quarters and dt.date.fromisoformat(quarters[0]["period_end"]) > rdate - dt.timedelta(days=75) else None
        rev_actual, rev_src = None, None
        if stmt_q:
            rev_actual, rev_src = stmt_q["revenue"], f"yfinance statement {stmt_q['period_end']}"
        elif man and man.get("revenue"):
            rev_actual, rev_src = man["revenue"], man.get("source", "manual (press release)")
        else:
            flags.append("revenue for the latest report is not in yfinance statements yet (statement lag) — add it with --actual from the press release")
        year_ago_rev = rev_est.get("0q", {}).get("yearAgoRevenue") if rev_consensus_src and "0q" in rev_consensus_src else (before[-1]["q0"].get("year_ago_revenue") if before else None)
        latest = {
            "date": last["date"],
            "eps": {"actual": last["eps_actual"], "consensus": last["eps_estimate"], "surprise_pct": last["surprise_pct"], "beat": last.get("beat"),
                    "year_ago": eps_est.get("0q", {}).get("yearAgoEps") if rev_consensus_src and "0q" in rev_consensus_src else None},
            "revenue": {"actual": rev_actual, "actual_source": rev_src, "consensus": rev_consensus, "consensus_source": rev_consensus_src,
                        "surprise_pct": pct(rev_actual, rev_consensus),
                        "beat": None if rev_actual is None or rev_consensus is None else ("beat" if rev_actual > rev_consensus else "miss"),
                        "year_ago": year_ago_rev,
                        "yoy_pct": stmt_q.get("revenue_yoy_pct") if stmt_q else pct(rev_actual, year_ago_rev)},
            "reaction": last.get("reaction"),
        }
        if latest["eps"]["year_ago"] is not None:
            latest["eps"]["yoy_pct"] = pct(last["eps_actual"], latest["eps"]["year_ago"])
        elif stmt_q and stmt_q.get("eps_yoy_pct") is not None:
            # Statement EPS is GAAP; the headline EPS may be adjusted, so label the basis.
            latest["eps"]["yoy_pct"] = stmt_q["eps_yoy_pct"]
            latest["eps"]["yoy_basis"] = "GAAP diluted EPS from statements"

    # --- company guidance for the next quarter (recorded from the press release with --guidance)
    guide = None
    if latest:
        g = guidance.get((ticker, latest["date"]))
        if g:
            h.setdefault("guidance", {})[latest["date"]] = g
        guide = h.get("guidance", {}).get(latest["date"])

    # --- forward consensus
    def fwd(period):
        e, r = eps_est.get(period, {}), rev_est.get(period, {})
        return {"eps": e.get("avg"), "eps_low": e.get("low"), "eps_high": e.get("high"), "eps_analysts": e.get("numberOfAnalysts"),
                "eps_growth_pct": round(e["growth"] * 100, 2) if e.get("growth") is not None else None,
                "revenue": r.get("avg"), "revenue_low": r.get("low"), "revenue_high": r.get("high"),
                "revenue_analysts": r.get("numberOfAnalysts"),
                "revenue_growth_pct": round(r["growth"] * 100, 2) if r.get("growth") is not None else None}

    # If the latest report used the current 0q, the next quarter to watch is +1q
    next_key = "+1q" if latest and latest["revenue"]["consensus_source"] and "0q" in latest["revenue"]["consensus_source"] else "0q"
    forward = {"next_quarter": fwd(next_key), "next_quarter_key": next_key, "this_year": fwd("0y"), "next_year": fwd("+1y")}
    nq = forward["next_quarter"]
    if guide:
        cmp = {}
        for k in ("revenue", "eps"):
            if k in guide:
                mid = guide[k]["mid"]
                cmp[k] = dict(guide[k], consensus=nq.get(k), vs_consensus_pct=pct(mid, nq.get(k)),
                              verdict=None if nq.get(k) is None else ("above" if mid > nq[k] else "below"))
        forward["guidance"] = {"source": guide.get("source", "press release"), **cmp}
    if (nq.get("eps_analysts") or 0) < 3 and (nq.get("revenue_analysts") or 0) < 3:
        flags.append("thin coverage: fewer than 3 analysts on next-quarter consensus — treat surprises as noisy")

    return {
        "ticker": ticker, "symbol": symbol, "currency": stock.get("currency"), "entity": stock.get("entity"),
        "next_report": upcoming[0]["date"] if upcoming else None,
        "latest": latest, "beat_stats": stats, "eps_history": reported[-8:], "quarters": quarters,
        "forward": forward, "flags": flags, "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser(description="Earnings beat/miss scorecard from yfinance for /earnings-scorecard")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--tickers", nargs="*", help="Watchlist tickers to include (default: all with a market symbol)")
    ap.add_argument("--actual", action="append", help="Record a reported figure from the press release: TICKER:YYYY-MM-DD:revenue=21.56e9,eps=5.68")
    ap.add_argument("--guidance", action="append", help="Record next-quarter outlook from the press release: TICKER:YYYY-MM-DD:revenue=21.8e9-22.6e9,eps=5.65-6.15")
    ap.add_argument("--json", action="store_true", help="Print the JSON result instead of the Markdown summary")
    args = ap.parse_args()

    vault = Path(args.vault).resolve() if args.vault else find_vault(Path(__file__).resolve())
    dash = vault / "dashboard"
    stocks = json.loads((dash / "config" / "watchlist.json").read_text(encoding="utf-8"))["stocks"]
    stocks = [s for s in stocks if s.get("marketSymbol")]
    if args.tickers:
        wanted = {x.upper() for x in args.tickers}
        stocks = [s for s in stocks if s["ticker"].upper() in wanted]
    today = dt.date.today()
    hist_path = dash / "data" / "consensus-history.json"
    history = load_json(hist_path, {})
    manual = parse_actuals(args.actual)
    guidance = parse_guidance(args.guidance)

    out_path = dash / "data" / "earnings-data.json"
    existing = load_json(out_path, {"scorecards": {}})
    cards = existing.get("scorecards", {})
    for s in stocks:
        try:
            cards[s["ticker"]] = scorecard(s, history, manual, guidance, today)
        except Exception as e:
            cards[s["ticker"]] = {"ticker": s["ticker"], "symbol": s["marketSymbol"], "errors": [f"{type(e).__name__}: {e}"]}

    result = {"provider": "yfinance (Yahoo Finance consensus and statements)", "fetchedAt": dt.datetime.now(dt.timezone.utc).isoformat(), "scorecards": cards}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hist_path.write_text(json.dumps(history, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    def big(v):
        v = num(v)
        if v is None:
            return "n/a"
        return f"{v / 1e9:.2f}B" if abs(v) >= 1e9 else f"{v / 1e6:.1f}M" if abs(v) >= 1e6 else f"{v:.2f}"

    print(f"# Earnings scorecard {today} · {result['provider']}\n")
    for s in stocks:
        c = cards.get(s["ticker"], {})
        print(f"## {s['ticker']} ({s['marketSymbol']})")
        if c.get("errors"):
            print(f"errors: {'; '.join(c['errors'])}")
        L = c.get("latest")
        if L:
            e, r = L["eps"], L["revenue"]
            print(f"Latest report {L['date']}: EPS {e['actual']} vs {e['consensus']} ({e['beat']}, {e['surprise_pct']}%)"
                  f" · Revenue {big(r['actual'])} vs {big(r['consensus'])} ({r['beat'] or 'n/a'}, {r['surprise_pct']}%) · YoY rev {r['yoy_pct']}%")
            if L.get("reaction"):
                tag = " (intraday, not final)" if L["reaction"].get("intraday") else ""
                print(f"Price reaction: day {L['reaction']['d0_pct']}%{tag} · +5d {L['reaction']['d5_pct']}%")
        b = c.get("beat_stats") or {}
        print(f"EPS beat rate {b.get('beat_rate_pct')}% over {b.get('quarters')} quarters · avg surprise {b.get('avg_surprise_pct')}%")
        f = (c.get("forward") or {}).get("next_quarter") or {}
        print(f"Next quarter consensus: EPS {f.get('eps')} ({f.get('eps_analysts')} analysts) · revenue {big(f.get('revenue'))} ({f.get('revenue_analysts')} analysts) · next report {c.get('next_report')}")
        g = (c.get("forward") or {}).get("guidance")
        if g:
            for k in ("revenue", "eps"):
                if k in g:
                    print(f"Guidance {k}: {big(g[k]['low'])}–{big(g[k]['high'])} (mid {big(g[k]['mid'])}) vs consensus {big(g[k]['consensus'])} → {g[k]['verdict']} by {g[k]['vs_consensus_pct']}%")
        for fl in c.get("flags", []):
            print(f"! {fl}")
        print()
    print(f"Wrote {out_path.relative_to(vault).as_posix()} and {hist_path.relative_to(vault).as_posix()}")


if __name__ == "__main__":
    main()
