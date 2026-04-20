# Future-Proofing — Hardened Config & Best Practices

## Hardened Config Template

A production `.seospiderconfig` file is XML. Build it via SF GUI once, then
version control and deploy to servers. Key settings to lock in:

### Core Settings Checklist

```xml
<!-- Essential settings to verify in any production config -->

<!-- Crawl behaviour -->
<crawlAllSubdomains>false</crawlAllSubdomains>
<maxUrls>1000</maxUrls>
<maxCrawlDepth>10</maxCrawlDepth>
<crawlDelay>500</crawlDelay>   <!-- ms; 500ms is polite, safe for Cars24 -->
<threads>5</threads>
<followInternalNofollow>false</followInternalNofollow>
<followExternalNofollow>false</followExternalNofollow>
<crawlExternalLinks>false</crawlExternalLinks>

<!-- User agent -->
<userAgent>Mozilla/5.0 (compatible; ScreamingFrog/21.0; +https://www.cars24.com)</userAgent>

<!-- JS rendering -->
<useRenderer>true</useRenderer>
<rendererTimeout>10000</rendererTimeout>   <!-- 10s per page -->

<!-- Storage -->
<storageType>DATABASE</storageType>   <!-- DATABASE for large crawls, RAM for small -->
```

---

## The Config Version Control System

```
/etc/screaming-frog/
├── cars24-production.seospiderconfig     # Live config
├── cars24-js-extraction.seospiderconfig  # With JS + custom extraction
├── cars24-gsc.seospiderconfig            # With GSC integration
├── bikes24-production.seospiderconfig    # Bikes24 config
├── teambhp-production.seospiderconfig    # TeamBHP config
└── README.md                             # What each config does
```

```bash
# Git-track all configs
cd /etc/screaming-frog
git init
git add *.seospiderconfig README.md
git commit -m "Initial SF configs"

# After any config change
git diff cars24-production.seospiderconfig
git add cars24-production.seospiderconfig
git commit -m "Add custom extraction for schema JSON-LD"
```

---

## Future-Proof Architecture

### Recommended Directory Structure

```
/data/seo-audits/
├── configs/                          # Versioned SF configs
│   └── (symlinks to /etc/screaming-frog/)
├── cars24-new-cars/
│   ├── 2025-01-15/                   # One folder per run
│   │   ├── internal_html.csv
│   │   ├── *.csv
│   │   ├── crawl.log
│   │   └── audit.crawl
│   └── latest -> 2025-01-15/         # Symlink to latest
├── bikes24/
│   └── latest -> .../
├── teambhp/
│   └── latest -> .../
└── logs/
    └── sf-audit-YYYY-MM-DD.log
```

```bash
# After each crawl, update symlink
ln -sfn "$OUTPUT_DIR" /data/seo-audits/cars24-new-cars/latest
```

---

## 10 Additional Improvements for Future-Proofing

### 1. Delta Comparison (Week-on-Week)

```python
#!/usr/bin/env python3
# /usr/local/bin/sf-delta.py — Compare this week's crawl vs last week

import pandas as pd
import sys
from pathlib import Path

THIS_WEEK = Path(sys.argv[1])
LAST_WEEK = Path(sys.argv[2])

for csv_name in ['internal_html.csv', 'response_codes_all.csv', 'h1_all.csv']:
    try:
        curr = pd.read_csv(THIS_WEEK / csv_name)
        prev = pd.read_csv(LAST_WEEK / csv_name)

        curr_urls = set(curr['Address'])
        prev_urls = set(prev['Address'])

        new_urls = curr_urls - prev_urls
        lost_urls = prev_urls - curr_urls

        print(f"\n=== {csv_name} ===")
        print(f"  Current: {len(curr_urls)} URLs")
        print(f"  Previous: {len(prev_urls)} URLs")
        print(f"  New URLs: {len(new_urls)}")
        print(f"  Lost URLs: {len(lost_urls)}")

        if lost_urls:
            print("  Lost URLs:")
            for url in list(lost_urls)[:10]:
                print(f"    - {url}")
    except FileNotFoundError:
        print(f"  ⚠  {csv_name} not found in one of the folders")
```

### 2. Health Score Tracker

