#!/usr/bin/env python3
"""Validate the sector JSON files in data/ before publishing.

Usage:
    python3 scripts/validate_data.py                 # check every file
    python3 scripts/validate_data.py --quarter Q2FY27   # also enforce the Q2 schema additions
    python3 scripts/validate_data.py --quarter Q2FY27 --sector co-working

Errors make the script exit with status 1. Warnings are printed but do not fail.
With --quarter, problems in older quarters' entries are reported as warnings only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INDEX = ROOT / "index.html"

QUARTER_RE = re.compile(r"^Q([1-4])FY(\d{2})$")
TONES = {"Strongly Bullish", "Bullish", "Constructive", "Cautiously Optimistic", "Cautious", "Bearish"}
GT_STATUSES = {"met", "exceeded", "partial", "missed"}
REQUIRED = ["quarter", "hasNumericGuidance", "tone", "metrics", "fyPerformance", "highlights", "asOf"]


def quarter_key(q):
    m = QUARTER_RE.match(q or "")
    return (int(m.group(2)), int(m.group(1))) if m else None


def data_files_from_index():
    """Read the DATA_FILES list from index.html so the check matches what the site loads."""
    text = INDEX.read_text(encoding="utf-8")
    m = re.search(r"const DATA_FILES = \[(.*?)\];", text, re.S)
    if not m:
        return None
    return re.findall(r"'([^']+)'", m.group(1))


def check_new_fields(e, where, err):
    wc = e.get("whatChanged")
    if not isinstance(wc, str) or not wc.strip():
        err(f"{where}: missing whatChanged (one sentence)")
    risks = e.get("risks")
    if not isinstance(risks, list) or not 2 <= len(risks) <= 3 or not all(isinstance(r, str) and r.strip() for r in risks):
        err(f"{where}: risks must be a list of 2-3 non-empty strings")
    for i, m in enumerate(e.get("metrics") or []):
        if not isinstance(m.get("valueNum"), (int, float)) or isinstance(m.get("valueNum"), bool):
            err(f"{where}: metrics[{i}] ({m.get('label')}) needs numeric valueNum")
        if "yoyPct" not in m or not (m["yoyPct"] is None or (isinstance(m["yoyPct"], (int, float)) and not isinstance(m["yoyPct"], bool))):
            err(f"{where}: metrics[{i}] ({m.get('label')}) needs yoyPct (number or null)")


def check_entry(e, where, err, warn):
    for k in REQUIRED:
        if k not in e:
            err(f"{where}: missing '{k}'")
    if e.get("tone") and e["tone"] not in TONES:
        err(f"{where}: unknown tone '{e['tone']}'")
    metrics = e.get("metrics") or []
    if not 1 <= len(metrics) <= 4:
        warn(f"{where}: {len(metrics)} metrics (site shows up to 4)")
    for i, m in enumerate(metrics):
        for k in ("label", "value", "change"):
            if not m.get(k):
                err(f"{where}: metrics[{i}] missing '{k}'")
        if m.get("positive") not in (-1, 0, 1):
            err(f"{where}: metrics[{i}] positive must be -1, 0 or 1")
    for i, g in enumerate(e.get("guidanceTracking") or []):
        if g.get("status") not in GT_STATUSES:
            err(f"{where}: guidanceTracking[{i}] status '{g.get('status')}' not in {sorted(GT_STATUSES)}")
        for k in ("metric", "guided", "actual"):
            if not g.get(k):
                err(f"{where}: guidanceTracking[{i}] missing '{k}'")
    if e.get("hasNumericGuidance"):
        if not e.get("guidance"):
            err(f"{where}: hasNumericGuidance is true but guidance is empty")
    elif not e.get("outlook"):
        warn(f"{where}: hasNumericGuidance is false but no outlook text")
    if "risks" in e and not isinstance(e["risks"], list):
        err(f"{where}: risks must be a list")
    if not e.get("quote"):
        warn(f"{where}: no quote")


SUMMARY_CATS = ["trends", "tailwinds", "headwinds", "opportunities", "risks", "insights"]
MAJORITY_CATS = {"trends", "tailwinds", "headwinds"}


def check_sector_summary(summary, companies, concall, fname, args, err, warn):
    """Check the sector-level sectorSummary array (newest quarter first)."""
    if not isinstance(summary, list):
        err(f"{fname}: sectorSummary must be a list")
        return
    quarters = [x.get("quarter") for x in summary if isinstance(x, dict)]
    keys = [quarter_key(q) for q in quarters]
    if not all(keys):
        err(f"{fname}: sectorSummary has a bad quarter in {quarters}")
    elif keys != sorted(keys, reverse=True) or len(set(keys)) != len(keys):
        err(f"{fname}: sectorSummary must be newest-first with one object per quarter: {quarters}")

    for x in summary:
        if not isinstance(x, dict):
            err(f"{fname}: sectorSummary items must be objects")
            continue
        q = x.get("quarter")
        where = f"{fname}: sectorSummary [{q}]"
        # Older quarters only warn when a newer quarter is being worked on
        e = err if not args.quarter or q == args.quarter else (lambda m: warn("(older) " + m))
        with_entry = {n for n in companies if any(h.get("quarter") == q for h in concall.get(n) or [])}
        if not isinstance(x.get("overview"), str) or not x["overview"].strip():
            e(f"{where}: missing overview")
        cc = x.get("callsCovered")
        if not isinstance(cc, int) or isinstance(cc, bool):
            e(f"{where}: callsCovered must be a whole number")
        elif cc != len(with_entry):
            e(f"{where}: callsCovered is {cc} but {len(with_entry)} companies have a {q} entry")
        if not any(x.get(c) for c in SUMMARY_CATS):
            e(f"{where}: no items in any of {SUMMARY_CATS}")
        for cat in x:
            if cat not in SUMMARY_CATS + ["quarter", "asOf", "callsCovered", "overview"]:
                warn(f"{where}: unknown key '{cat}' (not shown on site)")
        for cat in SUMMARY_CATS:
            items = x.get(cat)
            if items is None:
                continue
            if not isinstance(items, list):
                e(f"{where}: {cat} must be a list")
                continue
            for i, it in enumerate(items):
                tag = f"{where}: {cat}[{i}]"
                if isinstance(it, str):
                    if not it.strip():
                        e(f"{tag} is empty")
                    continue
                if not isinstance(it, dict) or not isinstance(it.get("text"), str) or not it["text"].strip():
                    e(f"{tag} must be a string or an object with 'text'")
                    continue
                cos = it.get("companies", [])
                if not isinstance(cos, list):
                    e(f"{tag}: companies must be a list")
                    continue
                if len(set(cos)) != len(cos):
                    e(f"{tag}: duplicate company names")
                for n in cos:
                    if n not in companies:
                        e(f"{tag}: '{n}' is not in this sector's companies list")
                    elif n not in with_entry:
                        e(f"{tag}: '{n}' has no {q} entry to support this point")
                if cat in MAJORITY_CATS and with_entry and cos and len(cos) * 2 < len(with_entry):
                    warn(f"{tag}: raised by {len(cos)} of {len(with_entry)} companies; under half, consider insights/opportunities/risks")

    if args.quarter and args.quarter not in quarters:
        n = sum(1 for c in companies if (concall.get(c) or [{}])[0].get("quarter") == args.quarter)
        if n:
            warn(f"{fname}: {n} companies have {args.quarter} entries but there is no {args.quarter} sectorSummary yet")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quarter", help="Quarter being added, e.g. Q2FY27. Entries for it must carry the new fields.")
    ap.add_argument("--sector", help="Only check this data file (name without .json)")
    args = ap.parse_args()

    if args.quarter and not quarter_key(args.quarter):
        sys.exit(f"--quarter must look like Q2FY27, got {args.quarter}")

    errors, warnings = [], []
    err, warn = errors.append, warnings.append

    listed = data_files_from_index()
    on_disk = sorted(p.stem for p in DATA.glob("*.json"))
    if listed is None:
        warn("could not read DATA_FILES from index.html")
        listed = on_disk
    for f in listed:
        if f not in on_disk:
            err(f"index.html lists '{f}' but data/{f}.json does not exist")
    for f in on_disk:
        if f not in listed:
            warn(f"data/{f}.json is not in DATA_FILES, so the site never loads it")

    files = [args.sector] if args.sector else listed
    total = covered = 0
    missing_q = []

    for f in files:
        path = DATA / f"{f}.json"
        if not path.exists():
            err(f"{path.name}: not found")
            continue
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            err(f"{path.name}: invalid JSON at line {ex.lineno}: {ex.msg}")
            continue

        sec = d.get("sector") or {}
        for k in ("name", "accent", "accentLight"):
            if not sec.get(k):
                err(f"{path.name}: sector.{k} missing")
        companies = d.get("companies") or []
        concall = {k: v for k, v in (d.get("concall") or {}).items() if k != "_template"}

        if "sectorSummary" in d:
            check_sector_summary(d["sectorSummary"], companies, concall, path.name, args, err, warn)

        if len(set(companies)) != len(companies):
            err(f"{path.name}: duplicate names in companies list")
        for name in concall:
            if name not in companies:
                warn(f"{path.name}: '{name}' has concall data but is not in the companies list (not shown on site)")

        for name in companies:
            total += 1
            hist = concall.get(name)
            if not hist:
                warn(f"{path.name}: '{name}' has no concall entries")
                if args.quarter:
                    missing_q.append(f"{f}: {name}")
                continue
            quarters = [e.get("quarter") for e in hist]
            for q in quarters:
                if not quarter_key(q):
                    err(f"{path.name}: '{name}' has bad quarter '{q}' (expected like Q2FY27)")
            if len(set(quarters)) != len(quarters):
                err(f"{path.name}: '{name}' has duplicate quarters {quarters}")
            keys = [quarter_key(q) for q in quarters]
            if all(keys) and keys != sorted(keys, reverse=True):
                err(f"{path.name}: '{name}' history is not newest-first: {quarters}")

            for e in hist:
                where = f"{path.name}: {name} [{e.get('quarter')}]"
                if args.quarter and e.get("quarter") == args.quarter:
                    check_entry(e, where, err, warn)
                    check_new_fields(e, where, err)
                elif args.quarter:
                    # Older quarters: report problems without blocking the new quarter's work
                    check_entry(e, where, lambda m: warn("(older) " + m), warn)
                else:
                    check_entry(e, where, err, warn)

            if args.quarter:
                if quarters[0] == args.quarter:
                    covered += 1
                else:
                    missing_q.append(f"{f}: {name} (latest {quarters[0]})")

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print()
    print(f"{len(files)} file(s), {total} companies, {len(errors)} error(s), {len(warnings)} warning(s)")
    if args.quarter:
        print(f"{args.quarter} coverage: {covered}/{total}")
        if missing_q and len(missing_q) <= 40:
            print("Not yet on " + args.quarter + ":")
            for m in missing_q:
                print("  -", m)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
