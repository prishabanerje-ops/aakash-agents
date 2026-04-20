---
name: full-check
description: >
  Full technical SEO audit covering Canonical Tags, Redirects, Title Tags, Heading Tags,
  and Structured Data (29 checks). Triggers on the /full-check command in any of three
  modes: loading a saved Screaming Frog crawl by name, spidering a URL directly, or
  crawling from a sitemap in list mode. Always use this skill when the user types
  /full-check or asks to run an SEO audit, technical SEO check, site health report,
  canonical audit, redirect audit, schema audit, or any phrase like "run SEO checks",
  "check my site", "audit my URLs", "SEO health check". Outputs a structured .md report
  and posts to Slack #aakash-ai-experiment.
compatibility:
  tools: [bash_tool, Slack MCP]
  requires: Screaming Frog SEO Spider (licensed, CLI accessible)
automation:
  headless_invocation: "claude --dangerously-skip-permissions -p \"/full-check - {URL}\""
  note: >
    When running unattended (cron, schedule, CI), always invoke Claude with
    --dangerously-skip-permissions so no tool-use prompts interrupt the audit.
    Example: claude --dangerously-skip-permissions -p "/full-check - https://www.cars24.com"
---

> **Automation note:** Running headlessly? Use:
> ```
> claude --dangerously-skip-permissions -p "/full-check - {URL or Crawl Name}"
> ```

# SEO Technical Audit — `/full-check` Command

## Input Syntax

```
/full-check                     → No argument: list all saved Screaming Frog crawls
/full-check - {Crawl Name}      → Load a saved Screaming Frog crawl by name
/full-check - {URL}             → Spider mode: crawl the URL live
/full-check - {Sitemap-URL}     → List mode: fetch sitemap, crawl all URLs
```

**Detection rules** (in order):
1. If **no argument** is provided after `/full-check`, OR user says "show me list of SF crawl" / "list SF crawls" / "show SF crawls" → **List saved crawls** (see Step 1a), then wait for user to select
2. If input ends in `/sitemap.xml` or contains the word `sitemap` → **Sitemap / List mode**
3. If input starts with `http://` or `https://` (and is not a sitemap) → **Spider mode**
4. Otherwise → **Load saved crawl** by that name

---

## Step 1 — Detect OS & Set SF Binary Path

```bash
if [[ "$OSTYPE" == "darwin"* ]]; then
  SF="/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  SF="C:/Program Files (x86)/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe"
else
  SF="screamingfrogseospider"   # Linux — assumes on PATH
fi

echo "SF binary: $SF"
"$SF" --version
```

If the binary is not found, stop and tell the user to install Screaming Frog or verify PATH.

---

## Step 1a — List Saved Crawls (triggered when `/full-check` has no argument OR user says "show me list of SF crawl")

Run this immediately and **do not proceed to Step 2**. Call the SF MCP tool to list crawls,
then present the list and wait for the user to select one.

**Use the MCP tool** (preferred — no CLI needed):
```
mcp__screaming-frog__list_crawls  (no parameters)
```

Parse the result and display a clean summary table grouped by domain/site, showing the most
recent complete crawls first. Format:

```
📋 Saved Screaming Frog Crawls
───────────────────────────────────────────────────────────────────
#   Name / URL                          URLs     Complete  Date
─── ───────────────────────────────────  ──────  ──────── ─────────
1.  team-bhp.com/new-cars/              59,205   100%     01-Apr-26
2.  Aakash — cars24.com/new-cars/…     133,798   100%     31-Mar-26
3.  cars24.com/new-cars/ (full)      1,180,539   97.7%    06-Mar-26
...

Which crawl do you want to run the full-check on? (reply with the number or name)
```

**After the user replies**, extract the Database ID from the list result for the selected
crawl and proceed to Step 2 using **Mode A** (Load Saved Crawl) with that Database ID.

If the MCP tool returns no crawls, fall back to the SF CLI:
```bash
"$SF" --list-crawls 2>&1
```

If that also fails, respond:
> "No saved crawls found in Screaming Frog. Start a fresh crawl with:
> `/full-check - https://yoursite.com`"

---

## Step 2 — Set Output Directory

```bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DOMAIN=$(echo "$INPUT" | sed 's|https\?://||' | sed 's|/.*||' | sed 's|\s.*||')
OUTPUT_DIR="./seo-audit-output/${DOMAIN}_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"
echo "Output folder: $OUTPUT_DIR"
```

---

## Step 3 — Run the Correct Crawl Mode

### Mode A — Load Saved Crawl (`{Crawl Name}`)

```bash
"$SF" \
  --load-crawl "{Crawl Name}" \
  --headless \
  --output-folder "$OUTPUT_DIR" \
  --export-format csv \
  --export-tabs "Internal:All,Canonicals:All,Redirects:All,Page Titles:All,H1:All,Structured Data:All" \
  --bulk-export "All Redirect Chains,Canonical Errors" \
  --save-report "Redirect Chains,Canonical Errors,Page Titles,H1" \
  --use-pagespeed \
  --use-google-search-console
```

> To list available saved crawls: `"$SF" --list-crawls`

---

### Mode B — Spider Mode (`{URL}`)

```bash
"$SF" \
  --crawl "{URL}" \
  --headless \
  --output-folder "$OUTPUT_DIR" \
  --timestamped-output \
  --export-format csv \
  --export-tabs "Internal:All,Canonicals:All,Redirects:All,Page Titles:All,H1:All,Structured Data:All" \
  --bulk-export "All Redirect Chains,Canonical Errors" \
  --save-report "Redirect Chains,Canonical Errors,Page Titles,H1" \
  --use-pagespeed \
  --use-google-search-console
```

---

### Mode C — Sitemap / List Mode (`{Sitemap-URL}`)

First fetch the sitemap and extract all URLs:

```bash
SITEMAP_URL="{Sitemap-URL}"
URLLIST="$OUTPUT_DIR/url-list.txt"

curl -s "$SITEMAP_URL" | grep -oP '(?<=<loc>)[^<]+' > "$URLLIST"
URL_COUNT=$(wc -l < "$URLLIST")
echo "Found $URL_COUNT URLs in sitemap"

if [ "$URL_COUNT" -eq 0 ]; then
  echo "ERROR: No URLs found in sitemap. Check the URL and try again."
  exit 1
fi
```

Then run list-mode crawl:

```bash
"$SF" \
  --crawl-list "$URLLIST" \
  --headless \
  --output-folder "$OUTPUT_DIR" \
  --timestamped-output \
  --export-format csv \
  --export-tabs "Internal:All,Canonicals:All,Redirects:All,Page Titles:All,H1:All,Structured Data:All" \
  --bulk-export "All Redirect Chains,Canonical Errors" \
  --save-report "Redirect Chains,Canonical Errors,Page Titles,H1" \
  --use-pagespeed \
  --use-google-search-console
```

---

## Step 4 — Parse CSV Exports

```bash
python3 << 'PYEOF'
import csv, json, os, glob

output_dir = os.environ.get("OUTPUT_DIR", ".")

def load_csv(pattern):
    files = glob.glob(f"{output_dir}/**/{pattern}", recursive=True)
    if not files: return []
    with open(files[0], encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

data = {
    "internal":        load_csv("*internal*all*.csv"),
    "canonicals":      load_csv("*canonical*all*.csv"),
    "titles":          load_csv("*page_title*all*.csv") or load_csv("*title*all*.csv"),
    "h1":              load_csv("*h1*all*.csv"),
    "redirects":       load_csv("*redirect*all*.csv"),
    "structured":      load_csv("*structured*data*all*.csv"),
    "redirect_chains": load_csv("*redirect*chain*.csv"),
    "canonical_errs":  load_csv("*canonical*error*.csv"),
}

with open(f"{output_dir}/parsed.json", "w") as f:
    json.dump(data, f, indent=2)

print(json.dumps({k: len(v) for k, v in data.items()}))
PYEOF
```

Expected CSV → column mapping (for reference when writing check logic):

| File pattern | Key columns |
|---|---|
| `*internal*all*` | `Address`, `Status Code`, `Indexability`, `Meta Robots 1` |
| `*canonical*all*` | `Address`, `Canonical Link Element 1`, `Canonical Link Element 1 Source` |
| `*page_title*all*` | `Address`, `Title 1`, `Title 1 Length` |
| `*h1*all*` | `Address`, `H1-1`, `H1-1 Length` |
| `*redirect*all*` | `Address`, `Redirect URL`, `Status Code` |
| `*structured*data*all*` | `Address`, `Type`, `Properties`, `Errors`, `Warnings` |
| `*redirect*chain*` | `Source`, `Redirect URL`, `Status Code`, `Hops` |
| `*canonical*error*` | `Address`, `Issue` |

