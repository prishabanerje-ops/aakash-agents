---
name: seo-crawl-audit
description: >
  SEO Audit Automation using Screaming Frog MCP. Supports three invocation modes:
  /Crawl-full-website <URL> to spider crawl the full site,
  /Crawl-sitemap <sitemap-url-1> ... to crawl only sitemap URLs,
  /Crawl-all <URL> <sitemap-url-1> ... to crawl both and merge.
  Analyses 150 issues across 21 sections, generates an executive summary,
  section-by-section findings, and a priority action plan.
  Use when user says "/Crawl-full-website", "/Crawl-sitemap", "/Crawl-all",
  "SEO crawl audit", "Screaming Frog audit", or "crawl and audit".
---

# SEO Audit Automation — Claude Code Prompt (Screaming Frog MCP)

## Execution Steps

When any of the above commands is invoked, follow these steps **in order**:

### Step 0 — Select the Crawl to Analyse

Before starting any analysis, call `mcp__screaming-frog__list_crawls` to retrieve all saved crawls from the Screaming Frog database. Present the list to the user in a clean table showing:

| # | Name | URL | URLs | % Complete | Modified |
|---|------|-----|------|------------|----------|

Then ask: **"Which crawl would you like to use for this audit?"** — allowing the user to pick by number or name. If only one relevant crawl exists, suggest it and proceed unless the user says otherwise.

Once the crawl is selected, note its **Database ID** — use this for all subsequent `export_crawl` calls.

### Step 1 — Run the Crawl via Screaming Frog MCP

- For `Crawl-full-website`: Start a spider crawl from the provided URL.
- For `Crawl-sitemap`: Load each sitemap URL and crawl the URLs listed inside them.
- For `Crawl-all`: Start a spider crawl from the URL AND load each sitemap, then merge all data.

Use the Screaming Frog MCP tools to:
1. Configure the crawl (respect robots.txt, render JavaScript, follow redirects).
2. Start the crawl and wait for completion.
3. Export all relevant reports/tabs from Screaming Frog.

Print progress updates:
```
→ [1/3] Starting Screaming Frog crawl of <URL> ...
→ [1/3] Crawl complete. X,XXX URLs discovered.
→ [2/3] Analysing issues across 21 sections (150 checks)...
```

### Step 2 — Extract & Map Data to the Issue Checklist

Once the crawl is complete, extract data from Screaming Frog's outputs and map findings to every issue category below. For each issue, record:

- **Issue Name** (from the checklist)
- **Status**: ✅ Pass | ⚠️ Warning | ❌ Fail | ℹ️ Info / Not Applicable
- **Count**: Number of affected URLs
- **Sample URLs**: Up to 5 example URLs per issue
- **Recommendation**: One-line fix suggestion

Print section progress as each section is processed:
```
→ [Section 1/21] HTTP Status Codes — checking 11 issues...
→ [Section 2/21] Security & Headers — checking 2 issues...
...
```

---

## Issue Checklist — Complete Mapping

### 1. HTTP Status Codes

| # | Issue | SF Data Source |
|---|-------|---------------|
| 1 | 3xx responses | Response Codes → 3xx tab |
| 2 | 4xx responses | Response Codes → 4xx tab |
| 3 | 5xx responses | Response Codes → 5xx tab |
| 4 | 200 served with wrong Content-Type | Response Codes → filter Content-Type mismatch |
| 5 | Broken internal links | Response Codes → Client Error (4xx) → inlinks filter |
| 6 | Broken external links | External tab → filter status 4xx/5xx |
| 7 | Redirect chains | Response Codes → Redirect Chains report |
| 8 | Redirect loops | Response Codes → Redirect Loops report |
| 9 | Temporary redirects to permanent URLs | Response Codes → 3xx → filter 302/307 |
| 10 | Non-200 status on main ranking pages | Cross-reference ranking URLs with status codes |
| 11 | HTTPS to HTTP redirect issues | Response Codes → 3xx → filter HTTPS→HTTP |

