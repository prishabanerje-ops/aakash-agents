---
name: sf-headless-tester
description: >
  Diagnose, test, and validate a headless Screaming Frog SEO Spider CLI setup.
  Systematically tests every major function — crawling, exports, config, scheduling,
  API integrations (GSC, GA4, PageSpeed), custom extraction, and output formats.
  Generates a pass/fail diagnostic report and a hardened config template.
  Use when user says "test screaming frog", "screaming frog not working",
  "headless SF broken", "SF CLI issues", "diagnose screaming frog",
  "screaming frog setup", or "validate SF config". Always use this skill
  for any Screaming Frog headless/CLI troubleshooting or setup validation task.
---

# Screaming Frog Headless CLI — Diagnostic & Test Suite

## Overview

This skill runs a structured battery of tests against a headless Screaming Frog
installation and produces a pass/fail report with fix instructions. It covers
30 test groups across 7 categories.

**Read reference files as needed:**
- `references/install-checks.md` — installation, Java, display, license
- `references/crawl-tests.md` — crawl modes, config flags, export types
- `references/api-integrations.md` — GSC, GA4, PageSpeed, Majestic
- `references/extraction-tests.md` — custom extraction, XPath, regex, JS rendering
- `references/output-formats.md` — CSV, XLSX, Google Sheets, Sitemap output
- `references/scheduling.md` — cron, automation, CI/CD integration
- `references/future-proofing.md` — hardened config, best practices, upgrade path

---

## Phase 0 — Environment Discovery

Before running any test, gather environment facts:

```bash
# 1. OS & architecture
uname -a
lsb_release -a 2>/dev/null

# 2. Java version (SF requires Java 11+)
java -version 2>&1

# 3. Display server (SF needs DISPLAY or Xvfb for headless)
echo $DISPLAY
which Xvfb 2>/dev/null && Xvfb -help 2>&1 | head -3

# 4. Screaming Frog binary location
which ScreamingFrogSEOSpider 2>/dev/null
find /usr /opt /home -name "ScreamingFrogSEOSpider" 2>/dev/null | head -5

# 5. Version
ScreamingFrogSEOSpider --version 2>&1

# 6. License status
ScreamingFrogSEOSpider --license-info 2>&1

# 7. Available RAM (SF needs 2GB+ for large crawls)
free -h

# 8. Available disk space
df -h /tmp /home 2>/dev/null
```

Record all outputs. These facts determine which tests apply and explain
many common failures before any crawl runs.

---

## Phase 1 — Installation & Binary Tests (Category 1)

Read `references/install-checks.md` for this phase.

Run the 7 installation checks in order. Stop at first blocking failure
and report the fix before continuing.

**Quick triage:** Most headless SF failures fall into one of 4 buckets:
1. Missing/wrong Java version — `JAVA_HOME` or `java` not on PATH
2. No display server — `DISPLAY` not set, Xvfb not running
3. Unlicensed — free tier crawl cap (500 URLs) hit silently
4. Wrong config path — `--config` flag points to non-existent file

---

## Phase 2 — Core Crawl Tests (Category 2)

Read `references/crawl-tests.md` for this phase.

Tests to run (in order of complexity):

| # | Test | Command snippet | Pass condition |
|---|------|-----------------|----------------|
| C1 | Minimal crawl (1 URL) | `--crawl https://example.com --headless` | Exits 0, creates output |
| C2 | Crawl with depth limit | `--crawl-depth 1` | Respects depth, no infinite loops |
| C3 | Crawl with URL list | `--crawl-list urls.txt` | All URLs attempted |
| C4 | Spider mode vs list mode | Both modes | Output differs correctly |
| C5 | Robots.txt respect | `--respect-robots-txt true` | Blocked URLs excluded |
| C6 | JS rendering ON | `--use-renderer true` | JS-rendered content captured |
| C7 | JS rendering OFF | `--use-renderer false` | Raw HTML only, faster |
| C8 | Custom user agent | `--user-agent "Cars24Bot/1.0"` | UA string in request headers |
| C9 | Crawl delay | `--crawl-delay 500` | Respects delay between requests |
| C10 | Max URLs cap | `--max-urls 50` | Stops at cap, no overflow |

For each test, capture:
- Exit code (`echo $?`)
- Error output on stderr
- Output directory contents
- Time taken

---

## Phase 3 — Export & Output Tests (Category 3)

Read `references/output-formats.md` for this phase.

| # | Test | Pass condition |
|---|------|----------------|
| E1 | Export all tabs to CSV | `/output/` contains `internal_html.csv` etc. |
| E2 | Export specific tab | `--export-tabs "Internal:All"` produces single file |
| E3 | Bulk export | All tabs exported in one pass |
| E4 | XLSX export | Valid Excel file, opens without errors |
| E5 | Sitemap export | Valid XML, passes schema check |
| E6 | Google Sheets export | Sheet created/updated (requires OAuth token) |
| E7 | Custom report export | `--save-report` produces named file |
| E8 | Crawl overview export | Summary stats file present |
| E9 | Redirect chains export | `redirect_chains.csv` present when redirects exist |
| E10 | Orphan pages export | Requires GSC integration (see Phase 5) |

---

## Phase 4 — Config File Tests (Category 4)

SF headless is almost always run with a saved `.seospiderconfig` file.
These tests verify the config system works correctly.