---

## Step 5 — Run All 29 Checks

Read `references/checks.md` for exact pass/fail criteria per Check ID.

For every check, record: `status` (PASS/FAIL/WARN/N/A), `count` (affected URLs),
`sample` (up to 3 URLs), `finding` (one sentence).

### Canonical Tags (9 checks)

| Check ID | Data source | Key logic |
|---|---|---|
| CANONICAL-001 | `canonicals` | Empty `Canonical Link Element 1` → FAIL |
| CANONICAL-002 | `canonicals` | Canonical ≠ `Address` on intended canonical pages |
| CANONICAL-003 | `canonicals` | `Address` ≠ `Canonical Link Element 1` on non-paginated pages |
| CANONICAL-007 | `canonical_errs` + live fetch | Multiple canonical tags per page |
| CANONICAL-008 | `canonicals` + `internal` | Canonical href Status Code ≠ 200 |
| CANONICAL-010 | `canonicals` | Build graph, detect cycles |
| CANONICAL-013 | Live fetch | `http://` page canonical points to `https://` |
| CANONICAL-014 | Live fetch | www and non-www both point to same preferred canonical |
| CANONICAL-020 | Live fetch (3–5 pages) | `rel=canonical` appears in `<body>` |

### Redirects (7 checks)

| Check ID | Data source | Key logic |
|---|---|---|
| REDIRECT-002 | `redirect_chains` | Rows where `Hops` > 1 |
| REDIRECT-003 | `redirect_chains` | A→B where B redirects back to A |
| REDIRECT-004 | Live fetch | `http://` returns 301 with `https://` Location header |
| REDIRECT-005 | Live fetch | Non-preferred www/non-www variant returns 301 |
| REDIRECT-007 | User-supplied list | Old URLs return 301 to new destination |
| REDIRECT-013 | `internal` + redirect dest | Redirect destination Indexability = "Non-Indexable" → FAIL |
| REDIRECT-014 | User-supplied URL map | Old category URL returns 301 to new category URL |

### Title Tags (5 checks)

| Check ID | Data source | Key logic |
|---|---|---|
| TITLE-001 | `titles` | Empty `Title 1` → FAIL |
| TITLE-002 | `titles` | Group by `Title 1`; count > 1 → FAIL |
| TITLE-004 | `titles` | Title contains no keyword relevant to URL/topic |
| TITLE-009 | `titles` + spot-check | Title doesn't match page content |
| TITLE-015 | `titles` | Homepage title = "Home", "Welcome", or empty → FAIL |

### Heading Tags (3 checks)

| Check ID | Data source | Key logic |
|---|---|---|
| H1-001 | `h1` | Empty `H1-1` → FAIL |
| H1-003 | `h1` | H1 contains no keyword relevant to page topic |
| H1-012 | Live fetch (3–5 pages) | H1 has `display:none` or `visibility:hidden` |

### Structured Data (6 checks)

| Check ID | Data source | Key logic |
|---|---|---|
| SCHEMA-002 | `structured` | Listing pages: `Type` lacks `Vehicle` or `Car` |
| SCHEMA-008 | `structured` | `Errors` column > 0 → FAIL |
| SCHEMA-009 | Live fetch vs PSI | Schema absent from raw HTML |
| SCHEMA-010 | Live fetch spot-check | Schema values not visible on page |
| SCHEMA-015 | `structured` | `Properties` contains placeholder text |
| SCHEMA-017 | Advisory | Confirm Rich Results Test has been run |

---

## Step 6 — Score Calculation

```python
# Per category
category_score = (pass_count / total_checks) * 100

# Overall
overall_score = (total_pass / 29) * 100

# Severity (see references/checks.md for full matrix)
CRITICAL = ["CANONICAL-008","CANONICAL-010","REDIRECT-003","REDIRECT-013",
            "TITLE-001","H1-001","SCHEMA-008"]
HIGH     = ["CANONICAL-001","CANONICAL-002","CANONICAL-007","REDIRECT-002",
            "REDIRECT-004","TITLE-002","SCHEMA-009","SCHEMA-010"]
# All other FAILs = Medium; all WARNs = Advisory
```