### 2. Security & Headers

| # | Issue | SF Data Source |
|---|-------|---------------|
| 12 | Incorrect Vary header | Custom Extraction or HTTP Headers tab |
| 13 | HTTPS mixed content | Insecure Content report under Security tab |

### 3. Canonical Tags

| # | Issue | SF Data Source |
|---|-------|---------------|
| 14 | Missing canonical | Canonicals → Missing |
| 15 | Canonical points to non-indexable page | Canonicals → cross-ref with Indexability |
| 16 | Multiple canonicals | Canonicals → Multiple |
| 17 | Conflicting canonicals (HTTP header vs HTML) | Canonicals → Mismatch filter |
| 18 | Canonical is relative | Canonicals → contains relative URLs |
| 19 | Canonical contains fragment (#) | Canonicals → filter URLs containing # |
| 20 | Canonical outside `<head>` | Canonicals → Rendered vs Raw comparison |
| 21 | Canonical to wrong country folder | Canonicals → filter cross-country patterns |
| 22 | Self-canonical not used | Canonicals → Self-Referencing filter = No |
| 23 | Canonicalized pages still indexable | Canonicals → non-self → Indexability = Indexable |
| 24 | Canonical to non-200 URL | Canonicals → target status ≠ 200 |
| 25 | Pagination canonical wrong | Pagination report → canonical mismatch |
| 26 | Canonical rewritten by JS | Rendered Page → compare raw vs rendered canonical |

### 4. Title Tags

| # | Issue | SF Data Source |
|---|-------|---------------|
| 27 | Missing title | Page Titles → Missing |
| 28 | Duplicate titles | Page Titles → Duplicate |
| 29 | Too short (under 30 chars) | Page Titles → Below 30 Characters |
| 30 | Too long (over 60 chars) | Page Titles → Over 60 Characters |
| 31 | Same as H1 | Page Titles → Same as H1 |
| 32 | Multiple titles | Page Titles → Multiple |
| 33 | Title outside `<head>` | Rendered Page → raw HTML inspection |
| 34 | Dynamic parameters in titles | Page Titles → contains ?, =, & patterns |

### 5. Meta Descriptions

| # | Issue | SF Data Source |
|---|-------|---------------|
| 35 | Missing description | Meta Description → Missing |
| 36 | Duplicate descriptions | Meta Description → Duplicate |
| 37 | Too short (<70 chars) | Meta Description → Below 70 Characters |
| 38 | Too long (>160 chars) | Meta Description → Over 160 Characters |
| 39 | Multiple descriptions | Meta Description → Multiple |
| 40 | Description outside `<head>` | Rendered Page → raw HTML inspection |

### 6. Headings

| # | Issue | SF Data Source |
|---|-------|---------------|
| 41 | H1 missing | H1 → Missing |
| 42 | H1 duplicate | H1 → Duplicate |
| 43 | Multiple H1s | H1 → Multiple |
| 44 | Missing hierarchy (H1→H6) | H1/H2 → cross-check heading levels |
| 45 | Missing H2/H3 | H2 → Missing |
| 46 | Hidden headings | Rendered Page → display:none on headings |

### 7. Content Quality

| # | Issue | SF Data Source |
|---|-------|---------------|
| 47 | Low word count pages | Word Count → Below threshold (e.g. <300) |
| 48 | Thin variant pages | Word Count → filter variant/parameter URLs with low content |
| 49 | Exact duplicates | Content → Exact Duplicates |
| 50 | Near duplicates (90%+) | Content → Near Duplicates |
| 51 | Soft 404 pages | Response Codes → Soft 404 detection |
| 52 | No localised content for city pages | Custom filter → city page URLs with duplicate/template content |
| 53 | Non-visible text used | Rendered Page → hidden text detection |
| 54 | AI-only content | Manual / Custom Extraction → content fingerprinting |

### 8. Indexability & Directives

| # | Issue | SF Data Source |
|---|-------|---------------|
| 55 | HTML (non-HTML served as pages) | Content Type filter → non text/html |
| 56 | Noindex pages | Directives → Noindex |
| 57 | Nofollow on critical URLs | Directives → Nofollow |
| 58 | Noindex + canonical conflicts | Directives → Noindex AND has canonical |
| 59 | Meta refresh tags | Directives → Meta Refresh |
| 60 | X-Robots HTTP tag errors | HTTP Headers → X-Robots-Tag |

### 9. Hreflang & Internationalisation

| # | Issue | SF Data Source |
|---|-------|---------------|
| 61 | Incorrect hreflang x-default | Hreflang → x-default issues |
| 62 | Hreflang chains | Hreflang → redirect targets |
| 63 | Hreflang missing return tags | Hreflang → Missing Return Tags |

### 10. JavaScript & Rendering

| # | Issue | SF Data Source |
|---|-------|---------------|
| 64 | Sitemap vs Robots conflict | Sitemaps + Robots.txt comparison |
| 65 | JS rendering issues | JavaScript → Rendering tab |
| 66 | Content missing in rendered HTML | Rendered Page → Word Count raw vs rendered |
| 67 | Pagination not crawlable | Pagination → links not found |
| 68 | JS-fired internal links | JavaScript → JS-rendered links only |
| 69 | Client-side rendering without SSR | Rendered Page → empty raw HTML body |

### 11. HTML Validation

| # | Issue | SF Data Source |
|---|-------|---------------|
| 70 | Multiple `<head>` tags | Custom Extraction or Validation tab |
| 71 | Missing doctype | Custom Extraction → `<!DOCTYPE>` check |
| 72 | Missing language attribute | Custom Extraction → `<html lang>` check |
| 73 | Broken structured data | Structured Data → Validation Errors |
| 74 | Deeply nested DOM | Rendered Page → DOM depth metric |
| 75 | Images missing alt text | Images → Missing Alt Text |
| 76 | Alt text duplicates | Images → Duplicate Alt Text |
| 77 | Mismatched canonical vs OG URL | Custom Extraction → compare canonical & og:url |
| 78 | Robots meta outside `<head>` | Custom Extraction / Rendered Page |
| 79 | Improper pagination markup | Pagination → rel=next/prev issues |

### 12. Sitemaps

| # | Issue | SF Data Source |
|---|-------|---------------|
| 80 | URLs missing from sitemap | Sitemaps → URLs Not in Sitemap |
| 81 | 3xx in sitemap | Sitemaps → 3xx filter |
| 82 | 4xx in sitemap | Sitemaps → 4xx filter |
| 83 | 5xx in sitemap | Sitemaps → 5xx filter |
| 84 | Disallowed URLs in sitemap | Sitemaps → cross-ref Robots.txt |
| 85 | Parameter URLs in sitemap | Sitemaps → filter URLs with ? or & |
| 86 | Very large sitemaps (>50k URLs) | Sitemaps → URL count per sitemap |
| 87 | Incorrect lastmod dates | Sitemaps → Lastmod validation |
| 88 | CDP URLs not updated on new inventory | Custom check → inventory page freshness |
| 89 | City pages not in sitemap | Custom filter → /city/ pattern not in sitemap |

### 13. Robots.txt

| # | Issue | SF Data Source |
|---|-------|---------------|
| 90 | Blocked critical paths | Robots.txt → Disallow analysis |
| 91 | Blocked JS or CSS | Robots.txt → blocked resource filter |
| 92 | CDN overwrites robots | HTTP Headers → robots from CDN vs origin |
| 93 | Incorrect noindex (via robots) | Robots.txt + HTTP Headers |
| 94 | Incorrect nofollow (via robots) | Robots.txt + HTTP Headers |
| 95 | Indexable pages with noindex headers | Directives → conflict detection |

### 14. Redirects (detailed)

| # | Issue | SF Data Source |
|---|-------|---------------|
| 96 | 302 instead of 301 on permanent moves | Response Codes → 302 filter |
| 97 | Multiple redirects | Response Codes → Redirect Chains |
| 98 | Redirect chains | Response Codes → Redirect Chains report |
| 99 | Redirect loops | Response Codes → Redirect Loops report |
| 100 | Redirecting canonical pages | Canonicals → target redirects |
| 101 | Hard 404 | Response Codes → 404 |
| 102 | Soft 404 | Content → Soft 404 detection |
| 103 | Dead image URLs | Images → 4xx/5xx status |

### 15. Core Web Vitals & Performance

| # | Issue | SF Data Source |
|---|-------|---------------|
| 104 | Poor LCP | PageSpeed / CrUX integration → LCP > 2.5s |
| 105 | Poor CLS | PageSpeed / CrUX integration → CLS > 0.1 |
| 106 | Poor FID / INP | PageSpeed / CrUX integration → INP > 200ms |
| 107 | Images not compressed | Images → file size analysis |
| 108 | Too many third-party scripts | Custom Extraction → 3P script count |
| 109 | Large JS bundles | Resources → JS file sizes |
| 110 | Render-blocking JS | Resources → Render Blocking filter |
| 111 | Lazy load of above-the-fold content | Custom Extraction → lazy-load on LCP element |
| 112 | CLS on car images | Custom → car image elements missing width/height |
| 113 | Missing font-swap | Custom Extraction → @font-face without font-display |
| 114 | Font blocking | Resources → font load behaviour |
| 115 | No critical CSS | Rendered Page → FOUC detection |
| 116 | Broken preload chain | Resources → preload link analysis |
| 117 | Excessive tracking scripts | Custom Extraction → tracking script count |

### 16. Structured Data / Schema

| # | Issue | SF Data Source |
|---|-------|---------------|
| 118 | Missing Organization schema | Structured Data → Organization not found |
| 119 | Missing Breadcrumb schema | Structured Data → BreadcrumbList not found |
| 120 | Missing Product schema for cars | Structured Data → Product not found on car pages |
| 121 | Dealer schema issues | Structured Data → AutoDealer validation |
| 122 | FAQ schema misuse | Structured Data → FAQPage on non-FAQ pages |
| 123 | Invalid schema | Structured Data → Validation Errors |
| 124 | Schema not matching on-page content | Structured Data → content mismatch |
| 125 | Missing price, model, brand in schema | Structured Data → Product fields incomplete |
| 126 | Missing availability schema | Structured Data → Offer → availability missing |
| 127 | No aggregate rating for CDPs | Structured Data → AggregateRating missing on CDP |
| 128 | No local schema on hub pages | Structured Data → LocalBusiness missing on hubs |

### 17. UX & Crawlability Blockers

| # | Issue | SF Data Source |
|---|-------|---------------|
| 129 | Excessive popups | Custom Extraction / manual |
| 130 | Interstitials blocking crawl | Rendered Page → overlay detection |
| 131 | Multiple tag managers | Custom Extraction → GTM/Adobe count |
| 132 | Infinite scroll with no SSR backup | Rendered Page → pagination link check |

### 18. Local SEO

| # | Issue | SF Data Source |
|---|-------|---------------|
| 133 | Missing local business schema | Structured Data → LocalBusiness missing |
| 134 | Broken Google Business Profile links | External links → GBP URL status |
| 135 | Duplicate hub pages | Content → Duplicate hub URL detection |

### 19. Internal Linking

| # | Issue | SF Data Source |
|---|-------|---------------|
| 136 | No linking to high-value CLPs | Inlinks → CLP pages with 0 inlinks |
| 137 | Thin pages getting too many links | Inlinks count vs Word Count cross-ref |
| 138 | No link hubs from cities | Inlinks → city hub pages with poor outlinks |
| 139 | Orphan pages | Orphan Pages report |
| 140 | Pagination not indexed | Pagination → Indexability filter |
| 141 | Internal search pages crawlable by mistake | URL filter → /search? in crawled URLs |

### 20. Images

| # | Issue | SF Data Source |
|---|-------|---------------|
| 142 | Missing alt tags | Images → Missing Alt Text |
| 143 | Heavy images | Images → Over 100KB |
| 144 | No WebP | Images → format filter ≠ webp |
| 145 | Lazy load errors | Images → lazy loading attribute issues |
| 146 | Missing captions for car variants | Custom → car variant images without caption |
| 147 | Images over 200KB | Images → Over 200KB |
| 148 | Watermark images | Manual / image analysis |

### 21. Navigation & Breadcrumbs

| # | Issue | SF Data Source |
|---|-------|---------------|
| 149 | Breadcrumb missing | Structured Data → BreadcrumbList absent + Custom Extraction |
| 150 | No flat navigation | Crawl Depth → pages deeper than 3 clicks |

---

## Step 3 — Generate the Report

After mapping all findings, generate a structured report:

### Report Structure

```
1. EXECUTIVE SUMMARY
   - Crawl date, URL/sitemaps crawled
   - Total URLs discovered
   - Overall health score (% of checks passed)
   - Top 10 critical issues (sorted by impact)

2. SECTION-BY-SECTION FINDINGS
   For each of the 21 sections:
   - Section title
   - Summary: X passed, Y warnings, Z failed
   - Table: Issue | Status | Count | Sample URLs | Recommendation

3. FULL URL-LEVEL EXPORT
   - CSV/table listing every URL with all detected issues

4. PRIORITY ACTION PLAN
   - Critical (fix immediately): issues causing indexing/ranking loss
   - High (fix this sprint): issues affecting UX or crawl efficiency
   - Medium (fix this month): content quality & schema gaps
   - Low (backlog): cosmetic or minor optimisations
```

### Output Formats

Produce the report in **three formats**:
1. **Word File (.docx)** — saved to disk; filename must include date and time
2. **Detailed XLSX** — saved to disk with one sheet per section plus a master sheet; filename must include date and time
3. **Slack Canvas** — create a full Slack Canvas document (via `mcp__claude_ai_Slack__slack_create_canvas`) containing the complete report (Executive Summary, all 21 section findings, Priority Action Plan). Then post a message to Slack channel `aakash-ai-experiment` with:
   - A summary of the top 10 issues
   - A direct link to the Canvas
   - The Canvas must be created before the Slack message is sent

Print completion:
```
→ [3/3] Generating report...
→ ✅ Report saved: seo-audit-<domain>-<YYYY-MM-DD-HH-MM>.xlsx
→ ✅ Word report saved: seo-audit-<domain>-<YYYY-MM-DD-HH-MM>.docx
→ ✅ Slack Canvas created: <canvas-url>
→ ✅ Slack message sent to: #aakash-ai-experiment
```

---

## Behavioural Rules

1. **Never skip an issue.** Even if Screaming Frog returns zero results for a category, report it as ✅ Pass with count 0.
2. **Be specific with URLs.** Always show real URLs, not placeholders.
3. **Cross-reference data.** Many issues require combining two SF exports (e.g., canonicals + indexability). Do the join.
4. **Handle large crawls gracefully.** If a crawl exceeds 100k URLs, process in batches and merge.
5. **Log progress.** Print status updates as each section is processed.
6. **Ask for clarification only if the invocation is malformed.** Otherwise, run the full audit autonomously.
7. **Run fully autonomously.** This skill must be invoked with the `--dangerously-skip-permissions` flag so Claude Code can execute all MCP tool calls, file writes, and Slack actions without interrupting the user for approval at each step. The full audit pipeline (crawl → analyse → generate XLSX → generate DOCX → create Canvas → post to Slack) must complete end-to-end without manual intervention.