```bash
# Save a config from scratch
ScreamingFrogSEOSpider \
  --headless \
  --save-config /tmp/test.seospiderconfig \
  --crawl https://example.com \
  --max-urls 1

# Load the saved config
ScreamingFrogSEOSpider \
  --headless \
  --config /tmp/test.seospiderconfig \
  --crawl https://example.com

# Verify config contents (it's XML)
cat /tmp/test.seospiderconfig | grep -E "<|>" | head -30
```

| # | Test | Pass condition |
|---|------|----------------|
| CF1 | Save config | File created, non-empty |
| CF2 | Load config | Crawl runs with loaded settings |
| CF3 | Config override | CLI flag overrides config value |
| CF4 | Multiple configs | Can switch between configs per crawl |
| CF5 | Config validation | Invalid config produces clear error |

---

## Phase 5 — API Integration Tests (Category 5)

Read `references/api-integrations.md` for this phase.

### Google Search Console
```bash
ScreamingFrogSEOSpider \
  --headless \
  --crawl https://www.cars24.com/new-cars/ \
  --gsc-property "https://www.cars24.com" \
  --gsc-date-range LAST_3_MONTHS
```

| # | Test | Pass condition |
|---|------|----------------|
| API1 | GSC connection | No auth error, impressions/clicks columns in export |
| API2 | GSC date range | Correct date range applied |
| API3 | GA4 connection | Sessions/users data appears in export |
| API4 | PageSpeed Insights | CWV scores in `pagespeed.csv` |
| API5 | Majestic (if licensed) | Trust Flow/Citation Flow columns present |

**Common auth failure path:**
1. Tokens stored in `~/.ScreamingFrogSEOSpider/` — check they exist
2. Token expiry — re-auth via GUI first, then re-export tokens
3. Service account vs OAuth — SF supports both for GSC; service account is more reliable for headless

---

## Phase 6 — Custom Extraction Tests (Category 6)

Read `references/extraction-tests.md` for this phase.

Custom extraction is the most commonly broken feature in headless mode
because it requires a saved config with the extraction rules baked in.

```bash
# Test XPath extraction
# Config must have custom extraction rules saved

ScreamingFrogSEOSpider \
  --headless \
  --config /path/to/config-with-extraction.seospiderconfig \
  --crawl https://www.cars24.com/new-cars/

# Verify extraction columns in output
head -1 /output/internal_html.csv | tr ',' '\n' | grep -i "custom"
```

| # | Test | Pass condition |
|---|------|----------------|
| X1 | XPath extraction | Custom column present in CSV with data |
| X2 | CSS selector extraction | CSS-based rule returns data |
| X3 | Regex extraction | Pattern match returns expected values |
| X4 | Multiple extractors | All 3 extractor slots fire correctly |
| X5 | JS-rendered extraction | Data extracted after JS renders |
| X6 | Structured data extraction | JSON-LD values captured |

**Cars24-specific extractors to test:**
- `//script[@type='application/ld+json']` — schema markup
- `//meta[@name='description']/@content` — meta descriptions
- `//h1/text()` — H1 text
- `//*[@class='price']` — price elements (checks JS rendering)

---

## Phase 7 — Scheduling & Automation Tests (Category 7)

Read `references/scheduling.md` for this phase.

| # | Test | Pass condition |
|---|------|----------------|
| S1 | Cron job fires | Job runs at scheduled time |
| S2 | Output path is absolute | No "file not found" on cron run |
| S3 | Environment vars available | `DISPLAY`, `JAVA_HOME` set in cron env |
| S4 | Log capture | stderr/stdout redirected to log file |
| S5 | Exit code monitoring | Non-zero exit triggers alert |
| S6 | Concurrent run protection | Lock file prevents parallel crawls |
| S7 | Post-crawl hook | Script/webhook fires after completion |
| S8 | GitHub Actions integration | Workflow YAML runs crawl in CI |

---

## Diagnostic Report Format

After all tests, output this report:

```
═══════════════════════════════════════════════════
SCREAMING FROG HEADLESS DIAGNOSTIC REPORT
Cars24 SEO — [DATE]
═══════════════════════════════════════════════════

ENVIRONMENT
  OS:          [value]
  Java:        [value] — [PASS/FAIL]
  Display:     [value] — [PASS/FAIL]
  SF Version:  [value]
  License:     [LICENSED/FREE/UNKNOWN]
  RAM:         [value]

CATEGORY RESULTS
  Cat 1 — Installation:     [X/7 passed]
  Cat 2 — Core Crawl:       [X/10 passed]
  Cat 3 — Exports/Output:   [X/10 passed]
  Cat 4 — Config System:    [X/5 passed]
  Cat 5 — API Integrations: [X/5 passed]
  Cat 6 — Custom Extraction:[X/6 passed]
  Cat 7 — Scheduling:       [X/8 passed]

OVERALL: [X/51 passed]

BLOCKING ISSUES (must fix first)
  ✗ [issue] — [fix]

HIGH PRIORITY
  ⚠  [issue] — [fix]

WORKING CORRECTLY
  ✓ [feature]

NEXT STEPS
  1. [action]
  2. [action]
```

---

## Running This Skill

1. Claude runs Phase 0 (environment discovery) via bash
2. Reports environment facts to user
3. Asks: "Which categories do you want to test? All / specific ones?"
4. Runs selected test phases using bash_tool
5. Captures all outputs
6. Generates the diagnostic report
7. Offers to create hardened config (read `references/future-proofing.md`)