---

## Step 7 — Write the `.md` Report File

**Output path:**
```
./seo-audit-output/{domain}_{TIMESTAMP}/seo-audit-report-{domain}-{TIMESTAMP}.md
```

Use the template in `references/report-template.md` to build the file.

Write the file with `bash_tool`:
```bash
cat > "$OUTPUT_DIR/seo-audit-report-${DOMAIN}-${TIMESTAMP}.md" << 'MDEOF'
{assembled report content}
MDEOF

echo "Report written: $OUTPUT_DIR/seo-audit-report-${DOMAIN}-${TIMESTAMP}.md"
```

---

## Step 8 — Post to Slack

Use the Slack MCP `slack_send_message` tool.
**Channel:** `aakash-ai-experiment`

**Part 1 — Summary (main message):**
```
📊 *SEO Technical Audit* | {domain} | {date}
──────────────────────
📈 *Score: {X}/100*   🔢 URLs audited: {n}   🥾 Mode: {Spider|List|Saved Crawl}

🔗 Canonical Tags   {pass}/9   ({pct}%)
↪️  Redirects        {pass}/7   ({pct}%)
📄 Title Tags       {pass}/5   ({pct}%)
🏷️  Heading Tags     {pass}/3   ({pct}%)
🧩 Structured Data  {pass}/6   ({pct}%)

🚨 Critical: {n}  ❌ High: {n}  ⚠️ Medium: {n}  ℹ️ Advisory: {n}

Full check-by-check results in thread ↓
```

**Part 2 — Full results as thread reply** (compact list of all 29 checks with status emoji and one-line finding).

**Part 3 — Google Sheet + thread reply:**

1. Create a Google Sheet named `SEO Audit — {domain} — {date}` with the following tabs:

   **Tab 1: Summary**
   | Category | Checks Passed | Total Checks | Score (%) | Status |
   Populate one row per category (Canonical Tags, Redirects, Title Tags, Heading Tags, Structured Data) plus a Total row.

   **Tab 2: All Checks**
   | # | Category | Check Name | Status | Severity | Finding | Affected URLs (count) | Sample URLs |
   Populate all 29 checks — one row per check. Status = ✅ Pass / ❌ Fail / ⚠️ Warning. Include severity (Critical / High / Medium / Advisory) and a brief finding note. Add up to 3 sample URLs for failed/warning checks.

   **Tab 3: Issues Only**
   Same columns as "All Checks" but filtered to only rows where Status ≠ ✅ Pass, sorted by Severity (Critical → High → Medium → Advisory).

2. After creating the sheet, reply in the same Slack thread (same `thread_ts` as Part 2) with:
   ```
   📋 *Detailed audit sheet:* <Google Sheet URL>
   ```

If Google Sheets is not connected, skip silently and add a note to the terminal output: "Google Sheets not connected — skipping Part 3. Authenticate via VS Code MCP settings."

If Slack is not connected, print the full report to terminal and tell the user to connect the Slack MCP in VS Code settings.

---

## Error Handling

| Situation | Action |
|---|---|
| SF binary not found | Stop; tell user to install SF or fix PATH |
| `--load-crawl` name not found | Run `--list-crawls`; show available names |
| Sitemap returns non-200 | Stop; report HTTP status; ask user to verify URL |
| Sitemap has 0 `<loc>` entries | Stop; check if sitemap is an index (nested sitemaps) |
| CSV files missing after crawl | List `$OUTPUT_DIR` contents; identify what exported |
| PSI / GSC not authenticated | Skip; note "Not available — authenticate in SF settings" |
| Slack not connected | Print full report to terminal; advise connecting Slack MCP |

---

## Final Confirmation Output

```
✅ Crawl complete — {n} URLs audited
✅ Report saved — {path/to/seo-audit-report-*.md}
✅ Slack posted — #aakash-ai-experiment (ts: {timestamp})
✅ Google Sheet created — {sheet URL}
✅ Sheet link posted in thread — #aakash-ai-experiment
```
