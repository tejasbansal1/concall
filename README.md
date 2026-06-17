# Concall Research Dashboard
**Live at:** `concall.equityinsightselite.com`

Sector-wise Q4FY26 concall guidance tracker. The HTML shell (`index.html`) never needs editing — all research content lives in the `data/` JSON files.

---

## One-time Setup

### 1. Create a new GitHub repo
Create a public repo named `concall` (or anything you like) on your GitHub account.

### 2. Upload these files
Push the entire folder structure to the `main` branch:
```
concall/
├── index.html
├── CNAME
├── .nojekyll
├── README.md
└── data/
    ├── co-working.json
    ├── peb.json
    ├── gold-finance.json
    ├── mfi.json
    └── real-estate.json
```

### 3. Enable GitHub Pages
Go to **Settings → Pages → Source → Deploy from branch → main → / (root)** → Save.

### 4. Add a DNS CNAME record
In your domain registrar (Cloudflare, GoDaddy, etc.) add:

| Type  | Name    | Value                        | TTL  |
|-------|---------|------------------------------|------|
| CNAME | concall | `yourgithubusername.github.io` | Auto |

Wait 5–10 minutes. GitHub will auto-provision the SSL certificate. Your site goes live at `concall.equityinsightselite.com`.

---

## Adding a New Company

Open the relevant sector file in `data/` and add the company name to the `"companies"` array:

```json
"companies": [
  "AWFIS Space Solutions Ltd",
  "EFC (I) Ltd",
  "New Company Ltd"       ← add here
]
```

Commit and push. The company now appears in the dashboard with a "No data yet" badge. Add the concall entry when you have it.

---

## Adding Concall Data

Open the sector JSON file and add an entry to the `"concall"` object. The company name must match **exactly** (including "Ltd", spacing, brackets).

### Full entry — when numeric guidance is available

```json
"concall": {
  "Company Name Ltd": {
    "quarter": "Q4FY26",
    "hasNumericGuidance": true,
    "tone": "Strongly Bullish",
    "toneColor": "#059669",
    "metrics": [
      { "label": "Revenue (Q4)",  "value": "₹X Cr", "change": "+X% YoY",    "positive": 1  },
      { "label": "EBITDA (Q4)",   "value": "₹X Cr", "change": "+X% YoY",    "positive": 1  },
      { "label": "PAT (Q4)",      "value": "₹X Cr", "change": "+X% YoY",    "positive": 1  },
      { "label": "EBITDA Margin", "value": "X%",    "change": "+X bps YoY", "positive": 1  }
    ],
    "fyPerformance": [
      "FY26 Revenue: ₹X Cr (+X% YoY)",
      "FY26 PAT: ₹X Cr (+X% YoY)",
      "Any other annual highlights"
    ],
    "guidance": [
      { "metric": "Revenue Growth (FY27E)", "value": "X–X%"  },
      { "metric": "EBITDA Margin (FY27E)",  "value": "X%"    },
      { "metric": "CapEx (FY27E)",          "value": "₹X Cr" }
    ],
    "highlights": [
      "Key concall takeaway one",
      "Key concall takeaway two",
      "Key concall takeaway three"
    ],
    "quote": "\"Exact MD/CEO quote from the concall transcript.\"",
    "quotePerson": "Name, Designation"
  }
}
```

### Tone-only entry — when no numeric guidance given

```json
"Company Name Ltd": {
  "quarter": "Q4FY26",
  "hasNumericGuidance": false,
  "tone": "Cautiously Optimistic",
  "toneColor": "#D97706",
  "metrics": [
    { "label": "Revenue (Q4)", "value": "₹X Cr", "change": "+X% YoY", "positive": 1 }
  ],
  "fyPerformance": [
    "FY26 Revenue: ₹X Cr (+X% YoY)"
  ],
  "guidance": null,
  "outlook": "Write 2–3 sentences summarising what management said about FY27 — demand environment, expansion plans, margin direction, and any key risks mentioned.",
  "highlights": [
    "Bullet point highlight 1",
    "Bullet point highlight 2"
  ],
  "quote": "\"Key quote from the concall.\"",
  "quotePerson": "Name, Designation"
}
```

---

## Field Reference

| Field               | Required | Notes |
|--------------------|----------|-------|
| `quarter`           | ✓        | e.g. `"Q4FY26"`, `"Q1FY27"` |
| `hasNumericGuidance`| ✓        | `true` shows Guidance table; `false` shows Outlook paragraph |
| `tone`              | ✓        | See tone values below |
| `toneColor`         | ✓        | See tone values below |
| `metrics`           | Optional | Array of up to 4 stat cards. Set to `null` to hide the row. |
| `fyPerformance`     | Optional | Array of strings for the annual summary section |
| `guidance`          | Optional | Array of `{metric, value}` pairs. Only shown when `hasNumericGuidance: true` |
| `outlook`           | Optional | Long-form management tone paragraph. Only shown when `hasNumericGuidance: false` |
| `highlights`        | Optional | Array of bullet-point strings |
| `quote`             | Optional | Wrap in escaped double-quotes: `\"Like this.\"` |
| `quotePerson`       | Optional | Name and title of the speaker |

### `positive` values for metrics
| Value | Colour | Use when |
|-------|--------|----------|
| `1`   | Green  | Positive change (+% growth, margin expansion) |
| `-1`  | Red    | Negative change (margin compression, decline) |
| `0`   | Grey   | Neutral / informational (e.g. "FY26 full year") |

### Tone values
| Tone                  | toneColor  |
|-----------------------|-----------|
| `"Strongly Bullish"`  | `"#059669"` |
| `"Bullish"`           | `"#059669"` |
| `"Cautiously Optimistic"` | `"#D97706"` |
| `"Neutral"`           | `"#64748B"` |
| `"Cautious"`          | `"#D97706"` |
| `"Bearish"`           | `"#EF4444"` |

---

## Quarterly Update Workflow

Each results season (happens 4× a year — around May, Aug, Nov, Feb):

1. Open the relevant `data/sector-name.json` in GitHub's web editor (or locally)
2. Update the `"quarter"` field to the new quarter (e.g. `"Q1FY27"`)
3. Update `"metrics"`, `"fyPerformance"`, `"guidance"` / `"outlook"`, `"highlights"`, `"quote"`
4. Commit → site refreshes within ~60 seconds

To add a new sector later, create a new JSON file in `data/` (e.g. `data/cement.json`) following the same structure, and add it to the `DATA_FILES` array in `index.html` (line ~40).

---

## Local Testing

Opening `index.html` directly in a browser will fail because `fetch()` is blocked on `file://`. Use a local server:

```bash
# Python (built in)
cd concall-dashboard
python -m http.server 8000
# Open http://localhost:8000

# Or with Node
npx serve .
```

---

## File Sizes at Scale

At 400 companies with full concall entries (~1.5 KB each):
- Total JSON data: ~600 KB
- Spread across 5 files: ~120 KB per file
- Gzip-compressed (GitHub Pages does this automatically): ~35 KB per file
- Load time on a typical connection: under 1 second total

No performance issues at this scale.
