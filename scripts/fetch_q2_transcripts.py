#!/usr/bin/env python3
"""Find and validate Q2 FY27 NSE earnings-call transcripts, one sector at a time."""

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "research/q2fy27/source-register.csv"
PDFINFO = "/Users/tejasbansal/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdfinfo"
PDFTOTEXT = "/Users/tejasbansal/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftotext"
FOLDERS = {
    "high-growth-models": "high-growth-models companies", "pharma": "pharma companies",
    "internet-platform": "internet companies", "wires-cables": "wires cables companies",
    "ems": "ems companies", "auto-anc": "auto ancillary companies",
    "gold-finance": "gold finance companies", "mfi": "mfi companies",
    "affordable-housing": "affordable housing companies", "value-retail": "value retail companies",
    "jewelry-retail": "jewelry retail companies", "hospitals": "hospitals companies",
    "diagnostics": "diagnostics companies", "capital-markets": "capital markets companies",
    "hotels": "hotels companies", "nbfc": "nbfc companies",
    "sfb": "small finance banks", "real-estate": "real estate companies",
    "it": "technology companies", "banks": "mid-tier banks",
    "building-material": "building materials companies", "exporters": "exporters companies",
    "recycling": "recycling companies", "pipes-tubes": "pipes tubes companies",
    "co-working": "co-working companies", "peb": "peb companies",
    "fmcg": "fmcg companies", "cement": "cement companies",
    "writing-instruments": "writing instruments companies",
}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
TODAY = "2026-11-14"


def curl(url: str, output: Path) -> bool:
    args = ["curl", "--http1.1", "-fLsS", "--retry", "2", "--max-time", "45",
            "-A", UA, "-H", "Accept: application/json, text/plain, */*",
            "-H", "Referer: https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            "-o", str(output), url]
    return subprocess.run(args, capture_output=True).returncode == 0


def announcements(symbol: str) -> list[dict]:
    query = urlencode({"index": "equities", "from_date": "01-10-2026",
                       "to_date": "14-11-2026", "symbol": symbol})
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "announcements.json"
        if not curl("https://www.nseindia.com/api/corporate-announcements?" + query, output):
            raise RuntimeError("NSE API request failed")
        value = json.loads(output.read_text())
        if not isinstance(value, list):
            raise RuntimeError("NSE API returned non-list response")
        return value


def candidate_items(items: list[dict]) -> list[dict]:
    found = []
    for item in items:
        combined = " ".join(str(item.get(k) or "") for k in ("desc", "attchmntText", "attchmntFile"))
        if "transcript" not in combined.lower():
            continue
        url = item.get("attchmntFile") or ""
        if not url.startswith("https://") or not url.lower().split("?")[0].endswith(".pdf"):
            continue
        found.append(item)
    return sorted(found, key=lambda x: x.get("sort_date") or x.get("an_dt") or "", reverse=True)


def check_pdf(path: Path) -> tuple[int, str]:
    if not path.exists() or path.stat().st_size < 10_000 or path.open("rb").read(5) != b"%PDF-":
        return 0, "not a substantive PDF"
    info = subprocess.run([PDFINFO, str(path)], capture_output=True, text=True)
    match = re.search(r"^Pages:\s*(\d+)", info.stdout, re.M)
    if info.returncode or not match:
        return 0, "PDF parser failed"
    pages = int(match.group(1))
    if pages <= 4:
        return pages, "four pages or fewer"
    extracted = subprocess.run([PDFTOTEXT, "-layout", str(path), "-"], capture_output=True, text=True)
    if extracted.returncode:
        return pages, "text extraction failed"
    text = extracted.stdout.lower()
    quarter = bool(re.search(r"q\s*2\s*(?:(?:&|and)\s*h\s*1\s*)?(?:fy\s*['’]?\s*27|fy\s*2027|2026\s*[-–/]\s*27)|second quarter", text))
    period = bool(re.search(r"(?:september|sep\.?)[^\n]{0,30}2026|30[\s/-]+09[\s/-]+2026", text))
    discussion = "moderator" in text and ("question" in text or "q&a" in text)
    if not (quarter or period):
        return pages, "Q2 FY27 period not confirmed"
    if not discussion:
        return pages, "management Q&A not confirmed"
    return pages, "verified earnings-call transcript"


def filename_for(row: dict, folder: Path) -> str:
    name = row["company"]
    for old in folder.glob("*Q1FY27*Concall_Transcript.pdf"):
        stem = re.sub(r"[^a-z0-9]", "", old.name.split("_Q1FY27", 1)[0].lower())
        company = re.sub(r"[^a-z0-9]", "", re.sub(r"\b(?:limited|ltd)\b", "", name.lower()))
        if stem == company or stem in company or company in stem:
            return old.name.replace("Q1FY27", "Q2FY27")
    clean = re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"\b(?:Limited|Ltd)\b", "", name)).strip("_")
    return clean + "_Q2FY27_Concall_Transcript.pdf"


