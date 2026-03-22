---
name: new-cars-report
description: >
  Generate and send the weekly New Auto Organic Traffic report to Slack.
  Fetches GSC clicks and positions for Cars24, Bikes24, TeamBHP New Cars, and
  TeamBHP New Bikes. Asks for Content Pieces Shipped count then posts to the
  aakash-ai-experiment Slack channel. Use when user says "Send New Auto Report",
  "weekly report", or "organic traffic report".
---

# New Cars Weekly Organic Traffic Report

## Overview

Generate the "New Auto – Organic Traffic Update" report and send it to Slack.

## Step-by-Step Process

### Step 1 — Collect User Inputs

Ask the user two questions before fetching any data:

1. **Content Pieces Shipped**: "How many content pieces were shipped this month?"
2. **Report End Date**: "What is the end date for the report? (No format like 14th Mar)"

Wait for both answers before proceeding.

Then calculate all date ranges:

- **Current period**: 1st of the end date's month → end date (user-provided)
  - Example: if end date is 2026-03-17, current period = 2026-03-01 to 2026-03-17
- **Previous same-period**: 1st of previous month → same day-of-month as end date
  - Example: 2026-02-01 to 2026-02-17
- **Previous full month** (Month -1): full calendar month
- **Month -2**: full calendar month
- **Month -3**: full calendar month

### Step 2 — List GSC Properties

Use `mcp__gsc__list_sites` to retrieve all connected Search Console properties. Identify which properties map to:

| Report Label       | Property to find                                      |
|--------------------|-------------------------------------------------------|
| Cars24 – New Cars  | cars24.com property (look for /new-cars/ or new-cars) |
| Bikes 24           | bikes24.com property                                  |
| TeamBHP New Cars   | team-bhp.com property (new cars section)              |
| TeamBHP New Bikes  | team-bhp.com property (new bikes section)             |

If multiple properties exist for the same domain, prefer the `sc-domain:` version.

### Step 3 — Fetch GSC Data

For **each project**, fetch data for all required date ranges using `mcp__gsc__search_analytics`.

Make **two separate API calls** per property per date range:

**Call 1 — Clicks (global, no country filter):**
- `type`: "web"
- No `countryFilter`
- Fetch: **Total Clicks**

**Call 2 — Position (India only):**
- `type`: "web"
- `countryFilter`: "IND"
- Fetch: **Average Position**

- For TeamBHP, filter by URL path prefix: `/new-cars/` for New Cars, `/new-bikes/` for New Bikes (use `dimensionFilterGroups` if supported)

### Step 4 — Ask for Content Pieces Shipped

Ask the user:

> "How many content pieces were shipped this month (current period)?"

Wait for the user's numeric answer before continuing.

### Step 5 — Format the Report

Build the report using **fixed-width plain text tables** (NOT markdown `| --- |` style). These will be wrapped in triple backticks in Slack so columns stay aligned in monospace.

Use this exact format (fill in actual numbers, right-align numeric columns):

```
Organic Traffic (Clicks)

Project              | 1–X Mon   | 1–X PrevM | PrevM Full| Mon-2 Full| Mon-3 Full
---------------------|-----------|-----------|-----------|-----------|----------
Cars24 – New Cars    |    XX,XXX |    XX,XXX |   XXX,XXX |   XXX,XXX |   XXX,XXX
Bikes24              |    XX,XXX |    XX,XXX |    XX,XXX |    XX,XXX |    XX,XXX
TeamBHP New Cars     |    XX,XXX |    XX,XXX |    XX,XXX |    XX,XXX |    XX,XXX
TeamBHP New Bikes    |     X,XXX |     X,XXX |     X,XXX |     X,XXX |       N/A
Total                |   XXX,XXX |   XXX,XXX |   XXX,XXX |   XXX,XXX |   XXX,XXX


Avg Organic Position (India)

Project              | 1–X Mon   | 1–X PrevM | PrevM Full| Mon-2 Full
---------------------|-----------|-----------|-----------|----------
Cars24 – New Cars    |      XX.X |      XX.X |      XX.X |      XX.X
Bikes24              |      XX.X |      XX.X |      XX.X |      XX.X
TeamBHP New Cars     |      XX.X |      XX.X |      XX.X |      XX.X
TeamBHP New Bikes    |      XX.X |      XX.X |      XX.X |      XX.X


Content Pieces Shipped

Period               | 1–X Mon   | PrevM Full| Mon-2 Full| Mon-3 Full
---------------------|-----------|-----------|-----------|----------
Pieces Shipped       |        XX |       XXX |       XXX |        XX
```

