# Q2 FY27 concall update plan

## Scope and baseline

- Update every company in the 29 sector files listed in `index.html`: 287 visible companies as of 14 November 2026.
- Treat Q2 FY27 as the quarter ended 30 September 2026. Keep each company's Q1 FY27 and Q4 FY26 entries as history and insert the Q2 entry first.
- Use the existing Q1 FY27 entry as the presentation model: up to four quarterly metrics, performance bullets, a comparison of prior guidance with actual delivery, current management guidance or outlook, highlights, a verified quote, and an `asOf` date.
- The previous source workflow is documented by each sector's local `sources.md`: find official NSE/BSE announcements or company investor-relations transcripts, save the PDF in the matching sector directory, and record the company, symbol, filing date, filename, URL, or a precise not-found note. There is no reusable download script checked into this repository.
- Nine visible companies have no Q1 FY27 entry. Sixteen additional records in `data/high-growth-models.json` are outside its `companies` list. Reconcile these records during the baseline audit so the visible company list defines the update scope and no company is silently skipped.
- The local transcript folders and their `sources.md` files are ignored by Git. For Q2, keep those PDFs as working material and add a **tracked** source register under `research/` so the evidence survives on another checkout.

## Research register and progress

- Create one tracked register row per visible company (287 rows), keyed by sector file and exact dashboard company name. Record the exchange symbol, call date, filing date, official transcript URL, supplemental results URL if used, local PDF name, and research status.
- Use the statuses **not started**, **source found**, **reading**, **drafted**, **verified**, **awaiting transcript**, and **no earnings call found**. Record a dated search note for unavailable transcripts and revisit those companies before release. An unavailable filing does not hold up the next company or sector.
- Keep concise, tracked sector research notes with page references for material numbers, guidance changes, risks, and quotes. A second pass should check each published fact against those references. Do not include a quote unless its exact wording and speaker can be verified.
- Source URLs and call dates stay in the research register only. They are not added to the JSON entries or shown on the site.

## Q2 entry schema additions

Every Q2 FY27 entry adds these fields to the existing schema:

| Field | Type | Rule |
| --- | --- | --- |
| `whatChanged` | string | One sentence on what is new versus the company's Q1 FY27 call: a new target, a changed outlook, a reversal, or a new risk. Shown as a callout at the top of the company page. |
| `risks` | array of 2–3 strings | Concerns raised on the call or visible in the numbers: margin pressure, demand slowdown, debt, working capital, asset quality, execution delays. Never left empty when the call contains one. |
| `metrics[].valueNum` | number | The metric value in the display unit (for example `425` for `₹425 Cr`, `55` for `55%`). |
| `metrics[].yoyPct` | number or null | YoY change in percent (`27` for `+27% YoY`); `null` when the change is not a YoY percentage. The sector page sorts by the first metric's `yoyPct`, so put the headline metric (revenue, AUM, or loan book) first. |
| `performanceLabel` | string, optional | Overrides the performance heading, for example `H1 FY27 Performance`. Without it, Q4 entries show "Full Year Performance" and other quarters "Quarter Performance". |

### Tone rubric

Assign `tone` from what management said, not from how upbeat they sounded:

| Tone | Use when |
| --- | --- |
| Strongly Bullish | Guidance raised, or growth clearly accelerating, and no material new risk |
| Bullish | Guidance maintained and delivered on track; demand described as healthy |
| Constructive | Mixed quarter, but management expects improvement with specific reasons |
| Cautiously Optimistic | Guidance maintained but with stated near-term headwinds, or partial delivery |
| Cautious | Guidance cut or deferred, a missed quarter, or a material new risk |
| Bearish | Guidance withdrawn, demand declining, or balance-sheet stress |

A sector where every company is Bullish or above should be rechecked against this table.

## Sector queue

Pilot the process on Co-Working (five companies), including the source register, summary format, and site rendering. Then follow the site's display order for the remaining sectors. Finish each sector's available calls and log its exceptions before moving on.