def run_sector(slug: str) -> None:
    with REGISTER.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields, rows = reader.fieldnames, list(reader)
    folder = ROOT / FOLDERS[slug]
    audit = []
    for row in rows:
        if row["sector_file"] != f"data/{slug}.json" or row["status"] == "source found":
            continue
        symbol = row["symbol"]
        print(f"{row['company']} ({symbol})", flush=True)
        if not re.fullmatch(r"[A-Z0-9&-]+", symbol):
            row.update(status="awaiting transcript", last_checked=TODAY,
                       notes="NSE symbol unavailable/ambiguous; manual BSE or company IR search required")
            continue
        try:
            items = announcements(symbol)
        except Exception as exc:
            row.update(status="not started", last_checked=TODAY, notes=f"NSE lookup error: {exc}")
            continue
        candidates = candidate_items(items)
        candidate_log = []
        for item in candidates:
            url = item["attchmntFile"]
            with tempfile.TemporaryDirectory() as temp:
                provisional = Path(temp) / "candidate.pdf"
                if not curl(url, provisional):
                    candidate_log.append({"url": url, "reason": "download failed"})
                    continue
                pages, reason = check_pdf(provisional)
                candidate_log.append({"url": url, "pages": pages, "reason": reason,
                                      "filing": item.get("an_dt"), "description": item.get("attchmntText")})
                if reason != "verified earnings-call transcript":
                    continue
                final = folder / filename_for(row, folder)
                final.write_bytes(provisional.read_bytes())
                filing = item.get("an_dt", "")
                try:
                    filing = dt.datetime.strptime(filing, "%d-%b-%Y %H:%M:%S").date().isoformat()
                except ValueError:
                    pass
                row.update(filing_date=filing, transcript_url=url,
                           local_pdf=str(final.relative_to(ROOT)), pdf_pages=str(pages),
                           status="source found", last_checked=TODAY,
                           notes="NSE filing; PDF >4 pages; Q2 period and management Q&A confirmed; manual review pending")
                break
        else:
            row.update(status="awaiting transcript", last_checked=TODAY,
                       notes="No qualifying NSE PDF found; check BSE/company IR manually")
        audit.append({"company": row["company"], "symbol": symbol,
                      "result": row["status"], "candidates": candidate_log})
        print(f"  -> {row['status']} ({row['pdf_pages'] or '-'} pages)", flush=True)
    out = ROOT / f"research/q2fy27/{slug}-nse-audit.json"
    previous = json.loads(out.read_text()) if out.exists() else []
    combined = {x["company"]: x for x in previous}
    combined.update({x["company"]: x for x in audit})
    out.write_text(json.dumps(list(combined.values()), indent=2, ensure_ascii=False) + "\n")
    with REGISTER.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out.relative_to(ROOT)}; reviewed {len(audit)} companies", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sector", choices=FOLDERS)
    run_sector(parser.parse_args().sector)