```python
#!/usr/bin/env python3
# /usr/local/bin/sf-score.py — Generate SEO health score from crawl output

import pandas as pd
from pathlib import Path
import json, sys
from datetime import datetime

OUTPUT_DIR = Path(sys.argv[1])
results = {}

def safe_read(fname):
    f = OUTPUT_DIR / fname
    return pd.read_csv(f) if f.exists() else None

# 1. Response code health
df = safe_read('response_codes_all.csv')
if df is not None:
    total = len(df)
    ok = len(df[df.iloc[:,2].astype(str).str.startswith('2')])
    results['response_health'] = round(ok/total*100, 1) if total else 0

# 2. Title coverage
df = safe_read('page_titles_all.csv')
if df is not None:
    total = len(df)
    missing = len(df[df.iloc[:,1].isna() | (df.iloc[:,1] == '')])
    results['title_coverage'] = round((total-missing)/total*100, 1) if total else 0

# 3. H1 coverage
df = safe_read('h1_all.csv')
if df is not None:
    total = len(df)
    missing = len(df[df.iloc[:,1].isna() | (df.iloc[:,1] == '')])
    results['h1_coverage'] = round((total-missing)/total*100, 1) if total else 0

# 4. Alt text coverage
df = safe_read('images_all.csv')
if df is not None:
    total = len(df)
    missing_df = safe_read('images_missing_alt_text.csv')
    missing = len(missing_df) if missing_df is not None else 0
    results['alt_text_coverage'] = round((total-missing)/total*100, 1) if total else 0

# Overall score
scores = list(results.values())
overall = round(sum(scores)/len(scores), 1) if scores else 0

output = {
    'date': datetime.now().isoformat(),
    'overall_score': overall,
    'breakdown': results
}

print(json.dumps(output, indent=2))

# Append to history
history_file = OUTPUT_DIR.parent / 'score-history.jsonl'
with open(history_file, 'a') as f:
    f.write(json.dumps(output) + '\n')

print(f"\nScore history: {history_file}")
```

### 3. Parallel Multi-Property Crawls

```bash
#!/bin/bash
# Run all 4 properties in parallel (different configs, non-overlapping)

DATE=$(date +%Y%m%d)
LOG_DIR="/data/seo-audits/logs"

run_crawl() {
  local property="$1"
  local url="$2"
  local config="$3"
  local max_urls="$4"

  DISPLAY=:99 ScreamingFrogSEOSpider \
    --headless \
    --config "$config" \
    --crawl "$url" \
    --max-urls "$max_urls" \
    --output-folder "/data/seo-audits/$property/$DATE" \
    --overwrite \
    >> "$LOG_DIR/$property-$DATE.log" 2>&1
  echo "$(date): $property done (exit $?)"
}

# Run in parallel using & and wait
run_crawl "cars24-new-cars"   "https://www.cars24.com/new-cars/"   "/etc/sf/cars24.seospiderconfig"        1000 &
run_crawl "bikes24"           "https://www.bikes24.com/"           "/etc/sf/bikes24.seospiderconfig"        500  &
run_crawl "teambhp-new-cars"  "https://www.team-bhp.com/new-cars/" "/etc/sf/teambhp.seospiderconfig"        500  &
run_crawl "teambhp-new-bikes" "https://www.team-bhp.com/new-bikes/" "/etc/sf/teambhp-bikes.seospiderconfig" 300  &

wait  # Wait for all background jobs
echo "All crawls complete"
```

### 4. GSC Orphan Detection

```python
#!/usr/bin/env python3
# Finds URLs in GSC with impressions but NOT in SF crawl output
# (orphaned pages — indexed but not internally linked)

import pandas as pd

# Load SF crawl output
sf_urls = set(pd.read_csv('/data/seo-audits/cars24-new-cars/latest/internal_html.csv')['Address'])

# Load GSC export (from SF output if GSC integration active)
gsc_df = pd.read_csv('/data/seo-audits/cars24-new-cars/latest/internal_html.csv')
gsc_cols = [c for c in gsc_df.columns if 'impression' in c.lower()]

if gsc_cols:
    gsc_urls = set(gsc_df[gsc_df[gsc_cols[0]] > 0]['Address'])
    orphans = gsc_urls - sf_urls
    print(f"Orphaned URLs (in GSC but not crawled): {len(orphans)}")
    for url in sorted(orphans)[:20]:
        print(f"  {url}")
```

### 5. SF Version Auto-Update Check