| Order | Sector | Data file | Visible companies |
| ---: | --- | --- | ---: |
| 1 | Co-Working (pilot) | `data/co-working.json` | 5 |
| 2 | High Growth Models | `data/high-growth-models.json` | 25 |
| 3 | Pharmaceuticals | `data/pharma.json` | 21 |
| 4 | Internet & Platforms | `data/internet-platform.json` | 12 |
| 5 | Wires & Cables | `data/wires-cables.json` | 5 |
| 6 | EMS | `data/ems.json` | 8 |
| 7 | Auto Ancillaries | `data/auto-anc.json` | 15 |
| 8 | Gold Finance | `data/gold-finance.json` | 5 |
| 9 | MFI | `data/mfi.json` | 6 |
| 10 | Affordable Housing | `data/affordable-housing.json` | 5 |
| 11 | Value Retail | `data/value-retail.json` | 3 |
| 12 | Jewelry Retail | `data/jewelry-retail.json` | 5 |
| 13 | Hospitals | `data/hospitals.json` | 15 |
| 14 | Diagnostics | `data/diagnostics.json` | 7 |
| 15 | Asset & Wealth Mgmt | `data/capital-markets.json` | 13 |
| 16 | Hotels | `data/hotels.json` | 9 |
| 17 | NBFC | `data/nbfc.json` | 16 |
| 18 | Small Finance Banks | `data/sfb.json` | 7 |
| 19 | Real Estate | `data/real-estate.json` | 20 |
| 20 | IT & Technology | `data/it.json` | 10 |
| 21 | Mid-Tier Banks | `data/banks.json` | 12 |
| 22 | Building Material | `data/building-material.json` | 13 |
| 23 | Exporters | `data/exporters.json` | 8 |
| 24 | Recycling | `data/recycling.json` | 6 |
| 25 | Pipes & Tubes | `data/pipes-tubes.json` | 9 |
| 26 | PEB | `data/peb.json` | 3 |
| 27 | FMCG | `data/fmcg.json` | 12 |
| 28 | Cement | `data/cement.json` | 8 |
| 29 | Writing Instruments | `data/writing-instruments.json` | 4 |
| | **Total** | | **287** |

## Procedure for each sector

1. **Inventory.** Match every name in the JSON `companies` array to its symbol and prior source entry. Check aliases and name changes; do not infer that a similarly named filing belongs to the company.
2. **Find and archive Q2 sources.** Search official NSE/BSE corporate announcements and company investor-relations pages for the Q2 FY27 earnings-call transcript. Check the document title and call date, download the PDF to the corresponding local sector directory, and append its filing date, saved filename, and original URL to `sources.md`. If a transcript is unavailable, record the search result and date rather than inventing content. Use an official results release or investor presentation only to corroborate financial figures, clearly distinguishing it from the call transcript.
3. **Read and extract.** Read the full call, including Q&A. Capture quarterly revenue, profitability, margins, business-specific operating metrics, management's explicit targets, changes to guidance, demand/risk commentary, and attributable verbatim quotes. Note the PDF page for each material claim in the research notes so numbers and quotes can be checked. Label calculated figures as calculations and check their formula and units against the underlying filing.
4. **Compare prior guidance.** Compare Q1 FY27 promises with Q2 actuals only when timing and metric definitions match. Mark `met`, `exceeded`, `partial`, or `missed` with a concise factual basis; leave untestable or full-year goals out of the delivery tracker until they can be assessed. State the old and new values when management reiterated, raised, lowered, or withdrew guidance.
5. **Write the sector JSON.** Prepend one Q2 FY27 object per verified company using the current schema. Populate `metrics` (with `valueNum` and `yoyPct`), `fyPerformance`, `guidanceTracking`, `guidance` or `outlook`, `whatChanged`, `risks`, `highlights`, `quote`, `quotePerson`, and `asOf` as supported. Set `tone` using the rubric above. Do not carry Q1 wording or figures into Q2. Use `hasNumericGuidance: false` and a sourced outlook when no numerical guidance was given.
6. **Validate the sector.** Run `python3 scripts/validate_data.py --quarter Q2FY27`; it checks JSON parsing, exact company-key matches, one entry per quarter, newest-first history, and the new fields. Then check by hand: source-file existence, quote accuracy, arithmetic/units, and whether all claims belong to Q2. Open the sector in the local site and inspect company cards, detail pages, the What changed and Risks sections, guidance status, sorting, and quarter tabs.

## Completion and release

- A company without a verified Q2 transcript stays on its last verified quarter; it never receives a synthetic Q2 entry. Report its register status and search date.
- After all 29 sectors have been reviewed, change the global quarter and `asOf` labels plus page metadata in `index.html` to Q2 FY27. Display the number of companies with verified Q2 entries and each company's latest available quarter so the global label does not imply complete company coverage.
- Run a final coverage audit against the 287 visible companies, confirm every company has exactly one register row, parse every sector JSON, and smoke-test the home page, sector pages, company details, and direct URLs. Report the number updated and the named exceptions before publishing.

This document is the planning stage. No Q2 research entries or site labels have been changed yet.