Rules:
- Column headers use abbreviated month names: "Mar", "Feb", "Jan", "Dec"
- For current and previous period columns, use format "1–Xth Mon" (e.g., "1–14th Mar")
- Right-align all numeric values within their column width
- Format clicks with comma separators (e.g., 89,189)
- Round positions to 1 decimal place
- Calculate the Total row as sum of all 4 projects
- For Content Pieces Shipped, use these values:
  - Current month = user-provided count
  - Feb (hardcoded) = 104
  - Jan (hardcoded) = 160
  - Dec (hardcoded) = 89

### Step 6 — Write SEO Performance Report Card

Before sending, write a concise SEO performance narrative using the data. 3–5 sentences max, punchy and scannable.

**Structure (follow this order):**
1. **Opening insight** — State the key metric and trend (% change MoM) with the primary finding. If clicks are down but positions are stable, call it a CTR issue, not a penalty. If positions improved alongside clicks, call it a rankings win.
2. **Root cause analysis** — 2–3 factors driving the trend (seasonal events, competitive launches, algorithm changes, content gaps, etc.)
3. **Status update** — Brief reality check on trajectory (on track / behind / ahead)
4. **Mitigating actions** — What's being done: content shipped, technical updates, optimizations rolling out (reference the content pieces count)
5. **Silver linings** — Call out which projects or metrics are actually winning

**Tone:** Casual, data-driven, honest about challenges but optimistic about solutions. Use emojis sparingly (1–2 max).

**Example output:**
```
# SEO Traffic Report — [Month] Performance

* **[Project] surged X% MoM** (X,XXX → X,XXX clicks) — [reason e.g. new content + improved SERP visibility]

* **[Project] dipped X%** despite stable rankings (X.X) — CTR problem, likely from [reason]

* **[Project] flat but rankings dropped X.X** (X.X → X.X) — need [action e.g. title/meta tag optimization]

* **[X content pieces shipped]** in [Month] — [impact e.g. should drive recovery]

* **Overall organic traffic hit X,XXX clicks** — [context e.g. strongest month yet 💪]

* **[Project] performing well** at X.X avg position despite [context]

* **Next actions:** [2-3 specific actions based on data]

---

**Quick takeaway:** [1-sentence summary of overall health and priority fix]. 🚀
```

### Step 7 — Send to Slack

Use `mcp__claude_ai_Slack__slack_search_channels` to find the channel "aakash-ai-experiment".

Then use `mcp__claude_ai_Slack__slack_send_message` to post the formatted report.

Message format:
```
*New Auto – Organic Traffic Update* 📊
_(report period: [start date] to [end date])_

[SEO Performance Report Card from Step 6]

*📋 At a Glance — [1–Xth Mon] vs [1–Xth PrevMon]*
• 🚗 Cars24 New Cars:  X,XXX clicks  ↑X.X% MoM  |  Pos X.X  ↑/↓ X.X
• 🏍️ Bikes24:          X,XXX clicks  ↑X.X% MoM  |  Pos X.X  ↑/↓ X.X
• 🏎️ TeamBHP New Cars: X,XXX clicks  ↑X.X% MoM  |  Pos X.X  ↑/↓ X.X
• 🏍️ TeamBHP Bikes:    X,XXX clicks  ↑X.X% MoM  |  Pos X.X  ↑/↓ X.X
• 📊 Combined:        XX,XXX clicks  ↑/↓X.X% MoM
• 📦 Content shipped: X pieces this month

*📊 Full Data*
```
[paste the full fixed-width tables from Step 5 here — exactly as formatted]
```

_Data sources: Google Search Console | Content Pieces: Manual_
```

**Rules for the At a Glance bullets:**
- Calculate MoM % change by comparing current period vs previous same-period (not full month)
- Use ↑ for increase, ↓ for decrease
- Round % to 1 decimal place (e.g., ↑12.3%)
- For position: lower number = better ranking, so position improving (number going down) = ↑, getting worse = ↓
- Keep each bullet to one line — leadership should be able to skim in 10 seconds
- Align the numbers loosely with spaces so the bullets scan cleanly

### Error Handling

- If a GSC property is not found: note "Property not found" in that row and continue
- If data is unavailable for a date range: use "N/A"
- If Slack channel not found: report the error and display the formatted report in chat for manual copying
- If position data returns 0 or null: use "N/A"