```bash
#!/bin/bash
CURRENT=$(ScreamingFrogSEOSpider --version 2>&1 | grep -oP '\d+\.\d+')
LATEST=$(curl -s "https://www.screamingfrog.co.uk/seo-spider/release-notes/" | \
  grep -oP 'Version \K[\d.]+' | head -1)

if [ "$CURRENT" != "$LATEST" ]; then
  echo "⚠  SF update available: $CURRENT → $LATEST"
else
  echo "✓ SF is up to date: $CURRENT"
fi
```

### 6. Slack Notification with Summary Table

```python
#!/usr/bin/env python3
import pandas as pd, requests, json, sys
from pathlib import Path

OUTPUT_DIR = Path(sys.argv[1])
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK"

def count_rows(fname):
    f = OUTPUT_DIR / fname
    if not f.exists(): return 0
    return max(0, len(pd.read_csv(f)) - 1)

metrics = {
    "Pages crawled":    count_rows("internal_html.csv"),
    "4xx errors":       count_rows("response_codes_client_error_4xx.csv"),
    "5xx errors":       count_rows("response_codes_server_error_5xx.csv"),
    "Missing H1":       count_rows("h1_missing.csv"),
    "Duplicate titles": count_rows("page_titles_duplicate.csv"),
    "Missing alt text": count_rows("images_missing_alt_text.csv"),
}

lines = ["*Cars24 New Cars SEO Audit Complete*", ""]
for k, v in metrics.items():
    icon = "✓" if v == 0 or k == "Pages crawled" else ("✗" if v > 10 else "⚠")
    lines.append(f"{icon} {k}: *{v}*")

requests.post(SLACK_WEBHOOK, json={"text": "\n".join(lines)})
print("Slack notified")
```

### 7. Robots.txt Monitoring

```bash
CURRENT_ROBOTS=$(curl -s https://www.cars24.com/robots.txt | md5sum)
STORED_ROBOTS=$(cat /data/seo-audits/.robots-hash 2>/dev/null || echo "")

if [ "$CURRENT_ROBOTS" != "$STORED_ROBOTS" ]; then
  echo "⚠  robots.txt CHANGED — verify no important paths blocked"
  curl -s https://www.cars24.com/robots.txt | diff /data/seo-audits/.robots.txt - || true
  curl -s https://www.cars24.com/robots.txt > /data/seo-audits/.robots.txt
fi
echo "$CURRENT_ROBOTS" > /data/seo-audits/.robots-hash
```

### 8. Storage Management

```bash
# Keep only last 30 days of crawl data per property
find /data/seo-audits/cars24-new-cars/ -maxdepth 1 -type d -mtime +30 | while read dir; do
  echo "Removing old crawl: $dir"
  rm -rf "$dir"
done
```

### 9. Claude Post-Processing Integration

```bash
#!/bin/bash
OUTPUT_DIR="$1"
ISSUES_SUMMARY=$(python3 /usr/local/bin/sf-score.py "$OUTPUT_DIR")

curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{
    \"model\": \"claude-sonnet-4-6\",
    \"max_tokens\": 2000,
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"Analyze this Cars24 SEO audit and list top 5 priority fixes:\n\n$ISSUES_SUMMARY\"
    }]
  }" | jq -r '.content[0].text' > "$OUTPUT_DIR/ai-analysis.md"

echo "AI analysis written to $OUTPUT_DIR/ai-analysis.md"
```

### 10. Health Dashboard (Simple HTML)

```python
#!/usr/bin/env python3
import json
from pathlib import Path

history_file = Path('/data/seo-audits/score-history.jsonl')
if not history_file.exists():
    print("No score history yet")
    exit()

scores = [json.loads(l) for l in history_file.read_text().strip().split('\n')]
scores.sort(key=lambda x: x['date'])

rows = ""
for s in scores[-30:]:
    date = s['date'][:10]
    score = s['overall_score']
    color = "green" if score > 90 else "orange" if score > 70 else "red"
    rows += f"<tr><td>{date}</td><td style='color:{color}'>{score}</td></tr>\n"

html = f"""<html><body>
<h1>Cars24 SEO Health Score</h1>
<table border=1>
<tr><th>Date</th><th>Score</th></tr>
{rows}
</table></body></html>"""

Path('/data/seo-audits/dashboard.html').write_text(html)
print("Dashboard: /data/seo-audits/dashboard.html")
```
